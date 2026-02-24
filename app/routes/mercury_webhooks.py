"""
Mercury Webhooks — Recepción y conciliación de pagos directos
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import get_db
from ..services.mercury_client import get_mercury_client
from ..services.payment_processor import PaymentProcessor

router = APIRouter(prefix="/api/mercury", tags=["Mercury"])
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def mercury_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook Mercury para conciliar depósitos entrantes.
    """
    try:
        raw_body = await request.body()
        signature = request.headers.get("X-Mercury-Signature", "")

        mercury_client = get_mercury_client()
        if not mercury_client.verify_webhook_signature(raw_body.decode(), signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = await request.json()
        processor = PaymentProcessor(db)
        result = processor.reconcile_direct_payment_webhook(payload)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mercury webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
