"""
Agreement Workflow Service — State machine for multi-stage developer portal agreements.

Flow: generated → pending → viewed → in_review → signed | rejected

Reuses the existing agreements infrastructure (templates, signing, PDF generation)
and adds workflow orchestration on top.
"""

from datetime import datetime
from typing import Optional
import hashlib
import logging
import os
import re

from sqlalchemy.orm import Session

from ..models.database import (
    AgreementTemplate, AgreementType, AgreementTarget,
    SignedAgreement,
    DeveloperApp, DeveloperAgreementFlow,
    Partner, Customer,
    SessionLocal,
)

logger = logging.getLogger(__name__)

PDF_BASE_PATH = os.getenv("AGREEMENT_PDF_PATH", "/opt/Erp_core/data/agreements")
os.makedirs(PDF_BASE_PATH, exist_ok=True)

# ═══════════════════════════════════════════
#  STATE MACHINE — Valid transitions
# ═══════════════════════════════════════════

VALID_TRANSITIONS = {
    "generated":  ["pending"],
    "pending":    ["viewed"],
    "viewed":     ["in_review"],
    "in_review":  ["signed", "rejected"],
}


def can_transition(current: str, target: str) -> bool:
    """Check if a status transition is allowed."""
    return target in VALID_TRANSITIONS.get(current, [])


# ═══════════════════════════════════════════
#  TEMPLATE RENDERING
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
                h2 {{ color: #003B73; border-bottom: 2px solid #003B73; padding-bottom: 8px; }}
                h3 {{ color: #333; margin-top: 24px; }}
                ul {{ padding-left: 24px; }}
                li {{ margin: 4px 0; }}
                hr {{ border: none; border-top: 1px solid #ddd; margin: 24px 0; }}
                .signature-block {{ margin-top: 40px; border-top: 2px solid #1a1a1a; padding-top: 20px; }}
                .signature {{ font-family: 'Brush Script MT', 'Segoe Script', cursive;
                             font-size: 28px; color: #003B73; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        return HTML(string=full_html).write_pdf()
    except ImportError:
        logger.warning("weasyprint not installed, skipping PDF generation")
        return b""
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return b""


# ═══════════════════════════════════════════
#  WORKFLOW OPERATIONS
# ═══════════════════════════════════════════

def create_app(
    db: Session,
    *,
    name: str,
    description: str = "",
    api_suite: str = "eats_marketplace",
    partner_id: int | None = None,
    customer_id: int | None = None,
    created_by: str = "",
    organization_name: str = "",
) -> DeveloperApp:
    """Create a new developer app and auto-generate required agreement flows."""
    app = DeveloperApp(
        name=name,
        description=description,
        api_suite=api_suite,
        app_mode="test",
        status="created",
        partner_id=partner_id,
        customer_id=customer_id,
        created_by=created_by,
        organization_name=organization_name,
    )
    db.add(app)
    db.flush()  # get app.id

    # Auto-generate agreement flows for required developer templates
    templates = db.query(AgreementTemplate).filter(
        AgreementTemplate.target.in_(["developer", "both"]),
        AgreementTemplate.is_active == True,
        AgreementTemplate.is_required == True,
    ).order_by(AgreementTemplate.sort_order).all()

    for tmpl in templates:
        flow = DeveloperAgreementFlow(
            app_id=app.id,
            template_id=tmpl.id,
            status="generated",
            generated_at=datetime.utcnow(),
        )
        db.add(flow)

    db.commit()
    db.refresh(app)
    return app


def link_organization(db: Session, app_id: int, org_name: str) -> DeveloperApp:
    """Link an organization to the app (step 2 of the flow)."""
    app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
    if not app:
        raise ValueError("App no encontrada")

    app.organization_name = org_name
    app.organization_linked = True
    app.status = "org_linked"

    # Move agreement flows to "pending"
    flows = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.app_id == app_id,
        DeveloperAgreementFlow.status == "generated",
    ).all()
    for flow in flows:
        flow.status = "pending"

    if flows:
        app.status = "agreements_pending"

    db.commit()
    db.refresh(app)
    return app


def transition_flow(
    db: Session,
    flow_id: int,
    target_status: str,
    *,
    reviewer_id: str | None = None,
    rejection_reason: str | None = None,
) -> DeveloperAgreementFlow:
    """Transition an agreement flow to a new status with validation."""
    flow = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.id == flow_id
    ).first()
    if not flow:
        raise ValueError("Flujo de acuerdo no encontrado")

    if not can_transition(flow.status, target_status):
        raise ValueError(
            f"Transición inválida: {flow.status} → {target_status}. "
            f"Transiciones válidas: {VALID_TRANSITIONS.get(flow.status, [])}"
        )

    now = datetime.utcnow()
    flow.status = target_status
    flow.updated_at = now

    if target_status == "viewed":
        flow.viewed_at = now
    elif target_status == "in_review":
        flow.submitted_at = now
    elif target_status == "signed":
        flow.signed_at = now
        flow.reviewed_at = now
        flow.reviewer_id = reviewer_id
    elif target_status == "rejected":
        flow.rejected_at = now
        flow.reviewed_at = now
        flow.reviewer_id = reviewer_id
        flow.rejection_reason = rejection_reason

    db.commit()
    db.refresh(flow)
    return flow


def sign_developer_agreement(
    db: Session,
    flow_id: int,
    *,
    signer_name: str,
    signer_email: str,
    signer_title: str = "",
    signer_company: str = "",
    signature_data: str,
    ip_address: str = "",
    user_agent: str = "",
    partner_id: int | None = None,
    customer_id: int | None = None,
) -> dict:
    """
    Sign a developer agreement: transitions flow to in_review, creates signed record.
    Admin can then approve (→ signed) or reject.
    """
    flow = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.id == flow_id
    ).first()
    if not flow:
        raise ValueError("Flujo de acuerdo no encontrado")

    if flow.status != "viewed":
        raise ValueError(f"Solo se puede firmar un acuerdo en estado 'viewed', estado actual: {flow.status}")

    template = db.query(AgreementTemplate).filter(
        AgreementTemplate.id == flow.template_id,
        AgreementTemplate.is_active == True,
    ).first()
    if not template:
        raise ValueError("Template no encontrado o inactivo")

    now = datetime.utcnow()
    variables = {
        "signer_name": signer_name,
        "signer_company": signer_company,
        "signer_email": signer_email,
        "date": now.strftime("%d de %B de %Y"),
        "ip_address": ip_address,
    }
    rendered_html = _render_template(template.html_content, variables)

    # Add signature block
    signature_html = f"""
    <div class="signature-block">
        <p><strong>Firmado electrónicamente por:</strong></p>
        <p class="signature">{signature_data}</p>
        <p><strong>{signer_name}</strong></p>
        <p>{signer_title or ""} — {signer_company or ""}</p>
        <p style="font-size:12px;color:#666;">
            Fecha: {now.strftime("%Y-%m-%d %H:%M:%S UTC")} | IP: {ip_address}
        </p>
    </div>
    """
    full_html = rendered_html + signature_html
    doc_hash = hashlib.sha256(full_html.encode()).hexdigest()

    # Generate PDF
    pdf_bytes = _generate_pdf(full_html, template.title)
    pdf_path = None
    if pdf_bytes:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", template.title[:50])
        filename = f"dev_{safe_name}_{flow.app_id}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(PDF_BASE_PATH, filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

    # Create signed agreement record
    signed = SignedAgreement(
        template_id=template.id,
        partner_id=partner_id,
        customer_id=customer_id,
        signer_name=signer_name,
        signer_email=signer_email,
        signer_title=signer_title,
        signer_company=signer_company,
        signature_data=signature_data,
        signature_type="typed",
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else "",
        document_hash=doc_hash,
        pdf_path=pdf_path,
        signed_at=now,
    )
    db.add(signed)
    db.flush()

    # Update flow
    flow.signed_agreement_id = signed.id
    flow.status = "in_review"
    flow.submitted_at = now
    flow.updated_at = now

    db.commit()
    db.refresh(flow)

    return {
        "flow_id": flow.id,
        "signed_id": signed.id,
        "document_hash": doc_hash,
        "status": flow.status,
        "signed_at": now.isoformat(),
        "has_pdf": pdf_path is not None,
    }


def approve_flow(db: Session, flow_id: int, reviewer_id: str) -> DeveloperAgreementFlow:
    """Admin approves an in_review agreement → signed."""
    flow = transition_flow(db, flow_id, "signed", reviewer_id=reviewer_id)

    # Check if all flows for this app are signed → update app status
    _update_app_status_after_review(db, flow.app_id)
    return flow


def reject_flow(db: Session, flow_id: int, reviewer_id: str, reason: str) -> DeveloperAgreementFlow:
    """Admin rejects an in_review agreement → rejected."""
    return transition_flow(
        db, flow_id, "rejected",
        reviewer_id=reviewer_id,
        rejection_reason=reason,
    )


def _update_app_status_after_review(db: Session, app_id: int):
    """After all agreements are signed, grant sandbox access."""
    flows = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.app_id == app_id
    ).all()

    all_signed = all(f.status == "signed" for f in flows)
    if all_signed and flows:
        app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
        if app:
            app.sandbox_access = True
            app.status = "sandbox_granted"
            app.updated_at = datetime.utcnow()
            db.commit()


def generate_preview_pdf(db: Session, flow_id: int, signer_info: dict) -> str | None:
    """Generate a preview PDF for a flow (before signing)."""
    flow = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.id == flow_id
    ).first()
    if not flow:
        return None

    template = db.query(AgreementTemplate).filter(
        AgreementTemplate.id == flow.template_id
    ).first()
    if not template:
        return None

    now = datetime.utcnow()
    variables = {
        "signer_name": signer_info.get("name", "[Nombre del Firmante]"),
        "signer_company": signer_info.get("company", "[Empresa]"),
        "signer_email": signer_info.get("email", "[email@ejemplo.com]"),
        "date": now.strftime("%d de %B de %Y"),
        "ip_address": "PREVIEW",
    }
    rendered_html = _render_template(template.html_content, variables)

    # Mark as watermark
    rendered_html += '<p style="text-align:center;color:#ccc;font-size:24px;margin-top:40px;">— VISTA PREVIA —</p>'

    pdf_bytes = _generate_pdf(rendered_html, f"PREVIEW - {template.title}")
    if pdf_bytes:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", template.title[:50])
        filename = f"preview_{safe_name}_{flow.app_id}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(PDF_BASE_PATH, filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        flow.pdf_preview_path = pdf_path
        db.commit()
        return pdf_path

    return None


def get_app_summary(db: Session, app_id: int) -> dict | None:
    """Get full app summary with agreement flow statuses."""
    app = db.query(DeveloperApp).filter(DeveloperApp.id == app_id).first()
    if not app:
        return None

    flows = db.query(DeveloperAgreementFlow).filter(
        DeveloperAgreementFlow.app_id == app_id
    ).order_by(DeveloperAgreementFlow.id).all()

    # Compute overall progress
    total = len(flows)
    signed_count = sum(1 for f in flows if f.status == "signed")
    progress_stages = {
        "app_created": True,
        "org_linked": app.organization_linked,
        "agreements_signed": total > 0 and signed_count == total,
        "sandbox_access": app.sandbox_access,
        "verification_requested": app.status == "verification_requested",
        "verified": app.status == "verified",
    }

    return {
        "id": app.id,
        "name": app.name,
        "description": app.description,
        "api_suite": app.api_suite,
        "app_mode": app.app_mode,
        "status": app.status,
        "organization_name": app.organization_name,
        "organization_linked": app.organization_linked,
        "sandbox_access": app.sandbox_access,
        "webhook_url": app.webhook_url,
        "client_id": app.client_id,
        "created_by": app.created_by,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        "progress": progress_stages,
        "agreements": [
            {
                "id": f.id,
                "template_id": f.template_id,
                "template_title": f.template.title if f.template else None,
                "template_type": f.template.agreement_type.value if f.template and f.template.agreement_type else None,
                "status": f.status,
                "generated_at": f.generated_at.isoformat() if f.generated_at else None,
                "viewed_at": f.viewed_at.isoformat() if f.viewed_at else None,
                "submitted_at": f.submitted_at.isoformat() if f.submitted_at else None,
                "signed_at": f.signed_at.isoformat() if f.signed_at else None,
                "rejected_at": f.rejected_at.isoformat() if f.rejected_at else None,
                "rejection_reason": f.rejection_reason,
                "has_pdf_preview": bool(f.pdf_preview_path),
                "signed_agreement_id": f.signed_agreement_id,
            }
            for f in flows
        ],
        "agreements_total": total,
        "agreements_signed": signed_count,
    }
