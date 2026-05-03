"""
⚠️  DEPRECADO — Este módulo está deprecado desde 2026-04-XX.

Usar en su lugar:
  - app.services.odoo_database_manager.create_tenant_from_template()  (SQL fast-path)
  - app.services.odoo_database_manager.provision_tenant()             (HTTP fallback)
  - app.routes.onboarding._provision_tenant_from_checkout()           (orquestador completo)

Las funciones provision_tenant() y create_odoo_database() de este módulo
ya no se invocan desde onboarding.py. La función repair_missing_deployments()
sigue en uso temporal desde provisioning.py y se migrará en una fase posterior.
"""
import warnings
warnings.warn(
    "odoo_provisioner está deprecado. "
    "Usar odoo_database_manager.create_tenant_from_template() en su lugar.",
    DeprecationWarning,
    stacklevel=2,
)

import subprocess
import logging
import os
import re
import shlex
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy import text

logger = logging.getLogger(__name__)


class ProvisioningError(Exception):
    """Error en provisioning de tenant"""
    pass


class ValidationError(Exception):
    """Error de validación de datos"""
    pass


def _validate_subdomain(subdomain: str) -> None:
    """
    Valida que el subdomain sea válido
    - Solo alfanuméricos y guiones
    - Máximo 63 caracteres
    - No puede empezar o terminar con guión
    """
    if not subdomain or not isinstance(subdomain, str):
        raise ValidationError("Subdomain debe ser un string no vacío")
    
    if len(subdomain) > 63:
        raise ValidationError("Subdomain máximo 63 caracteres")
    
    if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', subdomain.lower()):
        raise ValidationError("Subdomain solo permite alfanuméricos y guiones. No puede empezar/terminar con guión")
    
    if subdomain.lower() in ['admin', 'api', 'www', 'mail', 'ftp', 'ns', 'root']:
        raise ValidationError(f"Subdomain '{subdomain}' está reservado")


def _validate_email(email: str) -> None:
    """Valida formato de email"""
    if not email or not isinstance(email, str):
        raise ValidationError("Email debe ser un string no vacío")
    
    if len(email) > 254:
        raise ValidationError("Email muy largo (máximo 254 caracteres)")
    
    # Rechazar puntos consecutivos, inicio/fin con punto en parte local
    local_part = email.split('@')[0] if '@' in email else email
    if '..' in local_part or local_part.startswith('.') or local_part.endswith('.'):
        raise ValidationError(f"Email inválido: {email}")
    
    if not re.match(r'^[a-zA-Z0-9_%+-]+(\.[a-zA-Z0-9_%+-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$', email):
        raise ValidationError(f"Email inválido: {email}")


def _validate_company_name(company_name: str) -> None:
    """Valida nombre de empresa"""
    if not company_name or not isinstance(company_name, str):
        raise ValidationError("Company name debe ser un string no vacío")
    
    if len(company_name) < 2:
        raise ValidationError("Company name mínimo 2 caracteres")
    
    if len(company_name) > 255:
        raise ValidationError("Company name máximo 255 caracteres")


def _validate_ip_address(ip: str) -> None:
    """Valida formato de dirección IP"""
    if not ip or not isinstance(ip, str):
        raise ValidationError("IP address debe ser un string no vacío")
    
    # IPv4
    ipv4_pattern = r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(ipv4_pattern, ip):
        octets = ip.split('.')
        if all(0 <= int(octet) <= 255 for octet in octets):
            return
    
    # IPv6 básico
    if ':' in ip and re.match(r'^[a-fA-F0-9:]+$', ip):
        return
    
    raise ValidationError(f"IP address inválida: {ip}")


def _validate_port(port: int) -> None:
    """Valida número de puerto"""
    if not isinstance(port, int):
        raise ValidationError("Port debe ser un entero")
    
    if port < 1 or port > 65535:
        raise ValidationError(f"Port debe estar entre 1 y 65535, recibido: {port}")


def _get_config_from_env() -> Dict[str, Any]:
    """
    Obtiene configuración desde variables de entorno
    Lanza ProvisioningError si faltan variables requeridas
    """
    config = {
        "lxc_container_id": os.getenv("LXC_CONTAINER_ID"),
        "domain": os.getenv("DOMAIN"),
        "create_tenant_script": os.getenv("CREATE_TENANT_SCRIPT"),
        "default_container_ip": os.getenv("DEFAULT_CONTAINER_IP"),
        "default_local_port": os.getenv("DEFAULT_LOCAL_PORT"),
        "enable_cloudflare": os.getenv("ENABLE_CLOUDFLARE", "true").lower() == "true"
    }
    
    # Validar configuración requerida
    if not config["lxc_container_id"]:
        raise ProvisioningError("Variable LXC_CONTAINER_ID no configurada en .env")
    
    if not config["domain"]:
        raise ProvisioningError("Variable DOMAIN no configurada en .env")
    
    if not config["create_tenant_script"]:
        raise ProvisioningError("Variable CREATE_TENANT_SCRIPT no configurada en .env")
    
    if not config["default_container_ip"]:
        raise ProvisioningError("Variable DEFAULT_CONTAINER_IP no configurada en .env")
    
    if not config["default_local_port"]:
        raise ProvisioningError("Variable DEFAULT_LOCAL_PORT no configurada en .env")
    
    # Validar puerto
    try:
        port = int(config["default_local_port"])
        _validate_port(port)
        config["default_local_port"] = port
    except (ValueError, ValidationError) as e:
        raise ProvisioningError(f"DEFAULT_LOCAL_PORT inválido: {e}")
    
    # Validar IP
    try:
        _validate_ip_address(config["default_container_ip"])
    except ValidationError as e:
        raise ProvisioningError(f"DEFAULT_CONTAINER_IP inválido: {e}")
    
    return config


async def provision_tenant(
    subdomain: str,
    admin_email: str,
    company_name: str,
    subscription_id: Optional[int] = None,
    container_ip: Optional[str] = None,
    local_port: Optional[int] = None,
    create_tunnel: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Provision a new Odoo tenant on LXC container with Cloudflare tunnel
    
    Args:
        subdomain: Subdomain para el tenant (ej: "acme")
        admin_email: Email del admin del tenant
        company_name: Nombre de la empresa/organización
        subscription_id: ID de suscripción para actualizar estado
        container_ip: IP del contenedor LXC (None = usar DEFAULT_CONTAINER_IP)
        local_port: Puerto local de Odoo (None = usar DEFAULT_LOCAL_PORT)
        create_tunnel: Crear Cloudflare tunnel (None = usar ENABLE_CLOUDFLARE)
    
    Returns:
        Dict con status, url, database name, tunnel info
    
    Raises:
        ValidationError: Si los datos de entrada son inválidos
        ProvisioningError: Si falla el provisioning
    """
    try:
        # 1. Obtener configuración desde .env
        config = _get_config_from_env()
        
        # 2. Usar defaults si no se proporcionan valores
        if container_ip is None:
            container_ip = config["default_container_ip"]
        if local_port is None:
            local_port = config["default_local_port"]
        if create_tunnel is None:
            create_tunnel = config["enable_cloudflare"]
        
        # 3. Validar todos los parámetros
        logger.info(f"Validando parámetros para tenant: {subdomain}")
        _validate_subdomain(subdomain)
        _validate_email(admin_email)
        _validate_company_name(company_name)
        _validate_ip_address(container_ip)
        _validate_port(local_port)
        
        if not isinstance(create_tunnel, bool):
            raise ValidationError("create_tunnel debe ser boolean")
        
        if subscription_id is not None and not isinstance(subscription_id, int):
            raise ValidationError("subscription_id debe ser un entero")
        
        logger.info(f"✅ Validación completada para {subdomain}")
        
        # 4. Obtener valores de configuración
        lxc_id = config["lxc_container_id"]
        domain = config["domain"]
        script_path = config["create_tenant_script"]
        
        # 5. Ejecutar provisioning script
        script_cmd = (
            f"cd /root/Cloudflare && {shlex.quote(script_path)} {shlex.quote(subdomain)} "
            f"--without-demo {shlex.quote(container_ip)} {int(local_port)}"
        )
        cmd = ["pct", "exec", str(lxc_id), "--", "bash", "-lc", script_cmd]
        
        logger.info(f"📦 Aprovisionando tenant: {subdomain} on {container_ip}:{local_port}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Fallo provisioning: {result.stderr}")
            raise ProvisioningError(f"Script de provisioning falló: {result.stderr}")
        
        hostname = f"{subdomain}.{domain}"
        url = f"https://{hostname}"
        
        # 6. Crear Cloudflare tunnel si está habilitado
        tunnel_info = None
        if create_tunnel:
            logger.info(f"🌐 Creando Cloudflare tunnel para {hostname}")
            tunnel_info = await create_cloudflare_tunnel(
                subdomain=subdomain,
                container_ip=container_ip,
                local_port=local_port,
                domain=domain
            )
            if not tunnel_info.get("success"):
                logger.warning(f"⚠️  Fallo crear tunnel (continuando): {tunnel_info.get('error')}")
        else:
            logger.info("⏭️  Cloudflare tunnel deshabilitado, saltando")
        
        # 7. Actualizar suscripción + crear TenantDeployment en BD
        deployment_id = None
        if subscription_id:
            try:
                from ..models.database import (
                    SessionLocal, Subscription, SubscriptionStatus,
                    TenantDeployment, LXCContainer, PlanType
                )
                db = SessionLocal()
                
                subscription = db.query(Subscription).filter_by(id=subscription_id).first()
                if subscription:
                    subscription.status = SubscriptionStatus.active
                    subscription.tenant_provisioned = True
                    subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    
                    # Determinar plan_type desde plan_name de la suscripción
                    plan_map = {
                        "basic": PlanType.basic,
                        "pro": PlanType.pro,
                        "enterprise": PlanType.enterprise,
                    }
                    plan_name = getattr(subscription, "plan_name", "basic") or "basic"
                    plan_type = plan_map.get(plan_name.split("_")[0], PlanType.basic)
                    
                    # Buscar container por IP (o usar el primero disponible)
                    container = db.query(LXCContainer).filter(
                        LXCContainer.ip_address == container_ip
                    ).first()
                    if not container:
                        container = db.query(LXCContainer).first()
                    
                    if container:
                        # Evitar duplicados: verificar si ya existe deployment para esta suscripción
                        existing = db.query(TenantDeployment).filter_by(
                            subscription_id=subscription_id
                        ).first()
                        
                        if not existing:
                            cf_tunnel_id = os.getenv("CLOUDFLARE_TUNNEL_ID", "")
                            actual_tunnel_id = (
                                tunnel_info.get("tunnel_id", cf_tunnel_id)
                                if tunnel_info and tunnel_info.get("success")
                                else cf_tunnel_id
                            )
                            
                            deployment = TenantDeployment(
                                subscription_id=subscription_id,
                                container_id=container.id,
                                customer_id=subscription.customer_id,
                                subdomain=subdomain,
                                database_name=subdomain,
                                odoo_port=local_port if isinstance(local_port, int) else 8069,
                                tunnel_url=f"https://{subdomain}.{domain}",
                                direct_url=f"http://{container_ip}:{local_port}",
                                tunnel_active=bool(actual_tunnel_id),
                                tunnel_id=actual_tunnel_id or None,
                                plan_type=plan_type,
                                deployed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            )
                            db.add(deployment)
                            db.flush()
                            deployment_id = deployment.id
                            logger.info(
                                f"✅ TenantDeployment #{deployment_id} creado: "
                                f"{subdomain} → container {container.id}, "
                                f"customer {subscription.customer_id}"
                            )
                        else:
                            deployment_id = existing.id
                            logger.info(f"ℹ️  TenantDeployment ya existe (id={existing.id}) para sub {subscription_id}")
                    else:
                        logger.warning("⚠️  No hay LXCContainer registrado — TenantDeployment NO creado")
                    
                    db.commit()
                    logger.info(f"✅ Suscripción {subscription_id} actualizada a active")
                else:
                    logger.warning(f"⚠️  Suscripción {subscription_id} no encontrada")
                
                db.close()
            except Exception as db_error:
                logger.error(f"❌ Error actualizando suscripción/deployment: {db_error}")
                # No fallar el provisioning si falla la actualización de BD
        
        # 8. Preparar respuesta
        result_data = {
            "success": True,
            "database": subdomain,
            "hostname": hostname,
            "url": url,
            "container_ip": container_ip,
            "local_port": local_port,
            "subscription_id": subscription_id,
            "deployment_id": deployment_id,
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }
        
        if tunnel_info and tunnel_info.get("success"):
            result_data["tunnel"] = {
                "tunnel_id": tunnel_info.get("tunnel_id"),
                "tunnel_name": tunnel_info.get("tunnel_name"),
                "domain": tunnel_info.get("domain"),
                "status": "active"
            }
        
        logger.info(f"✅ Tenant aprovisionado exitosamente: {url}")
        return result_data
            
    except ValidationError as ve:
        logger.error(f"❌ Error de validación: {ve}")
        return {
            "success": False,
            "error_type": "validation_error",
            "error": str(ve)
        }
    except ProvisioningError as pe:
        logger.error(f"❌ Error de provisioning: {pe}")
        return {
            "success": False,
            "error_type": "provisioning_error",
            "error": str(pe)
        }
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout provisioning tenant {subdomain}")
        return {
            "success": False,
            "error_type": "timeout_error",
            "error": "Provisioning tardó más de 5 minutos"
        }
    except Exception as e:
        logger.exception(f"❌ Error no esperado en provision_tenant: {str(e)}")
        return {
            "success": False,
            "error_type": "unknown_error",
            "error": str(e)
        }


async def create_cloudflare_tunnel(
    subdomain: str,
    container_ip: str,
    local_port: int,
    domain: str
) -> Dict[str, Any]:
    """
    Crea un Cloudflare tunnel para el tenant
    
    Args:
        subdomain: Subdominio del tenant
        container_ip: IP del contenedor
        local_port: Puerto local
        domain: Dominio base
    
    Returns:
        Dict con status del tunnel
    """
    try:
        from .cloudflare_manager import CloudflareManager
        from ..config import CLOUDFLARE_TUNNEL_ID

        # Crear registro DNS CNAME apuntando al tunnel principal
        tunnel_id = CLOUDFLARE_TUNNEL_ID
        if not tunnel_id:
            return {"success": False, "error": "CLOUDFLARE_TUNNEL_ID no configurado"}

        result = await CloudflareManager.create_dns_record(
            subdomain=subdomain,
            tunnel_id=tunnel_id,
            domain=domain,
        )
        
        return result
        
    except ImportError:
        logger.warning("❌ CloudflareManager no disponible - saltando tunnel")
        return {"success": False, "error": "CloudflareManager no disponible"}
    except Exception as e:
        logger.error(f"❌ Error creando tunnel Cloudflare: {e}")
        return {"success": False, "error": str(e)}


async def check_tenant_exists(subdomain: str) -> bool:
    """
    Verifica si un tenant ya existe
    
    Args:
        subdomain: Subdominio a verificar
    
    Returns:
        True si existe, False caso contrario
    """
    try:
        # Validar subdomain
        _validate_subdomain(subdomain)
        
        config = _get_config_from_env()
        lxc_id = config["lxc_container_id"]
        
        cmd = [
            "pct", "exec", str(lxc_id), "--",
            "sudo", "-u", "postgres", "psql", "-lqt",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        exists = result.returncode == 0 and any(line.split("|", 1)[0].strip() == subdomain for line in result.stdout.splitlines())
        logger.info(f"Tenant {subdomain} exists: {exists}")
        return exists
        
    except ValidationError as ve:
        logger.error(f"Error validando subdomain: {ve}")
        return False
    except ProvisioningError as pe:
        logger.error(f"Error de configuración: {pe}")
        return False
    except Exception as e:
        logger.error(f"Error checando tenant: {str(e)}")
        return False


async def delete_tenant(
    subdomain: str,
    delete_tunnel: bool = True
) -> Dict[str, Any]:
    """
    Elimina un tenant (base de datos y tunnel)
    
    Args:
        subdomain: Subdominio del tenant
        delete_tunnel: Si se debe eliminar el tunnel de Cloudflare
    
    Returns:
        Dict con status de eliminación
    
    Raises:
        ValidationError: Si subdomain es inválido
        ProvisioningError: Si falla la eliminación
    """
    try:
        # Validar subdomain
        _validate_subdomain(subdomain)
        
        config = _get_config_from_env()
        lxc_id = config["lxc_container_id"]
        
        logger.info(f"🗑️  Eliminando tenant: {subdomain}")
        
        # 1. Eliminar base de datos
        sql = f'DROP DATABASE IF EXISTS "{subdomain}" WITH (FORCE);'
        cmd = [
            "pct", "exec", str(lxc_id), "--",
            "sudo", "-u", "postgres", "psql", "-c", sql,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"❌ Error eliminando BD: {result.stderr}")
            raise ProvisioningError(f"Error eliminando BD: {result.stderr}")
        
        logger.info(f"✅ Base de datos eliminada: {subdomain}")
        
        # 2. Eliminar Cloudflare tunnel si está habilitado
        if delete_tunnel:
            try:
                from .cloudflare_manager import CloudflareManager
                tunnel_name = f"{subdomain}-tunnel"
                await CloudflareManager.delete_tunnel(tunnel_name)
                logger.info(f"✅ Tunnel eliminado: {tunnel_name}")
            except Exception as e:
                logger.warning(f"⚠️  Error eliminando tunnel (continuando): {e}")
        
        # 3. Eliminar TenantDeployment de la BD
        try:
            from ..models.database import SessionLocal, TenantDeployment
            db = SessionLocal()
            deployment = db.query(TenantDeployment).filter_by(subdomain=subdomain).first()
            if deployment:
                db.delete(deployment)
                db.commit()
                logger.info(f"✅ TenantDeployment eliminado: {subdomain}")
            db.close()
        except Exception as e:
            logger.warning(f"⚠️  Error eliminando TenantDeployment: {e}")
        
        logger.info(f"✅ Tenant eliminado completamente: {subdomain}")
        return {
            "success": True,
            "message": f"Tenant {subdomain} eliminado exitosamente",
            "deleted_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }
        
    except ValidationError as ve:
        logger.error(f"❌ Error de validación: {ve}")
        return {
            "success": False,
            "error_type": "validation_error",
            "error": str(ve)
        }
    except ProvisioningError as pe:
        logger.error(f"❌ Error de provisioning: {pe}")
        return {
            "success": False,
            "error_type": "provisioning_error",
            "error": str(pe)
        }
    except Exception as e:
        logger.exception(f"❌ Error eliminando tenant: {str(e)}")
        return {
            "success": False,
            "error_type": "unknown_error",
            "error": str(e)
        }


async def repair_missing_deployments() -> Dict[str, Any]:
    """
    Busca suscripciones con tenant_provisioned=True que NO tienen TenantDeployment
    y las crea automáticamente usando los datos del customer y la infraestructura existente.
    
    Útil para reparar el estado después de migraciones o si provision_tenant() no creó el deployment.
    
    Returns:
        Dict con lista de deployments creados/errores
    """
    from ..models.database import (
        SessionLocal, Subscription, Customer, TenantDeployment,
        LXCContainer, PlanType
    )
    
    created = []
    errors = []
    
    try:
        db = SessionLocal()
        
        # Buscar suscripciones provisioned sin deployment
        subs_without_deployment = (
            db.query(Subscription)
            .outerjoin(
                TenantDeployment,
                TenantDeployment.subscription_id == Subscription.id
            )
            .filter(
                Subscription.tenant_provisioned == True,
                TenantDeployment.id == None
            )
            .all()
        )
        
        if not subs_without_deployment:
            db.close()
            return {"success": True, "message": "No hay deployments faltantes", "created": [], "errors": []}
        
        # Buscar container por defecto
        container = db.query(LXCContainer).first()
        if not container:
            db.close()
            return {
                "success": False,
                "error": "No hay LXCContainer registrado en la BD",
                "created": [],
                "errors": ["No LXCContainer found"]
            }
        
        cf_tunnel_id = os.getenv("CLOUDFLARE_TUNNEL_ID", "")
        domain = os.getenv("ODOO_BASE_DOMAIN", "sajet.us")
        
        plan_map = {
            "basic": PlanType.basic,
            "pro": PlanType.pro,
            "enterprise": PlanType.enterprise,
        }
        
        for sub in subs_without_deployment:
            try:
                customer = db.query(Customer).filter_by(id=sub.customer_id).first()
                if not customer or not customer.subdomain:
                    errors.append(f"Sub {sub.id}: customer {sub.customer_id} sin subdomain")
                    continue
                
                plan_name = getattr(sub, "plan_name", "basic") or "basic"
                plan_type = plan_map.get(plan_name.split("_")[0], PlanType.basic)
                
                deployment = TenantDeployment(
                    subscription_id=sub.id,
                    container_id=container.id,
                    customer_id=sub.customer_id,
                    subdomain=customer.subdomain,
                    database_name=customer.subdomain,
                    odoo_port=8069,
                    tunnel_url=f"https://{customer.subdomain}.{domain}",
                    direct_url=f"http://{container.ip_address}:{8069}",
                    tunnel_active=bool(cf_tunnel_id),
                    tunnel_id=cf_tunnel_id or None,
                    plan_type=plan_type,
                    deployed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                db.add(deployment)
                db.flush()
                
                created.append({
                    "deployment_id": deployment.id,
                    "subdomain": customer.subdomain,
                    "subscription_id": sub.id,
                    "customer_id": sub.customer_id,
                })
                logger.info(
                    f"🔧 Repaired: TenantDeployment #{deployment.id} "
                    f"for {customer.subdomain} (sub {sub.id})"
                )
            except Exception as e:
                errors.append(f"Sub {sub.id}: {str(e)}")
                logger.error(f"❌ Error reparando sub {sub.id}: {e}")
        
        db.commit()
        db.close()
        
        return {
            "success": True,
            "message": f"Reparados {len(created)} deployments, {len(errors)} errores",
            "created": created,
            "errors": errors,
        }
        
    except Exception as e:
        logger.exception(f"❌ Error en repair_missing_deployments: {e}")
        return {
            "success": False,
            "error": str(e),
            "created": created,
            "errors": errors,
        }
