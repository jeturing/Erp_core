"""
Odoo Database Manager Service
Integra directamente con /web/database/* endpoints de Odoo para gestión de BDs
"""
import httpx
import logging
import subprocess
import shlex
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


# Credenciales Odoo — from centralized config (no hardcoded fallbacks)
from ..config import (
    ODOO_DEFAULT_ADMIN_LOGIN as DEFAULT_ADMIN_LOGIN,
    ODOO_DEFAULT_ADMIN_PASSWORD as DEFAULT_ADMIN_PASSWORD,
    ODOO_MASTER_PASSWORD as DEFAULT_MASTER_PASSWORD,
    ODOO_DB_HOST as DEFAULT_DB_HOST,
    ODOO_DB_PORT as DEFAULT_DB_PORT,
    ODOO_DB_USER as DEFAULT_DB_USER,
    ODOO_DB_PASSWORD as DEFAULT_DB_PASSWORD,
    ODOO_DEFAULT_LANG as DEFAULT_LANG,
    ODOO_DEFAULT_COUNTRY as DEFAULT_COUNTRY,
    ODOO_BASE_DOMAIN as BASE_DOMAIN,
    ODOO_TEMPLATE_DB as TEMPLATE_DB,
    ODOO_FILESTORE_PATH as FILESTORE_PATH,
    ODOO_PRIMARY_IP, ODOO_PRIMARY_PCT_ID, ODOO_PRIMARY_PORT,
)


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
        pct_id=ODOO_PRIMARY_PCT_ID,
        ip=ODOO_PRIMARY_IP,
        port=ODOO_PRIMARY_PORT,
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
        """Verifica si una base de datos existe (directo a postgres, sin Odoo HTTP)"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=DEFAULT_DB_HOST, port=DEFAULT_DB_PORT,
                dbname="postgres", user=DEFAULT_DB_USER,
                password=DEFAULT_DB_PASSWORD, connect_timeout=5,
            )
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            logger.warning(f"database_exists fallback to list: {e}")
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
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="{DEFAULT_DB_PASSWORD}"; psql -h {DEFAULT_DB_HOST} -p {DEFAULT_DB_PORT} -U {DEFAULT_DB_USER} -d {db_name} -c "{sql_commands}"' '''
            
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
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="{DEFAULT_DB_PASSWORD}"; psql -h {DEFAULT_DB_HOST} -p {DEFAULT_DB_PORT} -U {DEFAULT_DB_USER} -d {db_name} -c "{sql_commands}"' '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Configuración reseteada para {db_name}")
            else:
                logger.warning(f"⚠️ Error reseteando config: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"Error reseteando BD {db_name}: {e}")
    
    async def drop_database(self, db_name: str) -> Dict[str, Any]:
        """Elimina una base de datos directamente via psycopg2 + limpia filestore"""
        try:
            protected_dbs = ['postgres', 'template0', 'template1', 'template_tenant', 'cliente1', 'erp_core_db']
            if db_name.lower() in protected_dbs:
                return {"success": False, "error": f"BD '{db_name}' está protegida"}

            import psycopg2
            # 1. Terminar conexiones activas
            conn_term = psycopg2.connect(
                host=DEFAULT_DB_HOST, port=DEFAULT_DB_PORT,
                dbname="postgres", user=DEFAULT_DB_USER,
                password=DEFAULT_DB_PASSWORD, connect_timeout=10,
            )
            conn_term.set_isolation_level(0)
            cur = conn_term.cursor()
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (db_name,)
            )
            cur.close()
            conn_term.close()

            # 2. DROP DATABASE
            conn_drop = psycopg2.connect(
                host=DEFAULT_DB_HOST, port=DEFAULT_DB_PORT,
                dbname="postgres", user=DEFAULT_DB_USER,
                password=DEFAULT_DB_PASSWORD, connect_timeout=10,
            )
            conn_drop.set_isolation_level(0)
            cur2 = conn_drop.cursor()
            cur2.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            cur2.close()
            conn_drop.close()

            # 3. Limpiar filestore en LXC 105 via SSH→pct
            _run_pct_shell(
                self.server.pct_id,
                f'rm -rf {FILESTORE_PATH}/{db_name}'
            )

            logger.info(f"✅ BD '{db_name}' eliminada")
            return {"success": True, "database": db_name, "deleted_at": datetime.utcnow().isoformat()}

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
            
            cmd = f'''pct exec {self.server.pct_id} -- bash -c 'export PGPASSWORD="{DEFAULT_DB_PASSWORD}"; psql -h {DEFAULT_DB_HOST} -p {DEFAULT_DB_PORT} -U {DEFAULT_DB_USER} -d {db_name} -t -A -F"," -c "{sql}"' '''
            
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
    """Crea registro DNS CNAME en Cloudflare apuntando al tunnel principal"""
    try:
        from .cloudflare_manager import CloudflareManager
        from ..config import CLOUDFLARE_TUNNEL_ID
        
        tunnel_id = CLOUDFLARE_TUNNEL_ID
        if not tunnel_id:
            logger.warning("CLOUDFLARE_TUNNEL_ID no configurado, no se puede crear DNS")
            return {"success": False, "error": "CLOUDFLARE_TUNNEL_ID no configurado"}

        result = await CloudflareManager.create_dns_record(
            subdomain=subdomain,
            tunnel_id=tunnel_id,
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
    """
    Ejecuta SQL en PostgreSQL de Odoo (10.10.10.137) via:
      LXC 160  →SSH→  Proxmox host  →pct exec 105→  psql -h 10.10.10.137
    
    Esto garantiza que el SQL corra en el contexto correcto del LXC de Odoo.
    Para queries de administración de BD (CREATE DATABASE etc.) se usa psycopg2 directo.
    """
    try:
        from ..config import PROXMOX_SSH_HOST, PROXMOX_SSH_USER, PROXMOX_SSH_KEY
        # Escapar SQL para pasar por shell remota doble (SSH → pct exec → bash)
        sql_escaped = sql.replace("'", "'\\''").replace('"', '\\"')
        remote_cmd = (
            f'pct exec {pct_id} -- bash -c '
            f'"PGPASSWORD={DEFAULT_DB_PASSWORD} psql -h {DEFAULT_DB_HOST} -p {DEFAULT_DB_PORT} '
            f'-U {DEFAULT_DB_USER} -d {database} -t -A -c \\"{sql_escaped}\\""'
        )
        cmd = [
            'ssh', '-i', PROXMOX_SSH_KEY,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{PROXMOX_SSH_USER}@{PROXMOX_SSH_HOST}',
            remote_cmd
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Timeout SSH→pct"
    except Exception as e:
        return False, str(e)


def _run_pct_shell(pct_id: int, bash_cmd: str, timeout: int = 60) -> tuple:
    """
    Ejecuta un comando de shell arbitrario dentro del LXC via SSH al host Proxmox.
    Usado para operaciones de filestore (cp, mkdir, chown).
    """
    try:
        from ..config import PROXMOX_SSH_HOST, PROXMOX_SSH_USER, PROXMOX_SSH_KEY
        remote_cmd = f"pct exec {pct_id} -- bash -c {shlex.quote(bash_cmd)}"
        cmd = [
            'ssh', '-i', PROXMOX_SSH_KEY,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{PROXMOX_SSH_USER}@{PROXMOX_SSH_HOST}',
            remote_cmd
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout SSH→pct shell"
    except Exception as e:
        return False, str(e)


def query_admin_login_pg(server_ip: str, db_name: str, db_port: int = 5432) -> Optional[str]:
    """
    Consulta el login real del admin (id=2) directamente en PostgreSQL de Odoo.
    Retorna el login o None si no se puede conectar.
    """
    try:
        import psycopg
        with psycopg.connect(
            host=DEFAULT_DB_HOST,
            port=DEFAULT_DB_PORT,
            dbname=db_name,
            user=DEFAULT_DB_USER,
            password=DEFAULT_DB_PASSWORD,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT login FROM res_users WHERE id = 2")
                row = cur.fetchone()
                if row:
                    return row[0]
    except Exception as e:
        logger.warning(f"No se pudo consultar admin login en {db_name}@{server_ip}: {e}")
    return None


async def create_tenant_from_template(
    subdomain: str,
    company_name: str = None,
    server_id: str = None,
    admin_login: str = None,
    admin_password: str = None
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
    
    # Resolver login/password finales
    final_login = admin_login or DEFAULT_ADMIN_LOGIN
    final_password = admin_password or DEFAULT_ADMIN_PASSWORD
    
    # Obtener servidor
    server = ODOO_SERVERS.get(server_id) if server_id else list(ODOO_SERVERS.values())[0]
    if not server:
        return {"success": False, "error": "Servidor no disponible"}
    
    pct_id = server.pct_id
    
    try:
        # 1. Verificar si ya existe
        check_sql = f"SELECT 1 FROM pg_database WHERE datname = '{subdomain}'"
        success, output = _run_pct_sql(pct_id, "postgres", check_sql)
        if "1" in output:
            # BD ya existe — verificar si es funcional (tiene tabla res_company)
            verify_sql = "SELECT name FROM res_company WHERE id = 1 LIMIT 1"
            v_ok, v_out = _run_pct_sql(pct_id, subdomain, verify_sql)
            existing_name = v_out.strip().split('\n')[-1].strip() if v_ok and v_out.strip() else company_name
            base_url = f"https://{subdomain}.{BASE_DOMAIN}"
            
            # Asegurar filestore completo incluso si BD ya existía
            fs_fix_cmd = (
                f'mkdir -p {FILESTORE_PATH}/{subdomain}; '
                f'cp -an {FILESTORE_PATH}/{TEMPLATE_DB}/. {FILESTORE_PATH}/{subdomain}/ 2>/dev/null; '
                f'chown -R odoo:odoo {FILESTORE_PATH}/{subdomain}/'
            )
            _run_pct_shell(pct_id, fs_fix_cmd, timeout=60)
            
            logger.info(f"BD '{subdomain}' ya existe y es funcional — retornando éxito idempotente")
            return {
                "success": True,
                "already_existed": True,
                "database": subdomain,
                "company_name": existing_name or company_name,
                "server": server.id,
                "server_name": server.name,
                "url": base_url,
                "admin_login": final_login,
                "admin_password": final_password,
                "created_at": datetime.utcnow().isoformat(),
            }
        
        # 2. Verificar template existe
        check_template = f"SELECT 1 FROM pg_database WHERE datname = '{TEMPLATE_DB}'"
        success, output = _run_pct_sql(pct_id, "postgres", check_template)
        if "1" not in output:
            return {"success": False, "error": f"Template '{TEMPLATE_DB}' no existe"}
        
        logger.info(f"Creando tenant '{subdomain}' desde template...")
        
        # 3. Terminar conexiones al template
        terminate_sql = f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{TEMPLATE_DB}' AND pid <> pg_backend_pid()"
        _run_pct_sql(pct_id, "postgres", terminate_sql)
        
        # 4. Duplicar BD directamente via psycopg2 con AUTOCOMMIT
        try:
            import psycopg2
            conn_create = psycopg2.connect(
                host=DEFAULT_DB_HOST,
                port=DEFAULT_DB_PORT,
                dbname="postgres",
                user=DEFAULT_DB_USER,
                password=DEFAULT_DB_PASSWORD,
                connect_timeout=30,
            )
            conn_create.set_isolation_level(0)  # AUTOCOMMIT requerido para CREATE DATABASE
            cur_create = conn_create.cursor()
            cur_create.execute(f'CREATE DATABASE "{subdomain}" WITH TEMPLATE "{TEMPLATE_DB}" OWNER "{DEFAULT_DB_USER}"')
            cur_create.close()
            conn_create.close()
            logger.info(f"BD '{subdomain}' creada exitosamente")
        except Exception as e:
            logger.error(f"Error creando BD: {e}")
            return {"success": False, "error": f"Error duplicando BD: {str(e)}"}
        
        logger.info(f"BD '{subdomain}' duplicada, copiando filestore...")
        
        # 4.5 Copiar filestore del template al nuevo tenant
        # El filestore está en el filesystem del LXC 105 — se accede via SSH→pct exec
        fs_cmd = (
            f'mkdir -p {FILESTORE_PATH}/{subdomain} && '
            f'cp -an {FILESTORE_PATH}/{TEMPLATE_DB}/. {FILESTORE_PATH}/{subdomain}/ && '
            f'chown -R odoo:odoo {FILESTORE_PATH}/{subdomain} && '
            f'echo filestore_ok'
        )
        fs_ok, fs_out = _run_pct_shell(pct_id, fs_cmd, timeout=90)
        if fs_ok and "filestore_ok" in fs_out:
            logger.info(f"✅ Filestore copiado para '{subdomain}'")
        else:
            logger.warning(f"⚠️ No se pudo copiar filestore: {fs_out} — iconos podrían no funcionar")
        
        # 5. Configurar nueva BD
        base_url = f"https://{subdomain}.{BASE_DOMAIN}"
        config_sql = f"""
        UPDATE res_company SET name = '{company_name}' WHERE id = 1;
        UPDATE res_partner SET name = '{company_name}' WHERE id = 1;
        UPDATE ir_config_parameter SET value = '{base_url}' WHERE key = 'web.base.url';
        UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
        """
        
        _run_pct_sql(pct_id, subdomain, config_sql)
        
        # 6. Actualizar credenciales admin si son diferentes al default
        if final_login != DEFAULT_ADMIN_LOGIN or final_password != DEFAULT_ADMIN_PASSWORD:
            cred_sql = f"""
            UPDATE res_users SET login = '{final_login}' WHERE id = 2;
            UPDATE res_partner SET email = '{final_login}' WHERE id IN (SELECT partner_id FROM res_users WHERE id = 2);
            """
            if final_password != DEFAULT_ADMIN_PASSWORD:
                cred_sql += f"UPDATE res_users SET password = '{final_password}' WHERE id = 2;\n"
            
            ok, out = _run_pct_sql(pct_id, subdomain, cred_sql)
            if ok:
                logger.info(f"✅ Credenciales admin actualizadas: login={final_login}")
            else:
                logger.warning(f"⚠️ Error actualizando credenciales: {out}")
        
        logger.info(f"✅ Tenant '{subdomain}' creado exitosamente")
        
        return {
            "success": True,
            "database": subdomain,
            "company_name": company_name,
            "server": server.id,
            "server_name": server.name,
            "url": f"https://{subdomain}.{BASE_DOMAIN}",
            "admin_login": final_login,
            "admin_password": final_password,
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
        admin_login: Email admin (from env ODOO_DEFAULT_ADMIN_LOGIN)
        admin_password: Password admin (from env ODOO_DEFAULT_ADMIN_PASSWORD)
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

