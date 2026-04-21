#!/usr/bin/env python3
"""
Migra variables de .env/.env.test/.env.production a system_config.

- .env            -> claves runtime (KEY)
- .env.test       -> perfiles (ENV_TEST_KEY)
- .env.production -> perfiles (ENV_PRODUCTION_KEY)

Además genera llaves resumidas para UI de Ambiente:
- ENV_<PROFILE>_DB_HOST
- ENV_<PROFILE>_DB_PORT
- ENV_<PROFILE>_DB_NAME
- ENV_<PROFILE>_STRIPE_MODE
- ENV_<PROFILE>_STRIPE_MODE_MED (si existe STRIPE_MED_MODE)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Tuple

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILES = {
    "development": ROOT / ".env",
    "test": ROOT / ".env.test",
    "production": ROOT / ".env.production",
}

SECRET_HINTS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "KEY",
    "PRIVATE",
    "WEBHOOK",
)


def parse_env(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        key = k.strip()
        value = v.strip().strip('"').strip("'")
        data[key] = value
    return data


def infer_category(key: str) -> str:
    u = key.upper()
    if u.startswith("STRIPE"):
        return "stripe"
    if u.startswith("ODOO"):
        return "odoo"
    if u.startswith("CLOUDFLARE"):
        return "cloudflare"
    if u.startswith("DB_") or "DATABASE" in u:
        return "database"
    if u.startswith("JWT") or u.startswith("ADMIN_") or "AUTH" in u:
        return "auth"
    if u.startswith("SMTP") or u.startswith("MAIL") or "POSTAL" in u:
        return "mail"
    if u.startswith("ENV_") or u.startswith("APP_") or u.startswith("ERP_"):
        return "infrastructure"
    return "general"


def is_secret(key: str) -> bool:
    u = key.upper()
    return any(h in u for h in SECRET_HINTS)


def parse_database_url(url: str) -> Tuple[str, str, str]:
    # postgres://user:pass@host:port/db
    host = ""
    port = ""
    db = ""
    if "@" in url:
        after_at = url.split("@", 1)[1]
        host_port, _, db_name = after_at.partition("/")
        db = db_name
        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host = host_port
    return host, port, db


def _build_database_url() -> str:
    """
    Prioridad:
    1) DATABASE_URL (si ya viene desde shell)
    2) .env -> DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME forzando host actual 10.10.20.200
    """
    direct = os.getenv("DATABASE_URL", "").strip()
    if direct:
        return direct

    base = parse_env(ROOT / ".env")
    user = (base.get("DB_USER") or "jeturing").strip()
    password = (base.get("DB_PASSWORD") or "").strip()
    port = (base.get("DB_PORT") or "5432").strip()
    name = (base.get("DB_NAME") or "erp_core_db").strip()
    host = os.getenv("DB_HOST_OVERRIDE", "10.10.20.200").strip() or "10.10.20.200"
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def upsert(engine, key: str, value: str, updated_by: str = "migration_env_to_db") -> bool:
    update_stmt = text(
        """
        UPDATE system_config
        SET
            value = :value,
            description = :description,
            category = :category,
            is_secret = :is_secret,
            updated_at = now(),
            updated_by = :updated_by
        WHERE key = :key
        """
    )
    insert_stmt = text(
        """
        INSERT INTO system_config (
            key, value, description, category, is_secret, is_editable, created_at, updated_at, updated_by
        )
        VALUES (
            :key, :value, :description, :category, :is_secret, true, now(), now(), :updated_by
        )
        """
    )

    params = {
        "key": key,
        "value": value,
        "description": f"Migrated from env file ({updated_by})",
        "category": infer_category(key),
        "is_secret": is_secret(key),
        "updated_by": updated_by,
    }

    try:
        with engine.begin() as conn:
            result = conn.execute(update_stmt, params)
            if result.rowcount == 0:
                conn.execute(insert_stmt, params)
        return True
    except Exception:
        return False


def migrate_file(engine, profile: str, env_data: Dict[str, str]) -> Tuple[int, int]:
    ok = 0
    fail = 0

    # 1) runtime (solo development) y perfiles para test/production
    for k, v in env_data.items():
        target_key = k if profile == "development" else f"ENV_{profile.upper()}_{k}"
        if upsert(engine, target_key, v, updated_by=f"env:{profile}"):
            ok += 1
        else:
            fail += 1

    # 2) llaves resumidas de ambiente para UI
    db_host = env_data.get("DB_HOST", "")
    db_port = env_data.get("DB_PORT", "")
    db_name = env_data.get("DB_NAME", "")
    if (not db_host or not db_port or not db_name) and env_data.get("DATABASE_URL"):
        p_host, p_port, p_db = parse_database_url(env_data["DATABASE_URL"])
        db_host = db_host or p_host
        db_port = db_port or p_port
        db_name = db_name or p_db

    mode = env_data.get("STRIPE_MODE", "").strip().lower()
    if not mode:
        sk = env_data.get("STRIPE_SECRET_KEY", "")
        mode = "live" if "live" in sk else ("test" if sk else "")

    med_mode = env_data.get("STRIPE_MED_MODE", "").strip().lower()
    if not med_mode and env_data.get("STRIPE_MED_SECRET_KEY"):
        skm = env_data.get("STRIPE_MED_SECRET_KEY", "")
        med_mode = "live" if "live" in skm else "test"

    summary = {
        f"ENV_{profile.upper()}_DB_HOST": db_host,
        f"ENV_{profile.upper()}_DB_PORT": db_port,
        f"ENV_{profile.upper()}_DB_NAME": db_name,
        f"ENV_{profile.upper()}_STRIPE_MODE": mode,
        f"ENV_{profile.upper()}_STRIPE_MODE_MED": med_mode,
    }

    for k, v in summary.items():
        if not v:
            continue
        if upsert(engine, k, v, updated_by=f"summary:{profile}"):
            ok += 1
        else:
            fail += 1

    return ok, fail


def main() -> int:
    db_url = _build_database_url()
    engine = create_engine(db_url, pool_pre_ping=True, future=True)

    total_ok = 0
    total_fail = 0

    for profile, path in FILES.items():
        data = parse_env(path)
        if not data:
            print(f"[skip] {profile}: archivo no existe o vacío -> {path}")
            continue

        ok, fail = migrate_file(engine, profile, data)
        total_ok += ok
        total_fail += fail
        print(f"[done] {profile}: ok={ok} fail={fail} file={path}")

    print(f"\nResumen: ok={total_ok} fail={total_fail}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
