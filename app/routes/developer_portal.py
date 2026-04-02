"""
Developer Portal API — Apps, Agreement Workflows & Signing Flow

Implements the multi-stage agreement signing flow for the Sajet Developer Portal,
similar to Uber's Developer Dashboard pattern:
  App Created → Organization Linked → Agreements (Generate→Pending→View→Review→Signed)
  → Sandbox Access → Verification → Verified

Uses the existing agreements infrastructure + agreement_workflow service.
"""

from fastapi import APIRouter, HTTPException, Request, Cookie
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import io
import logging
import os

from ..models.database import (
    DeveloperApp, DeveloperAgreementFlow, AgreementTemplate,
    SessionLocal,
)
from ..services import agreement_workflow as workflow
from ..routes.secure_auth import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/developer-portal", tags=["Developer Portal"])


# ═══════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════

def _extract_token(request: Request, access_token: Optional[str] = None) -> str:
    token = access_token or request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "No autenticado")
    return token


def _get_payload(request: Request, access_token: str = Cookie(None)) -> dict:
    token = _extract_token(request, access_token)
    try:
        return TokenManager.verify_access_token(token)
    except Exception:
        raise HTTPException(401, "Token inválido")


def _require_admin(request: Request, access_token: str = Cookie(None)):
    payload = _get_payload(request, access_token)
    if payload.get("role") not in ("admin", "operator"):
        raise HTTPException(403, "Solo administradores")
    return payload


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class CreateAppRequest(BaseModel):
    name: str
    description: str = ""
    api_suite: str = "eats_marketplace"
    organization_name: str = ""


class LinkOrgRequest(BaseModel):
    organization_name: str


class SignFlowRequest(BaseModel):
    signer_name: str
    signer_title: Optional[str] = None
    signer_company: Optional[str] = None
    signature_data: str  # typed name (cursive)


class ReviewFlowRequest(BaseModel):
    action: str  # "approve" | "reject"
    reason: Optional[str] = None


class UpdateAppRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    organization_name: Optional[str] = None


# ═══════════════════════════════════════════
#  APP CRUD
# ═══════════════════════════════════════════

@router.get("/apps")
async def list_apps(request: Request, access_token: str = Cookie(None)):
    """List all developer apps for the current user (or all for admin)."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    db = SessionLocal()
    try:
        q = db.query(DeveloperApp).order_by(DeveloperApp.created_at.desc())

        if role not in ("admin", "operator"):
            if role == "partner":
                q = q.filter(DeveloperApp.partner_id == user_id)
            else:
                q = q.filter(DeveloperApp.customer_id == user_id)

        apps = q.limit(100).all()
        items = []
        for app in apps:
            summary = workflow.get_app_summary(db, app.id)
            if summary:
                items.append(summary)

        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.get("/apps/{app_id}")
async def get_app(app_id: int, request: Request, access_token: str = Cookie(None)):
    """Get a single developer app with full agreement flow details."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        # Access control
        if role not in ("admin", "operator"):
            if role == "partner" and app.partner_id != user_id:
                raise HTTPException(403, "Acceso denegado")
            elif role not in ("partner",) and app.customer_id != user_id:
                raise HTTPException(403, "Acceso denegado")

        summary = workflow.get_app_summary(db, app_id)
        if not summary:
            raise HTTPException(404, "App no encontrada")

        return summary
    finally:
        db.close()


@router.post("/apps")
async def create_app(data: CreateAppRequest, request: Request, access_token: str = Cookie(None)):
    """Create a new developer app. Auto-generates required agreement flows."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if not data.name or len(data.name.strip()) < 2:
        raise HTTPException(400, "Nombre de la app requerido (mínimo 2 caracteres)")

    db = SessionLocal()
    try:
        app = workflow.create_app(
            db,
            name=data.name.strip(),
            description=data.description,
            api_suite=data.api_suite,
            partner_id=user_id if role == "partner" else None,
            customer_id=user_id if role in ("tenant", "customer") else None,
            created_by=email or str(user_id),
            organization_name=data.organization_name,
        )

        summary = workflow.get_app_summary(db, app.id)
        return {
            "message": "App creada exitosamente",
            "app": summary,
        }
    except Exception as e:
        logger.error(f"Error creating developer app: {e}")
        raise HTTPException(500, f"Error al crear app: {str(e)}")
    finally:
        db.close()


@router.put("/apps/{app_id}")
async def update_app(app_id: int, data: UpdateAppRequest, request: Request, access_token: str = Cookie(None)):
    """Update app details."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        # Access control
        if role not in ("admin", "operator"):
            if role == "partner" and app.partner_id != user_id:
                raise HTTPException(403, "Acceso denegado")
            elif role not in ("partner",) and app.customer_id != user_id:
                raise HTTPException(403, "Acceso denegado")

        if data.name is not None:
            app.name = data.name
        if data.description is not None:
            app.description = data.description
        if data.webhook_url is not None:
            app.webhook_url = data.webhook_url
        if data.organization_name is not None:
            app.organization_name = data.organization_name

        app.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "App actualizada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.delete("/apps/{app_id}")
async def delete_app(app_id: int, request: Request, access_token: str = Cookie(None)):
    """Delete a developer app (only if no signed agreements)."""
    payload = _require_admin(request, access_token)

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        signed_count = db.query(DeveloperAgreementFlow).filter(
            DeveloperAgreementFlow.app_id == app_id,
            DeveloperAgreementFlow.status == "signed",
        ).count()
        if signed_count > 0:
            raise HTTPException(400, f"No se puede eliminar: {signed_count} acuerdos firmados. Desactívela en su lugar.")

        db.delete(app)
        db.commit()
        return {"message": "App eliminada"}
    except HTTPException:
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════
#  ORGANIZATION LINKING
# ═══════════════════════════════════════════

@router.post("/apps/{app_id}/link-organization")
async def link_organization(app_id: int, data: LinkOrgRequest, request: Request, access_token: str = Cookie(None)):
    """Link an organization to the app → triggers agreement generation."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    if not data.organization_name or len(data.organization_name.strip()) < 2:
        raise HTTPException(400, "Nombre de organización requerido")

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        if role not in ("admin", "operator"):
            if role == "partner" and app.partner_id != user_id:
                raise HTTPException(403, "Acceso denegado")

        app = workflow.link_organization(db, app_id, data.organization_name.strip())
        summary = workflow.get_app_summary(db, app_id)
        return {
            "message": "Organización vinculada exitosamente",
            "app": summary,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════
#  AGREEMENT FLOW — View, Sign, Review
# ═══════════════════════════════════════════

@router.get("/flows/{flow_id}")
async def get_flow(flow_id: int, request: Request, access_token: str = Cookie(None)):
    """Get a single agreement flow with template content."""
    payload = _get_payload(request, access_token)

    db = SessionLocal()
    try:
        flow = db.query(DeveloperAgreementFlow).filter(
            DeveloperAgreementFlow.id == flow_id
        ).first()
        if not flow:
            raise HTTPException(404, "Flujo de acuerdo no encontrado")

        template = flow.template

        return {
            "id": flow.id,
            "app_id": flow.app_id,
            "template_id": flow.template_id,
            "template_title": template.title if template else None,
            "template_type": template.agreement_type.value if template and template.agreement_type else None,
            "template_version": template.version if template else None,
            "html_content": template.html_content if template else "",
            "status": flow.status,
            "generated_at": flow.generated_at.isoformat() if flow.generated_at else None,
            "viewed_at": flow.viewed_at.isoformat() if flow.viewed_at else None,
            "submitted_at": flow.submitted_at.isoformat() if flow.submitted_at else None,
            "signed_at": flow.signed_at.isoformat() if flow.signed_at else None,
            "rejected_at": flow.rejected_at.isoformat() if flow.rejected_at else None,
            "rejection_reason": flow.rejection_reason,
            "has_pdf_preview": bool(flow.pdf_preview_path),
            "signed_agreement_id": flow.signed_agreement_id,
        }
    finally:
        db.close()


@router.post("/flows/{flow_id}/view")
async def mark_flow_viewed(flow_id: int, request: Request, access_token: str = Cookie(None)):
    """Mark an agreement as viewed (transition pending → viewed)."""
    payload = _get_payload(request, access_token)

    db = SessionLocal()
    try:
        flow = db.query(DeveloperAgreementFlow).filter(
            DeveloperAgreementFlow.id == flow_id
        ).first()
        if not flow:
            raise HTTPException(404, "Flujo de acuerdo no encontrado")

        if flow.status == "viewed":
            return {"message": "Ya fue marcado como visto", "status": flow.status}

        flow = workflow.transition_flow(db, flow_id, "viewed")
        return {
            "message": "Acuerdo marcado como visto",
            "status": flow.status,
            "viewed_at": flow.viewed_at.isoformat() if flow.viewed_at else None,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


@router.post("/flows/{flow_id}/sign")
async def sign_flow(flow_id: int, data: SignFlowRequest, request: Request, access_token: str = Cookie(None)):
    """Sign a developer agreement (transition viewed → in_review)."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if not data.signer_name or len(data.signer_name.strip()) < 2:
        raise HTTPException(400, "Nombre del firmante requerido (mínimo 2 caracteres)")
    if not data.signature_data or len(data.signature_data.strip()) < 2:
        raise HTTPException(400, "Firma requerida")

    ip = _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")

    db = SessionLocal()
    try:
        result = workflow.sign_developer_agreement(
            db,
            flow_id,
            signer_name=data.signer_name.strip(),
            signer_email=email or "",
            signer_title=data.signer_title or "",
            signer_company=data.signer_company or "",
            signature_data=data.signature_data.strip(),
            ip_address=ip,
            user_agent=ua,
            partner_id=user_id if role == "partner" else None,
            customer_id=user_id if role in ("tenant", "customer") else None,
        )
        return {
            "message": "Acuerdo firmado exitosamente. Pendiente de revisión.",
            **result,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error signing developer agreement: {e}")
        raise HTTPException(500, f"Error al firmar: {str(e)}")
    finally:
        db.close()


@router.post("/flows/{flow_id}/review")
async def review_flow(flow_id: int, data: ReviewFlowRequest, request: Request, access_token: str = Cookie(None)):
    """Admin reviews a signed agreement: approve or reject."""
    payload = _require_admin(request, access_token)
    reviewer_id = payload.get("sub", "admin")

    if data.action not in ("approve", "reject"):
        raise HTTPException(400, "Acción debe ser 'approve' o 'reject'")

    if data.action == "reject" and not data.reason:
        raise HTTPException(400, "Motivo de rechazo requerido")

    db = SessionLocal()
    try:
        if data.action == "approve":
            flow = workflow.approve_flow(db, flow_id, reviewer_id)
            return {
                "message": "Acuerdo aprobado exitosamente",
                "status": flow.status,
                "signed_at": flow.signed_at.isoformat() if flow.signed_at else None,
            }
        else:
            flow = workflow.reject_flow(db, flow_id, reviewer_id, data.reason or "")
            return {
                "message": "Acuerdo rechazado",
                "status": flow.status,
                "rejection_reason": flow.rejection_reason,
            }
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


@router.get("/flows/{flow_id}/preview-pdf")
async def get_preview_pdf(flow_id: int, request: Request, access_token: str = Cookie(None)):
    """Download preview PDF of an agreement flow."""
    payload = _get_payload(request, access_token)

    db = SessionLocal()
    try:
        flow = db.query(DeveloperAgreementFlow).filter(
            DeveloperAgreementFlow.id == flow_id
        ).first()
        if not flow:
            raise HTTPException(404, "Flujo no encontrado")

        pdf_path = flow.pdf_preview_path
        if not pdf_path:
            # Generate on-the-fly
            email = payload.get("sub", "")
            pdf_path = workflow.generate_preview_pdf(
                db, flow_id,
                {"name": "", "email": email, "company": ""}
            )

        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(404, "PDF no disponible")

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="agreement_preview_{flow_id}.pdf"'
            },
        )
    finally:
        db.close()


# ═══════════════════════════════════════════
#  ADMIN: Production app requests
# ═══════════════════════════════════════════

@router.post("/apps/{app_id}/request-production")
async def request_production(app_id: int, request: Request, access_token: str = Cookie(None)):
    """Request production access for an app (after sandbox is granted)."""
    payload = _get_payload(request, access_token)

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        if not app.sandbox_access:
            raise HTTPException(400, "Debe tener acceso sandbox antes de solicitar producción")

        if app.status in ("verification_requested", "verified"):
            raise HTTPException(400, f"La app ya está en estado: {app.status}")

        app.status = "verification_requested"
        app.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "Solicitud de producción enviada. Un administrador la revisará.", "status": app.status}
    except HTTPException:
        raise
    finally:
        db.close()


@router.post("/apps/{app_id}/verify")
async def verify_app(app_id: int, request: Request, access_token: str = Cookie(None)):
    """Admin verifies an app for production use."""
    payload = _require_admin(request, access_token)

    db = SessionLocal()
    try:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if not app:
            raise HTTPException(404, "App no encontrada")

        if app.status != "verification_requested":
            raise HTTPException(400, f"Solo se puede verificar apps en estado 'verification_requested', actual: {app.status}")

        app.status = "verified"
        app.app_mode = "production"
        app.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "App verificada para producción", "status": app.status}
    except HTTPException:
        raise
    finally:
        db.close()
