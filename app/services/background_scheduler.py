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

        # Health check de nodos Odoo — cada 5 minutos
        self._tasks.append(
            asyncio.create_task(
                self._periodic_task(
                    "node_health_check",
                    self._run_node_health_check,
                    interval_seconds=300,  # 5 minutos
                    initial_delay=120,  # 2 min después del startup
                )
            )
        )

        # Migration worker — cada 30 segundos procesa jobs pendientes
        self._tasks.append(
            asyncio.create_task(
                self._periodic_async_task(
                    "migration_worker",
                    self._run_migration_worker,
                    interval_seconds=30,
                    initial_delay=60,  # 1 min después del startup
                )
            )
        )

        # Limpieza lifecycle de API keys (GW-009) — cada 10 minutos
        self._tasks.append(
            asyncio.create_task(
                self._periodic_task(
                    "api_key_lifecycle_cleanup",
                    self._run_api_key_lifecycle_cleanup,
                    interval_seconds=600,
                    initial_delay=180,
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

    async def _periodic_async_task(
        self,
        name: str,
        func,
        interval_seconds: int,
        initial_delay: int = 60,
    ):
        """Ejecuta una función async periódicamente con manejo de errores."""
        await asyncio.sleep(initial_delay)
        logger.info(f"⏰ Async task '{name}' activated (interval: {interval_seconds}s)")

        while self._running:
            try:
                start = datetime.utcnow()
                await func()
                elapsed = (datetime.utcnow() - start).total_seconds()
                if elapsed > 1:
                    logger.info(f"✅ Task '{name}' completed in {elapsed:.1f}s")
            except Exception as e:
                logger.error(f"❌ Task '{name}' failed: {e}", exc_info=True)

            await asyncio.sleep(interval_seconds)

    def _run_reconciliation(self):
        """Ejecuta reconciliación Stripe vs DB."""
        from ..models.database import SessionLocal
        from ..services.stripe_reconciliation import StripeReconciliationService
        from ..services.stripe_billing import reconcile_billing_periods
        from ..config import get_runtime_setting

        db = SessionLocal()
        try:
            service = StripeReconciliationService(db, get_runtime_setting("STRIPE_SECRET_KEY", ""))
            result = service.run_reconciliation(scope="all", dry_run=False)
            billing_result = reconcile_billing_periods(db)
            logger.info(
                f"📊 Reconciliation complete: "
                f"checked={result['total_checked']}, "
                f"mismatches={result['mismatches_found']}, "
                f"auto_fixed={result['auto_fixed']} | "
                f"billing_checked={billing_result['checked']} "
                f"generated={billing_result['generated']} "
                f"voided_duplicates={billing_result['voided_duplicates']} "
                f"pending_stripe_sync={billing_result['pending_stripe_sync']}"
            )
            return {
                "stripe_reconciliation": result,
                "billing_periods": billing_result,
            }
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            raise
        finally:
            db.close()

    def _run_stripe_sync(self):
        """Sincroniza datos de Stripe → BD local."""
        from ..models.database import SessionLocal
        from ..config import get_runtime_setting
        from ..services.stripe_sync import full_stripe_sync
        import stripe

        stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
        db = SessionLocal()
        try:
            result = full_stripe_sync(db, months_back=6)
            logger.info(
                "🔄 Stripe sync complete: customers_linked=%s subs_created=%s subs_updated=%s invoices_imported=%s invoices_updated=%s",
                result["customers"].get("linked"),
                result["subscriptions"].get("created"),
                result["subscriptions"].get("updated"),
                result["invoices"].get("imported"),
                result["invoices"].get("updated"),
            )
            return result
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

    def _run_api_key_lifecycle_cleanup(self):
        """Ejecuta limpieza del ciclo de vida de API keys (GW-009)."""
        from ..models.database import SessionLocal
        from ..services.api_key_lifecycle import cleanup_api_keys

        db = SessionLocal()
        try:
            result = cleanup_api_keys(db)
            logger.info("🔑 API key lifecycle cleanup result: %s", result)
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _run_node_health_check(self):
        """
        Health check periódico de todos los nodos Odoo (Fase 1 multi-nodo).
        
        Estrategia híbrida:
          - Polling SSH: verifica conectividad SSH con 'echo ok'
          - HTTP check: si el nodo tiene odoo_local_api (puerto 8070), verifica /health
          - Actualiza status y last_health_check en BD
          - Si falla 3 checks consecutivos → marca offline + audit_event
        """
        import subprocess
        import os
        import httpx as _httpx

        from ..models.database import (
            SessionLocal,
            ProxmoxNode,
            TenantDeployment,
            NodeStatus,
            AuditEventRecord,
        )

        db = SessionLocal()
        try:
            nodes = db.query(ProxmoxNode).filter(
                ProxmoxNode.status.in_([NodeStatus.online, NodeStatus.maintenance])
            ).all()

            sshpass_bin = "/usr/bin/sshpass" if os.path.exists("/usr/bin/sshpass") else "/bin/sshpass"
            ssh_bin = "/usr/bin/ssh" if os.path.exists("/usr/bin/ssh") else "/bin/ssh"

            for node in nodes:
                is_healthy = False

                # 1. SSH ping
                use_password = bool(node.ssh_password)
                base_ssh = [sshpass_bin, "-p", node.ssh_password] if use_password else []
                cmd = base_ssh + [
                    ssh_bin, "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=5",
                    "-o", f"BatchMode={'no' if use_password else 'yes'}",
                    "-p", str(node.ssh_port or 22),
                    f"{node.ssh_user or 'root'}@{node.hostname}",
                    "echo ok",
                ]
                try:
                    r = subprocess.run(cmd, capture_output=True, timeout=10)
                    is_healthy = r.returncode == 0
                except Exception:
                    is_healthy = False

                # 2. HTTP health check al agente local (puerto 8070) si el SSH falló
                if not is_healthy:
                    try:
                        resp = _httpx.get(
                            f"https://{node.hostname}:8070/health",
                            timeout=5.0,
                            verify=False,
                        )
                        is_healthy = resp.status_code == 200
                    except Exception:
                        pass

                # 3. Actualizar BD
                now = datetime.utcnow()
                if is_healthy:
                    node.last_health_check = now
                    # Reset a online si estaba en maintenance check (no forzar si es maintenance manual)
                    if node.status == NodeStatus.online:
                        pass  # Mantener online

                    # Actualizar last_healthcheck_at en deployments del nodo
                    db.query(TenantDeployment).filter(
                        TenantDeployment.active_node_id == node.id
                    ).update(
                        {"last_healthcheck_at": now},
                        synchronize_session="fetch",
                    )
                else:
                    # Contar fallos consecutivos (basado en last_health_check vs ahora)
                    # Si no ha tenido health check exitoso en 15 min (3 × 5min) → offline
                    if node.last_health_check:
                        minutes_since_last = (now - node.last_health_check).total_seconds() / 60
                    else:
                        minutes_since_last = 999

                    if minutes_since_last >= 15 and node.status == NodeStatus.online:
                        node.status = NodeStatus.offline
                        logger.warning(
                            f"🔴 Nodo {node.name} ({node.hostname}) marcado OFFLINE "
                            f"— sin respuesta en {minutes_since_last:.0f} min"
                        )
                        # Registrar audit_event
                        try:
                            evt = AuditEventRecord(
                                event_type="NODE_AUTO_OFFLINE",
                                actor_username="scheduler",
                                resource=f"node:{node.name}",
                                action="health_check",
                                status="error",
                                details={
                                    "node_id": node.id,
                                    "hostname": node.hostname,
                                    "minutes_since_last_check": round(minutes_since_last),
                                },
                            )
                            db.add(evt)
                        except Exception:
                            pass

            db.commit()
            online_count = sum(1 for n in nodes if n.status == NodeStatus.online)
            logger.info(
                f"🏥 Node health check: {online_count}/{len(nodes)} online"
            )

        except Exception as e:
            logger.error(f"Node health check failed: {e}")
            db.rollback()
        finally:
            db.close()

    async def _run_migration_worker(self):
        """
        Migration Worker — procesa jobs de migración pendientes (Fase 2).
        
        Busca jobs en estados activos y avanza cada uno un paso.
        Procesa máximo 1 job por ciclo para mantener estabilidad.
        """
        from ..models.database import SessionLocal, TenantMigrationJob, MigrationState
        from ..services.migration_orchestrator import migration_orchestrator

        active_states = [
            MigrationState.queued,
            MigrationState.preflight,
            MigrationState.preparing_target,
            MigrationState.warming_target,
            MigrationState.cutover,
            MigrationState.verifying,
        ]

        db = SessionLocal()
        try:
            # Buscar el job más antiguo en estado activo
            job = db.query(TenantMigrationJob).filter(
                TenantMigrationJob.state.in_(active_states)
            ).order_by(TenantMigrationJob.created_at.asc()).first()

            if not job:
                return  # No hay jobs pendientes

            logger.info(
                f"🔄 Migration worker processing job {job.id} "
                f"({job.subdomain}, state={job.state.value})"
            )
            await migration_orchestrator.process_job(db, job.id)

        except Exception as e:
            logger.error(f"Migration worker error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()


# Singleton global
scheduler = BackgroundScheduler()
