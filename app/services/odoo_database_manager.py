"""
Odoo Database Manager Service
Integra directamente con /web/database/* endpoints de Odoo para gestión de BDs
"""
import httpx
import logging
import subprocess
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =====================================================
# CONFIGURACIÓN - Variables de entorno con fallbacks
# =====================================================
# Estas variables pueden ser sobreescritas desde el panel admin
# via la tabla system_config (ver app/models/database.py)
#
# Para editar desde /admin/settings o directamente en .env

def _get_config(key: str, default: str) -> str:
    """
    Obtiene configuración con prioridad: BD > ENV > default
    Importación tardía para evitar circular imports
    """
    try:
        from ..models.database import get_config
        return get_config(key, os.getenv(key, default))
    except:
        return os.getenv(key, default)


# Credenciales Odoo (editables desde /admin/settings)
DEFAULT_ADMIN_LOGIN = os.getenv("ODOO_DEFAULT_ADMIN_LOGIN", "admin@sajet.us")
DEFAULT_ADMIN_PASSWORD = os.getenv("ODOO_DEFAULT_ADMIN_PASSWORD", "321Abcd.")
DEFAULT_MASTER_PASSWORD = os.getenv("ODOO_MASTER_PASSWORD", "admin")

# Credenciales PostgreSQL
DEFAULT_DB_USER = os.getenv("ODOO_DB_USER", "Jeturing")
DEFAULT_DB_PASSWORD = os.getenv("ODOO_DB_PASSWORD", "123Abcd.")

# Configuración de idioma/país
DEFAULT_LANG = os.getenv("ODOO_DEFAULT_LANG", "es_DO")
DEFAULT_COUNTRY = os.getenv("ODOO_DEFAULT_COUNTRY", "DO")

# Dominio y template
BASE_DOMAIN = os.getenv("ODOO_BASE_DOMAIN", "sajet.us")
TEMPLATE_DB = os.getenv("ODOO_TEMPLATE_DB", "template_tenant")


def get_odoo_config() -> Dict[str, Any]:
    """
    Retorna configuración actual de Odoo.
    Usado por el panel admin para mostrar valores actuales.
    """
    return {
        "admin_login": _get_config("ODOO_DEFAULT_ADMIN_LOGIN", DEFAULT_ADMIN_LOGIN),
        "admin_password": "********",  # No exponer
        "master_password": "********",  # No exponer
        "db_user": _get_config("ODOO_DB_USER", DEFAULT_DB_USER),
        "db_password": "********",  # No exponer
        "default_lang": _get_config("ODOO_DEFAULT_LANG", DEFAULT_LANG),
        "default_country": _get_config("ODOO_DEFAULT_COUNTRY", DEFAULT_COUNTRY),
        "base_domain": _get_config("ODOO_BASE_DOMAIN", BASE_DOMAIN),
        "template_db": _get_config("ODOO_TEMPLATE_DB", TEMPLATE_DB),
    }


class ServerStatus(str, Enum):
    online = "online"
    offline = "offline"
    maintenance = "maintenance"
    full = "full"


@dataclass
class OdooServer:
    """Configuración de un servidor Odoo"""
    id: str
    name: str
    pct_id: int  # ID del contenedor Proxmox
    ip: str
    port: int = 8069
    max_databases: int = 50
    current_databases: int = 0
    status: ServerStatus = ServerStatus.online
    region: str = "default"
    priority: int = 1  # Mayor = más prioridad
    
    @property
    def base_url(self) -> str:
        return f"http://{self.ip}:{self.port}"
    
    @property
    def available_slots(self) -> int:
        return max(0, self.max_databases - self.current_databases)


# Pool de servidores disponibles
ODOO_SERVERS: Dict[str, OdooServer] = {
    "pct-105": OdooServer(
        id="pct-105",
        name="Servidor Principal (PCT 105)",
        pct_id=105,
        ip="10.10.10.100",
        port=8069,
        max_databases=50,
        priority=10,
        region="primary"
    ),
    # Agregar más servidores según se necesite
    # "pct-106": OdooServer(
    #     id="pct-106",
    #     name="Servidor Secundario (PCT 106)",
    #     pct_id=106,
    #     ip="10.10.10.101",
    #     port=8069,
    #     max_databases=50,
    #     priority=5,
    #     region="secondary"
    # ),
}


class OdooDatabaseManager:
    """
    Gestiona bases de datos Odoo directamente via HTTP API
    Usa los endpoints /web/database/* de Odoo
    """
    
    def __init__(self, server: OdooServer, master_password: str = DEFAULT_MASTER_PASSWORD):
        self.server = server
        self.master_password = master_password
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # =====================================================
    # OPERACIONES DE BASE DE DATOS
    # =====================================================
    
    async def list_databases(self) -> List[str]:
        """Lista todas las bases de datos en el servidor"""
        try:
            response = await self.client.post(
                f"{self.server.base_url}/web/database/list",
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            else:
                logger.error(f"Error listando BDs: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listando BDs en {self.server.name}: {e}")
            return []
    
    async def database_exists(self, db_name: str) -> bool:
        """Verifica si una base de datos existe"""
        databases = await self.list_databases()
        return db_name.lower() in [db.lower() for db in databases]
    
    async def create_database(
        self,
        db_name: str,
        admin_login: str = DEFAULT_ADMIN_LOGIN,
        admin_password: str = DEFAULT_ADMIN_PASSWORD,
        lang: str = DEFAULT_LANG,
        country_code: str = DEFAULT_COUNTRY,
        demo: bool = False
    ) -> Dict[str, Any]:
        """
        Crea una nueva base de datos Odoo
        
        Args:
            db_name: Nombre de la base de datos (será el subdominio)
            admin_login: Email del usuario admin
            admin_password: Password del admin
            lang: Código de idioma (es_DO, es_MX, en_US, etc.)
            country_code: Código ISO del país
            demo: Si cargar datos demo (False para producción)
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar si ya existe
            if await self.database_exists(db_name):
                return {
                    "success": False,
                    "error": f"La base de datos '{db_name}' ya existe",
                    "error_type": "database_exists"
                }
            
            logger.info(f"Creando BD '{db_name}' en {self.server.name}...")
            
            # Llamar al endpoint de creación de Odoo
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "master_pwd": self.master_password,
                    "name": db_name,
                    "login": admin_login,
                    "password": admin_password,
                    "lang": lang,
                    "country_code": country_code,
                    "phone": "",
                },
                "id": None
            }
            
            response = await self.client.post(
                f"{self.server.base_url}/web/database/create",
                json=payload,
                timeout=600.0  # 10 min para creación
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    error_msg = data["error"].get("data", {}).get("message", str(data["error"]))
                    logger.error(f"Error creando BD: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "odoo_error"
                    }
                
                logger.info(f"✅ BD '{db_name}' creada exitosamente")
                
                # Configurar parámetros post-creación
                await self._configure_new_database(db_name, admin_login, admin_password)
                
                return {
                    "success": True,
                    "database": db_name,
                    "server": self.server.id,
                    "server_name": self.server.name,
                    "url": f"https://{db_name}.{BASE_DOMAIN}",
                    "admin_login": admin_login,
                    "admin_password": admin_password,
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "http_error"
                }
                
        except httpx.TimeoutException:
            logger.error(f"Timeout creando BD '{db_name}'")
            return {
                "success": False,
                "error": "Timeout - la creación tardó más de 10 minutos",
                "error_type": "timeout"
            }
        except Exception as e:
            logger.exception(f"Error creando BD: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unknown"
            }
    
    async def _configure_new_database(
        self,
        db_name: str,
        admin_login: str,
        admin_password: str
    ):
        """Configura parámetros del sistema en la nueva BD via SQL"""
        try:
            base_url = f"https://{db_name}.{BASE_DOMAIN}"
            
            sql_commands = f"""
            UPDATE ir_config_parameter SET value = '{base_url}' WHERE key = 'web.base.url';
            UPDATE ir_config_parameter SET value = 'True' WHERE key = 'web.base.url.freeze';
            UPDATE ir_config_parameter SET value = '{db_name}.{BASE_DOMAIN}' WHERE key = 'mail.catchall.domain';
            """
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="123Abcd."; psql -h 127.0.0.1 -U Jeturing -d {db_name} -c "{sql_commands}"' '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Configurado web.base.url = {base_url}")
            else:
                logger.warning(f"⚠️ Error configurando BD: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"Error configurando BD {db_name}: {e}")
    
    async def duplicate_database(
        self,
        source_db: str,
        new_db_name: str,
        admin_login: str = DEFAULT_ADMIN_LOGIN,
        admin_password: str = DEFAULT_ADMIN_PASSWORD
    ) -> Dict[str, Any]:
        """
        Duplica una base de datos existente (más rápido que crear desde cero)
        """
        try:
            if await self.database_exists(new_db_name):
                return {
                    "success": False,
                    "error": f"La base de datos '{new_db_name}' ya existe"
                }
            
            if not await self.database_exists(source_db):
                return {
                    "success": False,
                    "error": f"La base de datos origen '{source_db}' no existe"
                }
            
            logger.info(f"Duplicando BD '{source_db}' → '{new_db_name}'...")
            
            response = await self.client.post(
                f"{self.server.base_url}/web/database/duplicate",
                json={
                    "jsonrpc": "2.0",
                    "params": {
                        "master_pwd": self.master_password,
                        "name": source_db,
                        "new_name": new_db_name
                    }
                },
                timeout=600.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    return {
                        "success": False,
                        "error": data["error"].get("data", {}).get("message", str(data["error"]))
                    }
                
                # Actualizar credenciales y configuración
                await self._reset_database_after_duplicate(new_db_name, admin_login, admin_password)
                
                logger.info(f"✅ BD '{new_db_name}' duplicada exitosamente")
                
                return {
                    "success": True,
                    "database": new_db_name,
                    "source": source_db,
                    "server": self.server.id,
                    "server_name": self.server.name,
                    "url": f"https://{new_db_name}.{BASE_DOMAIN}",
                    "admin_login": admin_login,
                    "admin_password": admin_password,
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.exception(f"Error duplicando BD: {e}")
            return {"success": False, "error": str(e)}
    
    async def _reset_database_after_duplicate(
        self,
        db_name: str,
        admin_login: str,
        admin_password: str
    ):
        """Resetea credenciales y configuración después de duplicar"""
        try:
            base_url = f"https://{db_name}.{BASE_DOMAIN}"
            
            sql_commands = f"""
            UPDATE res_users SET login = '{admin_login}' WHERE id = 2;
            UPDATE res_users SET password = '{admin_password}' WHERE id = 2;
            DELETE FROM ir_sessions;
            UPDATE res_company SET name = '{db_name}' WHERE id = 1;
            UPDATE res_partner SET name = '{db_name}' WHERE id = 1;
            UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
            UPDATE ir_config_parameter SET value = '{base_url}' WHERE key = 'web.base.url';
            """
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="123Abcd."; psql -h 127.0.0.1 -U Jeturing -d {db_name} -c "{sql_commands}"' '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Configuración reseteada para {db_name}")
            else:
                logger.warning(f"⚠️ Error reseteando config: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"Error reseteando BD {db_name}: {e}")
    
    async def drop_database(self, db_name: str) -> Dict[str, Any]:
        """Elimina una base de datos"""
        try:
            # Proteger BDs del sistema
            protected_dbs = ['postgres', 'template0', 'template1', 'cliente1']
            if db_name.lower() in protected_dbs:
                return {"success": False, "error": f"BD '{db_name}' está protegida"}
            
            response = await self.client.post(
                f"{self.server.base_url}/web/database/drop",
                json={
                    "jsonrpc": "2.0",
                    "params": {
                        "master_pwd": self.master_password,
                        "name": db_name
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return {"success": False, "error": str(data["error"])}
                
                logger.info(f"✅ BD '{db_name}' eliminada")
                return {"success": True, "database": db_name, "deleted_at": datetime.utcnow().isoformat()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.exception(f"Error eliminando BD: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_database_info(self, db_name: str) -> Dict[str, Any]:
        """Obtiene información de una base de datos"""
        try:
            # Obtener tamaño y estadísticas via SQL
            sql = f"""
            SELECT 
                pg_size_pretty(pg_database_size('{db_name}')) as size,
                (SELECT count(*) FROM res_users WHERE active = true) as active_users,
                (SELECT count(*) FROM res_company) as companies
            """
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="123Abcd."; psql -h 127.0.0.1 -U Jeturing -d {db_name} -t -A -F"," -c "{sql}"' '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                return {
                    "database": db_name,
                    "size": parts[0] if len(parts) > 0 else "unknown",
                    "active_users": int(parts[1]) if len(parts) > 1 else 0,
                    "companies": int(parts[2]) if len(parts) > 2 else 0,
                    "url": f"https://{db_name}.{BASE_DOMAIN}",
                    "server": self.server.id
                }
            return {"database": db_name, "error": "No se pudo obtener info"}
            
        except Exception as e:
            return {"database": db_name, "error": str(e)}


# =====================================================
# FUNCIONES DE ALTO NIVEL
# =====================================================

async def get_available_servers() -> List[Dict[str, Any]]:
    """Obtiene lista de servidores disponibles con su estado"""
    servers = []
    
    for server_id, server in ODOO_SERVERS.items():
        try:
            async with OdooDatabaseManager(server) as manager:
                databases = await manager.list_databases()
                server.current_databases = len(databases)
                
                servers.append({
                    "id": server.id,
                    "name": server.name,
                    "pct_id": server.pct_id,
                    "ip": server.ip,
                    "port": server.port,
                    "status": "online",
                    "current_databases": server.current_databases,
                    "max_databases": server.max_databases,
                    "available_slots": server.available_slots,
                    "region": server.region,
                    "priority": server.priority,
                    "databases": databases
                })
        except Exception as e:
            logger.error(f"Error obteniendo estado de {server_id}: {e}")
            servers.append({
                "id": server.id,
                "name": server.name,
                "pct_id": server.pct_id,
                "status": "offline",
                "error": str(e)
            })
    
    return servers


async def select_best_server() -> Optional[OdooServer]:
    """Selecciona el mejor servidor disponible automáticamente"""
    best_server = None
    best_score = -1
    
    for server_id, server in ODOO_SERVERS.items():
        if server.status != ServerStatus.online:
            continue
        
        try:
            async with OdooDatabaseManager(server) as manager:
                databases = await manager.list_databases()
                server.current_databases = len(databases)
                
                if server.available_slots <= 0:
                    continue
                
                # Score = prioridad * slots disponibles
                score = server.priority * server.available_slots
                
                if score > best_score:
                    best_score = score
                    best_server = server
                    
        except Exception as e:
            logger.warning(f"Servidor {server_id} no disponible: {e}")
            continue
    
    return best_server


async def provision_tenant(
    subdomain: str,
    company_name: str = None,
    admin_login: str = DEFAULT_ADMIN_LOGIN,
    admin_password: str = DEFAULT_ADMIN_PASSWORD,
    server_id: Optional[str] = None,
    use_template: bool = True,  # Usar template por defecto
    template_db: str = TEMPLATE_DB,
    demo: bool = False,
    lang: str = DEFAULT_LANG
) -> Dict[str, Any]:
    """
    Provisiona un nuevo tenant completo
    
    Args:
        subdomain: Nombre del tenant (será BD y subdominio)
        company_name: Nombre de la empresa (default = subdomain)
        admin_login: Email del admin
        admin_password: Password del admin
        server_id: ID del servidor específico (None = automático)
        use_template: Si usar BD template para duplicar (más rápido)
        template_db: Nombre de la BD template
        demo: Si cargar datos demo (False para producción)
        lang: Código de idioma (es_DO, es_MX, en_US)
    
    Returns:
        Dict con resultado del provisioning
    """
    # Normalizar subdomain
    subdomain = subdomain.lower().strip().replace(" ", "_").replace("-", "_")
    subdomain = ''.join(c for c in subdomain if c.isalnum() or c == '_')
    
    if len(subdomain) < 3:
        return {"success": False, "error": "El nombre debe tener al menos 3 caracteres"}
    
    if len(subdomain) > 30:
        return {"success": False, "error": "El nombre no puede exceder 30 caracteres"}
    
    # Palabras reservadas
    reserved = ['admin', 'api', 'www', 'mail', 'ftp', 'postgres', 'template', 'odoo']
    if subdomain in reserved:
        return {"success": False, "error": f"'{subdomain}' es un nombre reservado"}
    
    if company_name is None:
        company_name = subdomain.replace("_", " ").title()
    
    # Seleccionar servidor
    if server_id:
        server = ODOO_SERVERS.get(server_id)
        if not server:
            return {"success": False, "error": f"Servidor '{server_id}' no encontrado"}
    else:
        server = await select_best_server()
        if not server:
            return {"success": False, "error": "No hay servidores disponibles"}
    
    logger.info(f"Provisionando tenant '{subdomain}' en {server.name}")
    
    async with OdooDatabaseManager(server) as manager:
        # Verificar si ya existe
        if await manager.database_exists(subdomain):
            return {
                "success": False,
                "error": f"El tenant '{subdomain}' ya existe"
            }
        
        # Crear BD (duplicando template si existe, o desde cero)
        if use_template and await manager.database_exists(template_db):
            result = await manager.duplicate_database(
                source_db=template_db,
                new_db_name=subdomain,
                admin_login=admin_login,
                admin_password=admin_password
            )
        else:
            result = await manager.create_database(
                db_name=subdomain,
                admin_login=admin_login,
                admin_password=admin_password,
                lang=lang,
                demo=demo
            )
        
        if result.get("success"):
            result["company_name"] = company_name
            
            # Intentar crear DNS en Cloudflare
            try:
                dns_result = await _create_cloudflare_dns(subdomain, server)
                result["dns"] = dns_result
            except Exception as e:
                result["dns"] = {"success": False, "error": str(e)}
        
        return result


async def _create_cloudflare_dns(subdomain: str, server: OdooServer) -> Dict[str, Any]:
    """Crea registro DNS en Cloudflare para el nuevo tenant"""
    try:
        from .cloudflare_manager import CloudflareManager
        
        result = await CloudflareManager.create_dns_record(
            subdomain=subdomain,
            target_ip=server.ip
        )
        return result
    except ImportError:
        logger.warning("CloudflareManager no disponible")
        return {"success": False, "error": "CloudflareManager no disponible"}
    except Exception as e:
        logger.error(f"Error creando DNS: {e}")
        return {"success": False, "error": str(e)}


async def delete_tenant(subdomain: str, server_id: Optional[str] = None) -> Dict[str, Any]:
    """Elimina un tenant"""
    
    # Proteger tenants importantes
    protected = ['cliente1', 'tcs', 'demo_cliente']
    if subdomain.lower() in protected:
        return {"success": False, "error": f"'{subdomain}' está protegido y no puede eliminarse"}
    
    # Buscar en qué servidor está
    if server_id:
        servers_to_check = [ODOO_SERVERS.get(server_id)] if server_id in ODOO_SERVERS else []
    else:
        servers_to_check = list(ODOO_SERVERS.values())
    
    for server in servers_to_check:
        if not server:
            continue
        
        try:
            async with OdooDatabaseManager(server) as manager:
                if await manager.database_exists(subdomain):
                    return await manager.drop_database(subdomain)
        except Exception as e:
            logger.error(f"Error buscando en {server.id}: {e}")
    
    return {"success": False, "error": f"Tenant '{subdomain}' no encontrado"}


# =====================================================
# API PARA RUTAS
# =====================================================

async def get_servers_status() -> Dict[str, Any]:
    """Endpoint: obtiene estado de todos los servidores"""
    servers = await get_available_servers()
    
    total_dbs = sum(s.get("current_databases", 0) for s in servers if s.get("status") != "offline")
    total_slots = sum(s.get("available_slots", 0) for s in servers if s.get("status") != "offline")
    online_count = sum(1 for s in servers if s.get("status") == "online")
    
    return {
        "servers": servers,
        "summary": {
            "total_servers": len(servers),
            "online_servers": online_count,
            "total_databases": total_dbs,
            "available_slots": total_slots
        }
    }


def _run_pct_sql(pct_id: int, database: str, sql: str, timeout: int = 60) -> tuple:
    """Ejecuta SQL via pct exec (síncrono, para operaciones críticas)"""
    try:
        # Escapar comillas simples
        sql_safe = sql.replace("'", "''")
        cmd = f'''pct exec {pct_id} -- bash -c 'export PGPASSWORD="{DEFAULT_DB_PASSWORD}"; psql -h 127.0.0.1 -U {DEFAULT_DB_USER} -d {database} -c "{sql}"' '''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


async def create_tenant_from_template(
    subdomain: str,
    company_name: str = None,
    server_id: str = None
) -> Dict[str, Any]:
    """
    Crea tenant duplicando template_tenant via SQL directo (más rápido)
    
    Esta función es la recomendada para crear nuevos tenants en producción.
    Duplica template_tenant y configura los datos del nuevo tenant.
    """
    # Normalizar
    subdomain = subdomain.lower().strip().replace(" ", "_").replace("-", "_")
    subdomain = ''.join(c for c in subdomain if c.isalnum() or c == '_')
    
    if len(subdomain) < 3:
        return {"success": False, "error": "Nombre debe tener mínimo 3 caracteres"}
    if len(subdomain) > 30:
        return {"success": False, "error": "Nombre no puede exceder 30 caracteres"}
    
    reserved = ['admin', 'api', 'www', 'mail', 'postgres', 'template', 'template_tenant']
    if subdomain in reserved:
        return {"success": False, "error": f"'{subdomain}' es nombre reservado"}
    
    if company_name is None:
        company_name = subdomain.replace("_", " ").title()
    
    # Obtener servidor
    server = ODOO_SERVERS.get(server_id) if server_id else list(ODOO_SERVERS.values())[0]
    if not server:
        return {"success": False, "error": "Servidor no disponible"}
    
    pct_id = server.pct_id
    
    try:
        # 1. Verificar que no existe
        check_sql = f"SELECT 1 FROM pg_database WHERE datname = '{subdomain}'"
        success, output = _run_pct_sql(pct_id, "postgres", check_sql)
        if "1" in output:
            return {"success": False, "error": f"BD '{subdomain}' ya existe"}
        
        # 2. Verificar template existe
        check_template = f"SELECT 1 FROM pg_database WHERE datname = '{TEMPLATE_DB}'"
        success, output = _run_pct_sql(pct_id, "postgres", check_template)
        if "1" not in output:
            return {"success": False, "error": f"Template '{TEMPLATE_DB}' no existe"}
        
        logger.info(f"Creando tenant '{subdomain}' desde template...")
        
        # 3. Terminar conexiones al template
        terminate_sql = f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{TEMPLATE_DB}' AND pid <> pg_backend_pid()"
        _run_pct_sql(pct_id, "postgres", terminate_sql)
        
        # 4. Duplicar BD
        create_cmd = f'''pct exec {pct_id} -- bash -c 'export PGPASSWORD="{DEFAULT_DB_PASSWORD}"; psql -h 127.0.0.1 -U {DEFAULT_DB_USER} -d postgres -c "CREATE DATABASE \\"{subdomain}\\" WITH TEMPLATE \\"{TEMPLATE_DB}\\" OWNER \\"{DEFAULT_DB_USER}\\";"' '''
        
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0 or "ERROR" in result.stderr:
            logger.error(f"Error creando BD: {result.stderr}")
            return {"success": False, "error": f"Error duplicando BD: {result.stderr}"}
        
        logger.info(f"BD '{subdomain}' duplicada, configurando...")
        
        # 5. Configurar nueva BD
        base_url = f"https://{subdomain}.{BASE_DOMAIN}"
        config_sql = f"""
        UPDATE res_company SET name = '{company_name}' WHERE id = 1;
        UPDATE res_partner SET name = '{company_name}' WHERE id = 1;
        UPDATE ir_config_parameter SET value = '{base_url}' WHERE key = 'web.base.url';
        UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
        """
        
        _run_pct_sql(pct_id, subdomain, config_sql)
        
        logger.info(f"✅ Tenant '{subdomain}' creado exitosamente")
        
        return {
            "success": True,
            "database": subdomain,
            "company_name": company_name,
            "server": server.id,
            "server_name": server.name,
            "url": f"https://{subdomain}.{BASE_DOMAIN}",
            "admin_login": DEFAULT_ADMIN_LOGIN,
            "admin_password": DEFAULT_ADMIN_PASSWORD,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error creando tenant: {e}")
        return {"success": False, "error": str(e)}


async def create_tenant_api(
    subdomain: str,
    company_name: str = None,
    server_id: str = None,
    admin_login: str = DEFAULT_ADMIN_LOGIN,
    admin_password: str = DEFAULT_ADMIN_PASSWORD,
    use_fast_method: bool = True
) -> Dict[str, Any]:
    """
    Endpoint: crea un nuevo tenant
    
    Args:
        subdomain: Nombre del tenant
        company_name: Nombre de la empresa
        server_id: ID del servidor (opcional)
        admin_login: Email admin (default: admin@sajet.us)
        admin_password: Password admin (default: 321Abcd.)
        use_fast_method: Si usar SQL directo (más rápido) vs HTTP API
    
    Returns:
        Dict con resultado de la creación
    """
    if use_fast_method:
        # Método rápido via SQL directo (recomendado)
        return await create_tenant_from_template(
            subdomain=subdomain,
            company_name=company_name,
            server_id=server_id
        )
    else:
        # Método tradicional via HTTP API de Odoo
        return await provision_tenant(
            subdomain=subdomain,
            company_name=company_name,
            admin_login=admin_login,
            admin_password=admin_password,
            server_id=server_id
        )

