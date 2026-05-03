"""
Stripe Reconciliation Service — Épica 7
Compara registros de Stripe vs DB local y detecta discrepancias.
Legacy mode = solo lectura, sin acciones correctivas.
"""
import stripe
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from ..models.database import (
    ReconciliationRun, Subscription, Invoice, InvoiceStatus,
    BillingMode, SeatHighWater, SubscriptionStatus,
)

logger = logging.getLogger(__name__)


class StripeReconciliationService:
    """
    Ejecuta un run de reconciliación:
    1. Fetch suscripciones activas de Stripe
    2. Compara con DB local
    3. Detecta discrepancias (cantidad, precio, estado, cancelaciones)
    4. Para Legacy: solo log, sin acciones
    """

    def __init__(self, db: Session, stripe_api_key: str):
        self.db = db
        stripe.api_key = stripe_api_key

    def run_reconciliation(self, scope: str = "all", dry_run: bool = False) -> dict:
        """
        scope: 'all' | 'direct' | 'partner' | 'legacy'
        dry_run: True = solo reportar, no tocar nada
        """
        run = ReconciliationRun(
            run_date=datetime.now(timezone.utc).replace(tzinfo=None),
            scope=scope,
            status="running",
            total_checked=0,
            mismatches_found=0,
            auto_fixed=0,
            details_json={},
        )
        self.db.add(run)
        self.db.flush()

        mismatches = []
        auto_fixes = 0
        total_checked = 0

        try:
            # Obtener suscripciones activas de Stripe
            stripe_subs = self._fetch_stripe_subscriptions()

            # Obtener suscripciones locales
            local_subs = self._fetch_local_subscriptions(scope)

            # Indexar Stripe subs por ID
            stripe_index = {s["id"]: s for s in stripe_subs}
            local_index = {s.stripe_subscription_id: s for s in local_subs if s.stripe_subscription_id}

            # 1. Check: local subs que existen en Stripe
            for stripe_id, local_sub in local_index.items():
                total_checked += 1
                stripe_sub = stripe_index.get(stripe_id)

                if not stripe_sub:
                    mismatches.append({
                        "type": "missing_in_stripe",
                        "subscription_id": local_sub.id,
                        "stripe_id": stripe_id,
                        "detail": "Suscripción local existe pero no en Stripe",
                    })
                    continue

                # Comparar estado
                local_status = local_sub.status.value if local_sub.status else "unknown"
                stripe_status = stripe_sub.get("status", "unknown")
                if not self._status_compatible(local_status, stripe_status):
                    mismatches.append({
                        "type": "status_mismatch",
                        "subscription_id": local_sub.id,
                        "stripe_id": stripe_id,
                        "local_status": local_status,
                        "stripe_status": stripe_status,
                    })

                # Comparar cantidad (seats)
                stripe_qty = self._get_stripe_quantity(stripe_sub)
                local_hwm = self._get_local_hwm(local_sub.id)
                if stripe_qty is not None and local_hwm is not None:
                    if stripe_qty != local_hwm:
                        mismatch = {
                            "type": "quantity_mismatch",
                            "subscription_id": local_sub.id,
                            "stripe_id": stripe_id,
                            "stripe_qty": stripe_qty,
                            "local_hwm": local_hwm,
                        }
                        mismatches.append(mismatch)

                        # Auto-fix si NO es legacy y NO es dry_run
                        is_legacy = (local_sub.billing_mode == BillingMode.LEGACY_IMPORTED)
                        if not is_legacy and not dry_run:
                            try:
                                item_id = stripe_sub["items"]["data"][0]["id"]
                                stripe.SubscriptionItem.modify(item_id, quantity=local_hwm)
                                auto_fixes += 1
                                mismatch["auto_fixed"] = True
                                logger.info(
                                    f"Auto-fixed qty for sub {local_sub.id}: "
                                    f"Stripe {stripe_qty} → {local_hwm}"
                                )
                            except Exception as e:
                                mismatch["fix_error"] = str(e)

            # 2. Check: Stripe subs que no están en local
            for stripe_id, stripe_sub in stripe_index.items():
                if stripe_id not in local_index:
                    mismatches.append({
                        "type": "missing_in_local",
                        "stripe_id": stripe_id,
                        "stripe_status": stripe_sub.get("status"),
                        "detail": "Suscripción en Stripe no existe en DB local",
                    })
                    total_checked += 1

            # Guardar resultado
            run.total_checked = total_checked
            run.mismatches_found = len(mismatches)
            run.auto_fixed = auto_fixes
            run.details_json = {
                "mismatches": mismatches,
                "scope": scope,
                "dry_run": dry_run,
            }
            run.status = "completed"
            self.db.commit()

        except Exception as e:
            run.status = "error"
            run.details_json = {"error": str(e)}
            self.db.commit()
            logger.error(f"Reconciliation run {run.id} failed: {e}")
            raise

        return {
            "run_id": run.id,
            "total_checked": total_checked,
            "mismatches_found": len(mismatches),
            "auto_fixed": auto_fixes,
            "mismatches": mismatches,
        }

    def _fetch_stripe_subscriptions(self) -> list:
        """Fetch all active/past_due subscriptions from Stripe."""
        subs = []
        has_more = True
        starting_after = None

        while has_more:
            params = {"limit": 100, "status": "all"}
            if starting_after:
                params["starting_after"] = starting_after
            result = stripe.Subscription.list(**params)
            subs.extend(result["data"])
            has_more = result.get("has_more", False)
            if subs:
                starting_after = subs[-1]["id"]

        return subs

    def _fetch_local_subscriptions(self, scope: str) -> list:
        q = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id.isnot(None)
        )
        if scope == "direct":
            q = q.filter(Subscription.billing_mode.in_([
                BillingMode.JETURING_DIRECT_SUBSCRIPTION,
                BillingMode.PARTNER_DIRECT,
            ]))
        elif scope == "partner":
            q = q.filter(Subscription.billing_mode == BillingMode.PARTNER_PAYS_FOR_CLIENT)
        elif scope == "legacy":
            q = q.filter(Subscription.billing_mode == BillingMode.LEGACY_IMPORTED)
        return q.all()

    def _status_compatible(self, local: str, stripe_status: str) -> bool:
        """Check if local and Stripe statuses are compatible."""
        compat = {
            "active": ["active", "trialing"],
            "trialing": ["trialing", "active"],
            "past_due": ["past_due"],
            "canceled": ["canceled", "incomplete_expired"],
            "suspended": ["past_due", "unpaid"],
        }
        expected = compat.get(local, [local])
        return stripe_status in expected

    def _get_stripe_quantity(self, stripe_sub: dict) -> int | None:
        items = stripe_sub.get("items", {}).get("data", [])
        if items:
            return items[0].get("quantity")
        return None

    def _get_local_hwm(self, subscription_id: int) -> int | None:
        today = datetime.now(timezone.utc).replace(tzinfo=None).date()
        hwm = self.db.query(SeatHighWater).filter(
            SeatHighWater.subscription_id == subscription_id,
            SeatHighWater.period_date == today,
        ).first()
        return hwm.high_water_mark if hwm else None
