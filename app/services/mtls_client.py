"""HTTP client builder for upstream TLS/mTLS.

Phase 2 (GW-008): allows enabling client certificates for sensitive upstream calls
without breaking current flows when disabled.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import get_runtime_setting

logger = logging.getLogger(__name__)


_TRUE_SET = {"1", "true", "yes", "on"}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in _TRUE_SET


def _tls_options() -> tuple[bool | str, str | tuple[str, str] | None]:
    """Returns httpx `verify` and `cert` options from runtime config."""
    mtls_enabled = _as_bool(get_runtime_setting("UPSTREAM_MTLS_ENABLED", "false"), False)
    tls_verify_enabled = _as_bool(get_runtime_setting("UPSTREAM_TLS_VERIFY", "true"), True)

    ca_cert_path = str(get_runtime_setting("UPSTREAM_CA_CERT_PATH", "") or "").strip()
    client_cert_path = str(get_runtime_setting("UPSTREAM_CLIENT_CERT_PATH", "") or "").strip()
    client_key_path = str(get_runtime_setting("UPSTREAM_CLIENT_KEY_PATH", "") or "").strip()
    mtls_strict = _as_bool(get_runtime_setting("UPSTREAM_MTLS_STRICT", "false"), False)

    verify: bool | str = True if tls_verify_enabled else False
    if ca_cert_path:
        verify = ca_cert_path

    cert: str | tuple[str, str] | None = None
    if mtls_enabled:
        if client_cert_path and client_key_path:
            cert = (client_cert_path, client_key_path)
        elif client_cert_path:
            cert = client_cert_path
        elif mtls_strict:
            raise RuntimeError("UPSTREAM mTLS strict está habilitado pero faltan certificados")
        else:
            logger.warning("UPSTREAM_MTLS_ENABLED=true sin cert/key; se continúa sin cert de cliente")

    return verify, cert


def create_upstream_async_client(timeout: float = 10.0) -> httpx.AsyncClient:
    """Builds AsyncClient with runtime TLS/mTLS settings."""
    verify, cert = _tls_options()
    return httpx.AsyncClient(timeout=timeout, verify=verify, cert=cert)
