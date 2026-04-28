"""Small runtime security helpers shared by config, auth, and services."""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", os.getenv("ERP_ENV", "development")).lower() == "production"


def require_runtime_secret(name: str, value: str | None, *, production_only: bool = True) -> str:
    """Return a configured secret or fail fast when it is required."""
    secret = (value or "").strip()
    if not secret and (is_production() or not production_only):
        raise RuntimeError(f"{name} no configurado")
    return secret


def redact_secret_url(value: str | None) -> str:
    """Mask passwords in URL-like strings before logging or returning errors."""
    text = value or ""
    try:
        parts = urlsplit(text)
        if parts.password is None:
            return text
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        username = parts.username or ""
        netloc = f"{username}:****@{host}" if username else host
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return re.sub(r":([^:@/]+)@", ":****@", text)


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp for tokens and API timestamps."""
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """Naive UTC timestamp for legacy SQLAlchemy DateTime columns."""
    return utc_now().replace(tzinfo=None)
