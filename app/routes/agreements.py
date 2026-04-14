"""
Agreements API — Template CRUD (admin) + Signing flow (partner/customer)

Templates are editable HTML with variables: {{signer_name}}, {{signer_company}}, {{date}}, {{ip_address}}, {{signer_email}}
Signatures are typed (Stripe-style: type your name → generates cursive preview).
On signing: SHA256 hash of rendered HTML is stored, PDF generated via weasyprint.
"""

from fastapi import APIRouter, HTTPException, Request, Cookie, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib
import io
import logging
import os
import re

from ..models.database import (
    AgreementTemplate, AgreementType, AgreementTarget,
    SignedAgreement, Partner, Customer,
    SessionLocal, get_db,
)
from ..routes.secure_auth import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agreements", tags=["Agreements"])

# PDF storage path
PDF_BASE_PATH = os.getenv("AGREEMENT_PDF_PATH", "/opt/Erp_core/data/agreements")
os.makedirs(PDF_BASE_PATH, exist_ok=True)


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
    from ..utils.ip import get_real_ip
    return get_real_ip(request)


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class TemplateCreate(BaseModel):
    agreement_type: str = "nda"
    target: str = "partner"
    title: str
    version: str = "1.0"
    html_content: str
    is_active: bool = True
    is_required: bool = True
    sort_order: int = 0


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    html_content: Optional[str] = None
    is_active: Optional[bool] = None
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None
    version: Optional[str] = None


class SignRequest(BaseModel):
    template_id: int
    signer_name: str
    signer_title: Optional[str] = None
    signer_company: Optional[str] = None
    signature_data: str  # The typed name (cursive)


# ═══════════════════════════════════════════
#  HELPER: Render template variables
# ═══════════════════════════════════════════

def _render_template(html: str, variables: dict) -> str:
    """Replace {{variable}} placeholders with values."""
    for key, value in variables.items():
        html = html.replace(f"{{{{{key}}}}}", str(value or ""))
    return html


def _generate_pdf(html_content: str, title: str) -> bytes:
    """Generate PDF from HTML using weasyprint."""
    try:
        from weasyprint import HTML
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a1a;
                        max-width: 700px; margin: 40px auto; padding: 20px; font-size: 14px;
                        line-height: 1.6; }}
                h2 {{ color: #1a1a1a; border-bottom: 2px solid #e74c3c; padding-bottom: 8px; }}
                h3 {{ color: #333; margin-top: 24px; }}
                ul {{ padding-left: 24px; }}
                li {{ margin: 4px 0; }}
                hr {{ border: none; border-top: 1px solid #ddd; margin: 24px 0; }}
                .signature-block {{ margin-top: 40px; border-top: 2px solid #1a1a1a; padding-top: 20px; }}
                .signature {{ font-family: 'Brush Script MT', 'Segoe Script', cursive;
                             font-size: 28px; color: #1a1a2e; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        pdf_bytes = HTML(string=full_html).write_pdf()
        return pdf_bytes
    except ImportError:
        logger.warning("weasyprint not installed, skipping PDF generation")
        return b""
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return b""


# ═══════════════════════════════════════════
#  ADMIN ENDPOINTS — Template CRUD
# ═══════════════════════════════════════════

@router.get("/templates")
async def list_templates(
    request: Request,
    target: Optional[str] = None,
    access_token: str = Cookie(None),
):
    """List all agreement templates (admin)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        q = db.query(AgreementTemplate).order_by(AgreementTemplate.sort_order)
        if target:
            q = q.filter(AgreementTemplate.target == target)
        templates = q.all()

        return {
            "items": [
                {
                    "id": t.id,
                    "agreement_type": t.agreement_type.value if t.agreement_type else None,
                    "target": t.target.value if t.target else None,
                    "title": t.title,
                    "version": t.version,
                    "html_content": t.html_content,
                    "is_active": t.is_active,
                    "is_required": t.is_required,
                    "sort_order": t.sort_order,
                    "signed_count": db.query(SignedAgreement).filter(
                        SignedAgreement.template_id == t.id
                    ).count(),
                    "created_by": t.created_by,
                    "updated_by": t.updated_by,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in templates
            ],
            "total": len(templates),
        }
    finally:
        db.close()


@router.get("/templates/{template_id}")
async def get_template(template_id: int, request: Request, access_token: str = Cookie(None)):
    """Get single template by ID (admin)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        t = db.query(AgreementTemplate).filter(AgreementTemplate.id == template_id).first()
        if not t:
            raise HTTPException(404, "Template no encontrado")
        return {
            "id": t.id,
            "agreement_type": t.agreement_type.value if t.agreement_type else None,
            "target": t.target.value if t.target else None,
            "title": t.title,
            "version": t.version,
            "html_content": t.html_content,
            "is_active": t.is_active,
            "is_required": t.is_required,
            "sort_order": t.sort_order,
            "created_by": t.created_by,
            "updated_by": t.updated_by,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
    finally:
        db.close()


@router.post("/templates")
async def create_template(data: TemplateCreate, request: Request, access_token: str = Cookie(None)):
    """Create a new agreement template (admin)."""
    payload = _require_admin(request, access_token)

    db = SessionLocal()
    try:
        template = AgreementTemplate(
            agreement_type=data.agreement_type,
            target=data.target,
            title=data.title,
            version=data.version,
            html_content=data.html_content,
            is_active=data.is_active,
            is_required=data.is_required,
            sort_order=data.sort_order,
            created_by=payload.get("sub"),
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return {"message": "Template creado", "id": template.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))
    finally:
        db.close()


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int, data: TemplateUpdate, request: Request, access_token: str = Cookie(None)
):
    """Update an agreement template (admin)."""
    payload = _require_admin(request, access_token)

    db = SessionLocal()
    try:
        t = db.query(AgreementTemplate).filter(AgreementTemplate.id == template_id).first()
        if not t:
            raise HTTPException(404, "Template no encontrado")

        for field in ("title", "html_content", "is_active", "is_required", "sort_order", "version"):
            val = getattr(data, field, None)
            if val is not None:
                setattr(t, field, val)

        t.updated_by = payload.get("sub")
        t.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Template actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))
    finally:
        db.close()


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, request: Request, access_token: str = Cookie(None)):
    """Delete template (only if no signed agreements exist)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        t = db.query(AgreementTemplate).filter(AgreementTemplate.id == template_id).first()
        if not t:
            raise HTTPException(404, "Template no encontrado")

        signed_count = db.query(SignedAgreement).filter(
            SignedAgreement.template_id == template_id
        ).count()
        if signed_count > 0:
            raise HTTPException(400, f"No se puede eliminar: {signed_count} firmas asociadas. Desactívelo en su lugar.")

        db.delete(t)
        db.commit()
        return {"message": "Template eliminado"}
    except HTTPException:
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════
#  PUBLIC: Get required templates for signing
# ═══════════════════════════════════════════

@router.get("/required/{target_type}")
async def get_required_agreements(target_type: str, request: Request, access_token: str = Cookie(None)):
    """
    Get active required agreement templates for a target type (partner/customer).
    Also returns which ones the current user has already signed.
    """
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    db = SessionLocal()
    try:
        templates = db.query(AgreementTemplate).filter(
            AgreementTemplate.target.in_([target_type, "both"]),
            AgreementTemplate.is_active == True,
            AgreementTemplate.is_required == True,
        ).order_by(AgreementTemplate.sort_order).all()

        # Filtrar condicionalmente:
        if target_type == "partner" and user_id:
            from app.models.database import Partner
            partner = db.query(Partner).filter(Partner.id == user_id).first()
            if partner:
                country = (partner.country or "").lower().strip()
                is_us = country in ["us", "usa", "united states", "estados unidos"]
                # Si ES de USA, quizá no exijamos el W-8BEN-E, si NO es de USA sí lo exijimos.
                # Filtramos el título si consideramos que solo aplica fuera de USA.
                if is_us:
                    templates = [t for t in templates if "W-8" not in t.title and "W-9" not in t.title]

        # Check which are already signed
        result = []
        for t in templates:
            q = db.query(SignedAgreement).filter(SignedAgreement.template_id == t.id)
            if target_type == "partner" and user_id:
                q = q.filter(SignedAgreement.partner_id == user_id)
            elif target_type == "customer" and user_id:
                q = q.filter(SignedAgreement.customer_id == user_id)

            signed = q.first()
            result.append({
                "id": t.id,
                "agreement_type": t.agreement_type.value if t.agreement_type else None,
                "title": t.title,
                "version": t.version,
                "is_signed": signed is not None,
                "signed_at": signed.signed_at.isoformat() if signed else None,
                "html_content": t.html_content,
            })

        all_signed = all(r["is_signed"] for r in result) if result else True

        return {
            "items": result,
            "total": len(result),
            "all_signed": all_signed,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  SIGNING FLOW
# ═══════════════════════════════════════════

@router.post("/sign")
async def sign_agreement(data: SignRequest, request: Request, access_token: str = Cookie(None)):
    """
    Sign an agreement template. Creates a signed record with hash and optional PDF.
    """
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if not data.signer_name or len(data.signer_name.strip()) < 2:
        raise HTTPException(400, "Nombre del firmante requerido (mínimo 2 caracteres)")

    if not data.signature_data or len(data.signature_data.strip()) < 2:
        raise HTTPException(400, "Firma requerida")

    ip = _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")[:500]

    db = SessionLocal()
    try:
        template = db.query(AgreementTemplate).filter(
            AgreementTemplate.id == data.template_id,
            AgreementTemplate.is_active == True,
        ).first()
        if not template:
            raise HTTPException(404, "Template no encontrado o inactivo")

        # Check not already signed
        existing_q = db.query(SignedAgreement).filter(
            SignedAgreement.template_id == data.template_id
        )
        if role == "partner" and user_id:
            existing_q = existing_q.filter(SignedAgreement.partner_id == user_id)
        elif user_id:
            existing_q = existing_q.filter(SignedAgreement.customer_id == user_id)

        if existing_q.first():
            raise HTTPException(400, "Este acuerdo ya fue firmado")

        # Render template with variables
        now = datetime.utcnow()
        variables = {
            "signer_name": data.signer_name,
            "signer_company": data.signer_company or "",
            "signer_email": email or "",
            "date": now.strftime("%d de %B de %Y"),
            "ip_address": ip,
        }
        rendered_html = _render_template(template.html_content, variables)

        # Add signature block to rendered HTML
        signature_html = f"""
        <div class="signature-block">
            <p><strong>Firmado electrónicamente por:</strong></p>
            <p class="signature">{data.signature_data}</p>
            <p><strong>{data.signer_name}</strong></p>
            <p>{data.signer_title or ""} — {data.signer_company or ""}</p>
            <p style="font-size:12px;color:#666;">
                Fecha: {now.strftime("%Y-%m-%d %H:%M:%S UTC")} | IP: {ip}
            </p>
        </div>
        """
        full_html = rendered_html + signature_html

        # Compute document hash
        doc_hash = hashlib.sha256(full_html.encode()).hexdigest()

        # Generate PDF
        pdf_bytes = _generate_pdf(full_html, template.title)
        pdf_path = None
        if pdf_bytes:
            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", template.title[:50])
            filename = f"{safe_name}_{user_id}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(PDF_BASE_PATH, filename)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)

        # Create signed record
        signed = SignedAgreement(
            template_id=data.template_id,
            partner_id=user_id if role == "partner" else None,
            customer_id=user_id if role in ("tenant", "customer") else None,
            signer_name=data.signer_name,
            signer_email=email or "",
            signer_title=data.signer_title,
            signer_company=data.signer_company,
            signature_data=data.signature_data,
            signature_type="typed",
            ip_address=ip,
            user_agent=ua,
            document_hash=doc_hash,
            pdf_path=pdf_path,
            signed_at=now,
        )
        db.add(signed)

        # Update partner.contract_signed_at if partner NDA
        if role == "partner" and user_id:
            partner = db.query(Partner).filter(Partner.id == user_id).first()
            if partner:
                partner.contract_signed_at = now
                partner.contract_reference = f"AGR-{signed.id:06d}" if signed.id else None

        db.commit()
        db.refresh(signed)

        # Update contract reference with actual ID
        if role == "partner" and user_id:
            partner = db.query(Partner).filter(Partner.id == user_id).first()
            if partner:
                partner.contract_reference = f"AGR-{signed.id:06d}"
                db.commit()

        return {
            "message": "Acuerdo firmado exitosamente",
            "signed_id": signed.id,
            "document_hash": doc_hash,
            "signed_at": now.isoformat(),
            "has_pdf": pdf_path is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Agreement signing failed: {e}")
        raise HTTPException(500, f"Error al firmar: {str(e)}")
    finally:
        db.close()


# ═══════════════════════════════════════════
#  ADMIN: List signed agreements
# ═══════════════════════════════════════════

@router.get("/signed")
async def list_signed_agreements(
    request: Request,
    partner_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    access_token: str = Cookie(None),
):
    """List signed agreements (admin)."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        q = db.query(SignedAgreement).order_by(SignedAgreement.signed_at.desc())
        if partner_id:
            q = q.filter(SignedAgreement.partner_id == partner_id)
        if customer_id:
            q = q.filter(SignedAgreement.customer_id == customer_id)

        signed_list = q.limit(100).all()

        return {
            "items": [
                {
                    "id": s.id,
                    "template_id": s.template_id,
                    "template_title": s.template.title if s.template else None,
                    "agreement_type": s.template.agreement_type.value if s.template and s.template.agreement_type else None,
                    "partner_id": s.partner_id,
                    "customer_id": s.customer_id,
                    "signer_name": s.signer_name,
                    "signer_email": s.signer_email,
                    "signer_company": s.signer_company,
                    "document_hash": s.document_hash,
                    "has_pdf": bool(s.pdf_path),
                    "ip_address": s.ip_address,
                    "signed_at": s.signed_at.isoformat() if s.signed_at else None,
                }
                for s in signed_list
            ],
            "total": len(signed_list),
        }
    finally:
        db.close()


@router.get("/signed/{signed_id}/pdf")
async def download_signed_pdf(signed_id: int, request: Request, access_token: str = Cookie(None)):
    """Download PDF of a signed agreement."""
    payload = _get_payload(request, access_token)
    role = payload.get("role")
    user_id = payload.get("user_id")

    db = SessionLocal()
    try:
        signed = db.query(SignedAgreement).filter(SignedAgreement.id == signed_id).first()
        if not signed:
            raise HTTPException(404, "Acuerdo firmado no encontrado")

        # Access control: admin can see all, partner/customer only their own
        if role not in ("admin", "operator"):
            if role == "partner" and signed.partner_id != user_id:
                raise HTTPException(403, "Acceso denegado")
            if role in ("tenant", "customer") and signed.customer_id != user_id:
                raise HTTPException(403, "Acceso denegado")

        if not signed.pdf_path or not os.path.exists(signed.pdf_path):
            raise HTTPException(404, "PDF no disponible")

        with open(signed.pdf_path, "rb") as f:
            pdf_bytes = f.read()

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="agreement_{signed.id}.pdf"'
            },
        )
    finally:
        db.close()
