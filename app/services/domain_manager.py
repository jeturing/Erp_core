"""
Domain Manager Service
Gestiona dominios personalizados de clientes, integración con Cloudflare y configuración de tunnels.

Flujo:
1. Cliente registra dominio externo (www.impulse-max.com)
2. Sistema genera subdominio sajet.us (impulse-max.sajet.us)
3. Sistema crea CNAME en Cloudflare (impulse-max → tunnel)
4. Script en PCT 105 actualiza ingress rules del tunnel
5. Cliente configura CNAME en su DNS externo
6. Sistema verifica y activa el dominio
"""

import os
import re
import secrets
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.database import CustomDomain, Customer, TenantDeployment, DomainVerificationStatus


# Cloudflare Configuration
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID", "4a83b88793ac3688486ace69b6ae80f9")  # sajet.us
CF_TUNNEL_NAME = os.getenv("CLOUDFLARE_TUNNEL_NAME", "tcs-sajet-tunnel")
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


class DomainManager:
    """Gestor de dominios personalizados"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cf_headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json"
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
        
        # Generar subdominio de sajet.us
        sajet_subdomain = self._generate_sajet_subdomain(external_domain)
        
        # Verificar que el subdominio no existe
        existing_subdomain = self.db.query(CustomDomain).filter(
            CustomDomain.sajet_subdomain == sajet_subdomain
        ).first()
        if existing_subdomain:
            # Agregar sufijo único
            sajet_subdomain = f"{sajet_subdomain}-{secrets.token_hex(3)}"
        
        # Generar token de verificación
        verification_token = f"jeturing-verify-{secrets.token_hex(16)}"
        
        # Obtener IP del nodo si hay deployment
        target_node_ip = None
        target_port = 8069
        if tenant_deployment_id:
            deployment = self.db.query(TenantDeployment).filter(
                TenantDeployment.id == tenant_deployment_id
            ).first()
            if deployment and deployment.direct_url:
                # Parsear IP:puerto del direct_url
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
            target_node_ip=target_node_ip or "localhost",
            target_port=target_port,
            created_by=created_by
        )
        
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        
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
            "instructions": {
                "step1": f"Configure un registro CNAME en su DNS:",
                "record_type": "CNAME",
                "record_name": external_domain,
                "record_value": f"{sajet_subdomain}.sajet.us",
                "step2": "Una vez configurado, haga clic en 'Verificar' para activar el dominio"
            }
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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CF_API_BASE}/zones/{CF_ZONE_ID}/dns_records",
                headers=self.cf_headers,
                json={
                    "type": "CNAME",
                    "name": subdomain,
                    "content": f"{CF_TUNNEL_NAME}.cfargotunnel.com",
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
                f"{CF_API_BASE}/zones/{CF_ZONE_ID}/dns_records",
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
                f"{CF_API_BASE}/zones/{CF_ZONE_ID}/dns_records/{record_id}",
                headers=self.cf_headers
            )
            return response.json().get("success", False)
        except:
            return False
    
    # ==================== Domain Verification ====================
    
    async def verify_domain(self, domain_id: int) -> Dict[str, Any]:
        """
        Verifica que el CNAME del dominio externo apunte correctamente a sajet.us
        """
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        domain.verification_status = DomainVerificationStatus.verifying
        self.db.commit()
        
        # Verificar CNAME usando DNS lookup
        import dns.resolver
        try:
            answers = dns.resolver.resolve(domain.external_domain, 'CNAME')
            cname_target = str(answers[0].target).rstrip('.')
            
            # Verificar que apunte a nuestro subdominio
            expected = domain.sajet_full_domain
            if cname_target == expected or cname_target.endswith('.sajet.us'):
                domain.verification_status = DomainVerificationStatus.verified
                domain.verified_at = datetime.utcnow()
                domain.is_active = True
                self.db.commit()
                
                return {
                    "success": True,
                    "status": "verified",
                    "message": "Dominio verificado correctamente",
                    "cname_detected": cname_target,
                    "expected": expected
                }
            else:
                domain.verification_status = DomainVerificationStatus.failed
                self.db.commit()
                
                return {
                    "success": False,
                    "status": "failed",
                    "message": "CNAME no apunta al destino correcto",
                    "cname_detected": cname_target,
                    "expected": expected
                }
                
        except dns.resolver.NoAnswer:
            domain.verification_status = DomainVerificationStatus.failed
            self.db.commit()
            return {
                "success": False,
                "status": "failed",
                "message": "No se encontró registro CNAME",
                "instructions": f"Configure: {domain.external_domain} CNAME {domain.sajet_full_domain}"
            }
        except dns.resolver.NXDOMAIN:
            domain.verification_status = DomainVerificationStatus.failed
            self.db.commit()
            return {
                "success": False,
                "status": "failed", 
                "message": "El dominio no existe en DNS",
                "instructions": "Verifique que el dominio esté correctamente configurado"
            }
        except Exception as e:
            domain.verification_status = DomainVerificationStatus.pending
            self.db.commit()
            return {
                "success": False,
                "status": "error",
                "message": f"Error verificando dominio: {str(e)}"
            }
    
    def activate_domain(self, domain_id: int) -> Dict[str, Any]:
        """Activa manualmente un dominio"""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        domain.is_active = True
        domain.verification_status = DomainVerificationStatus.verified
        domain.verified_at = datetime.utcnow()
        self.db.commit()
        
        return {"success": True, "message": "Dominio activado"}
    
    def deactivate_domain(self, domain_id: int) -> Dict[str, Any]:
        """Desactiva un dominio"""
        domain = self.get_domain(domain_id=domain_id)
        if not domain:
            return {"success": False, "error": "Dominio no encontrado"}
        
        domain.is_active = False
        self.db.commit()
        
        return {"success": True, "message": "Dominio desactivado"}
    
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
            "ssl_status": domain.ssl_status,
            "is_active": domain.is_active,
            "is_primary": domain.is_primary,
            "target_node_ip": domain.target_node_ip,
            "target_port": domain.target_port,
            "created_at": domain.created_at.isoformat() if domain.created_at else None,
            "updated_at": domain.updated_at.isoformat() if domain.updated_at else None
        }
