"""
Integración Gusto Embedded Payroll para compañías USA.

Expone:
- Bootstrap del add-on Gusto en catálogo
- Generación de URL OAuth para tenants USA
- Callback OAuth para almacenar tokens cifrados
- Gestión de webhook subscriptions de Gusto
- Webhook receptor con validación HMAC estilo Uber
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Header, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from ..config import FIELD_ENCRYPT_KEY, JWT_SECRET_KEY, get_runtime_setting
from ..models.database import Customer, CustomerAddonSubscription, Partner, ServiceCatalogItem, ServiceCategory, SessionLocal
from ..services.stripe_connect import normalize_country_code
from .roles import _require_admin, verify_token_with_role

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Gusto Payroll"])

GUSTO_PAYROLL_SERVICE_CODE = "gusto_payroll_us"
DEFAULT_GUSTO_SCOPES = "public webhook_subscriptions:read webhook_subscriptions:write"
DEFAULT_GUSTO_API_VERSION = "2025-06-15"
DEFAULT_GUSTO_SUBSCRIPTION_TYPES = ["Company", "Employee"]
STATE_TTL_SECONDS = 900
COUNTRY_ALIASES = {
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "USA": "US",
    "ESTADOS UNIDOS": "US",
}


class GustoCatalogBootstrapRequest(BaseModel):
    name: str = "Gusto Payroll (USA)"
    description: Optional[str] = (
        "Conecta Gusto Embedded Payroll para compañías registradas en Estados Unidos."
    )
    price_monthly: float = 0.0
    sort_order: int = 120
    unit: str = "tenant/mes"


class GustoWebhookSubscriptionCreate(BaseModel):
    url: Optional[str] = None
    subscription_types: list[str] = Field(default_factory=lambda: list(DEFAULT_GUSTO_SUBSCRIPTION_TYPES))


class GustoWebhookVerifyRequest(BaseModel):
    verification_token: str


class GustoCompanyTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    company_uuid: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None


def _normalize_catalog_country(country: Optional[str]) -> Optional[str]:
    raw = (country or "").strip()
    if not raw:
        return None
    if len(raw) == 2 and raw.isalpha():
        return normalize_country_code(raw, raw.upper())
    return COUNTRY_ALIASES.get(raw.upper(), raw.upper())


def _get_fernet():
    key = FIELD_ENCRYPT_KEY or os.getenv("FIELD_ENCRYPT_KEY", "")
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode())
    except Exception as exc:
        logger.warning("Gusto Fernet init failed: %s", exc)
        return None


def _encrypt(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    fernet = _get_fernet()
    if fernet is None:
        return value
    return fernet.encrypt(value.encode()).decode()


def _gusto_env() -> str:
    return str(get_runtime_setting("GUSTO_ENV", "demo") or "demo").strip().lower()


def _gusto_base_url() -> str:
    explicit = str(get_runtime_setting("GUSTO_API_BASE", "") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    return "https://api.gusto.com" if _gusto_env() == "production" else "https://api.gusto-demo.com"


def _gusto_client_id() -> str:
    return str(get_runtime_setting("GUSTO_CLIENT_ID", "") or "").strip()


def _gusto_client_secret() -> str:
    return str(get_runtime_setting("GUSTO_CLIENT_SECRET", "") or "").strip()


def _gusto_redirect_uri() -> str:
    return str(get_runtime_setting("GUSTO_REDIRECT_URI", "https://sajet.us/redirect") or "https://sajet.us/redirect").strip()


def _gusto_webhook_url() -> str:
    return str(get_runtime_setting("GUSTO_WEBHOOK_URL", "https://sajet.us/api/v1/gusto/webhook") or "https://sajet.us/api/v1/gusto/webhook").strip()


def _gusto_webhook_secret() -> str:
    return str(get_runtime_setting("GUSTO_WEBHOOK_SECRET", "") or "").strip()


def _gusto_scopes() -> str:
    return str(get_runtime_setting("GUSTO_SCOPES", DEFAULT_GUSTO_SCOPES) or DEFAULT_GUSTO_SCOPES).strip()


def _gusto_api_version() -> str:
    return str(get_runtime_setting("GUSTO_API_VERSION", DEFAULT_GUSTO_API_VERSION) or DEFAULT_GUSTO_API_VERSION).strip()


def _oauth_state_secret() -> str:
    return str(get_runtime_setting("GUSTO_STATE_SECRET", JWT_SECRET_KEY) or JWT_SECRET_KEY).strip()


def _tenant_portal_url() -> str:
    return f"{str(get_runtime_setting('APP_URL', 'https://sajet.us')).rstrip('/')}" + "/tenant/portal"


def _mask_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}***{token[-4:]}"


def _encode_state(customer_id: int) -> str:
    payload = {"customer_id": customer_id, "ts": int(time.time())}
    payload_raw = json.dumps(payload, separators=(",", ":")).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_raw).decode().rstrip("=")
    signature = hmac.new(
        _oauth_state_secret().encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode_state(state: str) -> dict[str, Any]:
    if not state or "." not in state:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido")

    payload_b64, signature = state.rsplit(".", 1)
    expected_signature = hmac.new(
        _oauth_state_secret().encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Firma de estado OAuth inválida")

    padding = "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(f"{payload_b64}{padding}"))
    issued_at = int(payload.get("ts") or 0)
    if issued_at < int(time.time()) - STATE_TTL_SECONDS:
        raise HTTPException(status_code=400, detail="Estado OAuth expirado")
    return payload


def _verify_gusto_signature(body: bytes, signature: str) -> bool:
    webhook_secret = _gusto_webhook_secret()
    if not webhook_secret:
        return True
    expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _require_tenant(request: Request, access_token: Optional[str] = None) -> dict[str, Any]:
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return verify_token_with_role(token, required_role="tenant")


def _get_customer_and_partner(db, customer_id: int) -> tuple[Customer, Optional[Partner]]:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    partner = db.query(Partner).filter(Partner.id == customer.partner_id).first() if customer.partner_id else None
    return customer, partner


def _customer_country(customer: Customer, partner: Optional[Partner]) -> Optional[str]:
    return _normalize_catalog_country(customer.country or (partner.country if partner else None))


def _require_us_customer(customer: Customer, partner: Optional[Partner]) -> str:
    country = _customer_country(customer, partner)
    if country != "US":
        raise HTTPException(status_code=400, detail="Gusto solo está disponible para compañías registradas en Estados Unidos")
    return country


def _get_active_gusto_addon(db, customer_id: int) -> CustomerAddonSubscription:
    addon = db.query(CustomerAddonSubscription).filter(
        CustomerAddonSubscription.customer_id == customer_id,
        CustomerAddonSubscription.service_code == GUSTO_PAYROLL_SERVICE_CODE,
        CustomerAddonSubscription.status == "active",
    ).order_by(CustomerAddonSubscription.id.desc()).first()
    if not addon:
        raise HTTPException(status_code=404, detail="El cliente no tiene el add-on de Gusto activo")
    return addon


async def _request_system_access_token() -> str:
    client_id = _gusto_client_id()
    client_secret = _gusto_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Faltan credenciales Gusto en configuración")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{_gusto_base_url()}/oauth/token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "system_access",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    if response.status_code >= 400:
        logger.warning("Gusto system_access error: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="No se pudo obtener el token de sistema de Gusto")

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Respuesta inválida de Gusto al solicitar token de sistema")
    return token


def _gusto_api_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Gusto-API-Version": _gusto_api_version(),
    }


def _safe_addon_payload(addon: CustomerAddonSubscription) -> dict[str, Any]:
    metadata = dict(addon.metadata_json or {})
    if metadata.get("gusto_access_token_enc"):
        metadata["gusto_access_token_enc"] = "***"
    if metadata.get("gusto_refresh_token_enc"):
        metadata["gusto_refresh_token_enc"] = "***"
    return {
        "id": addon.id,
        "customer_id": addon.customer_id,
        "service_code": addon.service_code,
        "status": addon.status,
        "metadata_json": metadata,
    }


@router.post("/api/v1/gusto/admin/bootstrap-catalog")
async def bootstrap_gusto_catalog(
    payload: GustoCatalogBootstrapRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.service_code == GUSTO_PAYROLL_SERVICE_CODE,
        ).first()
        metadata = {
            "provider": "gusto",
            "integration_mode": "embedded_payroll",
            "allowed_countries": ["US"],
            "oauth_scopes": _gusto_scopes().split(),
            "redirect_uri": _gusto_redirect_uri(),
            "webhook_url": _gusto_webhook_url(),
            "gusto_env": _gusto_env(),
        }
        created = False
        if item is None:
            item = ServiceCatalogItem(
                category=ServiceCategory.payments_pos,
                name=payload.name,
                description=payload.description,
                unit=payload.unit,
                price_monthly=payload.price_monthly,
                is_addon=True,
                min_quantity=1,
                service_code=GUSTO_PAYROLL_SERVICE_CODE,
                metadata_json=metadata,
                sort_order=payload.sort_order,
                is_active=True,
            )
            db.add(item)
            created = True
        else:
            item.category = ServiceCategory.payments_pos
            item.name = payload.name
            item.description = payload.description
            item.unit = payload.unit
            item.price_monthly = payload.price_monthly
            item.is_addon = True
            item.min_quantity = 1
            item.sort_order = payload.sort_order
            item.is_active = True
            item.metadata_json = {**(item.metadata_json or {}), **metadata}

        db.commit()
        db.refresh(item)
        return {
            "success": True,
            "data": {
                "created": created,
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "service_code": item.service_code,
                    "category": item.category.value if item.category else None,
                    "metadata_json": item.metadata_json or {},
                },
            },
            "meta": {},
        }
    finally:
        db.close()


@router.get("/api/v1/gusto/tenant/connect-url")
async def get_gusto_connect_url(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    auth = _require_tenant(request, access_token)
    customer_id = auth.get("tenant_id") or auth.get("user_id")
    if not customer_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        customer, partner = _get_customer_and_partner(db, int(customer_id))
        country = _require_us_customer(customer, partner)
        addon = _get_active_gusto_addon(db, customer.id)

        if not _gusto_client_id():
            raise HTTPException(status_code=400, detail="GUSTO_CLIENT_ID no está configurado")

        state = _encode_state(customer.id)
        params = urlencode({
            "client_id": _gusto_client_id(),
            "redirect_uri": _gusto_redirect_uri(),
            "response_type": "code",
            "scope": _gusto_scopes(),
            "state": state,
        })
        authorize_url = f"{_gusto_base_url()}/oauth/authorize?{params}"

        metadata = dict(addon.metadata_json or {})
        metadata.update({
            "oauth_status": "pending",
            "oauth_last_started_at": datetime.utcnow().isoformat(),
        })
        addon.metadata_json = metadata
        db.commit()

        return {
            "success": True,
            "data": {
                "authorize_url": authorize_url,
                "redirect_uri": _gusto_redirect_uri(),
                "country": country,
                "service_code": GUSTO_PAYROLL_SERVICE_CODE,
            },
            "meta": {},
        }
    finally:
        db.close()


async def _handle_gusto_callback(code: Optional[str], state: Optional[str], error: Optional[str]) -> RedirectResponse:
    if error:
        return RedirectResponse(url=f"{_tenant_portal_url()}?gusto_error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(url=f"{_tenant_portal_url()}?gusto_error=missing_code", status_code=302)

    payload = _decode_state(state)
    customer_id = int(payload.get("customer_id") or 0)
    db = SessionLocal()
    try:
        customer, partner = _get_customer_and_partner(db, customer_id)
        _require_us_customer(customer, partner)
        addon = _get_active_gusto_addon(db, customer.id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_gusto_base_url()}/oauth/token",
                json={
                    "client_id": _gusto_client_id(),
                    "client_secret": _gusto_client_secret(),
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": _gusto_redirect_uri(),
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )

        if response.status_code >= 400:
            logger.warning("Gusto auth callback error: %s %s", response.status_code, response.text)
            metadata = dict(addon.metadata_json or {})
            metadata.update({
                "oauth_status": "error",
                "oauth_last_error": response.text[:500],
                "oauth_last_error_at": datetime.utcnow().isoformat(),
            })
            addon.metadata_json = metadata
            db.commit()
            return RedirectResponse(url=f"{_tenant_portal_url()}?gusto_error=token_exchange_failed", status_code=302)

        token_data = GustoCompanyTokenResponse.model_validate(response.json())
        expires_at = None
        if token_data.expires_in:
            expires_at = (datetime.utcnow() + timedelta(seconds=int(token_data.expires_in))).isoformat()

        metadata = dict(addon.metadata_json or {})
        metadata.update({
            "provider": "gusto",
            "oauth_status": "connected",
            "gusto_company_uuid": token_data.company_uuid,
            "gusto_token_type": token_data.token_type,
            "gusto_scope": token_data.scope,
            "gusto_connected_at": datetime.utcnow().isoformat(),
            "gusto_token_expires_at": expires_at,
            "gusto_access_token_enc": _encrypt(token_data.access_token),
            "gusto_refresh_token_enc": _encrypt(token_data.refresh_token),
            "gusto_access_token_preview": _mask_token(token_data.access_token),
        })
        addon.metadata_json = metadata
        db.commit()
        return RedirectResponse(url=f"{_tenant_portal_url()}?gusto_connected=true", status_code=302)
    finally:
        db.close()


@router.get("/redirect")
async def gusto_redirect_callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
):
    return await _handle_gusto_callback(code, state, error)


@router.get("/payroll/redirect")
async def gusto_redirect_alias(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
):
    return await _handle_gusto_callback(code, state, error)


@router.get("/payrol/redirect")
async def gusto_redirect_legacy_alias(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
):
    return await _handle_gusto_callback(code, state, error)


@router.post("/api/v1/gusto/admin/webhook-subscriptions")
async def create_gusto_webhook_subscription(
    payload: GustoWebhookSubscriptionCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    system_token = await _request_system_access_token()
    subscription_url = payload.url or _gusto_webhook_url()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{_gusto_base_url()}/v1/webhook_subscriptions",
            json={
                "subscription_types": payload.subscription_types,
                "url": subscription_url,
            },
            headers=_gusto_api_headers(system_token),
        )

    if response.status_code >= 400:
        logger.warning("Gusto webhook subscription create failed: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="No se pudo crear la suscripción webhook en Gusto")

    return {
        "success": True,
        "data": response.json(),
        "meta": {"webhook_url": subscription_url},
    }


@router.put("/api/v1/gusto/admin/webhook-subscriptions/{subscription_uuid}/verify")
async def verify_gusto_webhook_subscription(
    subscription_uuid: str,
    payload: GustoWebhookVerifyRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    system_token = await _request_system_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(
            f"{_gusto_base_url()}/v1/webhook_subscriptions/{subscription_uuid}/verify",
            json={"verification_token": payload.verification_token},
            headers=_gusto_api_headers(system_token),
        )

    if response.status_code >= 400:
        logger.warning("Gusto webhook subscription verify failed: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="No se pudo verificar la suscripción webhook en Gusto")

    return {
        "success": True,
        "data": response.json(),
        "meta": {},
    }


@router.post("/api/v1/gusto/webhook")
async def gusto_webhook_receiver(
    request: Request,
    x_gusto_signature: str = Header(default=""),
):
    body = await request.body()
    if _gusto_webhook_secret() and not _verify_gusto_signature(body, x_gusto_signature):
        logger.warning("Gusto webhook rechazado por firma inválida")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    event_type = payload.get("event_type") or payload.get("type") or "unknown"
    company_uuid = (
        payload.get("company_uuid")
        or (payload.get("resource") or {}).get("company_uuid")
        or (payload.get("entity") or {}).get("company_uuid")
    )

    db = SessionLocal()
    try:
        matched_addon = None
        if company_uuid:
            candidates = db.query(CustomerAddonSubscription).filter(
                CustomerAddonSubscription.service_code == GUSTO_PAYROLL_SERVICE_CODE,
                CustomerAddonSubscription.status == "active",
            ).all()
            for addon in candidates:
                metadata = addon.metadata_json or {}
                if metadata.get("gusto_company_uuid") == company_uuid:
                    matched_addon = addon
                    break

        if matched_addon:
            metadata = dict(matched_addon.metadata_json or {})
            metadata.update({
                "gusto_last_webhook_at": datetime.utcnow().isoformat(),
                "gusto_last_event_type": event_type,
                "gusto_last_event_payload": payload,
            })
            matched_addon.metadata_json = metadata
            db.commit()

        return {
            "success": True,
            "data": {
                "received": True,
                "event_type": event_type,
                "company_uuid": company_uuid,
                "matched_customer_id": matched_addon.customer_id if matched_addon else None,
            },
            "meta": {},
        }
    finally:
        db.close()
