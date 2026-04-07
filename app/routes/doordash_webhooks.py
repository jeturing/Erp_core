"""
DoorDash inbound webhook concentrator (SAJET PCT 160).

Recibe webhook único en:
- POST /kds/webhook/doordash-drive

Valida Bearer token y reenvía al tenant Odoo correspondiente.
Modelo operativo: igual al patrón centralizado de Uber (entrypoint único en sajet.us).
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from ..config import get_runtime_setting
from ..models.database import CustomDomain, SessionLocal, TenantDeployment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["DoorDash Webhooks"])


def _normalize_host(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    value = str(raw).strip().lower().strip(".")
    if not value:
        return None
    candidate = value if "://" in value else f"//{value}"
    parsed = urlparse(candidate)
    host = (parsed.netloc or parsed.path or "").strip().lower().strip(".")
    host = host.split("/")[0].split(":")[0]
    if not host:
        return None
    return host


def _expected_bearer_token() -> str:
    return str(get_runtime_setting("DOORDASH_WEBHOOK_BEARER", "") or "").strip()


def _configured_targets() -> list[str]:
    raw = str(get_runtime_setting("DOORDASH_WEBHOOK_TARGETS", "") or "").strip()
    if not raw:
        return []
    values: list[str] = []
    for part in raw.split(","):
        host = _normalize_host(part)
        if host:
            values.append(host)
    return values


def _extract_candidate_subdomain(payload: dict[str, Any]) -> Optional[str]:
    for key in ("tenant_subdomain", "tenant_db", "subdomain"):
        value = str(payload.get(key) or "").strip().lower()
        if value and "." not in value and "/" not in value:
            return value
    return None


def _resolve_targets(payload: dict[str, Any]) -> list[str]:
    # 1) Targets explícitos en config (override operacional)
    configured = _configured_targets()
    if configured:
        return configured

    db = SessionLocal()
    try:
        hosts: list[str] = []
        seen: set[str] = set()

        def _append(host: Optional[str]):
            normalized = _normalize_host(host)
            if not normalized:
                return
            if normalized in {"sajet.us", "www.sajet.us"}:
                return
            if normalized in seen:
                return
            seen.add(normalized)
            hosts.append(normalized)

        # 2) Resolución dirigida por subdominio si viene en payload
        subdomain = _extract_candidate_subdomain(payload)
        if subdomain:
            _append(f"{subdomain}.sajet.us")
            rows = db.query(CustomDomain).filter(
                CustomDomain.sajet_subdomain == subdomain,
                CustomDomain.is_active == True,
            ).all()
            for row in rows:
                _append(row.external_domain)

        # 3) Resolución dirigida por dominio explícito si viene en payload
        explicit_domain = _normalize_host(payload.get("tenant_domain") or payload.get("domain"))
        if explicit_domain:
            _append(explicit_domain)

        # 4) Fallback: tenants activos más recientes (sin incluir sajet.us)
        if not hosts:
            deployments = db.query(TenantDeployment).order_by(TenantDeployment.id.desc()).limit(300).all()
            for dep in deployments:
                if dep.subdomain:
                    _append(f"{dep.subdomain}.sajet.us")
                if dep.tunnel_url:
                    _append(dep.tunnel_url)

            custom_domains = db.query(CustomDomain).filter(CustomDomain.is_active == True).limit(300).all()
            for domain in custom_domains:
                _append(domain.external_domain)

        return hosts
    finally:
        db.close()


def _is_authorized(authorization: Optional[str]) -> bool:
    expected = _expected_bearer_token()
    if not expected:
        return False
    if not authorization:
        return False
    raw = authorization.strip()
    if raw == expected:
        return True
    if raw.startswith("Bearer "):
        return raw[7:].strip() == expected
    if raw.startswith("Basic "):
        return raw[6:].strip() == expected
    return False


@router.post("/kds/webhook/doordash-drive")
async def doordash_webhook_fanout(
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """
    Endpoint centralizado para DoorDash.

    Flujo:
    1) valida Bearer
    2) resuelve tenant targets
    3) reenvía webhook al endpoint Odoo de tenant
    """
    if not _is_authorized(authorization):
        raise HTTPException(status_code=401, detail="Invalid DoorDash webhook token")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    targets = _resolve_targets(payload)
    if not targets:
        raise HTTPException(status_code=503, detail="No tenant targets available")

    tried: list[dict[str, Any]] = []
    forwarded_to: Optional[str] = None
    first_ok_response: Optional[dict[str, Any]] = None

    async with httpx.AsyncClient(timeout=8.0) as client:
        for host in targets:
            url = f"https://{host}/kds/webhook/doordash-drive"
            try:
                response = await client.post(url, json=payload)
                preview = (response.text or "")[:160]
                tried.append({"target": host, "status_code": response.status_code, "preview": preview})

                if response.status_code >= 500:
                    continue

                json_body: dict[str, Any] = {}
                try:
                    json_body = response.json() if response.text else {}
                except Exception:
                    json_body = {}

                message = str(json_body.get("message") or "").lower()
                # Continuar buscando si ese tenant no reconoce el delivery
                if "not found" in message and "delivery" in message:
                    continue

                forwarded_to = host
                first_ok_response = json_body
                break
            except Exception as exc:
                tried.append({"target": host, "status_code": 0, "preview": str(exc)[:160]})
                continue

    if not forwarded_to:
        return {
            "success": False,
            "data": {
                "forwarded": False,
                "reason": "delivery_not_resolved",
                "targets_tried": len(tried),
                "tries": tried[:20],
            },
            "meta": {},
        }

    logger.info("DoorDash webhook routed to tenant host: %s", forwarded_to)
    return {
        "success": True,
        "data": {
            "forwarded": True,
            "target": forwarded_to,
            "tenant_response": first_ok_response or {},
            "targets_tried": len(tried),
        },
        "meta": {},
    }
