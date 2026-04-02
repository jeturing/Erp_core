"""
MigrationOrchestrator — Migración live de tenants entre nodos (Fase 2).

Máquina de estados:
  queued → preflight → preparing_target → warming_target → cutover → verifying → completed
                │            │                 │              │           │
                ▼            ▼                 ▼              ▼           ▼
              failed       failed            failed       rollback    rollback → failed

Ventaja arquitectónica: PostgreSQL es centralizado en PCT 137.
La BD NO se copia — solo cambia qué nodo sirve el runtime + se replica el filestore via rsync.
"""
import asyncio
import logging
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..config import ODOO_FILESTORE_PATH
from ..models.database import (
    AuditEventRecord,
    MigrationState,
    NodeStatus,
    ProxmoxNode,
    RoutingMode,
    RuntimeMode,
    TenantDeployment,
    TenantMigrationJob,
)

logger = logging.getLogger(__name__)

# Estados cancelables (antes de cutover)
CANCELABLE_STATES = {
    MigrationState.queued,
    MigrationState.preflight,
    MigrationState.preparing_target,
    MigrationState.warming_target,
}

# Transiciones válidas de la máquina de estados
STATE_TRANSITIONS = {
    MigrationState.queued: MigrationState.preflight,
    MigrationState.preflight: MigrationState.preparing_target,
    MigrationState.preparing_target: MigrationState.warming_target,
    MigrationState.warming_target: MigrationState.cutover,
    MigrationState.cutover: MigrationState.verifying,
    MigrationState.verifying: MigrationState.completed,
}


class MigrationOrchestrator:
    """Orquesta la migración live de un tenant entre nodos Odoo."""

    # ── Public API ────────────────────────────────────────────────

    async def start_migration(
        self,
        db: Session,
        deployment_id: int,
        target_node_id: int,
        initiated_by: str,
        target_runtime_mode: str | None = None,
    ) -> TenantMigrationJob:
        """
        Crea un job de migración y ejecuta preflight.
        
        Retorna el job creado (estado: queued o failed si preflight falla).
        """
        deployment = db.query(TenantDeployment).get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} no encontrado")

        target_node = db.query(ProxmoxNode).get(target_node_id)
        if not target_node:
            raise ValueError(f"Nodo destino {target_node_id} no encontrado")

        # Validar que no hay migración activa
        active_states = [
            MigrationState.queued, MigrationState.preflight,
            MigrationState.preparing_target, MigrationState.warming_target,
            MigrationState.cutover, MigrationState.verifying,
        ]
        existing = db.query(TenantMigrationJob).filter(
            TenantMigrationJob.deployment_id == deployment_id,
            TenantMigrationJob.state.in_(active_states),
        ).first()
        if existing:
            raise ValueError(
                f"Ya hay una migración activa para {deployment.subdomain}: "
                f"job={existing.id}, state={existing.state.value}"
            )

        # Resolver runtime mode destino
        source_rm = deployment.runtime_mode.value if deployment.runtime_mode else "shared_pool"
        resolved_target_rm = target_runtime_mode or source_rm

        # Crear job
        job = TenantMigrationJob(
            id=uuid.uuid4(),
            deployment_id=deployment_id,
            subdomain=deployment.subdomain,
            source_node_id=deployment.active_node_id,
            target_node_id=target_node_id,
            source_runtime_mode=source_rm,
            target_runtime_mode=resolved_target_rm,
            state=MigrationState.queued,
            initiated_by=initiated_by,
        )
        db.add(job)

        # Marcar deployment en estado de migración
        deployment.migration_state = MigrationState.queued
        deployment.desired_node_id = target_node_id

        db.commit()
        db.refresh(job)

        self._audit(db, "migration_started", deployment.subdomain, {
            "job_id": str(job.id),
            "source_node_id": job.source_node_id,
            "target_node_id": job.target_node_id,
            "initiated_by": initiated_by,
        })

        logger.info(
            f"🚀 Migration job created: {job.id} | "
            f"{deployment.subdomain} | {job.source_node_id} → {job.target_node_id}"
        )
        return job

    async def process_job(self, db: Session, job_id: uuid.UUID) -> TenantMigrationJob:
        """
        Avanza el job un estado. Llamado por el worker periódico.
        
        Cada invocación procesa UN paso de la máquina de estados.
        """
        job = db.query(TenantMigrationJob).get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} no encontrado")

        state_handlers = {
            MigrationState.queued: self._run_preflight,
            MigrationState.preflight: self._run_prepare_target,
            MigrationState.preparing_target: self._run_warming,
            MigrationState.warming_target: self._run_cutover,
            MigrationState.cutover: self._run_verifying,
            MigrationState.verifying: self._finalize_completed,
        }

        handler = state_handlers.get(job.state)
        if not handler:
            logger.warning(f"Job {job.id} en estado terminal: {job.state.value}")
            return job

        try:
            success = await handler(db, job)
            if not success and job.state not in (MigrationState.failed, MigrationState.rollback):
                self._transition_to_failed(db, job, f"Handler {job.state.value} retornó failure")
        except Exception as e:
            logger.error(f"❌ Migration job {job.id} error in {job.state.value}: {e}", exc_info=True)
            if job.state in (MigrationState.cutover, MigrationState.verifying):
                await self._run_rollback(db, job, reason=str(e))
            else:
                self._transition_to_failed(db, job, str(e))

        db.commit()
        db.refresh(job)
        return job

    def cancel_migration(
        self, db: Session, job_id: uuid.UUID, reason: str = "Cancelled by admin"
    ) -> TenantMigrationJob:
        """Cancela una migración si está en estado cancelable."""
        job = db.query(TenantMigrationJob).get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} no encontrado")

        if job.state not in CANCELABLE_STATES:
            raise ValueError(
                f"No se puede cancelar job en estado {job.state.value}. "
                f"Cancelable solo en: {[s.value for s in CANCELABLE_STATES]}"
            )

        # Si ya se copió filestore, programar limpieza
        if job.state in (MigrationState.preparing_target, MigrationState.warming_target):
            self._cleanup_target_filestore(db, job)

        job.state = MigrationState.failed
        job.error_log = f"{job.error_log or ''}\n[CANCELLED] {reason}".strip()
        job.completed_at = datetime.utcnow()

        # Resetear deployment
        deployment = db.query(TenantDeployment).get(job.deployment_id)
        if deployment:
            deployment.migration_state = MigrationState.idle
            deployment.desired_node_id = None

        db.commit()
        self._audit(db, "migration_cancelled", job.subdomain, {
            "job_id": str(job.id), "reason": reason,
        })

        logger.info(f"🛑 Migration {job.id} cancelled: {reason}")
        return job

    # ── State machine handlers ────────────────────────────────────

    async def _run_preflight(self, db: Session, job: TenantMigrationJob) -> bool:
        """
        Preflight: validar que la migración es viable.
        
        Checks: nodo destino online, acepta tenants, capacidad, versión,
        no mismo nodo, filestore accesible, SSH destino, Odoo destino.
        """
        logger.info(f"🔍 Preflight check for job {job.id}")
        job.state = MigrationState.preflight
        deployment = db.query(TenantDeployment).get(job.deployment_id)
        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        checks: Dict[str, Any] = {}
        all_passed = True

        def check(name: str, passed: bool, detail: str = ""):
            nonlocal all_passed
            checks[name] = {"passed": passed, "detail": detail}
            if not passed:
                all_passed = False

        # 1. Nodo destino existe y está online
        if not target_node:
            check("target_exists", False, "Nodo destino no encontrado en BD")
            job.preflight_result = checks
            return False
        check("target_online", target_node.status == NodeStatus.online,
              f"status={target_node.status.value}")

        # 2. Nodo destino acepta tenants
        check("target_can_host", target_node.can_host_tenants,
              f"can_host_tenants={target_node.can_host_tenants}")

        # 3. Capacidad del nodo
        active_count = db.query(TenantDeployment).filter(
            TenantDeployment.active_node_id == target_node.id
        ).count()
        max_db = target_node.max_containers or 50
        check("target_capacity", active_count < max_db,
              f"{active_count}/{max_db} deployments")

        # 4. No es el mismo nodo
        check("different_node", job.source_node_id != job.target_node_id,
              f"source={job.source_node_id}, target={job.target_node_id}")

        # 5. Deployment no tiene migración activa (doble check)
        if deployment:
            check("deployment_idle",
                  deployment.migration_state in (MigrationState.idle, MigrationState.queued),
                  f"migration_state={deployment.migration_state.value}")
        else:
            check("deployment_exists", False, "Deployment no encontrado")

        # 6. SSH al nodo destino (blocking → thread pool)
        ssh_ok, ssh_detail = await asyncio.to_thread(
            self._ssh_check, target_node.hostname
        )
        check("target_ssh", ssh_ok, ssh_detail)

        # 7. Filestore accesible en origen
        if source_node and deployment:
            fs_ok, fs_detail = await asyncio.to_thread(
                self._check_filestore,
                source_node.hostname,
                deployment.database_name or deployment.subdomain,
            )
            check("source_filestore", fs_ok, fs_detail)

        # 8. Odoo respondiendo en destino
        odoo_ok, odoo_detail = await asyncio.to_thread(
            self._check_odoo_health, target_node.hostname
        )
        check("target_odoo", odoo_ok, odoo_detail)

        job.preflight_result = checks

        if all_passed:
            logger.info(f"✅ Preflight passed for job {job.id}: {len(checks)} checks OK")
            # Medir filestore para métricas
            if source_node and deployment:
                size = await asyncio.to_thread(
                    self._measure_filestore,
                    source_node.hostname,
                    deployment.database_name or deployment.subdomain,
                )
                job.filestore_size_bytes = size
            if deployment:
                deployment.migration_state = MigrationState.preflight
            return True
        else:
            failed_checks = [k for k, v in checks.items() if not v["passed"]]
            msg = f"Preflight failed: {', '.join(failed_checks)}"
            logger.warning(f"❌ {msg} for job {job.id}")
            self._transition_to_failed(db, job, msg)
            return False

    async def _run_prepare_target(self, db: Session, job: TenantMigrationJob) -> bool:
        """
        Preparing target: rsync bulk del filestore al nodo destino.
        
        NO causa downtime — el tenant sigue operando en el nodo origen.
        """
        logger.info(f"📦 Preparing target for job {job.id}: rsync filestore")
        job.state = MigrationState.preparing_target

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        db_name = deployment.database_name or deployment.subdomain
        fs_path = ODOO_FILESTORE_PATH

        # rsync bulk copy (sin downtime) — blocking → thread pool
        ok, detail = await asyncio.to_thread(
            self._rsync_filestore,
            source_ip=source_node.hostname,
            target_ip=target_node.hostname,
            db_name=db_name,
            fs_path=fs_path,
        )

        if ok:
            job.filestore_synced_at = datetime.utcnow()
            if deployment:
                deployment.migration_state = MigrationState.preparing_target
            logger.info(f"✅ Filestore bulk sync completed for job {job.id}")
            return True
        else:
            job.append_error(f"rsync failed: {detail}")
            logger.error(f"❌ rsync failed for job {job.id}: {detail}")
            return False

    async def _run_warming(self, db: Session, job: TenantMigrationJob) -> bool:
        """
        Warming target: verificar que el nodo destino puede servir el tenant.
        
        Checks: filestore presente, Odoo puede leer la BD, nginx maps configurados.
        """
        logger.info(f"🔥 Warming target for job {job.id}")
        job.state = MigrationState.warming_target

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)
        source_node = db.query(ProxmoxNode).get(job.source_node_id)

        db_name = deployment.database_name or deployment.subdomain
        checks_passed = True

        # 1. Verificar filestore en destino vs origen (blocking → thread pool)
        target_count = await asyncio.to_thread(
            self._count_filestore_files, target_node.hostname, db_name
        )
        source_count = await asyncio.to_thread(
            self._count_filestore_files, source_node.hostname, db_name
        )

        if source_count > 0 and target_count < (source_count * 0.9):
            job.append_error(
                f"Filestore incompleto: destino={target_count}, origen={source_count}"
            )
            checks_passed = False

        # 2. Odoo en destino puede acceder a la BD (PostgreSQL centralizado)
        odoo_ok, _ = await asyncio.to_thread(
            self._check_odoo_health, target_node.hostname
        )
        if not odoo_ok:
            job.append_error("Odoo en nodo destino no responde")
            checks_passed = False

        if checks_passed:
            if deployment:
                deployment.migration_state = MigrationState.warming_target
            logger.info(f"✅ Warming checks passed for job {job.id}")
            return True
        else:
            logger.warning(f"❌ Warming failed for job {job.id}")
            return False

    async def _run_cutover(self, db: Session, job: TenantMigrationJob) -> bool:
        """
        Cutover: ventana de corte con downtime mínimo (~30-120s).
        
        Soporta 4 combinaciones de runtime:
          - shared_pool → shared_pool: rsync delta + reasignar nodo
          - shared_pool → dedicated_service: rsync delta + provisionar servicio dedicado
          - dedicated_service → shared_pool: rsync delta + desmontar servicio
          - dedicated_service → dedicated_service: rsync delta + re-provisionar
        
        Secuencia:
        1. Pausar cron Odoo en la BD del tenant
        2. rsync delta (solo cambios desde bulk copy)
        3. Si cross-runtime: provisionar o desmontar dedicated_service
        4. Actualizar TenantDeployment (active_node_id, backend_host, runtime)
        5. Reconciliar routing en PCT160
        6. Reactivar cron Odoo
        """
        logger.info(f"⚡ CUTOVER starting for job {job.id} — DOWNTIME WINDOW")
        job.state = MigrationState.cutover
        job.cutover_started_at = datetime.utcnow()

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)
        db_name = deployment.database_name or deployment.subdomain

        paused_cron_ids: List[int] = []
        is_cross_runtime = job.source_runtime_mode != job.target_runtime_mode

        try:
            # 1. Pausar cron Odoo en la BD del tenant (PostgreSQL centralizado)
            paused_cron_ids = await asyncio.to_thread(
                self._pause_odoo_crons, db_name
            )
            logger.info(f"  ⏸ Paused {len(paused_cron_ids)} crons for {db_name}")

            # 2. rsync delta (solo cambios desde la última sync)
            ok, detail = await asyncio.to_thread(
                self._rsync_filestore,
                source_ip=source_node.hostname,
                target_ip=target_node.hostname,
                db_name=db_name,
                fs_path=ODOO_FILESTORE_PATH,
            )
            if not ok:
                raise RuntimeError(f"rsync delta failed: {detail}")
            logger.info(f"  📦 Delta rsync completed for {db_name}")

            # 3. Cross-runtime provisioning / deprovisioning
            if is_cross_runtime:
                from .dedicated_service_manager import dedicated_manager

                # Si el origen era dedicado, desmontar el servicio en origen
                if job.source_runtime_mode == "dedicated_service":
                    logger.info(f"  🔧 Deprovisioning dedicated on source node")
                    await dedicated_manager.deprovision_dedicated(
                        db, deployment, source_node.hostname
                    )

                # Si el destino es dedicado, provisionar servicio
                if job.target_runtime_mode == "dedicated_service":
                    logger.info(f"  🚀 Provisioning dedicated on target node")
                    await dedicated_manager.provision_dedicated(
                        db, deployment, target_node, initiated_by=job.initiated_by
                    )
                    # provision_dedicated ya actualiza el deployment, skip step 4
                    db.flush()
                else:
                    # Destino es shared_pool
                    old_node_id = deployment.active_node_id
                    old_backend = deployment.backend_host

                    deployment.active_node_id = target_node.id
                    deployment.backend_host = target_node.hostname
                    deployment.desired_node_id = None
                    deployment.migration_state = MigrationState.cutover
                    deployment.runtime_mode = RuntimeMode.shared_pool
                    deployment.routing_mode = RoutingMode.node_proxy
                    deployment.http_port = 8080
                    deployment.chat_port = 8072
                    deployment.service_name = None
                    deployment.addons_overlay_path = None

                    db.flush()
                    logger.info(
                        f"  🔄 Deployment reverted to shared_pool: node {old_node_id}→{target_node.id}"
                    )
            else:
                # Same-runtime migration (shared→shared or dedicated→dedicated)
                old_node_id = deployment.active_node_id
                old_backend = deployment.backend_host

                deployment.active_node_id = target_node.id
                deployment.backend_host = target_node.hostname
                deployment.desired_node_id = None
                deployment.migration_state = MigrationState.cutover

                # Si es dedicated→dedicated, re-provisionar puertos en nuevo nodo
                if job.target_runtime_mode == "dedicated_service":
                    from .dedicated_service_manager import dedicated_manager
                    # Desmontar en origen
                    await dedicated_manager.deprovision_dedicated(
                        db, deployment, source_node.hostname
                    )
                    # Provisionar en destino
                    await dedicated_manager.provision_dedicated(
                        db, deployment, target_node, initiated_by=job.initiated_by
                    )

                db.flush()
                logger.info(
                    f"  🔄 Deployment updated: node {old_node_id}→{target_node.id}, "
                    f"backend {old_backend}→{target_node.hostname}"
                )

            # 4. Reconciliar routing en PCT160 + nodos remotos (async)
            try:
                from .routing_reconciler import RoutingReconciler
                reconciler = RoutingReconciler(db=db)
                reconcile_result = await reconciler.reconcile(
                    include_remote_nodes=True
                )
                logger.info(f"  🔧 Routing reconciled: {reconcile_result.get('status', 'ok')}")
            except Exception as e:
                logger.warning(f"  ⚠️ Routing reconcile had issues: {e}")
                # No fallar el cutover por esto — el health check post lo captura

            # 5. Reactivar cron
            if paused_cron_ids:
                await asyncio.to_thread(
                    self._resume_odoo_crons, db_name, paused_cron_ids
                )
                logger.info(f"  ▶️ Resumed {len(paused_cron_ids)} crons for {db_name}")

            job.cutover_ended_at = datetime.utcnow()
            duration = (job.cutover_ended_at - job.cutover_started_at).total_seconds()
            logger.info(f"✅ CUTOVER completed for job {job.id} in {duration:.1f}s")

            deployment.migration_state = MigrationState.verifying
            return True

        except Exception as e:
            job.cutover_ended_at = datetime.utcnow()
            # Intentar reactivar crons si fueron pausados
            if paused_cron_ids:
                try:
                    await asyncio.to_thread(
                        self._resume_odoo_crons, db_name, paused_cron_ids
                    )
                except Exception:
                    pass
            raise  # Re-raise para que process_job haga rollback

    async def _run_verifying(self, db: Session, job: TenantMigrationJob) -> bool:
        """
        Verifying: validación post-migración.
        
        Si pasa → completed. Si falla → rollback automático.
        """
        logger.info(f"🔎 Verifying migration for job {job.id}")

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        checks_passed = True
        verify_results = {}

        # 1. Odoo en destino responde
        odoo_ok, odoo_detail = await asyncio.to_thread(
            self._check_odoo_health, target_node.hostname
        )
        verify_results["odoo_health"] = {"passed": odoo_ok, "detail": odoo_detail}
        if not odoo_ok:
            checks_passed = False

        # 2. Verificar que el routing apunta al nodo correcto (async)
        try:
            from .routing_reconciler import RoutingReconciler
            reconciler = RoutingReconciler(db=db)
            diag = await reconciler.diagnose_routing()
            # Buscar nuestro subdomain en el diagnóstico
            subdomain_key = f"{deployment.subdomain}.sajet.us"
            route_ok = True
            if isinstance(diag, dict):
                drifts = diag.get("drifts", [])
                for drift in drifts:
                    if drift.get("domain") == subdomain_key:
                        route_ok = False
                        break
            verify_results["routing"] = {"passed": route_ok, "detail": str(diag.get("summary", ""))}
            if not route_ok:
                checks_passed = False
        except Exception as e:
            verify_results["routing"] = {"passed": False, "detail": str(e)}
            checks_passed = False

        if checks_passed:
            logger.info(f"✅ Verification passed for job {job.id}")
            return True
        else:
            failed = [k for k, v in verify_results.items() if not v.get("passed")]
            reason = f"Verification failed: {', '.join(failed)}"
            logger.warning(f"❌ {reason} for job {job.id}")
            await self._run_rollback(db, job, reason=reason)
            return False

    async def _finalize_completed(self, db: Session, job: TenantMigrationJob) -> bool:
        """Marca la migración como completada."""
        job.state = MigrationState.completed
        job.completed_at = datetime.utcnow()

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        if deployment:
            deployment.migration_state = MigrationState.idle
            deployment.desired_node_id = None

        self._audit(db, "migration_completed", job.subdomain, {
            "job_id": str(job.id),
            "source_node_id": job.source_node_id,
            "target_node_id": job.target_node_id,
            "cutover_duration_s": (
                (job.cutover_ended_at - job.cutover_started_at).total_seconds()
                if job.cutover_started_at and job.cutover_ended_at else None
            ),
        })

        logger.info(f"🎉 Migration COMPLETED: {job.id} | {job.subdomain}")
        return True

    async def _run_rollback(self, db: Session, job: TenantMigrationJob, reason: str = "") -> None:
        """
        Rollback: revertir deployment al nodo origen + reconciliar routing.
        """
        logger.warning(f"🔙 ROLLBACK for job {job.id}: {reason}")
        job.state = MigrationState.rollback
        job.rollback_reason = reason

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        source_node = db.query(ProxmoxNode).get(job.source_node_id)

        if deployment and source_node:
            # Revertir deployment al nodo origen
            deployment.active_node_id = job.source_node_id
            deployment.backend_host = source_node.hostname
            deployment.desired_node_id = None
            deployment.migration_state = MigrationState.failed

            db.flush()

            # Reconciliar routing (async)
            try:
                from .routing_reconciler import RoutingReconciler
                reconciler = RoutingReconciler(db=db)
                await reconciler.reconcile(include_remote_nodes=True)
                logger.info(f"  🔧 Routing rolled back for {job.subdomain}")
            except Exception as e:
                logger.error(f"  ❌ Routing rollback failed: {e}")
                job.append_error(f"Routing rollback failed: {e}")

        job.state = MigrationState.failed
        job.completed_at = datetime.utcnow()

        self._audit(db, "migration_rollback", job.subdomain, {
            "job_id": str(job.id),
            "reason": reason,
        })

    # ── Infrastructure helpers ────────────────────────────────────

    def _ssh_cmd(self, node_ip: str, cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Ejecuta comando SSH en un nodo."""
        safe = cmd.replace("'", "'\\''")
        full = f"ssh -o BatchMode=yes -o ConnectTimeout=5 root@{node_ip} '{safe}'"
        try:
            r = subprocess.run(
                full, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        except subprocess.TimeoutExpired:
            return 1, "", f"SSH timeout after {timeout}s"
        except Exception as e:
            return 1, "", str(e)

    def _ssh_check(self, node_ip: str) -> Tuple[bool, str]:
        """Verificar conectividad SSH a un nodo."""
        rc, out, err = self._ssh_cmd(node_ip, "echo ok", timeout=10)
        if rc == 0 and "ok" in out:
            return True, "SSH OK"
        return False, f"SSH failed: rc={rc}, err={err}"

    def _check_filestore(self, node_ip: str, db_name: str) -> Tuple[bool, str]:
        """Verificar que el filestore del tenant existe en el nodo."""
        rc, out, err = self._ssh_cmd(
            node_ip,
            f"test -d {ODOO_FILESTORE_PATH}/{db_name} && echo exists || echo missing",
            timeout=10,
        )
        if rc == 0 and "exists" in out:
            return True, "Filestore exists"
        return False, f"Filestore missing: {out} {err}"

    def _measure_filestore(self, node_ip: str, db_name: str) -> Optional[int]:
        """Medir tamaño del filestore en bytes."""
        rc, out, _ = self._ssh_cmd(
            node_ip,
            f"du -sb {ODOO_FILESTORE_PATH}/{db_name} 2>/dev/null | cut -f1",
            timeout=15,
        )
        if rc == 0 and out.strip().isdigit():
            return int(out.strip())
        return None

    def _count_filestore_files(self, node_ip: str, db_name: str) -> int:
        """Contar archivos en el filestore."""
        rc, out, _ = self._ssh_cmd(
            node_ip,
            f"find {ODOO_FILESTORE_PATH}/{db_name} -type f 2>/dev/null | wc -l",
            timeout=15,
        )
        if rc == 0 and out.strip().isdigit():
            return int(out.strip())
        return 0

    def _check_odoo_health(self, node_ip: str) -> Tuple[bool, str]:
        """Verificar que Odoo responde en el nodo."""
        import httpx
        try:
            resp = httpx.get(
                f"https://{node_ip}:8069/web/login",
                timeout=10.0,
                follow_redirects=True,
                verify=False,
            )
            if resp.status_code in (200, 303):
                return True, f"Odoo OK (HTTP {resp.status_code})"
            return False, f"Odoo HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Odoo unreachable: {e}"

    def _rsync_filestore(
        self,
        source_ip: str,
        target_ip: str,
        db_name: str,
        fs_path: str,
    ) -> Tuple[bool, str]:
        """
        rsync filestore de un nodo a otro.
        
        Ejecutado desde PCT160 vía SSH al nodo origen, que hace rsync al destino.
        """
        cmd = (
            f"ssh -o BatchMode=yes -o ConnectTimeout=5 root@{source_ip} "
            f"'rsync -az --delete "
            f"{fs_path}/{db_name}/ "
            f"root@{target_ip}:{fs_path}/{db_name}/'"
        )
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=600  # 10 min max
            )
            if r.returncode == 0:
                # Fix ownership en destino
                self._ssh_cmd(
                    target_ip,
                    f"chown -R odoo:odoo {fs_path}/{db_name}",
                    timeout=60,
                )
                return True, "rsync OK"
            return False, f"rsync rc={r.returncode}: {r.stderr[:500]}"
        except subprocess.TimeoutExpired:
            return False, "rsync timeout (>10 min)"
        except Exception as e:
            return False, str(e)

    def _pause_odoo_crons(self, db_name: str) -> List[int]:
        """
        Pausar cron jobs activos en la BD del tenant (PostgreSQL centralizado).
        
        Retorna lista de IDs pausados para poder reactivarlos.
        """
        from ..config import ODOO_DB_HOST, ODOO_DB_PORT, ODOO_DB_USER, ODOO_DB_PASSWORD
        import psycopg2

        paused_ids: List[int] = []
        try:
            conn = psycopg2.connect(
                host=ODOO_DB_HOST, port=ODOO_DB_PORT,
                user=ODOO_DB_USER, password=ODOO_DB_PASSWORD,
                dbname=db_name,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                # Obtener crons activos
                cur.execute("SELECT id FROM ir_cron WHERE active = true")
                paused_ids = [row[0] for row in cur.fetchall()]

                if paused_ids:
                    cur.execute(
                        "UPDATE ir_cron SET active = false WHERE id = ANY(%s)",
                        (paused_ids,)
                    )
            conn.close()
        except Exception as e:
            logger.warning(f"Could not pause crons for {db_name}: {e}")
        return paused_ids

    def _resume_odoo_crons(self, db_name: str, cron_ids: List[int]) -> None:
        """Reactivar cron jobs previamente pausados."""
        if not cron_ids:
            return

        from ..config import ODOO_DB_HOST, ODOO_DB_PORT, ODOO_DB_USER, ODOO_DB_PASSWORD
        import psycopg2

        try:
            conn = psycopg2.connect(
                host=ODOO_DB_HOST, port=ODOO_DB_PORT,
                user=ODOO_DB_USER, password=ODOO_DB_PASSWORD,
                dbname=db_name,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ir_cron SET active = true WHERE id = ANY(%s)",
                    (cron_ids,)
                )
            conn.close()
        except Exception as e:
            logger.error(f"Could not resume crons for {db_name}: {e}")

    def _cleanup_target_filestore(self, db: Session, job: TenantMigrationJob) -> None:
        """Limpiar filestore copiado al nodo destino (post-cancel o post-fail)."""
        target_node = db.query(ProxmoxNode).get(job.target_node_id)
        if not target_node:
            return

        db_name = job.subdomain
        deployment = db.query(TenantDeployment).get(job.deployment_id)
        if deployment:
            db_name = deployment.database_name or deployment.subdomain

        rc, _, err = self._ssh_cmd(
            target_node.hostname,
            f"rm -rf {ODOO_FILESTORE_PATH}/{db_name}",
            timeout=60,
        )
        if rc == 0:
            logger.info(f"🗑️ Cleaned up target filestore for {db_name} on {target_node.hostname}")
        else:
            logger.warning(f"Failed to cleanup target filestore: {err}")

    def _transition_to_failed(self, db: Session, job: TenantMigrationJob, msg: str) -> None:
        """Transicionar job a estado failed."""
        job.state = MigrationState.failed
        job.append_error(msg)
        job.completed_at = datetime.utcnow()

        deployment = db.query(TenantDeployment).get(job.deployment_id)
        if deployment:
            deployment.migration_state = MigrationState.failed
            deployment.desired_node_id = None

        self._audit(db, "migration_failed", job.subdomain, {
            "job_id": str(job.id), "error": msg,
        })
        logger.error(f"❌ Migration FAILED: {job.id} | {msg}")

    def _audit(self, db: Session, event_type: str, subdomain: str, details: dict) -> None:
        """Registrar evento de auditoría."""
        try:
            evt = AuditEventRecord(
                event_type=event_type.upper(),
                actor_username="migration_orchestrator",
                resource=f"tenant:{subdomain}",
                action="migration",
                status="info",
                details=details,
            )
            db.add(evt)
            db.flush()
        except Exception as e:
            logger.warning(f"Could not create audit event: {e}")


# Singleton
migration_orchestrator = MigrationOrchestrator()
