"""
Quotations & Service Catalog Routes
Cotizaciones enviables + catálogo de precios oficial SAJET
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from ..models.database import (
    Quotation, ServiceCatalogItem, Partner, Customer, SessionLocal,
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
    sort_order: int = 0


def _quotation_to_dict(q: Quotation) -> dict:
    return {
        "id": q.id,
        "quote_number": q.quote_number,
        "created_by_partner_id": q.created_by_partner_id,
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
        "is_active": c.is_active,
        "sort_order": c.sort_order,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _generate_quote_number(db) -> str:
    """Genera QT-YYYY-NNNN secuencial."""
    year = datetime.utcnow().year
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
):
    """Catálogo de servicios/productos con precios."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.is_active == True)
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
            by_category[cat].append(_catalog_to_dict(item))

        return {
            "items": [_catalog_to_dict(i) for i in items],
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


# ═══════════════════════════════════════════
# QUOTATION ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/api/quotations")
async def list_quotations(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    partner_id: Optional[int] = None,
    status_filter: Optional[str] = None,
):
    """Lista cotizaciones con filtros."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Quotation)
        if partner_id:
            q = q.filter(Quotation.created_by_partner_id == partner_id)
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
            else:
                d["partner_name"] = None
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
        if payload.partner_id:
            partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
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
            created_by_partner_id=payload.partner_id,
            created_by_admin=payload.partner_id is None,
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
            valid_until=datetime.utcnow() + timedelta(days=payload.valid_days),
            notes=payload.notes,
            terms=payload.terms,
        )
        db.add(qt)
        db.commit()
        db.refresh(qt)

        return {"message": f"Cotización {quote_number} creada", "quotation": _quotation_to_dict(qt)}
    finally:
        db.close()


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
                    qt.sent_at = datetime.utcnow()
                elif new_status == QuotationStatus.accepted:
                    qt.accepted_at = datetime.utcnow()
                elif new_status == QuotationStatus.rejected:
                    qt.rejected_at = datetime.utcnow()
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
        qt.sent_at = datetime.utcnow()
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
