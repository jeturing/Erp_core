"""
Router de Migración de Tenants entre Nodos (Fase 2) + Dedicated Service (Fase 3).

Endpoints:
  POST  /api/migration/{subdomain}/start                — Iniciar migración
  GET   /api/migration/{subdomain}/status                — Estado de migración activa
  POST  /api/migration/{subdomain}/cancel                — Cancelar migración activa
  GET   /api/migration/jobs                              — Listar todos los jobs
  GET   /api/migration/jobs/{job_id}                     — Detalle de un job
  POST  /api/migration/{subdomain}/provision-dedicated   — Provisionar servicio dedicado
  POST  /api/migration/{subdomain}/deprovision-dedicated — Revertir a shared_pool
  GET   /api/migration/{subdomain}/dedicated-stats       — Stats del nodo del tenant
"""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..models.database import (
    MigrationState,
    ProxmoxNode,
    RuntimeMode,
    SessionLocal,
    TenantDeployment,
    TenantMigrationJob,
)
from ..schemas.migration import (
    CancelMigrationRequest,
    MigrateRequest,
    MigrationJobListResponse,
    MigrationJobResponse,
    MigrationStartResponse,
    MigrationStatusResponse,
    job_to_list_item,
    job_to_response,
)
from ..security.tokens import TokenManager
from ..services.migration_orchestrator import migration_orchestrator
from ..services.dedicated_service_manager import dedicated_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["Migration"])


# ── Auth helper ───────────────────────────────────────────────────

def _require_admin(request: Request, access_token: str = None) -> dict:
    """Verifica que el caller sea admin. Retorna payload del token."""
    token = access_token
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = TokenManager.verify_access_token(token)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Se requiere rol admin")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# ── POST /api/migration/{subdomain}/start ─────────────────────────

@router.post("/{subdomain}/start", response_model=MigrationStartResponse)
async def start_migration(
    subdomain: str,
    body: MigrateRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Inicia una migración live de un tenant a otro nodo.
    
    Crea un job que será procesado por el worker en background.
    El preflight se ejecuta antes de aceptar el job.
    """
    payload = _require_admin(request, access_token)
    initiator = body.initiated_by or payload.get("username", "admin")

    db = SessionLocal()
    try:
        # Buscar deployment por subdomain
        deployment = db.query(TenantDeployment).filter(
            TenantDeployment.subdomain == subdomain
        ).first()
        if not deployment:
            raise HTTPException(
                status_code=404,
                detail=f"Deployment no encontrado para subdomain: {subdomain}",
            )

        # Validar nodo destino
        target_node = db.query(ProxmoxNode).get(body.target_node_id)
        if not target_node:
            raise HTTPException(
                status_code=404,
                detail=f"Nodo destino {body.target_node_id} no encontrado",
            )

        job = await migration_orchestrator.start_migration(
            db=db,
            deployment_id=deployment.id,
            target_node_id=body.target_node_id,
            initiated_by=initiator,
            target_runtime_mode=body.target_runtime_mode,
        )

        source_node = db.query(ProxmoxNode).get(job.source_node_id)

        return MigrationStartResponse(
            success=True,
            data=job_to_response(job, source_node, target_node),
            meta={"message": f"Migración iniciada: {subdomain} → {target_node.name}"},
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting migration for {subdomain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── GET /api/migration/{subdomain}/status ──────────────────────────

@router.get("/{subdomain}/status", response_model=MigrationStatusResponse)
async def get_migration_status(
    subdomain: str,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtiene el estado de la migración activa para un subdomain."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        # Buscar job activo más reciente
        active_states = [
            MigrationState.queued, MigrationState.preflight,
            MigrationState.preparing_target, MigrationState.warming_target,
            MigrationState.cutover, MigrationState.verifying,
        ]

        job = db.query(TenantMigrationJob).filter(
            TenantMigrationJob.subdomain == subdomain,
            TenantMigrationJob.state.in_(active_states),
        ).order_by(TenantMigrationJob.created_at.desc()).first()

        # Si no hay activa, buscar la más reciente
        if not job:
            job = db.query(TenantMigrationJob).filter(
                TenantMigrationJob.subdomain == subdomain,
            ).order_by(TenantMigrationJob.created_at.desc()).first()

        if not job:
            return MigrationStatusResponse(
                success=True,
                data=None,
                meta={"has_active_migration": False},
            )

        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        is_active = job.state in active_states
        return MigrationStatusResponse(
            success=True,
            data=job_to_response(job, source_node, target_node),
            meta={"has_active_migration": is_active},
        )

    finally:
        db.close()


# ── POST /api/migration/{subdomain}/cancel ─────────────────────────

@router.post("/{subdomain}/cancel", response_model=MigrationStartResponse)
async def cancel_migration(
    subdomain: str,
    body: CancelMigrationRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """Cancela la migración activa para un subdomain."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        # Buscar job activo
        active_states = [
            MigrationState.queued, MigrationState.preflight,
            MigrationState.preparing_target, MigrationState.warming_target,
        ]

        job = db.query(TenantMigrationJob).filter(
            TenantMigrationJob.subdomain == subdomain,
            TenantMigrationJob.state.in_(active_states),
        ).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"No hay migración activa cancelable para {subdomain}",
            )

        job = migration_orchestrator.cancel_migration(
            db=db, job_id=job.id, reason=body.reason
        )

        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        return MigrationStartResponse(
            success=True,
            data=job_to_response(job, source_node, target_node),
            meta={"message": f"Migración cancelada: {subdomain}"},
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# ── GET /api/migration/jobs ────────────────────────────────────────

@router.get("/jobs", response_model=MigrationJobListResponse)
async def list_migration_jobs(
    request: Request,
    access_token: str = Cookie(None),
    state: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista todos los jobs de migración, con filtro opcional por estado."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        query = db.query(TenantMigrationJob)

        if state:
            try:
                state_enum = MigrationState(state)
                query = query.filter(TenantMigrationJob.state == state_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estado inválido: {state}. Válidos: {[s.value for s in MigrationState]}",
                )

        total = query.count()
        jobs = query.order_by(
            TenantMigrationJob.created_at.desc()
        ).offset(offset).limit(limit).all()

        return MigrationJobListResponse(
            success=True,
            data=[job_to_list_item(j) for j in jobs],
            meta={"total": total, "limit": limit, "offset": offset},
        )

    finally:
        db.close()


# ── GET /api/migration/jobs/{job_id} ───────────────────────────────

@router.get("/jobs/{job_id}", response_model=MigrationStatusResponse)
async def get_migration_job(
    job_id: str,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtiene el detalle completo de un job de migración."""
    _require_admin(request, access_token)

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="job_id inválido (no es UUID)")

    db = SessionLocal()
    try:
        job = db.query(TenantMigrationJob).get(job_uuid)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} no encontrado")

        source_node = db.query(ProxmoxNode).get(job.source_node_id)
        target_node = db.query(ProxmoxNode).get(job.target_node_id)

        active_states = [
            MigrationState.queued, MigrationState.preflight,
            MigrationState.preparing_target, MigrationState.warming_target,
            MigrationState.cutover, MigrationState.verifying,
        ]
        return MigrationStatusResponse(
            success=True,
            data=job_to_response(job, source_node, target_node),
            meta={"has_active_migration": job.state in active_states},
        )

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════
# Dedicated Service Management (Fase 3 — pasos 3.1–3.4)
# ══════════════════════════════════════════════════════════════════

@router.post("/{subdomain}/provision-dedicated")
async def provision_dedicated_service(
    subdomain: str,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Provisiona un servicio Odoo dedicado para un tenant existente.

    - Reserva puertos HTTP/chat en el nodo actual
    - Crea overlay de addons
    - Genera conf per-tenant + template systemd
    - Arranca el servicio y valida /web/login
    - Actualiza TenantDeployment a dedicated_service
    """
    payload = _require_admin(request, access_token)
    initiator = payload.get("username", "admin")

    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter(
            TenantDeployment.subdomain == subdomain
        ).first()
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment no encontrado: {subdomain}")

        if deployment.runtime_mode == RuntimeMode.dedicated_service:
            raise HTTPException(
                status_code=400,
                detail=f"Tenant {subdomain} ya tiene servicio dedicado: {deployment.service_name}",
            )

        node = db.query(ProxmoxNode).get(deployment.active_node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Nodo activo no encontrado")

        result = await dedicated_manager.provision_dedicated(
            db=db, deployment=deployment, node=node, initiated_by=initiator,
        )
        db.commit()

        return {"success": True, "data": result, "meta": {"message": result.get("message", "")}}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error provisioning dedicated for {subdomain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{subdomain}/deprovision-dedicated")
async def deprovision_dedicated_service(
    subdomain: str,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Desmonta el servicio dedicado de un tenant — revierte a shared_pool.

    - Detiene y deshabilita el servicio systemd
    - Elimina conf per-tenant y overlay de addons
    - Libera puertos
    - Actualiza TenantDeployment a shared_pool
    """
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter(
            TenantDeployment.subdomain == subdomain
        ).first()
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment no encontrado: {subdomain}")

        if deployment.runtime_mode != RuntimeMode.dedicated_service:
            raise HTTPException(
                status_code=400,
                detail=f"Tenant {subdomain} no tiene servicio dedicado (runtime={deployment.runtime_mode.value})",
            )

        node = db.query(ProxmoxNode).get(deployment.active_node_id)
        node_ip = node.hostname if node else deployment.backend_host or ""

        result = await dedicated_manager.deprovision_dedicated(
            db=db, deployment=deployment, node_ip=node_ip,
        )
        db.commit()

        return {"success": True, "data": result, "meta": {"message": result.get("message", "")}}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deprovisioning dedicated for {subdomain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{subdomain}/dedicated-stats")
async def get_dedicated_stats_for_tenant(
    subdomain: str,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtiene estadísticas de servicios dedicados del nodo donde está el tenant."""
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter(
            TenantDeployment.subdomain == subdomain
        ).first()
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment no encontrado: {subdomain}")

        if not deployment.active_node_id:
            raise HTTPException(status_code=400, detail="Tenant sin nodo asignado")

        stats = dedicated_manager.get_dedicated_stats(db, deployment.active_node_id)
        return {"success": True, "data": stats, "meta": {}}

    finally:
        db.close()
