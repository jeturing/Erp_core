"""
Quotations & Service Catalog Routes
Cotizaciones enviables + catálogo de precios oficial SAJET
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from ..models.database import (
    Quotation, ServiceCatalogItem, Partner, Customer, Plan,
    PlanCatalogLink, SessionLocal,
    QuotationStatus, ServiceCategory,
)
from .roles import _require_admin

router = APIRouter(tags=["Quotations & Catalog"])


# ── DTOs ──

class QuotationLineItem(BaseModel):
    service_id: Optional[int] = None
    name: str
    unit: str
    quantity: int = 1
    unit_price: float
    subtotal: Optional[float] = None


class QuotationCreate(BaseModel):
    partner_id: Optional[int] = None
    provider_id: Optional[int] = None
    customer_id: Optional[int] = None
    prospect_name: Optional[str] = None
    prospect_email: Optional[str] = None
    prospect_company: Optional[str] = None
    prospect_phone: Optional[str] = None
    lines: List[QuotationLineItem]
    partner_margin: float = 0
    notes: Optional[str] = None
    terms: Optional[str] = None
    valid_days: int = 30
    currency: str = "USD"


class QuotationUpdate(BaseModel):
    status: Optional[str] = None
    lines: Optional[List[QuotationLineItem]] = None
    partner_margin: Optional[float] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    valid_until: Optional[str] = None


class QuotationInvoicePreviewRequest(BaseModel):
    lines: List[QuotationLineItem]
    partner_margin: float = 0
    currency: str = "USD"
    tax_percent: float = 0
    due_days: int = 30


class CatalogItemCreate(BaseModel):
    category: str
    name: str
    description: Optional[str] = None
    unit: str
    price_monthly: float
    price_max: Optional[float] = None
    is_addon: bool = False
    requires_service_id: Optional[int] = None
    min_quantity: int = 1
    service_code: Optional[str] = None
    metadata_json: Optional[dict] = None
    sort_order: int = 0


class PlanCatalogLinkCreate(BaseModel):
    plan_id: int
    catalog_item_id: int
    included_quantity: int = 1
    is_included: bool = True
    discount_percent: float = 0
    notes: Optional[str] = None


def _quotation_to_dict(q: Quotation) -> dict:
    return {
        "id": q.id,
        "quote_number": q.quote_number,
        "created_by_partner_id": q.created_by_partner_id,
        "provider_id": q.created_by_partner_id,
        "created_by_admin": q.created_by_admin,
        "customer_id": q.customer_id,
        "prospect_name": q.prospect_name,
        "prospect_email": q.prospect_email,
        "prospect_company": q.prospect_company,
        "prospect_phone": q.prospect_phone,
        "lines": json.loads(q.lines_json) if q.lines_json else [],
        "subtotal": q.subtotal,
        "partner_margin": q.partner_margin,
        "total_monthly": q.total_monthly,
        "currency": q.currency,
        "status": q.status.value if q.status else None,
        "valid_until": q.valid_until.isoformat() if q.valid_until else None,
        "notes": q.notes,
        "terms": q.terms,
        "sent_at": q.sent_at.isoformat() if q.sent_at else None,
        "accepted_at": q.accepted_at.isoformat() if q.accepted_at else None,
        "rejected_at": q.rejected_at.isoformat() if q.rejected_at else None,
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "updated_at": q.updated_at.isoformat() if q.updated_at else None,
    }


def _catalog_to_dict(c: ServiceCatalogItem) -> dict:
    return {
        "id": c.id,
        "category": c.category.value if c.category else None,
        "name": c.name,
        "description": c.description,
        "unit": c.unit,
        "price_monthly": c.price_monthly,
        "price_max": c.price_max,
        "is_addon": c.is_addon,
        "requires_service_id": c.requires_service_id,
        "min_quantity": c.min_quantity,
        "service_code": c.service_code,
        "metadata_json": c.metadata_json or {},
        "is_active": c.is_active,
        "sort_order": c.sort_order,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _generate_quote_number(db) -> str:
    """Genera QT-YYYY-NNNN secuencial."""
    year = datetime.now(timezone.utc).replace(tzinfo=None).year
    last = (
        db.query(Quotation)
        .filter(Quotation.quote_number.like(f"QT-{year}-%"))
        .order_by(Quotation.id.desc())
        .first()
    )
    if last and last.quote_number:
        try:
            seq = int(last.quote_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"QT-{year}-{seq:04d}"


# ═══════════════════════════════════════════
# SERVICE CATALOG ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/api/catalog")
async def list_catalog(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    category: Optional[str] = None,
    include_inactive: bool = False,
):
    """Catálogo de servicios/productos con precios."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(ServiceCatalogItem)
        if not include_inactive:
            q = q.filter(ServiceCatalogItem.is_active == True)
        if category:
            try:
                q = q.filter(ServiceCatalogItem.category == ServiceCategory(category))
            except ValueError:
                pass
        items = q.order_by(ServiceCatalogItem.sort_order, ServiceCatalogItem.id).all()

        # Agrupar por categoría
        by_category = {}
        for item in items:
            cat = item.category.value if item.category else "other"
            if cat not in by_category:
                by_category[cat] = []
            d = _catalog_to_dict(item)
            # Incluir planes vinculados
            d["linked_plans"] = [
                {
                    "link_id": lnk.id,
                    "plan_id": lnk.plan_id,
                    "plan_name": lnk.plan.display_name if lnk.plan else None,
                    "included_quantity": lnk.included_quantity,
                    "is_included": lnk.is_included,
                    "discount_percent": lnk.discount_percent,
                }
                for lnk in (item.plan_links or [])
            ]
            by_category[cat].append(d)

        all_items = []
        for item in items:
            d = _catalog_to_dict(item)
            d["linked_plans"] = [
                {
                    "link_id": lnk.id,
                    "plan_id": lnk.plan_id,
                    "plan_name": lnk.plan.display_name if lnk.plan else None,
                    "included_quantity": lnk.included_quantity,
                    "is_included": lnk.is_included,
                    "discount_percent": lnk.discount_percent,
                }
                for lnk in (item.plan_links or [])
            ]
            all_items.append(d)

        return {
            "items": all_items,
            "total": len(items),
            "by_category": by_category,
            "categories": [{"value": c.value, "label": c.value.replace("_", " ").title()} for c in ServiceCategory],
        }
    finally:
        db.close()


@router.post("/api/catalog")
async def create_catalog_item(
    payload: CatalogItemCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Crea un item en el catálogo de servicios."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        try:
            cat = ServiceCategory(payload.category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Categoría inválida: {payload.category}")

        item = ServiceCatalogItem(
            category=cat,
            name=payload.name,
            description=payload.description,
            unit=payload.unit,
            price_monthly=payload.price_monthly,
            price_max=payload.price_max,
            is_addon=payload.is_addon,
            requires_service_id=payload.requires_service_id,
            min_quantity=payload.min_quantity,
            service_code=payload.service_code,
            metadata_json=payload.metadata_json,
            sort_order=payload.sort_order,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        return {"message": "Servicio añadido al catálogo", "item": _catalog_to_dict(item)}
    finally:
        db.close()


@router.put("/api/catalog/{item_id}")
async def update_catalog_item(
    item_id: int,
    payload: CatalogItemCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")

        for field, value in payload.dict().items():
            if field == "category":
                value = ServiceCategory(value)
            setattr(item, field, value)

        db.commit()
        db.refresh(item)
        return {"message": "Servicio actualizado", "item": _catalog_to_dict(item)}
    finally:
        db.close()


@router.delete("/api/catalog/{item_id}")
async def delete_catalog_item(
    item_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        item.is_active = False
        db.commit()
        return {"message": "Servicio desactivado"}
    finally:
        db.close()


@router.put("/api/catalog/{item_id}/reactivate")
async def reactivate_catalog_item(
    item_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Reactiva un item del catálogo previamente desactivado."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        item.is_active = True
        db.commit()
        return {"message": "Servicio reactivado", "item": _catalog_to_dict(item)}
    finally:
        db.close()


# ═══════════════════════════════════════════
# PLAN ↔ CATALOG LINK ENDPOINTS
# ═══════════════════════════════════════════

def _link_to_dict(link: PlanCatalogLink) -> dict:
    return {
        "id": link.id,
        "plan_id": link.plan_id,
        "catalog_item_id": link.catalog_item_id,
        "included_quantity": link.included_quantity,
        "is_included": link.is_included,
        "discount_percent": link.discount_percent,
        "notes": link.notes,
        "catalog_item": _catalog_to_dict(link.catalog_item) if link.catalog_item else None,
        "plan_name": link.plan.display_name if link.plan else None,
        "created_at": link.created_at.isoformat() if link.created_at else None,
    }


@router.get("/api/catalog/plan-links")
async def list_plan_catalog_links(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    plan_id: Optional[int] = None,
):
    """Lista vínculos plan↔catálogo. Filtra por plan_id si se pasa."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(PlanCatalogLink)
        if plan_id:
            q = q.filter(PlanCatalogLink.plan_id == plan_id)
        links = q.all()

        # Agrupar por plan
        by_plan = {}
        for lnk in links:
            pname = lnk.plan.display_name if lnk.plan else f"Plan #{lnk.plan_id}"
            if lnk.plan_id not in by_plan:
                by_plan[lnk.plan_id] = {"plan_name": pname, "items": []}
            by_plan[lnk.plan_id]["items"].append(_link_to_dict(lnk))

        return {
            "links": [_link_to_dict(l) for l in links],
            "total": len(links),
            "by_plan": by_plan,
        }
    finally:
        db.close()


@router.post("/api/catalog/plan-links")
async def create_plan_catalog_link(
    payload: PlanCatalogLinkCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Vincula un item del catálogo a un plan."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        # Validar plan
        plan = db.query(Plan).filter(Plan.id == payload.plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan no encontrado")

        # Validar catalog item
        item = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == payload.catalog_item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Servicio del catálogo no encontrado")

        # Check duplicado
        existing = db.query(PlanCatalogLink).filter(
            PlanCatalogLink.plan_id == payload.plan_id,
            PlanCatalogLink.catalog_item_id == payload.catalog_item_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Este servicio ya está vinculado a este plan")

        link = PlanCatalogLink(
            plan_id=payload.plan_id,
            catalog_item_id=payload.catalog_item_id,
            included_quantity=payload.included_quantity,
            is_included=payload.is_included,
            discount_percent=payload.discount_percent,
            notes=payload.notes,
        )
        db.add(link)
        db.commit()
        db.refresh(link)

        return {
            "message": f"Servicio '{item.name}' vinculado al plan '{plan.display_name}'",
            "link": _link_to_dict(link),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/api/catalog/plan-links/{link_id}")
async def update_plan_catalog_link(
    link_id: int,
    payload: PlanCatalogLinkCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza un vínculo plan↔catálogo."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        link = db.query(PlanCatalogLink).filter(PlanCatalogLink.id == link_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Vínculo no encontrado")

        link.included_quantity = payload.included_quantity
        link.is_included = payload.is_included
        link.discount_percent = payload.discount_percent
        link.notes = payload.notes
        db.commit()
        db.refresh(link)

        return {"message": "Vínculo actualizado", "link": _link_to_dict(link)}
    finally:
        db.close()


@router.delete("/api/catalog/plan-links/{link_id}")
async def delete_plan_catalog_link(
    link_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Elimina un vínculo plan↔catálogo."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        link = db.query(PlanCatalogLink).filter(PlanCatalogLink.id == link_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Vínculo no encontrado")
        db.delete(link)
        db.commit()
        return {"message": "Vínculo eliminado"}
    finally:
        db.close()


# ═══════════════════════════════════════════
# QUOTATION ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/api/quotations")
async def list_quotations(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    partner_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    status_filter: Optional[str] = None,
):
    """Lista cotizaciones con filtros."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Quotation)
        effective_partner_id = partner_id or provider_id
        if effective_partner_id:
            q = q.filter(Quotation.created_by_partner_id == effective_partner_id)
        if status_filter:
            try:
                q = q.filter(Quotation.status == QuotationStatus(status_filter))
            except ValueError:
                pass

        quotes = q.order_by(Quotation.created_at.desc()).all()
        items = []
        for qt in quotes:
            d = _quotation_to_dict(qt)
            if qt.created_by_partner_id:
                p = db.query(Partner).filter(Partner.id == qt.created_by_partner_id).first()
                d["partner_name"] = p.company_name if p else "—"
                d["provider_name"] = d["partner_name"]
            else:
                d["partner_name"] = None
                d["provider_name"] = None
            items.append(d)

        total_value = sum(i["total_monthly"] or 0 for i in items)

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "total_value": round(total_value, 2),
                "draft": sum(1 for i in items if i["status"] == "draft"),
                "sent": sum(1 for i in items if i["status"] == "sent"),
                "accepted": sum(1 for i in items if i["status"] == "accepted"),
            },
        }
    finally:
        db.close()


@router.get("/api/quotations/{quote_id}")
async def get_quotation(
    quote_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        qt = db.query(Quotation).filter(Quotation.id == quote_id).first()
        if not qt:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        data = _quotation_to_dict(qt)
        if qt.created_by_partner_id:
            p = db.query(Partner).filter(Partner.id == qt.created_by_partner_id).first()
            data["partner_name"] = p.company_name if p else "—"
            data["provider_name"] = data["partner_name"]
        else:
            data["provider_name"] = None
        return data
    finally:
        db.close()


@router.post("/api/quotations")
async def create_quotation(
    payload: QuotationCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Crea una cotización nueva."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        effective_partner_id = payload.partner_id or payload.provider_id

        # Calcular líneas
        lines = []
        subtotal = 0
        for line in payload.lines:
            sub = round(line.quantity * line.unit_price, 2)
            lines.append({
                "service_id": line.service_id,
                "name": line.name,
                "unit": line.unit,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "subtotal": sub,
            })
            subtotal += sub

        # Validar margen del partner (≤30% del subtotal según cláusula 8.7)
        if effective_partner_id:
            partner = db.query(Partner).filter(Partner.id == effective_partner_id).first()
            if partner:
                max_margin = subtotal * (partner.margin_cap / 100)
                if payload.partner_margin > max_margin:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Margen del partner excede el cap ({partner.margin_cap}%). Máximo: ${max_margin:.2f}"
                    )

        total_monthly = round(subtotal + payload.partner_margin, 2)
        quote_number = _generate_quote_number(db)

        qt = Quotation(
            quote_number=quote_number,
            created_by_partner_id=effective_partner_id,
            created_by_admin=effective_partner_id is None,
            customer_id=payload.customer_id,
            prospect_name=payload.prospect_name,
            prospect_email=payload.prospect_email,
            prospect_company=payload.prospect_company,
            prospect_phone=payload.prospect_phone,
            lines_json=json.dumps(lines),
            subtotal=round(subtotal, 2),
            partner_margin=payload.partner_margin,
            total_monthly=total_monthly,
            currency=payload.currency,
            status=QuotationStatus.draft,
            valid_until=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=payload.valid_days),
            notes=payload.notes,
            terms=payload.terms,
        )
        db.add(qt)
        db.commit()
        db.refresh(qt)

        return {"message": f"Cotización {quote_number} creada", "quotation": _quotation_to_dict(qt)}
    finally:
        db.close()


@router.post("/api/quotations/preview/invoice")
async def preview_quotation_invoice(
    payload: QuotationInvoicePreviewRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Genera preview de factura mensual a partir de líneas de cotización."""
    _require_admin(request, access_token)

    normalized_lines = []
    subtotal = 0.0
    for line in payload.lines:
        qty = max(1, int(line.quantity or 1))
        unit_price = float(line.unit_price or 0)
        line_subtotal = round(qty * unit_price, 2)
        normalized_lines.append({
            "service_id": line.service_id,
            "name": line.name,
            "unit": line.unit,
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": line_subtotal,
        })
        subtotal += line_subtotal

    subtotal = round(subtotal, 2)
    margin = round(float(payload.partner_margin or 0), 2)
    taxable_base = round(subtotal + margin, 2)
    tax_amount = round(max(0.0, float(payload.tax_percent or 0)) * taxable_base / 100.0, 2)
    total = round(taxable_base + tax_amount, 2)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    return {
        "success": True,
        "data": {
            "invoice_preview": {
                "issued_at": now.isoformat(),
                "due_at": (now + timedelta(days=max(1, int(payload.due_days or 30)))).isoformat(),
                "currency": payload.currency,
                "lines": normalized_lines,
                "subtotal": subtotal,
                "partner_margin": margin,
                "tax_percent": float(payload.tax_percent or 0),
                "tax_amount": tax_amount,
                "total": total,
            }
        },
        "meta": {
            "lines": len(normalized_lines),
        },
    }


@router.put("/api/quotations/{quote_id}")
async def update_quotation(
    quote_id: int,
    payload: QuotationUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        qt = db.query(Quotation).filter(Quotation.id == quote_id).first()
        if not qt:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        changes = []
        data = payload.dict(exclude_unset=True)

        if "status" in data:
            try:
                new_status = QuotationStatus(data["status"])
                qt.status = new_status
                if new_status == QuotationStatus.sent:
                    qt.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
                elif new_status == QuotationStatus.accepted:
                    qt.accepted_at = datetime.now(timezone.utc).replace(tzinfo=None)
                elif new_status == QuotationStatus.rejected:
                    qt.rejected_at = datetime.now(timezone.utc).replace(tzinfo=None)
                changes.append("status")
            except ValueError:
                pass

        if "lines" in data and data["lines"] is not None:
            lines = []
            subtotal = 0
            for line in data["lines"]:
                sub = round(line["quantity"] * line["unit_price"], 2)
                lines.append({**line, "subtotal": sub})
                subtotal += sub
            qt.lines_json = json.dumps(lines)
            qt.subtotal = round(subtotal, 2)
            margin = data.get("partner_margin", qt.partner_margin or 0)
            qt.total_monthly = round(subtotal + margin, 2)
            changes.extend(["lines", "subtotal", "total_monthly"])

        for field in ("partner_margin", "notes", "terms", "valid_until"):
            if field in data:
                val = data[field]
                if field == "valid_until" and isinstance(val, str):
                    val = datetime.fromisoformat(val)
                setattr(qt, field, val)
                changes.append(field)

        db.commit()
        db.refresh(qt)

        return {"message": "Cotización actualizada", "changes": changes, "quotation": _quotation_to_dict(qt)}
    finally:
        db.close()


@router.post("/api/quotations/{quote_id}/send")
async def send_quotation(
    quote_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Marca cotización como enviada."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        qt = db.query(Quotation).filter(Quotation.id == quote_id).first()
        if not qt:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        qt.status = QuotationStatus.sent
        qt.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        return {"message": f"Cotización {qt.quote_number} marcada como enviada"}
    finally:
        db.close()


@router.delete("/api/quotations/{quote_id}")
async def delete_quotation(
    quote_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        qt = db.query(Quotation).filter(Quotation.id == quote_id).first()
        if not qt:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        if qt.status not in (QuotationStatus.draft,):
            raise HTTPException(status_code=400, detail="Solo se pueden eliminar cotizaciones en borrador")

        db.delete(qt)
        db.commit()
        return {"message": "Cotización eliminada"}
    finally:
        db.close()
