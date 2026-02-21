"""
Customer Onboarding API — Flujo post-signup para clientes (tenant).

Steps:
  0 = Nuevo (sin completar perfil)
  1 = Perfil completado
  2 = e-CF completado (solo si country=DO y requires_ecf=True; si no, se salta)
  3 = Pago / Stripe checkout completado
  4 = Onboarding completo

Si el cliente viene referido por un partner, se vincula via partner_id.
Si el cliente es de República Dominicana y usa facturación electrónica,
debe completar el paso 2 (cuestionario DGII / e-CF).
"""

from fastapi import APIRouter, HTTPException, Request, Cookie, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import hashlib, secrets, json, logging, re

from ..models.database import (
    Customer, SessionLocal, Partner, get_db,
)
from ..routes.secure_auth import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customer-onboarding", tags=["Customer Onboarding"])


# ═══════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════

def _extract_token(request: Request, access_token: Optional[str] = None) -> str:
    """Extract JWT from cookie or Authorization header."""
    token = access_token or request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "No autenticado")
    return token


def _require_customer(request: Request, access_token: str = Cookie(None)) -> dict:
    """Verify JWT and return customer payload. Allows role tenant OR partner-referred."""
    token = _extract_token(request, access_token)
    try:
        payload = TokenManager.verify_access_token(token)
    except Exception:
        raise HTTPException(401, "Token inválido o expirado")

    role = payload.get("role")
    if role not in ("tenant", "admin"):
        raise HTTPException(403, "Acceso denegado — solo clientes")

    return {
        "username": payload.get("sub"),
        "role": role,
        "user_id": payload.get("user_id"),
        "tenant_id": payload.get("tenant_id"),
    }


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class CustomerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None


class ECFQuestionnaireRequest(BaseModel):
    """Cuestionario DGII para factura electrónica en RD."""
    requires_ecf: bool = True
    ecf_rnc: str                            # RNC o Cédula (9 u 11 dígitos)
    ecf_business_name: str                  # Razón social ante DGII
    ecf_establishment_type: str             # persona_fisica | persona_juridica | zona_franca
    ecf_ncf_series: Optional[str] = None    # Serie NCF (B01, B02, B14, B15, E31-E34)
    ecf_environment: str = "test_ecf"       # test_ecf | production

    @field_validator("ecf_rnc")
    @classmethod
    def validate_rnc(cls, v: str) -> str:
        clean = re.sub(r"[^0-9]", "", v)
        if len(clean) not in (9, 11):
            raise ValueError("RNC debe tener 9 dígitos o Cédula 11 dígitos")
        return clean

    @field_validator("ecf_establishment_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = ("persona_fisica", "persona_juridica", "zona_franca")
        if v not in allowed:
            raise ValueError(f"Tipo debe ser uno de: {', '.join(allowed)}")
        return v

    @field_validator("ecf_environment")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ("test_ecf", "production"):
            raise ValueError("Ambiente debe ser test_ecf o production")
        return v


class SetPasswordRequest(BaseModel):
    password: str
    password_confirm: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class SkipECFRequest(BaseModel):
    """Para clientes que no necesitan e-CF."""
    skip: bool = True


# ═══════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/status")
async def get_onboarding_status(request: Request, access_token: str = Cookie(None)):
    """Obtiene el estado actual del onboarding del cliente."""
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]
    if not customer_id:
        raise HTTPException(400, "No se encontró ID de cliente")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        # Determinar si necesita paso e-CF
        is_dominican = (customer.country or "").upper() in ("DO", "RD", "REPÚBLICA DOMINICANA", "REPUBLICA DOMINICANA", "DOMINICAN REPUBLIC")
        needs_ecf_step = is_dominican and customer.requires_ecf

        return {
            "customer_id": customer.id,
            "onboarding_step": customer.onboarding_step,
            "onboarding_completed": customer.onboarding_completed_at is not None,
            "full_name": customer.full_name,
            "company_name": customer.company_name,
            "email": customer.email,
            "phone": customer.phone,
            "country": customer.country,
            "plan": customer.plan.value if customer.plan else None,
            "partner_id": customer.partner_id,
            # e-CF state
            "is_dominican": is_dominican,
            "needs_ecf_step": needs_ecf_step,
            "requires_ecf": customer.requires_ecf,
            "ecf_rnc": customer.ecf_rnc,
            "ecf_business_name": customer.ecf_business_name,
            "ecf_establishment_type": customer.ecf_establishment_type,
            "ecf_ncf_series": customer.ecf_ncf_series,
            "ecf_environment": customer.ecf_environment,
        }
    finally:
        db.close()


@router.post("/set-password")
async def set_customer_password(data: SetPasswordRequest, request: Request, access_token: str = Cookie(None)):
    """Paso 0→1: Establece contraseña propia (reemplaza la temporal si la tuvo)."""
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]

    if data.password != data.password_confirm:
        raise HTTPException(400, "Las contraseñas no coinciden")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        # Generar hash salt:sha256
        salt = secrets.token_hex(16)
        password_hash = f"{salt}:{hashlib.sha256((data.password + salt).encode()).hexdigest()}"
        customer.password_hash = password_hash

        if customer.onboarding_step < 1:
            customer.onboarding_step = 1

        db.commit()
        return {"message": "Contraseña establecida", "onboarding_step": customer.onboarding_step}
    finally:
        db.close()


@router.post("/update-profile")
async def update_customer_profile(data: CustomerProfileUpdate, request: Request, access_token: str = Cookie(None)):
    """Paso 1→2(si RD) o 1→3(si no RD): Actualiza perfil del cliente."""
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        # Actualizar campos de perfil
        for field in ("full_name", "company_name", "phone", "country", "notes"):
            val = getattr(data, field, None)
            if val is not None:
                setattr(customer, field, val)

        # Determinar siguiente paso según país
        country = (customer.country or "").upper()
        is_dominican = country in ("DO", "RD", "REPÚBLICA DOMINICANA", "REPUBLICA DOMINICANA", "DOMINICAN REPUBLIC")

        if customer.onboarding_step < 1:
            customer.onboarding_step = 1

        # Si es dominicano, el siguiente paso será e-CF (2).
        # Si no, salta directamente a pago (3).
        if is_dominican:
            if customer.onboarding_step < 2:
                customer.onboarding_step = 2  # Ir a paso e-CF
        else:
            customer.requires_ecf = False
            if customer.onboarding_step < 3:
                customer.onboarding_step = 3  # Saltar e-CF, ir a pago

        db.commit()

        return {
            "message": "Perfil actualizado",
            "onboarding_step": customer.onboarding_step,
            "is_dominican": is_dominican,
            "needs_ecf_step": is_dominican,
        }
    finally:
        db.close()


@router.post("/ecf-questionnaire")
async def submit_ecf_questionnaire(data: ECFQuestionnaireRequest, request: Request, access_token: str = Cookie(None)):
    """
    Paso 2→3: Cuestionario e-CF para clientes de República Dominicana.
    Registra los datos fiscales necesarios para facturación electrónica
    ante la DGII (Dirección General de Impuestos Internos).
    """
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        # Guardar datos e-CF
        customer.requires_ecf = data.requires_ecf
        customer.ecf_rnc = data.ecf_rnc
        customer.ecf_business_name = data.ecf_business_name
        customer.ecf_establishment_type = data.ecf_establishment_type
        customer.ecf_ncf_series = data.ecf_ncf_series
        customer.ecf_environment = data.ecf_environment

        # Avanzar al paso 3 (pago)
        if customer.onboarding_step < 3:
            customer.onboarding_step = 3

        db.commit()

        logger.info(f"e-CF questionnaire completed for customer {customer_id}: RNC={data.ecf_rnc}")

        return {
            "message": "Datos fiscales e-CF registrados correctamente",
            "onboarding_step": customer.onboarding_step,
            "ecf_rnc": customer.ecf_rnc,
            "ecf_business_name": customer.ecf_business_name,
        }
    finally:
        db.close()


@router.post("/skip-ecf")
async def skip_ecf_step(data: SkipECFRequest, request: Request, access_token: str = Cookie(None)):
    """
    Permite a un cliente dominicano indicar que NO necesita e-CF
    (por ejemplo, si no emitirá facturas electrónicas inicialmente).
    """
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        customer.requires_ecf = False
        if customer.onboarding_step < 3:
            customer.onboarding_step = 3

        db.commit()
        return {"message": "Paso e-CF omitido", "onboarding_step": customer.onboarding_step}
    finally:
        db.close()


@router.post("/complete")
async def complete_onboarding(request: Request, access_token: str = Cookie(None)):
    """
    Marca el onboarding como completo (paso 4).
    Se llama después del pago exitoso o de que el admin lo marque manualmente.
    """
    auth = _require_customer(request, access_token)
    customer_id = auth["user_id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        customer.onboarding_step = 4
        customer.onboarding_completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Customer onboarding completed: {customer_id} ({customer.company_name})")

        return {
            "message": "¡Onboarding completado exitosamente!",
            "onboarding_step": 4,
            "onboarding_completed_at": customer.onboarding_completed_at.isoformat(),
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  ADMIN ENDPOINTS — gestionar onboarding de clientes
# ═══════════════════════════════════════════

def _require_admin(request: Request, access_token: str = Cookie(None)) -> dict:
    """Verify JWT and require admin role."""
    token = _extract_token(request, access_token)
    try:
        payload = TokenManager.verify_access_token(token)
    except Exception:
        raise HTTPException(401, "Token inválido")

    if payload.get("role") != "admin":
        raise HTTPException(403, "Solo administradores")

    return {"username": payload.get("sub"), "role": "admin"}


@router.get("/admin/pending")
async def list_pending_onboardings(request: Request, access_token: str = Cookie(None)):
    """Lista clientes con onboarding pendiente (admin)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        customers = db.query(Customer).filter(
            Customer.onboarding_step < 4,
            Customer.is_admin_account == False,
        ).order_by(Customer.created_at.desc()).all()

        return {
            "items": [
                {
                    "id": c.id,
                    "email": c.email,
                    "full_name": c.full_name,
                    "company_name": c.company_name,
                    "country": c.country,
                    "onboarding_step": c.onboarding_step,
                    "requires_ecf": c.requires_ecf,
                    "ecf_rnc": c.ecf_rnc,
                    "plan": c.plan.value if c.plan else None,
                    "partner_id": c.partner_id,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in customers
            ],
            "total": len(customers),
        }
    finally:
        db.close()


@router.post("/admin/advance/{customer_id}")
async def admin_advance_onboarding(customer_id: int, request: Request, access_token: str = Cookie(None)):
    """Avanza manualmente el paso de onboarding de un cliente (admin)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(404, "Cliente no encontrado")

        if customer.onboarding_step >= 4:
            return {"message": "Onboarding ya completado", "onboarding_step": 4}

        customer.onboarding_step += 1
        if customer.onboarding_step >= 4:
            customer.onboarding_completed_at = datetime.utcnow()

        db.commit()
        return {
            "message": f"Onboarding avanzado a paso {customer.onboarding_step}",
            "onboarding_step": customer.onboarding_step,
        }
    finally:
        db.close()


@router.get("/admin/ecf-customers")
async def list_ecf_customers(request: Request, access_token: str = Cookie(None)):
    """Lista clientes con e-CF activo (admin) — útil para soporte DGII."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        customers = db.query(Customer).filter(
            Customer.requires_ecf == True,
        ).order_by(Customer.company_name).all()

        return {
            "items": [
                {
                    "id": c.id,
                    "company_name": c.company_name,
                    "email": c.email,
                    "ecf_rnc": c.ecf_rnc,
                    "ecf_business_name": c.ecf_business_name,
                    "ecf_establishment_type": c.ecf_establishment_type,
                    "ecf_ncf_series": c.ecf_ncf_series,
                    "ecf_environment": c.ecf_environment,
                    "ecf_certificate_expiry": c.ecf_certificate_expiry.isoformat() if c.ecf_certificate_expiry else None,
                    "onboarding_step": c.onboarding_step,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in customers
            ],
            "total": len(customers),
        }
    finally:
        db.close()
