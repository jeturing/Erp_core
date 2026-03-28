"""
Domain Manager Service
Gestiona dominios personalizados de clientes, integración con Cloudflare y configuración de tunnels.

Flujo:
1. Cliente registra dominio externo (www.impulse-max.com)
2. Sistema lo vincula al subdominio SAJET del tenant (ej: techeels.sajet.us)
3. Sistema crea/asegura el CNAME interno en Cloudflare para el subdominio SAJET
4. Cliente configura su dominio externo hacia la IP pública de PCT160
5. Sistema verifica y activa el dominio
"""

import re
import secrets
import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..config import get_runtime_setting
from ..models.database import CustomDomain, Customer, TenantDeployment, DomainVerificationStatus
from .nginx_domain_configurator import NginxDomainConfigurator
from .odoo_website_configurator import OdooWebsiteConfigurator

logger = logging.getLogger("domain_manager")


CF_API_BASE = "https://api.cloudflare.com/client/v4"

# Lista negra de subdominios reservados
RESERVED_SUBDOMAINS = {
    "admin", "api", "www", "mail", "ftp", "smtp", "pop", "imap",
    "ns1", "ns2", "dns", "mx", "webmail", "cpanel", "whm",
    "blog", "shop", "store", "app", "dashboard", "portal",
    "secure", "ssl", "cdn", "static", "assets", "media",
    "dev", "staging", "test", "demo", "beta", "alpha",
    "support", "help", "docs", "status", "health",
    "sajet", "jeturing", "techeels", "odoo", "erp"
}


def _effective_target_node_ip(node_ip: Optional[str]) -> str:
    """Normaliza placeholders locales hacia la IP real del nodo Odoo."""
    value = (node_ip or "").strip()
    if not value or value.lower() in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return get_runtime_setting("ODOO_PRIMARY_IP", "")
    return value


def _cf_api_token() -> str:
    return get_runtime_setting("CLOUDFLARE_API_TOKEN", "")


def _cf_zone_id() -> str:
    return get_runtime_setting("CLOUDFLARE_ZONE_ID", "4a83b88793ac3688486ace69b6ae80f9")


def _cf_tunnel_id() -> str:
    return get_runtime_setting("CLOUDFLARE_TUNNEL_ID", "")


def _cf_tunnel_name() -> str:
    return get_runtime_setting("CLOUDFLARE_TUNNEL_NAME", "tcs-sajet-tunnel")


def _public_ip() -> str:
    return get_runtime_setting("ERP_CORE_PUBLIC_IP", "208.115.125.29")


class DomainManager:
    """Gestor de dominios personalizados"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cf_headers = {
            "Authorization": f"Bearer {_cf_api_token()}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _build_external_dns_instructions(external_domain: str) -> Dict[str, str]:
        """Instrucciones correctas para dominios externos: A record al frontend público."""
        return {
            "step1": (
                "Configure un registro A en el DNS publico del dominio. "
                "No use CNAME hacia *.sajet.us ni hacia *.cfargotunnel.com:"
            ),
            "record_type": "A",
            "record_name": external_domain,
            "record_value": _public_ip(),
            "step2": (
                "Luego verifique la propagacion DNS. "
                "Si su proveedor usa nombres relativos, use @ para el dominio raiz "
                "o el host correspondiente."
            ),
        }
    
    # ==================== CRUD Operations ====================
    
    def create_domain(
        self,
        external_domain: str,
        customer_id: int,
        tenant_deployment_id: Optional[int] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Registra un nuevo dominio personalizado.
        
        Args:
            external_domain: Dominio del cliente (ej: www.impulse-max.com)
            customer_id: ID del cliente
            tenant_deployment_id: ID del deployment (opcional)
            created_by: Usuario que crea el dominio
            
        Returns:
            Dict con información del dominio creado
        """
        # Normalizar dominio
        external_domain = self._normalize_domain(external_domain)
        
        # Validar dominio
        validation = self._validate_domain(external_domain)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        # Verificar que el cliente existe
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "error": "Cliente no encontrado"}
        
        # Verificar que el dominio no existe
        existing = self.db.query(CustomDomain).filter(
            CustomDomain.external_domain == external_domain
        ).first()
        if existing:
            return {"success": False, "error": "El dominio ya está registrado"}
        
        # El dominio externo debe quedar vinculado al subdominio SAJET real
        # del cliente/tenant, no a un alias derivado del dominio externo.
        sajet_subdomain = (customer.subdomain or "").strip().lower()
        if not sajet_subdomain:
            return {"success": False, "error": "Cliente no tiene subdominio SAJET asignado"}
        
        # Generar token de verificación
        verification_token = f"jeturing-verify-{secrets.token_hex(16)}"

        # Vinculación automática al deployment del cliente (si no se especifica)
        if not tenant_deployment_id:
            auto_dep = (
                self.db.query(TenantDeployment)
                .filter(TenantDeployment.customer_id == customer_id)
                .order_by(TenantDeployment.id.desc())
                .first()
            )
            if auto_dep:
                tenant_deployment_id = auto_dep.id
                logger.info(
                    "Domain auto-link: %s -> deployment_id=%s (customer_id=%s)",
                    external_domain,
                    tenant_deployment_id,
                    customer_id,
                )
        
        # Obtener IP del nodo si hay deployment
        # Prioridad: backend_host (multi-nodo) → direct_url (legacy) → fallback
        target_node_ip = None
        target_port = 8069
        if tenant_deployment_id:
            deployment = self.db.query(TenantDeployment).filter(
                TenantDeployment.id == tenant_deployment_id
            ).first()
            if deployment:
                # 1. Campos multi-nodo (Fase 0+)
                if deployment.backend_host:
                    target_node_ip = deployment.backend_host
                    target_port = deployment.http_port or 8080
                # 2. Legacy: parsear direct_url
                elif deployment.direct_url:
                    parts = deployment.direct_url.replace("http://", "").split(":")
                    target_node_ip = parts[0]
                    if len(parts) > 1:
                        target_port = int(parts[1])
        
        # Crear registro
        domain = CustomDomain(
            customer_id=customer_id,
            tenant_deployment_id=tenant_deployment_id,
            external_domain=external_domain,
            sajet_subdomain=sajet_subdomain,
            verification_status=DomainVerificationStatus.pending,
            verification_token=verification_token,
            target_node_ip=_effective_target_node_ip(target_node_ip),
            target_port=target_port,
            created_by=created_by
        )
        
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        
        instructions = self._build_external_dns_instructions(external_domain)

        return {
            "success": True,
            "domain": {
                "id": domain.id,
                "external_domain": domain.external_domain,
                "sajet_subdomain": domain.sajet_subdomain,
                "sajet_full_domain": domain.sajet_full_domain,
                "verification_status": domain.verification_status.value,
                "verification_token": domain.verification_token,
                "is_active": domain.is_active,
                "created_at": domain.created_at.isoformat()
            },
            "instructions": instructions,
        }
    
    def get_domain(self, domain_id: int = None, external_domain: str = None) -> Optional[CustomDomain]:
        """Obtiene un dominio por ID o nombre"""
        query = self.db.query(CustomDomain)
        if domain_id:
            return query.filter(CustomDomain.id == domain_id).first()
        if external_domain:
            return query.filter(CustomDomain.external_domain == external_domain).first()
        return None
    
    def list_domains(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista dominios con filtros"""
        query = self.db.query(CustomDomain)
        
        if customer_id:
            query = query.filter(CustomDomain.customer_id == customer_id)
        if status:
            query = query.filter(CustomDomain.verification_status == status)
        if is_active is not None:
            query = query.filter(CustomDomain.is_active == is_active)
        
        total = query.count()
        domains = query.order_by(CustomDomain.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "items": [self._domain_to_dict(d) for d in domains],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def update_domain(self, domain_id: int, **kwargs) -> Dict[str, Any]:
        """Actualiza un dominio"""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        allowed_fields = ["is_primary", "target_node_ip", "target_port", "tenant_deployment_id"]
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(domain, key):
                setattr(domain, key, value)
        
        domain.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(domain)
        
        return {"success": True, "domain": self._domain_to_dict(domain)}
    
    def delete_domain(self, domain_id: int = None, external_domain: str = None) -> Dict[str, Any]:
        """Elimina un dominio y su configuración de Cloudflare"""
        domain = self.get_domain(domain_id=domain_id, external_domain=external_domain)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        # Eliminar DNS record de Cloudflare si existe
        if domain.cloudflare_dns_record_id:
            self._delete_cloudflare_dns(domain.cloudflare_dns_record_id)
        
        # Eliminar config nginx si estaba configurado
        if domain.nginx_configured:
            self._remove_nginx_for_domain(domain)
        
        external = domain.external_domain
        self.db.delete(domain)
        self.db.commit()
        
        return {"success": True, "message": f"Dominio {external} eliminado correctamente"}
    
    # ==================== Cloudflare Integration ====================
    
    async def configure_cloudflare(self, domain_id: int) -> Dict[str, Any]:
        """
        Configura el DNS CNAME en Cloudflare para el dominio.
        Crea: {subdomain}.sajet.us → {tunnel}.cfargotunnel.com
        """
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        if domain.cloudflare_configured:
            return {"success": True, "message": "Ya está configurado en Cloudflare"}
        
        # Verificar si ya existe el record
        existing_record = await self._get_cloudflare_dns_record(domain.sajet_subdomain)
        
        if existing_record:
            # Ya existe, guardar el ID
            domain.cloudflare_dns_record_id = existing_record["id"]
            domain.cloudflare_configured = True
        else:
            # Crear nuevo record
            result = await self._create_cloudflare_dns(domain.sajet_subdomain)
            if not result["success"]:
                return result
            
            domain.cloudflare_dns_record_id = result["record_id"]
            domain.cloudflare_configured = True
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"DNS configurado: {domain.sajet_full_domain}",
            "record_id": domain.cloudflare_dns_record_id
        }
    
    async def _create_cloudflare_dns(self, subdomain: str) -> Dict[str, Any]:
        """Crea un registro CNAME en Cloudflare"""
        tunnel_ref = (_cf_tunnel_id() or _cf_tunnel_name() or "").strip()
        if not tunnel_ref:
            return {
                "success": False,
                "error": "CLOUDFLARE_TUNNEL_ID/CLOUDFLARE_TUNNEL_NAME no configurado"
            }

        tunnel_target = (
            tunnel_ref
            if tunnel_ref.endswith(".cfargotunnel.com")
            else f"{tunnel_ref}.cfargotunnel.com"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CF_API_BASE}/zones/{_cf_zone_id()}/dns_records",
                headers=self.cf_headers,
                json={
                    "type": "CNAME",
                    "name": subdomain,
                    "content": tunnel_target,
                    "proxied": True,
                    "ttl": 1  # Auto
                }
            )
            
            data = response.json()
            
            if data.get("success"):
                return {
                    "success": True,
                    "record_id": data["result"]["id"]
                }
            else:
                error = data.get("errors", [{}])[0].get("message", "Error desconocido")
                return {"success": False, "error": f"Cloudflare: {error}"}
    
    async def _get_cloudflare_dns_record(self, subdomain: str) -> Optional[Dict]:
        """Busca un registro DNS existente"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CF_API_BASE}/zones/{_cf_zone_id()}/dns_records",
                headers=self.cf_headers,
                params={"name": f"{subdomain}.sajet.us"}
            )
            
            data = response.json()
            
            if data.get("success") and data.get("result"):
                return data["result"][0]
            return None
    
    def _delete_cloudflare_dns(self, record_id: str) -> bool:
        """Elimina un registro DNS de Cloudflare (sync)"""
        import requests
        try:
            response = requests.delete(
                f"{CF_API_BASE}/zones/{_cf_zone_id()}/dns_records/{record_id}",
                headers=self.cf_headers
            )
            return response.json().get("success", False)
        except:
            return False
    
    # ==================== Domain Verification ====================

    # Rangos de IP de Cloudflare (proxy mode) — actualizado 2024
    CLOUDFLARE_IP_RANGES = [
        "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
        "103.31.4.0/22", "141.101.64.0/18", "108.162.192.0/18",
        "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22",
        "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
        "104.24.0.0/14", "172.64.0.0/13",
    ]

    def _is_cloudflare_ip(self, ip: str) -> bool:
        """Verifica si una IP pertenece a los rangos de Cloudflare."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            return any(
                addr in ipaddress.ip_network(cidr)
                for cidr in self.CLOUDFLARE_IP_RANGES
            )
        except ValueError:
            return False

    def _verify_via_cloudflare_api(self, domain_name: str) -> Dict[str, Any]:
        """Verifica que el dominio exista como registro DNS en nuestra zona de Cloudflare."""
        import requests
        try:
            response = requests.get(
                f"{CF_API_BASE}/zones/{_cf_zone_id()}/dns_records",
                headers=self.cf_headers,
                params={"name": domain_name, "type": "CNAME,A,AAAA"},
                timeout=10,
            )
            data = response.json()
            if data.get("success") and data.get("result"):
                records = data["result"]
                return {
                    "found": True,
                    "records": [
                        {
                            "type": r["type"],
                            "name": r["name"],
                            "content": r["content"],
                            "proxied": r.get("proxied", False),
                        }
                        for r in records
                    ],
                }
            return {"found": False, "records": []}
        except Exception as e:
            logger.warning(f"Error consultando CF API para {domain_name}: {e}")
            return {"found": False, "records": [], "error": str(e)}

    async def verify_domain(self, domain_id: int) -> Dict[str, Any]:
        """
        Verifica que el dominio esté correctamente configurado.
        
        Estrategias de verificación (en orden):
        1. Subdominios internos (.sajet.us): verifica via API de Cloudflare
        2. Rechaza CNAME externos hacia .sajet.us o .cfargotunnel.com
        3. A record apuntando a nuestra IP o a IPs de Cloudflare (proxy mode)
        4. Verificación via API de Cloudflare como fallback
        """
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}

        try:
            import dns.resolver
        except ImportError:
            return {
                "success": False,
                "status": "error",
                "message": "Módulo dnspython no instalado. Ejecute: pip install dnspython",
            }

        domain.verification_status = DomainVerificationStatus.verifying
        self.db.commit()

        def _mark_verified(method: str, details: dict = None) -> Dict[str, Any]:
            domain.verification_status = DomainVerificationStatus.verified
            domain.verified_at = datetime.utcnow()
            domain.is_active = True
            self.db.commit()
            result = {
                "success": True,
                "status": "verified",
                "message": f"Dominio verificado correctamente ({method})",
            }
            if details:
                result.update(details)
            return result

        def _mark_failed(message: str, details: dict = None) -> Dict[str, Any]:
            domain.verification_status = DomainVerificationStatus.failed
            self.db.commit()
            result = {"success": False, "status": "failed", "message": message}
            if details:
                result.update(details)
            return result

        try:
            is_sajet_subdomain = (
                domain.external_domain.endswith(".sajet.us")
                or domain.external_domain == domain.sajet_full_domain
            )

            # ── Estrategia 1: Subdominio interno de sajet.us ──
            # Estos dominios están en nuestra zona de Cloudflare con proxy activo.
            # No tienen CNAME visible (Cloudflare lo enmascara) y las IPs son de CF.
            # Verificamos directamente via API de Cloudflare.
            if is_sajet_subdomain:
                cf_check = self._verify_via_cloudflare_api(domain.external_domain)
                if cf_check["found"]:
                    return _mark_verified(
                        "Cloudflare DNS",
                        {
                            "method": "cloudflare_api",
                            "cf_records": cf_check["records"],
                        },
                    )
                # Si no está en CF pero es subdominio interno, verificar también
                # el sajet_full_domain (puede diferir del external_domain)
                if domain.external_domain != domain.sajet_full_domain:
                    cf_check2 = self._verify_via_cloudflare_api(domain.sajet_full_domain)
                    if cf_check2["found"]:
                        return _mark_verified(
                            "Cloudflare DNS (sajet)",
                            {
                                "method": "cloudflare_api",
                                "cf_records": cf_check2["records"],
                            },
                        )

            # ── Estrategia 2: CNAME directo ──
            try:
                answers = dns.resolver.resolve(domain.external_domain, "CNAME")
                cname_target = str(answers[0].target).rstrip(".")

                if not is_sajet_subdomain and (
                    cname_target.endswith(".sajet.us")
                    or cname_target.endswith(".cfargotunnel.com")
                ):
                    return _mark_failed(
                        "Los dominios externos no deben usar CNAME hacia sajet.us ni hacia Cloudflare Tunnel",
                        {
                            "cname_detected": cname_target,
                            **self._build_external_dns_instructions(domain.external_domain),
                        },
                    )

                # Para aliases externos legitimos (ej. www -> raiz) dejamos que la
                # resolucion A continue y valide el destino final.
                if is_sajet_subdomain:
                    return _mark_failed(
                        "CNAME no apunta al destino correcto",
                        {"cname_detected": cname_target, "expected": domain.sajet_full_domain},
                    )

            except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                pass  # Sin CNAME — continuar con A record

            except dns.resolver.NXDOMAIN:
                return _mark_failed(
                    "El dominio no existe en DNS",
                    {"instructions": "Verifique que el dominio esté correctamente configurado"},
                )

            # ── Estrategia 3: A record ──
            try:
                answers = dns.resolver.resolve(domain.external_domain, "A")
                a_records = [str(r) for r in answers]

                # Nuestra IP pública directa
                our_ips = {_public_ip()}
                if our_ips & set(a_records):
                    return _mark_verified("A record directo", {"a_records": a_records})

                # IPs de Cloudflare (proxy mode activado)
                cf_ips = [ip for ip in a_records if self._is_cloudflare_ip(ip)]
                if cf_ips:
                    return _mark_verified(
                        "Cloudflare proxy",
                        {"a_records": a_records, "cloudflare_ips": cf_ips},
                    )

                return _mark_failed(
                    "A record no apunta a la IP publica esperada ni a Cloudflare",
                    {
                        "a_records": a_records,
                        **self._build_external_dns_instructions(domain.external_domain),
                    },
                )

            except (dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.resolver.NXDOMAIN):
                pass  # Sin A record — continuar con fallback CF API

            # ── Estrategia 4: Fallback — verificar via API de Cloudflare ──
            if not is_sajet_subdomain and not domain.cloudflare_configured:
                cf_check = self._verify_via_cloudflare_api(domain.external_domain)
                if cf_check["found"]:
                    return _mark_verified(
                        "Cloudflare DNS (fallback)",
                        {"method": "cloudflare_api", "cf_records": cf_check["records"]},
                    )

            return _mark_failed(
                "No se encontró registro DNS válido",
                self._build_external_dns_instructions(domain.external_domain),
            )

        except Exception as e:
            domain.verification_status = DomainVerificationStatus.pending
            self.db.commit()
            return {
                "success": False,
                "status": "error",
                "message": f"Error verificando dominio: {str(e)}",
            }
    
    def activate_domain(self, domain_id: int) -> Dict[str, Any]:
        """Activa manualmente un dominio y configura nginx + Odoo website automáticamente"""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        domain.is_active = True
        domain.verification_status = DomainVerificationStatus.verified
        domain.verified_at = datetime.utcnow()
        self.db.commit()
        
        # ── Configurar nginx automáticamente ──
        nginx_result = self._configure_nginx_for_domain(domain)
        
        # ── Configurar website Odoo automáticamente ──
        website_result = self._configure_odoo_website_for_domain(domain)
        
        return {
            "success": True,
            "message": "Dominio activado",
            "nginx": nginx_result,
            "odoo_website": website_result,
        }
    
    def deactivate_domain(self, domain_id: int) -> Dict[str, Any]:
        """Desactiva un dominio y elimina su configuración nginx"""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        # ── Eliminar config nginx ──
        nginx_result = self._remove_nginx_for_domain(domain)
        
        domain.is_active = False
        self.db.commit()
        
        return {
            "success": True,
            "message": "Dominio desactivado",
            "nginx": nginx_result,
        }
    
    # ==================== Helper Methods ====================
    
    def _normalize_domain(self, domain: str) -> str:
        """Normaliza un dominio (lowercase, sin espacios, sin protocolo)"""
        domain = domain.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.rstrip('/')
        return domain
    
    def _validate_domain(self, domain: str) -> Dict[str, Any]:
        """Valida formato de dominio"""
        # Patrón básico de dominio
        pattern = r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        
        if not re.match(pattern, domain):
            return {"valid": False, "error": "Formato de dominio inválido"}
        
        if len(domain) > 253:
            return {"valid": False, "error": "El dominio es demasiado largo"}
        
        # No permitir dominios de sajet.us directamente
        if domain.endswith('.sajet.us') or domain == 'sajet.us':
            return {"valid": False, "error": "No puede usar dominios de sajet.us"}
        
        return {"valid": True}
    
    def _generate_sajet_subdomain(self, external_domain: str) -> str:
        """
        Genera un subdominio de sajet.us basado en el dominio externo.
        
        www.impulse-max.com → impulse-max
        my-company.io → my-company
        """
        # Remover www. y TLD
        parts = external_domain.split('.')
        
        # Filtrar 'www' y TLDs comunes
        tlds = {'com', 'org', 'net', 'io', 'co', 'us', 'mx', 'es', 'do'}
        filtered = [p for p in parts if p != 'www' and p not in tlds and len(p) > 0]
        
        if not filtered:
            # Fallback: usar todo excepto TLD
            filtered = parts[:-1]
        
        # Unir con guiones y sanitizar
        subdomain = '-'.join(filtered)
        subdomain = re.sub(r'[^a-z0-9-]', '', subdomain.lower())
        subdomain = re.sub(r'-+', '-', subdomain)  # Eliminar guiones múltiples
        subdomain = subdomain.strip('-')  # Eliminar guiones al inicio/fin
        
        # Limitar longitud
        if len(subdomain) > 63:
            subdomain = subdomain[:63].rstrip('-')
        
        # Verificar contra lista negra
        if subdomain in RESERVED_SUBDOMAINS:
            subdomain = f"{subdomain}-site"
        
        return subdomain or "custom-domain"
    
    # ==================== Nginx Integration ====================

    def _resolve_tenant_info(self, domain: CustomDomain) -> Dict[str, str]:
        """
        Resuelve el nombre de BD y subdominio del tenant para un dominio.
        Prioridad:
        1) TenantDeployment explícito del dominio
        2) Último TenantDeployment del customer
        3) Customer.subdomain
        4) domain.sajet_subdomain (fallback legacy)
        """
        customer_subdomain = None
        if domain.customer and domain.customer.subdomain:
            customer_subdomain = domain.customer.subdomain

        tenant_db = customer_subdomain or domain.sajet_subdomain
        tenant_subdomain = customer_subdomain or domain.sajet_subdomain

        deployment = None
        if domain.tenant_deployment_id:
            deployment = self.db.query(TenantDeployment).filter(
                TenantDeployment.id == domain.tenant_deployment_id
            ).first()

        if not deployment and domain.customer_id:
            deployment = (
                self.db.query(TenantDeployment)
                .filter(TenantDeployment.customer_id == domain.customer_id)
                .order_by(TenantDeployment.id.desc())
                .first()
            )

        if deployment:
            if deployment.database_name:
                tenant_db = deployment.database_name
            if deployment.subdomain:
                tenant_subdomain = deployment.subdomain

        return {"tenant_db": tenant_db, "tenant_subdomain": tenant_subdomain}

    def _configure_nginx_for_domain(self, domain: CustomDomain) -> Dict[str, Any]:
        """Configura nginx en PCT160 y CT105 para un dominio."""
        try:
            info = self._resolve_tenant_info(domain)
            node_ip = _effective_target_node_ip(
                domain.target_node_ip or get_runtime_setting("ODOO_PRIMARY_IP", "")
            )
            if node_ip != domain.target_node_ip:
                domain.target_node_ip = node_ip
                self.db.commit()

            configurator = NginxDomainConfigurator()
            result = configurator.configure_domain(
                external_domain=domain.external_domain,
                tenant_db=info["tenant_db"],
                tenant_subdomain=info["tenant_subdomain"],
                node_ip=node_ip,
            )

            if result["success"]:
                domain.nginx_configured = True
                self.db.commit()
                logger.info(f"Nginx configurado para {domain.external_domain}")
            else:
                logger.error(f"Nginx falló para {domain.external_domain}: {result.get('error')}")

            return result
        except Exception as e:
            logger.error(f"Error configurando nginx para {domain.external_domain}: {e}")
            return {"success": False, "error": str(e)}

    def _remove_nginx_for_domain(self, domain: CustomDomain) -> Dict[str, Any]:
        """Elimina configuración nginx de PCT160 y nodo Odoo para un dominio."""
        try:
            info = self._resolve_tenant_info(domain)
            node_ip = _effective_target_node_ip(
                domain.target_node_ip or get_runtime_setting("ODOO_PRIMARY_IP", "")
            )
            if node_ip != domain.target_node_ip:
                domain.target_node_ip = node_ip
                self.db.commit()

            configurator = NginxDomainConfigurator()
            result = configurator.remove_domain(
                external_domain=domain.external_domain,
                tenant_subdomain=info["tenant_subdomain"],
                node_ip=node_ip,
            )

            if result["success"]:
                domain.nginx_configured = False
                self.db.commit()
                logger.info(f"Nginx eliminado para {domain.external_domain}")
            else:
                logger.error(f"Nginx remove falló para {domain.external_domain}: {result.get('error')}")

            return result
        except Exception as e:
            logger.error(f"Error eliminando nginx para {domain.external_domain}: {e}")
            return {"success": False, "error": str(e)}

    def configure_nginx_manual(self, domain_id: int) -> Dict[str, Any]:
        """Endpoint manual para (re)configurar nginx de un dominio."""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        if not domain.is_active:
            return {"success": False, "error": "El dominio debe estar activo"}
        return self._configure_nginx_for_domain(domain)

    # ==================== Odoo Website Integration ====================

    def _configure_odoo_website_for_domain(self, domain: CustomDomain) -> Dict[str, Any]:
        """Configura un website en la BD Odoo del tenant para multi-website."""
        try:
            info = self._resolve_tenant_info(domain)
            from .nginx_domain_configurator import NginxDomainConfigurator
            nginx_conf = NginxDomainConfigurator()
            internal_subdomain = nginx_conf.generate_internal_subdomain(
                tenant_db=info["tenant_db"],
                external_domain=domain.external_domain,
            )
            configurator = OdooWebsiteConfigurator()
            result = configurator.configure_website(
                tenant_db=info["tenant_db"],
                external_domain=domain.external_domain,
                internal_subdomain=internal_subdomain,
            )
            if result.get("success"):
                logger.info(
                    f"Odoo website configurado para {domain.external_domain} "
                    f"→ {internal_subdomain} en BD {info['tenant_db']}: {result.get('action')}"
                )
            else:
                logger.error(
                    f"Odoo website falló para {domain.external_domain}: "
                    f"{result.get('error')}"
                )
            return result
        except Exception as e:
            logger.error(f"Error configurando Odoo website: {e}")
            return {"success": False, "error": str(e)}

    def _remove_odoo_website_for_domain(self, domain: CustomDomain) -> Dict[str, Any]:
        """Elimina el dominio de un website Odoo."""
        try:
            info = self._resolve_tenant_info(domain)
            from .nginx_domain_configurator import NginxDomainConfigurator
            nginx_conf = NginxDomainConfigurator()
            internal_subdomain = nginx_conf.generate_internal_subdomain(
                tenant_db=info["tenant_db"],
                external_domain=domain.external_domain,
            )
            configurator = OdooWebsiteConfigurator()
            return configurator.remove_website_domain(
                tenant_db=info["tenant_db"],
                external_domain=domain.external_domain,
                internal_subdomain=internal_subdomain,
            )
        except Exception as e:
            logger.error(f"Error eliminando Odoo website domain: {e}")
            return {"success": False, "error": str(e)}

    def configure_odoo_website_manual(self, domain_id: int) -> Dict[str, Any]:
        """Endpoint manual para configurar el website Odoo de un dominio."""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        if not domain.is_active:
            return {"success": False, "error": "El dominio debe estar activo"}
        return self._configure_odoo_website_for_domain(domain)

    def _domain_to_dict(self, domain: CustomDomain) -> Dict[str, Any]:
        """Convierte un dominio a diccionario"""
        return {
            "id": domain.id,
            "customer_id": domain.customer_id,
            "tenant_deployment_id": domain.tenant_deployment_id,
            "external_domain": domain.external_domain,
            "sajet_subdomain": domain.sajet_subdomain,
            "sajet_full_domain": domain.sajet_full_domain,
            "verification_status": domain.verification_status.value if domain.verification_status else "pending",
            "verification_token": domain.verification_token,
            "verified_at": domain.verified_at.isoformat() if domain.verified_at else None,
            "cloudflare_configured": domain.cloudflare_configured,
            "tunnel_ingress_configured": domain.tunnel_ingress_configured,
            "nginx_configured": domain.nginx_configured,
            "ssl_status": domain.ssl_status,
            "is_active": domain.is_active,
            "is_primary": domain.is_primary,
            "target_node_ip": domain.target_node_ip,
            "target_port": domain.target_port,
            "created_at": domain.created_at.isoformat() if domain.created_at else None,
            "updated_at": domain.updated_at.isoformat() if domain.updated_at else None
        }
