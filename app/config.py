"""
Centralized Configuration — Single source of truth for all settings.
ALL credentials, IPs, secrets, and environment-specific values MUST come from here.
NEVER hardcode credentials in route files, services, or models.

Environment selection:
  ERP_ENV=development  → loads .env           (local dev, BD 10.10.10.20)
  ERP_ENV=test         → loads .env.test      (pruebas, BD 10.10.10.20)
  ERP_ENV=production   → loads .env.production (HA cluster, BD 10.10.10.137)

Set ERP_ENV before starting the app or export it in your shell.
If not set, defaults to 'development' (.env).
"""
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .utils.runtime_security import redact_secret_url, require_runtime_secret

logger = logging.getLogger(__name__)

# ── Resolve which .env file to load ──
_project_root = Path(__file__).resolve().parent.parent
_erp_env = os.getenv("ERP_ENV", "development").lower().strip()

_ENV_FILES = {
    "development": _project_root / ".env",
    "test":        _project_root / ".env.test",
    "production":  _project_root / ".env.production",
}

_env_file = _ENV_FILES.get(_erp_env, _project_root / ".env")
if _env_file.exists():
    load_dotenv(_env_file, override=True)
else:
    # Fallback: load default .env if the specific file is missing
    load_dotenv(override=True)

ACTIVE_ENV_FILE = str(_env_file)


# ═══════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    _db_user = os.getenv("DB_USER", "jeturing")
    _db_pass = os.getenv("DB_PASSWORD", "")
    _db_host = os.getenv("DB_HOST", "127.0.0.1")
    _db_port = os.getenv("DB_PORT", "5432")
    _db_name = os.getenv("DB_NAME", "erp_core_db")
    DATABASE_URL = f"postgresql+psycopg2://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"

# Normalize driver to psycopg2
if "+psycopg" in DATABASE_URL and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+psycopg://", "+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)


# ═══════════════════════════════════════════════════════
# Stripe
# ═══════════════════════════════════════════════════════
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


# ═══════════════════════════════════════════════════════
# JWT / Auth
# ═══════════════════════════════════════════════════════
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin@sajet.us")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Clave Fernet para cifrar campos sensibles en BD (work order credentials, etc.)
# Generar con: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPT_KEY = os.getenv("FIELD_ENCRYPT_KEY", "")


# ═══════════════════════════════════════════════════════
# Odoo
# ═══════════════════════════════════════════════════════
ODOO_DEFAULT_ADMIN_LOGIN = os.getenv("ODOO_DEFAULT_ADMIN_LOGIN", "admin@sajet.us")
ODOO_DEFAULT_ADMIN_PASSWORD = os.getenv("ODOO_DEFAULT_ADMIN_PASSWORD", "")
ODOO_MASTER_PASSWORD = os.getenv("ODOO_MASTER_PASSWORD", "")
ODOO_DB_HOST = os.getenv("ODOO_DB_HOST", "10.10.10.137")
ODOO_DB_PORT = int(os.getenv("ODOO_DB_PORT", "5432"))
ODOO_DB_USER = os.getenv("ODOO_DB_USER", "Jeturing")
ODOO_DB_PASSWORD = os.getenv("ODOO_DB_PASSWORD", "")
ODOO_DEFAULT_LANG = os.getenv("ODOO_DEFAULT_LANG", "es_DO")
ODOO_DEFAULT_COUNTRY = os.getenv("ODOO_DEFAULT_COUNTRY", "DO")
ODOO_BASE_DOMAIN = os.getenv("ODOO_BASE_DOMAIN", "sajet.us")
ODOO_TEMPLATE_DB = os.getenv("ODOO_TEMPLATE_DB", "template_tenant")
ODOO_TEMPLATE_DB_BY_COUNTRY = os.getenv("ODOO_TEMPLATE_DB_BY_COUNTRY", "DO=tenant_do")
ODOO_FILESTORE_PATH = os.getenv("ODOO_FILESTORE_PATH", "/var/lib/odoo/filestore")
ODOO_FILESTORE_PCT_ID = int(os.getenv("ODOO_FILESTORE_PCT_ID", os.getenv("LXC_CONTAINER_ID", "105")))

# Proxmox host SSH — para operaciones pct exec desde LXC API
PROXMOX_SSH_HOST = os.getenv("PROXMOX_SSH_HOST", "10.10.10.1")
PROXMOX_SSH_USER = os.getenv("PROXMOX_SSH_USER", "root")
PROXMOX_SSH_KEY = os.getenv("PROXMOX_SSH_KEY", "/root/.ssh/id_ed25519")

# ═══════════════════════════════════════════════════════
# Dispersión Mercury — Feature Flags
# ═══════════════════════════════════════════════════════
MERCURY_DISPERSION_ENABLED = os.getenv("MERCURY_DISPERSION_ENABLED", "false").lower() == "true"
MERCURY_DISPERSION_REQUIRE_ADMIN_AUTH = os.getenv("MERCURY_DISPERSION_REQUIRE_ADMIN_AUTH", "true").lower() == "true"
MERCURY_DISPERSION_MAX_AUTO_USD = float(os.getenv("MERCURY_DISPERSION_MAX_AUTO_USD", "0"))  # 0 = siempre requiere auth

# ═══════════════════════════════════════════════════════
# Infrastructure IPs (PCT inventory actual: 200=PG, 201=Odoo17, 202=SAJET, 204=Odoo19, 205=NPM)
# ═══════════════════════════════════════════════════════
ODOO_PRIMARY_IP = os.getenv("ODOO_PRIMARY_IP", ODOO_DB_HOST or "10.10.20.201")
ODOO_PRIMARY_PCT_ID = int(os.getenv("ODOO_PRIMARY_PCT_ID", "201"))
ODOO_PRIMARY_PORT = int(os.getenv("ODOO_PRIMARY_PORT", "8069"))
ODOO_PRIMARY_API_PORT = int(os.getenv("ODOO_PRIMARY_API_PORT", "8070"))

ERP_CORE_IP = os.getenv("ERP_CORE_IP", "10.10.20.202")
ERP_CORE_PUBLIC_IP = os.getenv("ERP_CORE_PUBLIC_IP", "208.115.125.29")

# Alias legacy CT105_* mantenido por backwards-compat; resuelve a ODOO_PRIMARY_IP (PCT 201)
CT105_IP = os.getenv("CT105_IP", ODOO_PRIMARY_IP)
CT105_NGINX_PORT = int(os.getenv("CT105_NGINX_PORT", "8080"))


# ═══════════════════════════════════════════════════════
# Redis (PCT 149 — Session Store)
# ═══════════════════════════════════════════════════════
REDIS_HOST = os.getenv("REDIS_HOST", "10.10.10.7")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
_REDIS_URL_DEFAULT = (
    f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    if REDIS_PASSWORD
    else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)
REDIS_URL = os.getenv(
    "REDIS_URL",
    _REDIS_URL_DEFAULT
)

UPSTREAM_MTLS_ENABLED = os.getenv("UPSTREAM_MTLS_ENABLED", "false").lower() == "true"
UPSTREAM_MTLS_STRICT = os.getenv("UPSTREAM_MTLS_STRICT", "false").lower() == "true"
UPSTREAM_TLS_VERIFY = os.getenv("UPSTREAM_TLS_VERIFY", "true").lower() == "true"
UPSTREAM_CA_CERT_PATH = os.getenv("UPSTREAM_CA_CERT_PATH", "")
UPSTREAM_CLIENT_CERT_PATH = os.getenv("UPSTREAM_CLIENT_CERT_PATH", "")
UPSTREAM_CLIENT_KEY_PATH = os.getenv("UPSTREAM_CLIENT_KEY_PATH", "")

# ═══════════════════════════════════════════════════════
# DSAM — Dynamic Session & Anti-Theft Monitor
# ═══════════════════════════════════════════════════════
GEOIP_DB_PATH = os.getenv("GEOIP_DB_PATH", str(_project_root / "data" / "GeoLite2-City.mmdb"))
DSAM_POLL_INTERVAL_SECONDS = int(os.getenv("DSAM_POLL_INTERVAL_SECONDS", "60"))
DSAM_REDIS_SESSION_SOURCES = os.getenv(
    "DSAM_REDIS_SESSION_SOURCES",
    "0|odoo17:session:*|odoo17,2|odoo19:session:*|odoo19",
)
DSAM_IMPOSSIBLE_TRAVEL_MIN_HOURS = float(os.getenv("DSAM_IMPOSSIBLE_TRAVEL_MIN_HOURS", "3"))
DSAM_IMPOSSIBLE_TRAVEL_MIN_KM = float(os.getenv("DSAM_IMPOSSIBLE_TRAVEL_MIN_KM", "500"))


# ═══════════════════════════════════════════════════════
# Cloudflare
# ═══════════════════════════════════════════════════════
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID", "")
CLOUDFLARE_TUNNEL_ID = os.getenv("CLOUDFLARE_TUNNEL_ID", "")

# Zones loaded from env (comma-separated key=value pairs) or defaults
_cf_zones_raw = os.getenv("CLOUDFLARE_ZONES", "")
CLOUDFLARE_ZONES: dict = {}
if _cf_zones_raw:
    for pair in _cf_zones_raw.split(","):
        if "=" in pair:
            k, v = pair.strip().split("=", 1)
            CLOUDFLARE_ZONES[k.strip()] = v.strip()


# ═══════════════════════════════════════════════════════
# Runtime Config — DB first, env fallback
# ═══════════════════════════════════════════════════════
_RUNTIME_CACHE_TTL_SECONDS = float(os.getenv("RUNTIME_CONFIG_CACHE_TTL_SECONDS", "5"))
_RUNTIME_CACHE_LOCK = threading.RLock()
_RUNTIME_CACHE: dict[str, tuple[Any, float]] = {}
_RUNTIME_ENGINE = None
_RUNTIME_ENGINE_URL = None
_RUNTIME_DB_MISS = object()


def _get_runtime_engine():
    """Create a lightweight engine for runtime config reads using bootstrap DATABASE_URL."""
    global _RUNTIME_ENGINE, _RUNTIME_ENGINE_URL

    if not DATABASE_URL:
        return None

    with _RUNTIME_CACHE_LOCK:
        if _RUNTIME_ENGINE is not None and _RUNTIME_ENGINE_URL == DATABASE_URL:
            return _RUNTIME_ENGINE

        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _RUNTIME_ENGINE = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            future=True,
            connect_args=connect_args,
        )
        _RUNTIME_ENGINE_URL = DATABASE_URL
        return _RUNTIME_ENGINE


def _get_runtime_value_from_db(key: str):
    """Read a config value from system_config without importing ORM models."""
    engine = _get_runtime_engine()
    if engine is None:
        return _RUNTIME_DB_MISS

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT value FROM system_config WHERE key = :key LIMIT 1"),
                {"key": key},
            ).first()
            if row is None:
                return _RUNTIME_DB_MISS
            return row[0]
    except Exception as exc:
        logger.debug("Runtime config DB lookup failed for %s: %s", key, exc)
        return _RUNTIME_DB_MISS


def invalidate_runtime_config_cache(*keys: str) -> None:
    """Invalidate cached runtime config values."""
    with _RUNTIME_CACHE_LOCK:
        if not keys:
            _RUNTIME_CACHE.clear()
            return
        for key in keys:
            _RUNTIME_CACHE.pop(key, None)


def get_runtime_setting(key: str, default: Any = None) -> Any:
    """
    Runtime config lookup with priority: DB > env > default.
    Uses a short TTL cache so admin changes apply without service restart.
    """
    now = time.monotonic()
    with _RUNTIME_CACHE_LOCK:
        cached = _RUNTIME_CACHE.get(key)
        if cached and cached[1] > now:
            return cached[0]

    db_value = _get_runtime_value_from_db(key)
    if db_value is not _RUNTIME_DB_MISS and db_value is not None:
        value = db_value
    else:
        value = os.getenv(key, default)

    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE[key] = (value, now + _RUNTIME_CACHE_TTL_SECONDS)
    return value


def get_runtime_int(key: str, default: int) -> int:
    value = get_runtime_setting(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def get_runtime_float(key: str, default: float) -> float:
    value = get_runtime_setting(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_runtime_bool(key: str, default: bool = False) -> bool:
    value = get_runtime_setting(key, default)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def get_runtime_json(key: str, default: Any):
    value = get_runtime_setting(key, None)
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def get_runtime_kv_map(key: str, default: dict[str, str] | None = None) -> dict[str, str]:
    raw = get_runtime_setting(key, "")
    parsed = dict(default or {})
    if not raw:
        return parsed
    for pair in str(raw).split(","):
        if "=" not in pair:
            continue
        k, v = pair.strip().split("=", 1)
        if k.strip():
            parsed[k.strip()] = v.strip()
    return parsed


# ═══════════════════════════════════════════════════════
# Provisioning
# ═══════════════════════════════════════════════════════
PROVISIONING_API_KEY = os.getenv("PROVISIONING_API_KEY", "") or os.getenv("API_KEY_SECRET", "")


# ═══════════════════════════════════════════════════════
# Email / SMTP — Notificaciones
# ═══════════════════════════════════════════════════════
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Sajet ERP Alerts")
SMTP_ENCRYPTION = os.getenv("SMTP_ENCRYPTION", "SSL/TLS").upper()


def get_smtp_config(mask_secret: bool = False) -> dict:
    """Retorna la configuración SMTP centralizada desde el .env activo."""
    config = {
        "server": SMTP_SERVER.strip(),
        "port": SMTP_PORT,
        "user": SMTP_USER.strip(),
        "password": SMTP_PASSWORD,
        "from_email": SMTP_FROM_EMAIL.strip(),
        "from_name": SMTP_FROM_NAME.strip() if SMTP_FROM_NAME else "Sajet ERP Alerts",
        "encryption": SMTP_ENCRYPTION,
    }

    if mask_secret and config["password"]:
        config["password_masked"] = f"{'*' * 4}{config['password'][-4:]}"
        config["password"] = None

    return config


def smtp_is_configured() -> bool:
    """Indica si el .env activo contiene una configuración SMTP utilizable."""
    config = get_smtp_config()
    return bool(
        config["server"]
        and config["port"]
        and config["user"]
        and config["password"]
        and config["from_email"]
    )


# ═══════════════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════════════
APP_URL = os.getenv("APP_URL", "http://localhost:4443")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
ENABLE_WAF = os.getenv("ENABLE_WAF", "true").lower() == "true"
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "")


# ═══════════════════════════════════════════════════════
# Ollama / VLLM — Local LLM Models
# ═══════════════════════════════════════════════════════
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")  # Usually empty for local

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:11434/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "sk-dummy-local-key")
VLLM_DEFAULT_MODEL = os.getenv("VLLM_DEFAULT_MODEL", "mistral")

# OpenAI-compatible endpoint (works with Ollama/VLLM)
OPENAI_COMPATIBLE_API_BASE = os.getenv("OPENAI_COMPATIBLE_API_BASE", "http://localhost:11434/v1")
OPENAI_COMPATIBLE_API_KEY = os.getenv("OPENAI_COMPATIBLE_API_KEY", "sk-dummy-local-key")


def get_env_info() -> dict:
    """Return current environment info (for /api/env endpoint and logging)."""
    _masked_db = redact_secret_url(DATABASE_URL)
    return {
        "erp_env": _erp_env,
        "env_file": ACTIVE_ENV_FILE,
        "environment": ENVIRONMENT,
        "database_host": _masked_db.split("@")[-1].split("/")[0] if "@" in DATABASE_URL else "unknown",
        "database_name": DATABASE_URL.rsplit("/", 1)[-1] if "/" in DATABASE_URL else "unknown",
        "stripe_mode": "live" if "rk_live" in STRIPE_SECRET_KEY or "sk_live" in STRIPE_SECRET_KEY else "test",
        "app_url": APP_URL,
    }


def validate_required():
    """
    Call at startup to verify critical env vars are set.
    In production, empty secrets should be a fatal error.
    """
    missing = []
    critical = {
        "DATABASE_URL / DB_PASSWORD": DATABASE_URL,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "STRIPE_SECRET_KEY": STRIPE_SECRET_KEY,
    }
    for name, val in critical.items():
        if not val:
            missing.append(name)

    if missing and ENVIRONMENT == "production":
        raise RuntimeError(
            f"FATAL: Missing required environment variables: {', '.join(missing)}. "
            f"Set them in .env or system environment before starting in production."
        )
    elif missing:
        import logging
        logging.getLogger(__name__).warning(
            f"⚠️  Missing env vars (non-production): {', '.join(missing)}"
        )


def require_config_secret(name: str, value: str | None, *, production_only: bool = True) -> str:
    return require_runtime_secret(name, value, production_only=production_only)
