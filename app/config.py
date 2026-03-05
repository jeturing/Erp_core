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
import os
from pathlib import Path
from dotenv import load_dotenv

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
# Infrastructure IPs
# ═══════════════════════════════════════════════════════
ODOO_PRIMARY_IP = os.getenv("ODOO_PRIMARY_IP", ODOO_DB_HOST or "10.10.10.100")
ODOO_PRIMARY_PCT_ID = int(os.getenv("ODOO_PRIMARY_PCT_ID", "105"))
ODOO_PRIMARY_PORT = int(os.getenv("ODOO_PRIMARY_PORT", "8069"))
ODOO_PRIMARY_API_PORT = int(os.getenv("ODOO_PRIMARY_API_PORT", "8070"))

ERP_CORE_IP = os.getenv("ERP_CORE_IP", "10.10.10.20")

CT105_IP = os.getenv("CT105_IP", ODOO_PRIMARY_IP)
CT105_NGINX_PORT = int(os.getenv("CT105_NGINX_PORT", "8080"))


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
# Provisioning
# ═══════════════════════════════════════════════════════
PROVISIONING_API_KEY = os.getenv("PROVISIONING_API_KEY", "")


# ═══════════════════════════════════════════════════════
# Email / SMTP — Notificaciones
# ═══════════════════════════════════════════════════════
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "alerts@sajet.us")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Sajet ERP Alerts")


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
    # Mask sensitive parts of DATABASE_URL
    _masked_db = DATABASE_URL
    if "@" in _masked_db:
        _pre, _post = _masked_db.split("@", 1)
        _masked_db = _pre.rsplit(":", 1)[0] + ":****@" + _post
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
