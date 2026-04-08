"""
Meta inbound webhook concentrator (SAJET PCT 160).

Endpoints públicos:
- GET  /meta/webhook      (verificación challenge)
- POST /meta/webhook      (fanout multi-tenant)

Patrón operativo: equivalente a DoorDash/Uber centralizados en SAJET.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from ..config import get_runtime_setting
from ..models.database import CustomDomain, SessionLocal, TenantDeployment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Meta Webhooks"])


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
    return host or None


def _expected_bearer_token() -> str:
    return str(get_runtime_setting("META_WEBHOOK_BEARER", "") or "").strip()


def _configured_targets() -> list[str]:
    raw = str(get_runtime_setting("META_WEBHOOK_TARGETS", "") or "").strip()
    if not raw:
        return []
    values: list[str] = []
    for part in raw.split(","):
        host = _normalize_host(part)
        if host:
            values.append(host)
    return values


def _target_paths() -> list[str]:
    raw = str(get_runtime_setting("META_WEBHOOK_TARGET_PATHS", "") or "").strip()
    if not raw:
        return ["/jeturing_whatsapp/webhook", "/jeturing_meta/webhook"]
    paths: list[str] = []
    for part in raw.split(","):
        candidate = str(part or "").strip()
        if not candidate:
            continue
        if not candidate.startswith("/"):
            candidate = "/" + candidate
        paths.append(candidate)
    return paths or ["/jeturing_whatsapp/webhook", "/jeturing_meta/webhook"]


def _extract_candidate_subdomain(payload: dict[str, Any]) -> Optional[str]:
    for key in ("tenant_subdomain", "tenant_db", "subdomain"):
        value = str(payload.get(key) or "").strip().lower()
        if value and "." not in value and "/" not in value:
            return value
    return None


def _resolve_targets(payload: dict[str, Any]) -> list[str]:
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

        subdomain = _extract_candidate_subdomain(payload)
        if subdomain:
            _append(f"{subdomain}.sajet.us")
            rows = db.query(CustomDomain).filter(
                CustomDomain.sajet_subdomain == subdomain,
                CustomDomain.is_active == True,
            ).all()
            for row in rows:
                _append(row.external_domain)

        explicit_domain = _normalize_host(payload.get("tenant_domain") or payload.get("domain"))
        if explicit_domain:
            _append(explicit_domain)

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
        return True
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


@router.get("/meta/webhook")
async def meta_webhook_verify(
    request: Request,
    hub_mode: Optional[str] = Query(default=None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
):
    """Reenvía challenge de verificación Meta al tenant que valide el token."""
    query_params = dict(request.query_params)
    targets = _resolve_targets(query_params)
    if not targets:
        return PlainTextResponse("No tenant targets available", status_code=503)

    paths = _target_paths()
    async with httpx.AsyncClient(timeout=8.0) as client:
        for host in targets:
            for path in paths:
                url = f"https://{host}{path}"
                try:
                    response = await client.get(url, params=query_params)
                except Exception:
                    continue
                if response.status_code == 200:
                    body = response.text or hub_challenge or ""
                    return PlainTextResponse(body, status_code=200)

    if hub_mode == "subscribe":
        return PlainTextResponse("Invalid verify token", status_code=403)
    return PlainTextResponse("Not found", status_code=404)


@router.post("/meta/webhook")
async def meta_webhook_fanout(
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Recibe webhook Meta en SAJET y lo reenvía al endpoint interno del tenant."""
    if not _is_authorized(authorization):
        raise HTTPException(status_code=401, detail="Invalid Meta webhook token")

    raw_body = request.body()
    raw_body = await raw_body
    content_type = request.headers.get("content-type", "application/json")

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    targets = _resolve_targets(payload if isinstance(payload, dict) else {})
    if not targets:
        raise HTTPException(status_code=503, detail="No tenant targets available")

    headers = {
        "content-type": content_type,
    }
    signature = request.headers.get("x-hub-signature-256")
    if signature:
        headers["x-hub-signature-256"] = signature

    tried: list[dict[str, Any]] = []
    forwarded_to: Optional[str] = None
    forwarded_path: Optional[str] = None

    paths = _target_paths()
    async with httpx.AsyncClient(timeout=8.0) as client:
        for host in targets:
            for path in paths:
                url = f"https://{host}{path}"
                try:
                    response = await client.post(url, content=raw_body, headers=headers)
                    preview = (response.text or "")[:160]
                    tried.append({"target": host, "path": path, "status_code": response.status_code, "preview": preview})
                    if response.status_code == 200:
                        forwarded_to = host
                        forwarded_path = path
                        break
                except Exception as exc:
                    tried.append({"target": host, "path": path, "status_code": 0, "preview": str(exc)[:160]})
                    continue
            if forwarded_to:
                break

    if not forwarded_to:
        return {
            "success": False,
            "data": {
                "forwarded": False,
                "reason": "meta_webhook_not_resolved",
                "targets_tried": len(tried),
                "tries": tried[:20],
            },
            "meta": {},
        }

    logger.info("Meta webhook routed to tenant host: %s%s", forwarded_to, forwarded_path or "")
    return {
        "success": True,
        "data": {
            "forwarded": True,
            "target": forwarded_to,
            "path": forwarded_path,
            "targets_tried": len(tried),
        },
        "meta": {},
    }
