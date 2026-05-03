"""
Tenant Accounts Service — snapshot reutilizable de usuarios vivos por instancia.
"""
from __future__ import annotations

import re
import os
from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from fastapi import HTTPException
from sqlalchemy import create_engine, text

from ..config import (
    ODOO_DB_HOST,
    ODOO_DB_PASSWORD,
    ODOO_DB_USER,
    ODOO_DEFAULT_ADMIN_LOGIN,
    get_runtime_setting,
)
from .seat_events import get_non_billable_logins


def _odoo_default_admin_login() -> str:
    return get_runtime_setting("ODOO_DEFAULT_ADMIN_LOGIN", ODOO_DEFAULT_ADMIN_LOGIN)


def _odoo_db_host() -> str:
    return get_runtime_setting("ODOO_DB_HOST", ODOO_DB_HOST)


def _odoo_db_user() -> str:
    return get_runtime_setting("ODOO_DB_USER", ODOO_DB_USER)


def _odoo_db_password() -> str:
    return get_runtime_setting("ODOO_DB_PASSWORD", ODOO_DB_PASSWORD)


def normalize_tenant_db_name(subdomain: str) -> str:
    db_name = (subdomain or "").strip().lower().replace("-", "_")
    if not re.fullmatch(r"[a-z0-9_]{3,63}", db_name):
        raise HTTPException(status_code=400, detail="Subdomain inválido para base de datos")
    return db_name


@lru_cache(maxsize=64)
def _odoo_engine_for_db(db_name: str):
    db_name = normalize_tenant_db_name(db_name)
    host = quote_plus(_odoo_db_host() or "")
    user = quote_plus(_odoo_db_user() or "")
    pwd = quote_plus(_odoo_db_password() or "")
    if not host or not user:
        raise HTTPException(status_code=500, detail="Configuración ODOO_DB incompleta")
    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:5432/{db_name}"
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=int(os.getenv("ODOO_TENANT_DB_POOL_SIZE", "2")),
        max_overflow=int(os.getenv("ODOO_TENANT_DB_MAX_OVERFLOW", "2")),
        pool_recycle=int(os.getenv("ODOO_TENANT_DB_POOL_RECYCLE_SECONDS", "1800")),
    )


def fetch_tenant_accounts_snapshot(
    subdomain: str,
    *,
    include_inactive: bool = True,
    customer=None,
    admin_email: Optional[str] = None,
    excluded_logins: Optional[set[str]] = None,
) -> dict:
    """Retorna cuentas de la instancia y conteos facturables."""
    db_name = normalize_tenant_db_name(subdomain)
    engine = _odoo_engine_for_db(db_name)
    where = ""
    if not include_inactive:
        where = "WHERE u.active = true"

    sql = text(
        f"""
        SELECT
            u.id,
            u.login,
            u.email,
            p.name,
            u.active,
            COALESCE(u.share, false) AS share,
            u.write_date,
            u.create_date
        FROM res_users u
        LEFT JOIN res_partner p ON p.id = u.partner_id
        {where}
        ORDER BY u.active DESC, u.id ASC
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    effective_excluded = {
        item.strip().lower()
        for item in (
            excluded_logins
            or get_non_billable_logins(
                db_name,
                customer=customer,
                admin_email=admin_email,
            )
        )
        if item
    }

    accounts: list[dict] = []
    active_accounts = 0
    billable_active_accounts = 0
    default_admin_login = (_odoo_default_admin_login() or "").strip().lower()

    for row in rows:
        is_active = bool(row.get("active"))
        is_share = bool(row.get("share"))
        login = (row.get("login") or "").strip().lower()
        is_admin_login = login in {"admin", default_admin_login}
        is_excluded_login = login in effective_excluded

        if is_active:
            active_accounts += 1

        is_billable = is_active and not is_share and not is_admin_login and not is_excluded_login
        if is_billable:
            billable_active_accounts += 1

        accounts.append(
            {
                "id": row.get("id"),
                "login": row.get("login"),
                "email": row.get("email"),
                "name": row.get("name"),
                "active": is_active,
                "share": is_share,
                "is_admin": is_admin_login,
                "is_excluded": is_excluded_login,
                "is_billable": is_billable,
                "write_date": row.get("write_date").isoformat() if row.get("write_date") else None,
                "create_date": row.get("create_date").isoformat() if row.get("create_date") else None,
            }
        )

    return {
        "subdomain": db_name,
        "accounts": accounts,
        "total_accounts": len(accounts),
        "active_accounts": active_accounts,
        "billable_active_accounts": billable_active_accounts,
    }
