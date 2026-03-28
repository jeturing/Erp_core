"""
Odoo Database Manager Service
Integra directamente con /web/database/* endpoints de Odoo para gestión de BDs
"""
import httpx
import logging
import subprocess
import shlex
import os
import json
import shutil
import asyncio
import secrets
import string
from pathlib import Path
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
    ODOO_FILESTORE_PCT_ID,
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


# =====================================================
# LOCALIZACIÓN POR PAÍS — Configuración automática
# =====================================================
# Mapea country_code ISO → módulos l10n, chart of accounts,
# moneda, zona horaria, idioma e impuestos a instalar.
# El key "modules" lista los módulos técnicos de Odoo.
# "chart_template" es el xmlid del chart a instalar.

COUNTRY_LOCALIZATION: Dict[str, Dict[str, Any]] = {
    "DO": {
        "name": "República Dominicana",
        "modules": ["l10n_do", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_do.do_chart_template",
        "currency": "DOP",
        "timezone": "America/Santo_Domingo",
        "lang": "es_DO",
        "phone_code": "+1",
    },
    "US": {
        "name": "Estados Unidos",
        "modules": ["l10n_us"],
        "chart_template": "l10n_us.generate_l10n_us_chart",
        "currency": "USD",
        "timezone": "America/New_York",
        "lang": "en_US",
        "phone_code": "+1",
    },
    "MX": {
        "name": "México",
        "modules": ["l10n_mx", "l10n_mx_edi", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_mx.mx_coa",
        "currency": "MXN",
        "timezone": "America/Mexico_City",
        "lang": "es_MX",
        "phone_code": "+52",
    },
    "CO": {
        "name": "Colombia",
        "modules": ["l10n_co", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_co.l10n_co_chart_template",
        "currency": "COP",
        "timezone": "America/Bogota",
        "lang": "es_CO",
        "phone_code": "+57",
    },
    "ES": {
        "name": "España",
        "modules": ["l10n_es"],
        "chart_template": "l10n_es.account_chart_template_pymes",
        "currency": "EUR",
        "timezone": "Europe/Madrid",
        "lang": "es_ES",
        "phone_code": "+34",
    },
    "PA": {
        "name": "Panamá",
        "modules": ["l10n_pa", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_pa.pa_chart_template",
        "currency": "PAB",
        "timezone": "America/Panama",
        "lang": "es_PA",
        "phone_code": "+507",
    },
    "CL": {
        "name": "Chile",
        "modules": ["l10n_cl", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_cl.cl_chart",
        "currency": "CLP",
        "timezone": "America/Santiago",
        "lang": "es_CL",
        "phone_code": "+56",
    },
    "AR": {
        "name": "Argentina",
        "modules": ["l10n_ar", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_ar.l10nar_ri_chart",
        "currency": "ARS",
        "timezone": "America/Argentina/Buenos_Aires",
        "lang": "es_AR",
        "phone_code": "+54",
    },
    "PE": {
        "name": "Perú",
        "modules": ["l10n_pe", "l10n_latam_invoice_document", "l10n_latam_base"],
        "chart_template": "l10n_pe.pe_chart_template",
        "currency": "PEN",
        "timezone": "America/Lima",
        "lang": "es_PE",
        "phone_code": "+51",
    },
}

# Módulos base que siempre se instalan en cada tenant nuevo
TENANT_BASE_MODULES = [
    "contacts",
    "sale_management",
    "purchase",
    "stock",
    "account",
    "website",
    "crm",
]

# Módulos Jeturing de infraestructura — siempre se instalan (plataforma SaaS)
JETURING_INFRA_MODULES = [
    "jeturing_erp_sync",       # Sincronización webhooks con ERP Core
    "jeturing_branding",       # Rebranding Odoo → Jeturing/Sajet + catálogo errores
    "jeturing_universal_api",  # API REST universal para IA/MCP
    "redis_session_store",     # Sesiones HTTP en Redis (multi-nodo)
    "spiffy_theme_backend",    # Theme backend PWA + app drawer
]

# Módulo de sincronización Jeturing (backward compat)
JETURING_SYNC_MODULE = "jeturing_erp_sync"


def _resolve_blueprint_modules(blueprint_package_name: Optional[str] = None) -> List[str]:
    """
    Consulta la BD (module_packages) para obtener la lista de módulos técnicos
    del blueprint/paquete indicado.

    Si no se especifica paquete, retorna lista vacía.
    Los módulos core (web, portal) ya están en TENANT_BASE_MODULES,
    así que se filtran duplicados al momento de instalar.

    Args:
        blueprint_package_name: Nombre técnico del paquete (ej: 'pkg_restaurantes')

    Returns:
        Lista de technical_names de módulos del paquete
    """
    if not blueprint_package_name:
        return []

    try:
        from ..models.database import ModulePackage, SessionLocal
        db = SessionLocal()
        try:
            pkg = db.query(ModulePackage).filter(
                ModulePackage.name == blueprint_package_name,
                ModulePackage.is_active == True,
            ).first()
            if pkg and pkg.module_list:
                modules = list(pkg.module_list) if isinstance(pkg.module_list, list) else []
                logger.info(f"Blueprint '{blueprint_package_name}' → {len(modules)} módulos: {modules}")
                return modules
            else:
                logger.warning(f"Blueprint '{blueprint_package_name}' no encontrado o sin módulos")
                return []
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Error resolviendo blueprint '{blueprint_package_name}': {e}")
        return []


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
    can_host_tenants: bool = False
    
    @property
    def base_url(self) -> str:
        return f"http://{self.ip}:{self.port}"
    
    @property
    def available_slots(self) -> int:
        return max(0, self.max_databases - self.current_databases)


# Pool de servidores disponibles
_PRIMARY_SERVER_ID = f"pct-{ODOO_PRIMARY_PCT_ID}"


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _parse_server_status(value: Any) -> ServerStatus:
    try:
        if not value:
            return ServerStatus.online
        normalized = str(value).strip().lower()
        return ServerStatus(normalized)
    except Exception:
        return ServerStatus.online


def _load_extra_servers_from_config() -> List[OdooServer]:
    """
    Carga nodos extra desde config centralizada:
    - ODOO_EXTRA_NODES_JSON (preferencia: BD system_config > ENV)
    Formato esperado: JSON array de objetos con ip/pct_id opcionales de tuning.
    """
    raw = _get_config("ODOO_EXTRA_NODES_JSON", os.getenv("ODOO_EXTRA_NODES_JSON", "[]"))
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except Exception as e:
        logger.warning(f"ODOO_EXTRA_NODES_JSON inválido, se ignora: {e}")
        return []

    if isinstance(parsed, dict):
        parsed = parsed.get("servers", [])
    if not isinstance(parsed, list):
        logger.warning("ODOO_EXTRA_NODES_JSON debe ser lista o {'servers': [...]}.")
        return []

    servers: List[OdooServer] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue

        ip = str(item.get("ip", "")).strip()
        pct_id = _safe_int(item.get("pct_id"), 0)
        if not ip or pct_id <= 0:
            continue

        server_id = str(item.get("id") or f"pct-{pct_id}").strip().lower()
        server_name = str(item.get("name") or f"Servidor Odoo (PCT {pct_id})").strip()

        servers.append(
            OdooServer(
                id=server_id,
                name=server_name,
                pct_id=pct_id,
                ip=ip,
                port=_safe_int(item.get("port"), 8069),
                max_databases=max(1, _safe_int(item.get("max_databases"), 50)),
                priority=max(1, _safe_int(item.get("priority"), 5)),
                region=str(item.get("region") or "secondary").strip(),
                status=_parse_server_status(item.get("status")),
                can_host_tenants=bool(
                    item.get(
                        "can_host_tenants",
                        item.get("tenant_provisioning_enabled", False),
                    )
                ),
            )
        )
    return servers


def _build_odoo_servers() -> Dict[str, OdooServer]:
    servers: Dict[str, OdooServer] = {
        _PRIMARY_SERVER_ID: OdooServer(
            id=_PRIMARY_SERVER_ID,
            name=f"Servidor Principal (PCT {ODOO_PRIMARY_PCT_ID})",
            pct_id=ODOO_PRIMARY_PCT_ID,
            ip=ODOO_PRIMARY_IP,
            port=ODOO_PRIMARY_PORT,
            max_databases=50,
            priority=10,
            region="primary",
            can_host_tenants=True,
        )
    }

    for extra in _load_extra_servers_from_config():
        if extra.id in servers:
            logger.info(f"ODOO extra node '{extra.id}' sobrescribe definición existente")
        servers[extra.id] = extra

    return servers


ODOO_SERVERS: Dict[str, OdooServer] = _build_odoo_servers()


def refresh_odoo_servers() -> Dict[str, OdooServer]:
    """Recarga el catálogo de nodos Odoo delegando a NodeRegistry."""
    global ODOO_SERVERS
    try:
        from .node_registry import get_node_registry
        registry = get_node_registry()
        registry.invalidate()
        # NodeRegistry es async, pero refresh es sync context.
        # Actualizamos desde BD directamente.
        servers = registry._load_from_db()
        if servers:
            ODOO_SERVERS = servers
        else:
            ODOO_SERVERS = _build_odoo_servers()
    except Exception:
        ODOO_SERVERS = _build_odoo_servers()
    return ODOO_SERVERS


def _iter_tenant_hosting_servers() -> List[OdooServer]:
    """Retorna solo los nodos habilitados para provisionar tenants SaaS."""
    return [server for server in ODOO_SERVERS.values() if server.can_host_tenants]

def _load_protected_tenants() -> set[str]:
    """Lista de tenants protegidos para evitar borrados accidentales."""
    raw = os.getenv("PROTECTED_TENANTS", "cliente1,tcs")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


PROTECTED_TENANTS = _load_protected_tenants()


def is_tenant_protected(subdomain: str) -> bool:
    return subdomain.strip().lower() in PROTECTED_TENANTS


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
            
            # Odoo /web/database/create espera campos del formulario (x-www-form-urlencoded),
            # no JSON-RPC.
            payload = {
                "master_pwd": self.master_password,
                "name": db_name,
                "login": admin_login,
                "password": admin_password,
                "lang": lang,
                "country_code": country_code,
                "phone": "",
            }
            
            response = await self.client.post(
                f"{self.server.base_url}/web/database/create",
                data=payload,
                timeout=600.0  # 10 min para creación
            )
            
            if response.status_code == 200:
                body_lower = (response.text or "").lower()
                if "database creation error" in body_lower or "access denied" in body_lower:
                    if "database manager has been disabled" in body_lower:
                        msg = "Odoo DB manager deshabilitado o master password inválido"
                    else:
                        msg = "Odoo rechazó la creación de BD (Access Denied)"
                    logger.error(f"Error creando BD: {msg}")
                    return {"success": False, "error": msg, "error_type": "odoo_access_denied"}
                
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
                    "error": f"HTTP {response.status_code}: {(response.text or '')[:400]}",
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
            UPDATE ir_config_parameter SET value = 'False' WHERE key = 'web.base.url.freeze';
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
                data={
                    "master_pwd": self.master_password,
                    "name": source_db,
                    "new_name": new_db_name
                },
                timeout=600.0
            )
            
            if response.status_code == 200:
                body_lower = (response.text or "").lower()
                if "database duplication error" in body_lower or "access denied" in body_lower:
                    if "database manager has been disabled" in body_lower:
                        msg = "Odoo DB manager deshabilitado o master password inválido"
                    else:
                        msg = "Odoo rechazó la duplicación de BD (Access Denied)"
                    return {"success": False, "error": msg, "error_type": "odoo_access_denied"}
                
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
                    "error": f"HTTP {response.status_code}: {(response.text or '')[:400]}",
                    "error_type": "http_error"
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
            UPDATE ir_config_parameter SET value = 'False' WHERE key = 'web.base.url.freeze';
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
        """
        Elimina una base de datos vía PostgreSQL con reintentos y terminación de conexiones activas.
        Incluye verificación post-delete para evitar falsos positivos.
        """
        try:
            protected_dbs = ['postgres', 'template0', 'template1', 'template_tenant']
            if db_name.lower() in protected_dbs:
                return {"success": False, "error": f"BD '{db_name}' está protegida"}

            import psycopg2
            max_attempts = int(os.getenv("ODOO_DROP_DB_RETRIES", "4"))
            base_delay = float(os.getenv("ODOO_DROP_DB_RETRY_DELAY_SECONDS", "1.5"))

            last_error = None
            last_active_connections = 0
            total_terminated = 0

            for attempt in range(1, max_attempts + 1):
                try:
                    # 1) Terminar conexiones activas al tenant
                    with psycopg2.connect(
                        host=DEFAULT_DB_HOST,
                        port=DEFAULT_DB_PORT,
                        dbname="postgres",
                        user=DEFAULT_DB_USER,
                        password=DEFAULT_DB_PASSWORD,
                        connect_timeout=10,
                    ) as conn_term:
                        conn_term.set_isolation_level(0)
                        with conn_term.cursor() as cur:
                            cur.execute(
                                "SELECT count(*) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                                (db_name,),
                            )
                            row = cur.fetchone()
                            last_active_connections = int(row[0]) if row and row[0] is not None else 0

                            cur.execute(
                                "SELECT pg_terminate_backend(pid) "
                                "FROM pg_stat_activity "
                                "WHERE datname = %s AND pid <> pg_backend_pid()",
                                (db_name,),
                            )
                            terminated_rows = cur.fetchall() or []
                            terminated_now = sum(1 for r in terminated_rows if r and r[0] is True)
                            total_terminated += terminated_now

                    # 2) Intentar DROP DATABASE (FORCE cuando disponible)
                    with psycopg2.connect(
                        host=DEFAULT_DB_HOST,
                        port=DEFAULT_DB_PORT,
                        dbname="postgres",
                        user=DEFAULT_DB_USER,
                        password=DEFAULT_DB_PASSWORD,
                        connect_timeout=10,
                    ) as conn_drop:
                        conn_drop.set_isolation_level(0)
                        with conn_drop.cursor() as cur2:
                            try:
                                cur2.execute(f'DROP DATABASE "{db_name}" WITH (FORCE)')
                            except Exception:
                                cur2.execute(f'DROP DATABASE IF EXISTS "{db_name}"')

                    # 3) Verificación estricta post-delete
                    with psycopg2.connect(
                        host=DEFAULT_DB_HOST,
                        port=DEFAULT_DB_PORT,
                        dbname="postgres",
                        user=DEFAULT_DB_USER,
                        password=DEFAULT_DB_PASSWORD,
                        connect_timeout=10,
                    ) as conn_verify:
                        with conn_verify.cursor() as cur3:
                            cur3.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                            still_exists = cur3.fetchone() is not None

                    if not still_exists:
                        # 4) Limpiar filestore
                        _run_pct_shell(
                            self.server.pct_id,
                            f'rm -rf {FILESTORE_PATH}/{db_name}'
                        )

                        logger.info(
                            f"✅ BD '{db_name}' eliminada en intento {attempt} "
                            f"(conexiones_activas_previas={last_active_connections}, terminadas_total={total_terminated})"
                        )
                        return {
                            "success": True,
                            "database": db_name,
                            "deleted_at": datetime.utcnow().isoformat(),
                            "attempts": attempt,
                            "active_connections_before_drop": last_active_connections,
                            "terminated_connections": total_terminated,
                            "server": self.server.id,
                        }

                    last_error = (
                        f"La BD '{db_name}' sigue existiendo tras intento {attempt} "
                        f"(conexiones_activas_previas={last_active_connections})"
                    )
                    logger.warning(last_error)

                except Exception as attempt_err:
                    last_error = str(attempt_err)
                    logger.warning(
                        f"Intento {attempt}/{max_attempts} falló eliminando '{db_name}' "
                        f"en {self.server.id}: {attempt_err}"
                    )

                if attempt < max_attempts:
                    await asyncio.sleep(base_delay * attempt)

            return {
                "success": False,
                "error": (
                    f"No se pudo eliminar la BD '{db_name}' tras {max_attempts} intentos. "
                    f"Último error: {last_error or 'desconocido'}"
                ),
                "database": db_name,
                "attempts": max_attempts,
                "active_connections": last_active_connections,
                "terminated_connections": total_terminated,
                "server": self.server.id,
            }

        except Exception as e:
            logger.exception(f"Error eliminando BD: {e}")
            return {"success": False, "error": str(e)}

    async def create_database_backup(
        self,
        db_name: str,
        backup_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Genera un backup lógico (.dump) de la BD en el nodo de API."""
        try:
            if not await self.database_exists(db_name):
                return {"success": False, "error": f"Tenant '{db_name}' no encontrado para backup"}

            target_dir = backup_dir or os.getenv("TENANT_BACKUP_DIR", "/tmp/sajet_tenant_backups")
            Path(target_dir).mkdir(parents=True, exist_ok=True)

            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{db_name}_{ts}.dump"
            backup_path = str(Path(target_dir) / backup_file)

            env = os.environ.copy()
            env["PGPASSWORD"] = DEFAULT_DB_PASSWORD
            # erp-core.service define PATH solo al venv; incluir rutas del sistema para pg_dump
            env["PATH"] = f"{env.get('PATH', '')}:/usr/bin:/bin:/usr/lib/postgresql/15/bin"
            pg_dump_bin = shutil.which("pg_dump", path=env["PATH"])
            if not pg_dump_bin:
                return {"success": False, "error": "pg_dump no está disponible en el servidor API"}

            cmd = [
                pg_dump_bin,
                "-h", DEFAULT_DB_HOST,
                "-p", str(DEFAULT_DB_PORT),
                "-U", DEFAULT_DB_USER,
                "-Fc",
                "-f", backup_path,
                db_name,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or result.stdout.strip() or "pg_dump falló",
                }

            size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            if size <= 0:
                return {"success": False, "error": "Backup generado sin contenido"}

            return {
                "success": True,
                "database": db_name,
                "backup_path": backup_path,
                "backup_file": backup_file,
                "backup_size": size,
                "created_at": datetime.utcnow().isoformat(),
                "server": self.server.id,
                "server_name": self.server.name,
            }
        except Exception as e:
            logger.exception(f"Error generando backup de {db_name}: {e}")
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
    """Obtiene lista de servidores disponibles con su estado via NodeRegistry"""
    try:
        from .node_registry import get_node_registry
        registry = get_node_registry()
        all_servers = await registry.get_servers(force_refresh=True)
    except Exception:
        refresh_odoo_servers()
        all_servers = ODOO_SERVERS

    servers = []

    for server_id, server in all_servers.items():
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
                    "can_host_tenants": server.can_host_tenants,
                    "databases": databases
                })
        except Exception as e:
            logger.error(f"Error obteniendo estado de {server_id}: {e}")
            servers.append({
                "id": server.id,
                "name": server.name,
                "pct_id": server.pct_id,
                "status": "offline",
                "can_host_tenants": server.can_host_tenants,
                "error": str(e)
            })
    
    return servers


async def select_best_server() -> Optional[OdooServer]:
    """Selecciona el mejor servidor disponible delegando a NodeRegistry."""
    try:
        from .node_registry import get_node_registry
        registry = get_node_registry()
        return await registry.select_best_for_tenant()
    except Exception as e:
        logger.warning(f"NodeRegistry no disponible, usando fallback legacy: {e}")
        # Fallback legacy para compatibilidad
        refresh_odoo_servers()
        best_server = None
        best_score = -1

        for server in _iter_tenant_hosting_servers():
            if server.status != ServerStatus.online:
                continue

            try:
                async with OdooDatabaseManager(server) as manager:
                    databases = await manager.list_databases()
                    server.current_databases = len(databases)

                    if server.available_slots <= 0:
                        continue

                    score = server.priority * server.available_slots

                    if score > best_score:
                        best_score = score
                        best_server = server
            except Exception as ex:
                logger.warning(f"Servidor {server.id} no disponible: {ex}")
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
    lang: str = DEFAULT_LANG,
    country_code: str = None,  # Código ISO país para localización (DO, US, MX, etc.)
    blueprint_package_name: str = None,  # Nombre del paquete/blueprint
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
    refresh_odoo_servers()

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
        if not server.can_host_tenants:
            return {
                "success": False,
                "error": f"Servidor '{server_id}' no está habilitado para provisionar tenants"
            }
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
                "error": f"El tenant '{subdomain}' ya existe (detectado en {server.id})"
            }
        
        # Crear BD (duplicando template si existe, o desde cero)
        if use_template and await manager.database_exists(template_db):
            result = await manager.duplicate_database(
                source_db=template_db,
                new_db_name=subdomain,
                admin_login=admin_login,
                admin_password=admin_password
            )
            # Fallback robusto: cuando Odoo DB manager está deshabilitado o falla por master password,
            # usar ruta SQL directa desde template (no depende de /web/database/*).
            if not result.get("success"):
                logger.warning(
                    f"duplicate_database falló para '{subdomain}' en {server.id}: "
                    f"{result.get('error')}. Intentando fallback SQL directo."
                )
                direct_result = await create_tenant_from_template(
                    subdomain=subdomain,
                    company_name=company_name,
                    server_id=server.id,
                    admin_login=admin_login,
                    admin_password=admin_password,
                    country_code=country_code,
                    blueprint_package_name=blueprint_package_name,
                )
                if direct_result.get("success"):
                    result = direct_result
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
            
            # Localización por país + blueprint
            effective_country = (country_code or DEFAULT_COUNTRY).upper().strip()
            bp_modules = _resolve_blueprint_modules(blueprint_package_name)
            try:
                loc_result = _configure_tenant_localization(
                    pct_id=server.pct_id,
                    db_name=subdomain,
                    country_code=effective_country,
                    server_ip=server.ip,
                    server_port=server.port,
                    blueprint_modules=bp_modules,
                )
                result["localization"] = loc_result
            except Exception as loc_err:
                logger.warning(f"⚠️ Error localización en provision_tenant: {loc_err}")
                result["localization"] = {"success": False, "error": str(loc_err)}

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
    refresh_odoo_servers()
    
    # Proteger tenants importantes
    if is_tenant_protected(subdomain):
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


async def backup_tenant(subdomain: str, server_id: Optional[str] = None) -> Dict[str, Any]:
    """Genera backup de un tenant buscando automáticamente su servidor."""
    refresh_odoo_servers()
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
                    return await manager.create_database_backup(subdomain)
        except Exception as e:
            logger.error(f"Error generando backup en {server.id}: {e}")

    return {"success": False, "error": f"Tenant '{subdomain}' no encontrado para backup"}


# =====================================================
# API PARA RUTAS
# =====================================================

async def get_servers_status() -> Dict[str, Any]:
    """Endpoint: obtiene estado de todos los servidores"""
    refresh_odoo_servers()
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
    Ejecuta SQL con preferencia por conexión directa PostgreSQL.
    Si falla, usa fallback legacy SSH→pct exec.
    """
    # Fast path: conexión directa a PostgreSQL (evita dependencia de SSH/proxmox).
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=DEFAULT_DB_HOST,
            port=DEFAULT_DB_PORT,
            dbname=database,
            user=DEFAULT_DB_USER,
            password=DEFAULT_DB_PASSWORD,
            connect_timeout=10,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)

        output = ""
        if cur.description:
            rows = cur.fetchall()
            output = "\n".join(
                "|".join("" if c is None else str(c) for c in row)
                for row in rows
            )
        else:
            output = "OK"

        cur.close()
        conn.close()
        return True, output
    except Exception as direct_err:
        logger.warning(f"_run_pct_sql directo falló, usando fallback SSH→pct: {direct_err}")

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
            '-o', 'IdentitiesOnly=yes',
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
            '-o', 'IdentitiesOnly=yes',
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


# =====================================================
# LOCALIZACIÓN POST-PROVISIÓN
# =====================================================

def _configure_tenant_localization(
    pct_id: int,
    db_name: str,
    country_code: str,
    server_ip: str,
    server_port: int = 8069,
    blueprint_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Configura localización del tenant recién creado según país e instala
    módulos del blueprint seleccionado.

    1. SQL: país de la compañía, moneda, timezone, idioma
    2. XML-RPC: instala módulos (base + infra Jeturing + l10n + blueprint)

    Args:
        pct_id: ID del PCT donde está el Odoo server
        db_name: Nombre de la base de datos del tenant
        country_code: Código ISO 2 letras (DO, US, MX, etc.)
        server_ip: IP del servidor Odoo para XML-RPC
        server_port: Puerto HTTP de Odoo (default 8069)
        blueprint_modules: Módulos adicionales del paquete/blueprint seleccionado

    Returns:
        Dict con resultado de la configuración
    """
    country_code = (country_code or DEFAULT_COUNTRY).upper().strip()
    localization = COUNTRY_LOCALIZATION.get(country_code)

    if not localization:
        logger.warning(
            f"País '{country_code}' sin localización definida — se usará configuración por defecto ({DEFAULT_COUNTRY})"
        )
        localization = COUNTRY_LOCALIZATION.get(DEFAULT_COUNTRY, {})
        if not localization:
            return {"success": False, "error": f"No hay localización para '{country_code}' ni para default '{DEFAULT_COUNTRY}'"}

    lang = localization["lang"]
    timezone = localization["timezone"]
    currency_code = localization["currency"]
    modules_to_install = localization.get("modules", [])
    country_name = localization.get("name", country_code)

    result_details: Dict[str, Any] = {
        "country_code": country_code,
        "lang": lang,
        "timezone": timezone,
        "currency": currency_code,
        "modules": modules_to_install,
    }

    # ── Paso 1: Configurar país, moneda, idioma y timezone vía SQL ──
    safe_tz = timezone.replace("'", "''")
    safe_lang = lang.replace("'", "''")

    localization_sql = f"""
    -- Asignar país a la compañía principal
    UPDATE res_company SET
        country_id = (SELECT id FROM res_country WHERE code = '{country_code}' LIMIT 1)
    WHERE id = 1 AND (SELECT id FROM res_country WHERE code = '{country_code}' LIMIT 1) IS NOT NULL;

    -- Asignar al partner de la compañía
    UPDATE res_partner SET
        country_id = (SELECT id FROM res_country WHERE code = '{country_code}' LIMIT 1),
        lang = '{safe_lang}',
        tz = '{safe_tz}'
    WHERE id = 1 AND (SELECT id FROM res_country WHERE code = '{country_code}' LIMIT 1) IS NOT NULL;

    -- Configurar moneda de la compañía
    UPDATE res_company SET
        currency_id = (SELECT id FROM res_currency WHERE name = '{currency_code}' LIMIT 1)
    WHERE id = 1 AND (SELECT id FROM res_currency WHERE name = '{currency_code}' LIMIT 1) IS NOT NULL;

    -- Activar la moneda si no lo está
    UPDATE res_currency SET active = TRUE
    WHERE name = '{currency_code}';

    -- Timezone e idioma por defecto para nuevos usuarios
    UPDATE ir_config_parameter SET value = '{safe_tz}'
    WHERE key = 'resource.calendar.default.tz';

    -- Insertar si no existe
    INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
    SELECT 'resource.calendar.default.tz', '{safe_tz}', 1, 1, NOW(), NOW()
    WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'resource.calendar.default.tz');

    -- Idioma predeterminado del sistema
    UPDATE res_lang SET active = TRUE WHERE code = '{safe_lang}';

    -- Configurar idioma del admin
    UPDATE res_users SET lang = '{safe_lang}', tz = '{safe_tz}' WHERE id = 2;
    """

    ok, out = _run_pct_sql(pct_id, db_name, localization_sql)
    if ok:
        logger.info(f"✅ Localización SQL aplicada: {country_code} ({country_name}) en '{db_name}'")
        result_details["sql_config"] = "ok"
    else:
        logger.warning(f"⚠️ Error aplicando localización SQL para '{db_name}': {out}")
        result_details["sql_config"] = f"error: {out}"

    # ── Paso 2: Instalar módulos l10n via XML-RPC ──
    # Usamos XML-RPC porque la instalación de módulos requiere el ORM de Odoo.
    # Esto dispara un update del registro de módulos + instalación.
    if modules_to_install:
        try:
            import xmlrpc.client
            url = f"http://{server_ip}:{server_port}"

            # Autenticar como admin
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid = common.authenticate(db_name, DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD, {})

            if not uid:
                # Intentar con login del tenant
                tenant_login = f"{db_name}@{BASE_DOMAIN}"
                uid = common.authenticate(db_name, tenant_login, DEFAULT_ADMIN_PASSWORD, {})

            if uid:
                models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

                installed_modules = []
                failed_modules = []

                # Construir lista completa de módulos a instalar (deduplicada, orden preservado):
                # 1. Base ERP (contacts, sale, purchase, stock, account, website, crm)
                # 2. Localización por país (l10n_do, l10n_mx, etc.)
                # 3. Infraestructura Jeturing (branding, universal_api, redis, spiffy)
                # 4. Módulos del blueprint/paquete seleccionado
                _seen: set = set()
                all_modules: List[str] = []
                for m in (
                    TENANT_BASE_MODULES
                    + modules_to_install
                    + JETURING_INFRA_MODULES
                    + (blueprint_modules or [])
                ):
                    if m not in _seen:
                        _seen.add(m)
                        all_modules.append(m)

                logger.info(
                    f"📦 Módulos a instalar en '{db_name}': {len(all_modules)} total "
                    f"(base={len(TENANT_BASE_MODULES)}, l10n={len(modules_to_install)}, "
                    f"infra={len(JETURING_INFRA_MODULES)}, blueprint={len(blueprint_modules or [])})"
                )

                for module_name in all_modules:
                    try:
                        # Buscar el módulo en ir.module.module
                        module_ids = models.execute_kw(
                            db_name, uid, DEFAULT_ADMIN_PASSWORD,
                            'ir.module.module', 'search',
                            [[('name', '=', module_name)]]
                        )
                        if module_ids:
                            # Leer estado actual
                            module_data = models.execute_kw(
                                db_name, uid, DEFAULT_ADMIN_PASSWORD,
                                'ir.module.module', 'read',
                                [module_ids], {'fields': ['state']}
                            )
                            state = module_data[0]['state'] if module_data else 'uninstalled'

                            if state not in ('installed', 'to upgrade'):
                                # Marcar para instalación
                                models.execute_kw(
                                    db_name, uid, DEFAULT_ADMIN_PASSWORD,
                                    'ir.module.module', 'button_immediate_install',
                                    [module_ids]
                                )
                                installed_modules.append(module_name)
                                logger.info(f"  📦 Módulo '{module_name}' instalado en '{db_name}'")
                            else:
                                logger.info(f"  ✅ Módulo '{module_name}' ya instalado en '{db_name}'")
                                installed_modules.append(f"{module_name}(already)")
                        else:
                            logger.warning(f"  ⚠️ Módulo '{module_name}' no encontrado en '{db_name}'")
                            failed_modules.append(f"{module_name}(not_found)")
                    except Exception as mod_err:
                        logger.warning(f"  ⚠️ Error instalando '{module_name}' en '{db_name}': {mod_err}")
                        failed_modules.append(f"{module_name}(error)")

                result_details["modules_installed"] = installed_modules
                result_details["modules_failed"] = failed_modules
                logger.info(
                    f"✅ Módulos procesados para '{db_name}': "
                    f"OK={len(installed_modules)}, FAIL={len(failed_modules)}"
                )
            else:
                logger.warning(f"⚠️ No se pudo autenticar via XML-RPC en '{db_name}' — módulos no instalados")
                result_details["modules_error"] = "auth_failed"

        except Exception as xmlrpc_err:
            logger.warning(f"⚠️ Error XML-RPC instalando módulos en '{db_name}': {xmlrpc_err}")
            result_details["modules_error"] = str(xmlrpc_err)

    result_details["success"] = True
    return result_details


async def create_tenant_from_template(
    subdomain: str,
    company_name: str = None,
    server_id: str = None,
    admin_login: str = None,
    admin_password: str = None,
    partner_id: int = None,   # ID del partner en la BD de erp-core (para branding + usuario socio)
    country_code: str = None,  # Código ISO país para localización (DO, US, MX, etc.)
    blueprint_package_name: str = None,  # Nombre del paquete/blueprint (ej: pkg_restaurantes)
) -> Dict[str, Any]:
    """
    Crea tenant duplicando template_tenant via SQL directo (más rápido)
    
    Esta función es la recomendada para crear nuevos tenants en producción.
    Duplica template_tenant y configura los datos del nuevo tenant.

    Si se proporciona `partner_id`, se crea un usuario socio adicional con
    permisos Sales (imagen 2) y el email de bienvenida usa el branding del partner.
    """
    refresh_odoo_servers()
    _partner_id = partner_id  # alias interno para usar en los pasos 7b y 8

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
    final_login = admin_login or f"{subdomain}@{BASE_DOMAIN}"
    if admin_password:
        final_password = admin_password
    else:
        alphabet = string.ascii_letters + string.digits + "@#$%!-_"
        final_password = "".join(secrets.choice(alphabet) for _ in range(20))

    def _sql_literal(value: str) -> str:
        return (value or "").replace("'", "''")

    safe_company_name = _sql_literal(company_name)
    safe_base_url = _sql_literal(f"https://{subdomain}.{BASE_DOMAIN}")
    safe_final_login = _sql_literal(final_login)
    safe_final_password = _sql_literal(final_password)
    
    # Obtener servidor. Cuando no se fuerza `server_id`, el fast path debe
    # respetar la misma selección automática que el flujo estándar.
    server = ODOO_SERVERS.get(server_id) if server_id else await select_best_server()
    if not server:
        return {"success": False, "error": "Servidor no disponible"}
    if server_id and not server.can_host_tenants:
        return {
            "success": False,
            "error": f"Servidor '{server_id}' no está habilitado para provisionar tenants"
        }
    
    pct_id = server.pct_id
    filestore_pct_id = ODOO_FILESTORE_PCT_ID
    
    def _fast_error(code: str, message: str, raw: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "success": False,
            "error": message,
            "error_code": code,
        }
        if raw:
            payload["raw_error"] = raw
        return payload

    def _classify_fast_path_error(raw_error: str) -> str:
        text = (raw_error or "").lower()
        if "template" in text and ("no existe" in text or "does not exist" in text):
            return "template_missing"
        if (
            "cannot import name 'proxmox_ssh_host'" in text
            or 'cannot import name "proxmox_ssh_host"' in text
            or "permission denied" in text
            or "ssh:" in text
            or "timeout ssh" in text
            or "pct exec" in text
            or "pct shell" in text
        ):
            return "proxmox_ssh_unavailable"
        if (
            "authentication failed" in text
            or "connection failed" in text
            or "could not connect" in text
            or "timeout" in text
        ):
            return "template_check_failed"
        return "fast_path_unavailable"

    try:
        # 1. Verificar si ya existe
        check_sql = f"SELECT 1 FROM pg_database WHERE datname = '{subdomain}'"
        success, output = _run_pct_sql(pct_id, "postgres", check_sql)
        if not success:
            code = _classify_fast_path_error(output)
            msg = "Fast path no disponible para validar existencia del tenant"
            return _fast_error(code, msg, output)
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
            fs_fix_ok, fs_fix_out = _run_pct_shell(filestore_pct_id, fs_fix_cmd, timeout=60)
            if not fs_fix_ok:
                logger.warning(
                    f"No se pudo reforzar filestore para BD existente '{subdomain}' en pct {filestore_pct_id}: {fs_fix_out}"
                )
            
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
        if not success:
            return _fast_error(
                "template_check_failed",
                f"No se pudo validar el template '{TEMPLATE_DB}'",
                output,
            )
        if "1" not in output:
            return _fast_error("template_missing", f"Template '{TEMPLATE_DB}' no existe")
        
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
            code = _classify_fast_path_error(str(e))
            return _fast_error(code, f"Error duplicando BD: {str(e)}")
        
        logger.info(f"BD '{subdomain}' duplicada, copiando filestore...")
        
        # 4.5 Copiar filestore del template al nuevo tenant
        # El filestore vive en el nodo Odoo de aplicaciones (PCT dedicado) y no en el nodo de BD.
        fs_cmd = (
            f'test -d {FILESTORE_PATH}/{TEMPLATE_DB} && '
            f'mkdir -p {FILESTORE_PATH}/{subdomain} && '
            f'cp -an {FILESTORE_PATH}/{TEMPLATE_DB}/. {FILESTORE_PATH}/{subdomain}/ && '
            f'chown -R odoo:odoo {FILESTORE_PATH}/{subdomain} && '
            f'echo filestore_ok'
        )
        fs_ok, fs_out = _run_pct_shell(filestore_pct_id, fs_cmd, timeout=90)
        if fs_ok and "filestore_ok" in fs_out:
            logger.info(f"✅ Filestore copiado para '{subdomain}'")
        else:
            logger.error(
                f"❌ No se pudo copiar filestore para '{subdomain}' en pct {filestore_pct_id}: {fs_out}"
            )
            return _fast_error(
                "filestore_sync_failed",
                (
                    f"No se pudo copiar filestore desde '{TEMPLATE_DB}'. "
                    "Se bloqueó la creación para evitar tenant sin assets (iconos/apps)."
                ),
                fs_out,
            )
        
        # 4.6 Mantenimiento post-creación: verificar y reparar filestore
        logger.info(f"🔧 Ejecutando mantenimiento post-creación para '{subdomain}'...")
        verify_cmd = (
            f"set -e; "
            f"test -d {FILESTORE_PATH}/{TEMPLATE_DB}; "
            f"mkdir -p {FILESTORE_PATH}/{subdomain}; "
            f"cp -an {FILESTORE_PATH}/{TEMPLATE_DB}/. {FILESTORE_PATH}/{subdomain}/; "
            f"chown -R odoo:odoo {FILESTORE_PATH}/{subdomain}; "
            f"echo filestore_files=$(find {FILESTORE_PATH}/{subdomain} -type f | wc -l)"
        )
        maint_ok, maint_out = _run_pct_shell(filestore_pct_id, verify_cmd, timeout=90)
        if maint_ok and "filestore_files=" in maint_out:
            file_count = maint_out.split("filestore_files=")[-1].strip()
            logger.info(f"✅ Mantenimiento completado: {file_count} archivos verificados en filestore de '{subdomain}'")
        else:
            logger.warning(f"⚠️ Mantenimiento tuvo problemas pero la creación continúa: {maint_out}")
        
        # 5. Configurar nueva BD
        base_url = f"https://{subdomain}.{BASE_DOMAIN}"
        # Leer configuración de Postal desde env (relay interno seguro).
        # El relay SMTP vive en CT 200 / 10.10.10.151 y expone STARTTLS por 587.
        # Para tenants Sajet se prioriza la credencial dedicada de sajet.us.
        _postal_host = os.getenv("POSTAL_SMTP_HOST", "10.10.10.151")
        _postal_port = int(os.getenv("POSTAL_SMTP_PORT", "587"))
        _postal_key = (
            os.getenv("POSTAL_SMTP_KEY_SAJET")
            or os.getenv("POSTAL_SMTP_KEY")
            or "QSyHnBo8wWLbOafPRV7MWtmq"
        )
        _postal_encryption = os.getenv("POSTAL_SMTP_ENCRYPTION", "starttls").lower()
        _postal_from_filter = os.getenv("POSTAL_SMTP_FROM_FILTER", "").strip()
        if _postal_from_filter in {"*@mail.sajet.us", "*@sajet.us"}:
            _postal_from_filter = ""

        safe_postal_host = _postal_host.replace("'", "''")
        safe_postal_key = _postal_key.replace("'", "''")
        safe_postal_encryption = _postal_encryption.replace("'", "''")
        safe_postal_from_filter = _postal_from_filter.replace("'", "''")
        postal_from_filter_sql = f"'{safe_postal_from_filter}'" if safe_postal_from_filter else "NULL"

        config_sql = f"""
        UPDATE res_company SET name = '{safe_company_name}' WHERE id = 1;
        UPDATE res_partner SET name = '{safe_company_name}' WHERE id = 1;
        UPDATE ir_config_parameter SET value = '{safe_base_url}' WHERE key = 'web.base.url';
        UPDATE ir_config_parameter SET value = 'False' WHERE key = 'web.base.url.freeze';
        DELETE FROM ir_sessions;
        UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
        -- Servidor SMTP Postal (relay interno seguro)
        -- El tenant hereda esta configuración; puede añadir su propio servidor con menor sequence.
        DELETE FROM ir_mail_server;
        INSERT INTO ir_mail_server
            (name, smtp_host, smtp_port, smtp_user, smtp_pass, smtp_encryption,
             smtp_authentication, from_filter, active, sequence,
             create_uid, write_uid, create_date, write_date)
        VALUES
            ('Postal Relay — Campañas', '{safe_postal_host}', {_postal_port},
             '{safe_postal_key}', '{safe_postal_key}',
             '{safe_postal_encryption}', 'login', {postal_from_filter_sql},
             true, 20, 1, 1, NOW(), NOW());
        -- Dominio del website
        UPDATE website SET domain = '{subdomain}.{BASE_DOMAIN}' WHERE id = 1;
        """
        
        _run_pct_sql(pct_id, subdomain, config_sql)

        # 6. Credenciales admin Odoo (backend) — siempre actualizar
        cred_sql = (
            f"UPDATE res_users SET login = '{safe_final_login}' WHERE id = 2;\n"
            f"UPDATE res_partner SET email = '{safe_final_login}' WHERE id IN "
            f"(SELECT partner_id FROM res_users WHERE id = 2);\n"
            f"UPDATE res_users SET password = '{safe_final_password}' WHERE id = 2;\n"
        )
        ok, out = _run_pct_sql(pct_id, subdomain, cred_sql)
        if ok:
            logger.info(f"✅ Credenciales admin actualizadas: login={final_login}")
        else:
            logger.warning(f"⚠️ Error actualizando credenciales admin: {out}")

        # 6b. Localización por país + módulos del blueprint
        effective_country = (country_code or DEFAULT_COUNTRY).upper().strip()
        bp_modules = _resolve_blueprint_modules(blueprint_package_name)
        try:
            loc_result = _configure_tenant_localization(
                pct_id=pct_id,
                db_name=subdomain,
                country_code=effective_country,
                server_ip=server.ip,
                server_port=server.port,
                blueprint_modules=bp_modules,
            )
            if loc_result.get("success"):
                logger.info(
                    f"✅ Localización '{effective_country}' + blueprint '{blueprint_package_name or 'none'}' "
                    f"aplicada para '{subdomain}' — modules={loc_result.get('modules_installed', [])}"
                )
            else:
                logger.warning(f"⚠️ Localización parcial para '{subdomain}': {loc_result}")
        except Exception as loc_err:
            logger.warning(f"⚠️ Error en localización de '{subdomain}': {loc_err}")

        # 7. Crear usuario cliente portal (acceso portal Sajet — no accede al backend de Odoo)
        import secrets as _secrets
        client_login    = f"cliente@{subdomain}.sajet.us"
        client_password = _secrets.token_urlsafe(12)
        safe_client_login    = client_login.replace("'", "''")
        safe_client_password = client_password.replace("'", "''")
        safe_client_name     = (safe_company_name + " — Cliente")

        portal_sql = f"""
        DO $$
        DECLARE
            v_partner_id  INTEGER;
            v_user_id     INTEGER;
            v_group_id    INTEGER;
        BEGIN
            INSERT INTO res_partner (name, email, active, type, company_type,
                                     create_uid, write_uid, create_date, write_date)
            VALUES ('{safe_client_name}', '{safe_client_login}',
                    TRUE, 'contact', 'person', 1, 1, NOW(), NOW())
            RETURNING id INTO v_partner_id;

            INSERT INTO res_users (login, password, partner_id, active, share,
                                   create_uid, write_uid, create_date, write_date)
            VALUES ('{safe_client_login}', '{safe_client_password}',
                    v_partner_id, TRUE, TRUE, 1, 1, NOW(), NOW())
            RETURNING id INTO v_user_id;

            -- Asignar grupo Portal
            SELECT id INTO v_group_id FROM res_groups
            WHERE name = 'Portal'
              AND category_id = (
                  SELECT id FROM ir_module_category WHERE name = 'Hidden' LIMIT 1
              )
            LIMIT 1;

            IF v_group_id IS NOT NULL THEN
                INSERT INTO res_groups_users_rel (gid, uid)
                VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
            END IF;
        END$$;
        """
        ok_portal, out_portal = _run_pct_sql(pct_id, subdomain, portal_sql)
        if ok_portal:
            logger.info(f"✅ Usuario cliente portal creado: {client_login}")
        else:
            logger.warning(f"⚠️ Error creando usuario portal: {out_portal}")
            client_password = ""  # No exponer password si falló

        # 7b. Crear usuario socio (partner) con permisos Sales full — imagen 2
        #     Solo se crea si el tenant fue provisionado por un partner identificado.
        #     Si no hay partner, se omite para no contaminar la BD con cuentas huérfanas.
        partner_login    = None
        partner_password = None
        if _partner_id:
            partner_login    = f"partner@{subdomain}.sajet.us"
            partner_password = _secrets.token_urlsafe(12)
            safe_partner_login    = partner_login.replace("'", "''")
            safe_partner_password = partner_password.replace("'", "''")
            safe_partner_name     = (safe_company_name + " — Socio")

            partner_user_sql = f"""
            DO $$
            DECLARE
                v_partner_id   INTEGER;
                v_user_id      INTEGER;
                v_group_id     INTEGER;
                v_cat_id       INTEGER;
                v_hidden_id    INTEGER;
            BEGIN
                -- 1) Partner record
                INSERT INTO res_partner (name, email, active, type, company_type,
                                         create_uid, write_uid, create_date, write_date)
                VALUES ('{safe_partner_name}', '{safe_partner_login}',
                        TRUE, 'contact', 'person', 1, 1, NOW(), NOW())
                RETURNING id INTO v_partner_id;

                -- 2) Usuario interno (share=FALSE para acceso backend)
                INSERT INTO res_users (login, password, partner_id, active, share,
                                       create_uid, write_uid, create_date, write_date)
                VALUES ('{safe_partner_login}', '{safe_partner_password}',
                        v_partner_id, TRUE, FALSE, 1, 1, NOW(), NOW())
                RETURNING id INTO v_user_id;

                -- Quitar grupo "Public" si existe
                SELECT id INTO v_group_id FROM res_groups WHERE name = 'Public' LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    DELETE FROM res_groups_users_rel WHERE gid = v_group_id AND uid = v_user_id;
                END IF;

                -- 3) Grupo base "Internal User"
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Internal User'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Hidden' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Sales: Administrator
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Administrator'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Sales' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Accounting: Advisor
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Advisor'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Accounting' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Accounting: Validate Bank Accounts
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Validate bank account'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Accounting' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Inventory: Administrator
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Administrator'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Inventory' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Purchase: Administrator
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Administrator'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Purchase' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Website: Editor and Designer
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Editor and Designer'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Website' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Email Marketing: User
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'User'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Email Marketing' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

                -- Administration: Access Rights
                SELECT id INTO v_group_id FROM res_groups
                WHERE name = 'Access Rights'
                  AND category_id = (SELECT id FROM ir_module_category WHERE name = 'Administration' LIMIT 1)
                LIMIT 1;
                IF v_group_id IS NOT NULL THEN
                    INSERT INTO res_groups_users_rel (gid, uid)
                    VALUES (v_group_id, v_user_id) ON CONFLICT DO NOTHING;
                END IF;

            END$$;
            """
            ok_partner_user, out_partner_user = _run_pct_sql(pct_id, subdomain, partner_user_sql)
            if ok_partner_user:
                logger.info(f"✅ Usuario socio con permisos Sales creado: {partner_login}")
            else:
                logger.warning(f"⚠️ Error creando usuario socio: {out_partner_user}")
                partner_login    = None
                partner_password = None

        # 8. Resolver branding del partner para el email de bienvenida
        partner_brand = None
        if _partner_id:
            try:
                from ..models.database import Partner as PartnerModel, SessionLocal
                _db = SessionLocal()
                try:
                    _p = _db.query(PartnerModel).filter(PartnerModel.id == _partner_id).first()
                    if _p:
                        partner_brand = {
                            "brand_name":          _p.brand_name,
                            "brand_color_primary": _p.brand_color_primary,
                            "brand_color_accent":  _p.brand_color_accent,
                            "logo_url":            _p.logo_url,
                            "smtp_from_name":      _p.smtp_from_name,
                            "smtp_from_email":     _p.smtp_from_email,
                        }
                finally:
                    _db.close()
            except Exception as brand_err:
                logger.warning(f"⚠️ No se pudo obtener branding del partner {_partner_id}: {brand_err}")

        # 9. Enviar email de bienvenida con todas las credenciales
        try:
            from .email_service import send_tenant_welcome
            email_result = send_tenant_welcome(
                to_email=final_login,
                company_name=company_name,
                subdomain=subdomain,
                plan_name="basic",
                admin_login=final_login,
                admin_password=final_password,
                client_login=client_login,
                client_password=client_password,
                partner_login=partner_login,
                partner_password=partner_password,
                partner_brand=partner_brand,
            )
            if email_result.get("success"):
                logger.info(f"✅ Email de bienvenida enviado a {final_login}")
            else:
                logger.warning(f"⚠️ Email no enviado: {email_result.get('error')}")
        except Exception as email_err:
            logger.warning(f"⚠️ Error enviando email de bienvenida: {email_err}")

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
            "client_login": client_login,
            "client_password": client_password if client_password else None,
            "partner_login": partner_login,
            "partner_password": partner_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error creando tenant: {e}")
        code = _classify_fast_path_error(str(e))
        return _fast_error(code, str(e))


async def create_tenant_api(
    subdomain: str,
    company_name: str = None,
    server_id: str = None,
    admin_login: str = DEFAULT_ADMIN_LOGIN,
    admin_password: str = DEFAULT_ADMIN_PASSWORD,
    use_fast_method: bool = True,
    partner_id: int = None,   # ID del partner en erp-core (branding + usuario socio)
    country_code: str = None,  # Código ISO país para localización
    blueprint_package_name: str = None,  # Nombre del paquete/blueprint
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
        partner_id: ID del partner en erp-core (para branding + usuario socio)
        country_code: Código ISO del país (DO, US, MX, etc.)
        blueprint_package_name: Nombre del paquete/blueprint (ej: pkg_restaurantes)
    
    Returns:
        Dict con resultado de la creación
    """
    if use_fast_method:
        # Método rápido via SQL directo (recomendado)
        return await create_tenant_from_template(
            subdomain=subdomain,
            company_name=company_name,
            server_id=server_id,
            admin_login=admin_login,
            admin_password=admin_password,
            partner_id=partner_id,
            country_code=country_code,
            blueprint_package_name=blueprint_package_name,
        )
    else:
        # Método tradicional via HTTP API de Odoo
        return await provision_tenant(
            subdomain=subdomain,
            company_name=company_name,
            admin_login=admin_login,
            admin_password=admin_password,
            server_id=server_id,
            country_code=country_code,
            blueprint_package_name=blueprint_package_name,
        )
