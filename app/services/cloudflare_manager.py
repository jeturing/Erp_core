"""
Cloudflare Tunnel Manager - Gestión de proxies y tunnels para tenants
"""
import subprocess
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.database import (
    SessionLocal, TenantDeployment, ProxmoxNode,
    LXCContainer, Subscription
)

logger = logging.getLogger(__name__)


class CloudflareManager:
    """Gestiona Cloudflare Tunnels para exponer contenedores LXC"""
    
    # Rutas de configuración
    CF_CREDENTIALS_FILE = os.getenv("CF_CREDENTIALS_FILE", "/root/.cf_credentials")
    CF_DOMAINS_FILE = os.getenv("CF_DOMAINS_FILE", "/root/Cloudflare/dominios.json")
    CF_LOG_FILE = "/var/log/cf_manager.log"
    CLOUDFLARED_PATH = "/usr/bin/cloudflared"
    
    @classmethod
    def load_credentials(cls) -> Dict[str, str]:
        """Carga credenciales de Cloudflare"""
        try:
            with open(cls.CF_CREDENTIALS_FILE, 'r') as f:
                creds = {}
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        creds[key.strip()] = value.strip().strip('"').strip("'")
                return creds
        except Exception as e:
            logger.error(f"Error cargando credenciales: {e}")
            return {}
    
    @classmethod
    def load_domains(cls) -> List[Dict[str, str]]:
        """Carga lista de dominios"""
        try:
            with open(cls.CF_DOMAINS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando dominios: {e}")
            return []
    
    @classmethod
    async def create_tunnel(
        cls,
        subdomain: str,
        container_id: int,
        local_port: int = 8069,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un Cloudflare Tunnel para un tenant
        
        Args:
            subdomain: Subdominio del tenant (ej: "acme")
            container_id: ID del contenedor LXC
            local_port: Puerto local del contenedor (default 8069 para Odoo)
            domain: Dominio principal (default: sajet.us)
        
        Returns:
            Dict con status, tunnel_id, url
        """
        domain = domain or "sajet.us"
        full_domain = f"{subdomain}.{domain}"
        tunnel_name = f"{subdomain}-tunnel"
        
        try:
            db = SessionLocal()
            container = db.query(LXCContainer).filter_by(id=container_id).first()
            
            if not container:
                return {"success": False, "error": "Contenedor no encontrado"}
            
            if not container.ip_address:
                return {"success": False, "error": "Contenedor sin IP asignada"}
            
            # 1. Crear tunnel en Cloudflare
            logger.info(f"Creando tunnel {tunnel_name} para {full_domain}")
            
            cmd = f"{cls.CLOUDFLARED_PATH} tunnel create {tunnel_name} 2>&1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and "already exists" not in result.stderr.lower():
                logger.error(f"Error creando tunnel: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            # 2. Obtener Tunnel ID
            cmd = f"{cls.CLOUDFLARED_PATH} tunnel list | grep {tunnel_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            tunnel_id = None
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                tunnel_id = parts[0] if parts else None
            
            # 3. Configurar DNS en Cloudflare
            cmd = f"{cls.CLOUDFLARED_PATH} tunnel route dns {tunnel_name} {full_domain} 2>&1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and "already exists" not in result.stderr.lower():
                logger.warning(f"Advertencia en DNS: {result.stderr}")
            
            # 4. Crear archivo de configuración del tunnel
            config_file = f"/etc/cloudflared/tunnel-{tunnel_name}.json"
            config = {
                "tunnel": tunnel_id or tunnel_name,
                "credentials-file": f"/root/.cloudflared/{tunnel_id or tunnel_name}.json",
                "ingress": [
                    {
                        "hostname": full_domain,
                        "service": f"http://{container.ip_address}:{local_port}"
                    },
                    {
                        "service": "http_status:404"
                    }
                ]
            }
            
            try:
                os.makedirs("/etc/cloudflared", exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Config tunnel creada: {config_file}")
            except Exception as e:
                logger.warning(f"No se pudo crear archivo de config: {e}")
            
            # 5. Crear servicio systemd
            service_content = f"""[Unit]
Description=Cloudflare Tunnel for {full_domain}
After=network.target

[Service]
Type=simple
User=root
ExecStart={cls.CLOUDFLARED_PATH} tunnel --no-autoupdate run --url http://{container.ip_address}:{local_port} {tunnel_name}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
            
            service_file = f"/etc/systemd/system/cloudflared-{tunnel_name}.service"
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Habilitar e iniciar servicio
                subprocess.run("systemctl daemon-reload", shell=True, timeout=10)
                subprocess.run(f"systemctl enable cloudflared-{tunnel_name}", shell=True, timeout=10)
                subprocess.run(f"systemctl restart cloudflared-{tunnel_name}", shell=True, timeout=10)
                logger.info(f"Servicio systemd iniciado: {service_file}")
            except Exception as e:
                logger.warning(f"Error con servicio systemd: {e}")
            
            # 6. Actualizar deployment en BD
            deployment = db.query(TenantDeployment).filter_by(
                container_id=container_id
            ).first()
            
            if deployment:
                deployment.tunnel_url = f"https://{full_domain}"
                deployment.tunnel_active = True
                deployment.tunnel_id = tunnel_id or tunnel_name
                deployment.direct_url = f"http://{container.ip_address}:{local_port}"
                db.commit()
                logger.info(f"Deployment actualizado: {full_domain}")
            
            db.close()
            
            return {
                "success": True,
                "tunnel_name": tunnel_name,
                "tunnel_id": tunnel_id,
                "domain": full_domain,
                "url": f"https://{full_domain}",
                "direct_url": f"http://{container.ip_address}:{local_port}",
                "status": "active"
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout creando tunnel {tunnel_name}")
            return {"success": False, "error": "Timeout en operación"}
        except Exception as e:
            logger.exception(f"Error en create_tunnel: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def delete_tunnel(cls, tunnel_name: str) -> Dict[str, Any]:
        """Elimina un Cloudflare Tunnel"""
        try:
            # 1. Detener servicio
            service = f"cloudflared-{tunnel_name}"
            subprocess.run(f"systemctl stop {service}", shell=True, timeout=10)
            subprocess.run(f"systemctl disable {service}", shell=True, timeout=10)
            
            # 2. Eliminar archivo de servicio
            service_file = f"/etc/systemd/system/{service}.service"
            if os.path.exists(service_file):
                os.remove(service_file)
            
            subprocess.run("systemctl daemon-reload", shell=True, timeout=10)
            
            # 3. Eliminar tunnel de Cloudflare
            cmd = f"{cls.CLOUDFLARED_PATH} tunnel delete {tunnel_name} 2>&1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            # 4. Actualizar BD
            db = SessionLocal()
            deployment = db.query(TenantDeployment).filter_by(
                tunnel_id=tunnel_name
            ).first()
            
            if deployment:
                deployment.tunnel_active = False
                db.commit()
            
            db.close()
            
            return {
                "success": True,
                "message": f"Tunnel {tunnel_name} eliminado"
            }
            
        except Exception as e:
            logger.exception(f"Error eliminando tunnel: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def list_tunnels(cls) -> Dict[str, Any]:
        """Lista todos los Cloudflare Tunnels"""
        try:
            cmd = f"{cls.CLOUDFLARED_PATH} tunnel list 2>&1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {"success": False, "tunnels": []}
            
            # Parsear salida
            tunnels = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        tunnels.append({
                            "id": parts[0],
                            "name": parts[1],
                            "status": "active" if len(parts) > 2 else "unknown"
                        })
            
            return {"success": True, "tunnels": tunnels}
            
        except Exception as e:
            logger.error(f"Error listando tunnels: {e}")
            return {"success": False, "tunnels": [], "error": str(e)}
    
    @classmethod
    def get_tunnel_status(cls, tunnel_name: str) -> Dict[str, Any]:
        """Obtiene estado de un tunnel específico"""
        try:
            service = f"cloudflared-{tunnel_name}"
            
            # Verificar servicio
            result = subprocess.run(
                f"systemctl is-active {service}",
                shell=True,
                capture_output=True,
                timeout=5
            )
            
            is_active = result.returncode == 0
            
            return {
                "tunnel_name": tunnel_name,
                "service": service,
                "active": is_active,
                "status": "running" if is_active else "stopped"
            }
            
        except Exception as e:
            return {
                "tunnel_name": tunnel_name,
                "error": str(e),
                "status": "error"
            }
    
    @classmethod
    def restart_tunnel(cls, tunnel_name: str) -> Dict[str, Any]:
        """Reinicia un tunnel"""
        try:
            service = f"cloudflared-{tunnel_name}"
            subprocess.run(f"systemctl restart {service}", shell=True, timeout=15)
            
            return {
                "success": True,
                "message": f"Tunnel {tunnel_name} reiniciado"
            }
            
        except Exception as e:
            logger.error(f"Error reiniciando tunnel: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def get_tunnel_logs(cls, tunnel_name: str, lines: int = 50) -> List[str]:
        """Obtiene logs del tunnel"""
        try:
            service = f"cloudflared-{tunnel_name}"
            cmd = f"journalctl -u {service} -n {lines} --no-pager"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            return result.stdout.split('\n') if result.returncode == 0 else []
            
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
