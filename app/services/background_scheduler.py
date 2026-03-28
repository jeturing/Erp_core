"""
Background Scheduler — Tareas periódicas automatizadas
Ejecuta reconciliación Stripe, sync, y limpieza en intervalos configurables.
Usa asyncio nativo de FastAPI (sin dependencias externas).
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Scheduler liviano basado en asyncio para tareas periódicas.
    Se integra con el lifespan de FastAPI.
    """

    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self):
        """Inicia todas las tareas programadas."""
        self._running = True
        logger.info("⏰ Background Scheduler starting...")

        # Reconciliación Stripe — cada 6 horas
        self._tasks.append(
            asyncio.create_task(
                self._periodic_task(
                    "stripe_reconciliation",
                    self._run_reconciliation,
                    interval_seconds=6 * 3600,  # 6 horas
                    initial_delay=300,  # 5 min después del startup
                )
            )
        )

        # Sync Stripe → BD — cada 4 horas
        self._tasks.append(
            asyncio.create_task(
                self._periodic_task(
                    "stripe_sync",
                    self._run_stripe_sync,
                    interval_seconds=4 * 3600,  # 4 horas
                    initial_delay=600,  # 10 min después del startup
                )
            )
        )

        # Limpieza de eventos procesados (>30 días) — cada 24 horas
        self._tasks.append(
            asyncio.create_task(
                self._periodic_task(
                    "cleanup_old_events",
                    self._run_cleanup_events,
                    interval_seconds=24 * 3600,  # 24 horas
                    initial_delay=900,  # 15 min después del startup
                )
            )
        )

        logger.info(f"⏰ Background Scheduler started with {len(self._tasks)} tasks")

    async def stop(self):
        """Detiene todas las tareas."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("⏰ Background Scheduler stopped")

    async def _periodic_task(
        self,
        name: str,
        func,
        interval_seconds: int,
        initial_delay: int = 60,
    ):
        """Ejecuta una función periódicamente con manejo de errores."""
        await asyncio.sleep(initial_delay)
        logger.info(f"⏰ Task '{name}' activated (interval: {interval_seconds}s)")

        while self._running:
            try:
                start = datetime.utcnow()
                logger.info(f"⏰ Running task: {name}")
                await asyncio.to_thread(func)
                elapsed = (datetime.utcnow() - start).total_seconds()
                logger.info(f"✅ Task '{name}' completed in {elapsed:.1f}s")
            except Exception as e:
                logger.error(f"❌ Task '{name}' failed: {e}", exc_info=True)

            await asyncio.sleep(interval_seconds)

    def _run_reconciliation(self):
        """Ejecuta reconciliación Stripe vs DB."""
        from ..models.database import SessionLocal
        from ..services.stripe_reconciliation import StripeReconciliationService
        from ..config import get_runtime_setting

        db = SessionLocal()
        try:
            service = StripeReconciliationService(db, get_runtime_setting("STRIPE_SECRET_KEY", ""))
            result = service.run_reconciliation(scope="all", dry_run=False)
            logger.info(
                f"📊 Reconciliation complete: "
                f"checked={result['total_checked']}, "
                f"mismatches={result['mismatches_found']}, "
                f"auto_fixed={result['auto_fixed']}"
            )
            return result
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            raise
        finally:
            db.close()

    def _run_stripe_sync(self):
        """Sincroniza datos de Stripe → BD local."""
        from ..models.database import SessionLocal
        from ..config import get_runtime_setting
        import stripe

        stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
        db = SessionLocal()
        try:
            from ..services.stripe_sync import StripeSyncService
            service = StripeSyncService(db)
            result = service.sync_all()
            logger.info(f"🔄 Stripe sync complete: {result}")
            return result
        except ImportError:
            logger.warning("StripeSyncService not available, skipping sync")
        except Exception as e:
            logger.error(f"Stripe sync failed: {e}")
            raise
        finally:
            db.close()

    def _run_cleanup_events(self):
        """Limpia eventos de Stripe procesados con más de 30 días."""
        from ..models.database import SessionLocal, StripeEvent
        from datetime import timedelta

        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=30)
            deleted = db.query(StripeEvent).filter(
                StripeEvent.processed == True,
                StripeEvent.created_at < cutoff,
            ).delete()
            db.commit()
            logger.info(f"🗑️ Cleaned up {deleted} old Stripe events (>30 days)")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            db.rollback()
        finally:
            db.close()


# Singleton global
scheduler = BackgroundScheduler()
