"""
Schemas Pydantic para migración de tenants entre nodos (Fase 2).
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────

class MigrateRequest(BaseModel):
    """Request para iniciar una migración de tenant."""
    target_node_id: int = Field(..., description="ID del nodo destino en proxmox_nodes")
    target_runtime_mode: Optional[str] = Field(
        None,
        description="Modo de runtime destino: 'shared_pool' o 'dedicated_service'. "
                    "None = mantener el modo actual del tenant.",
    )
    initiated_by: Optional[str] = Field(
        None,
        description="Quién inicia (auto-populated con admin:{user} si es None)",
    )


class CancelMigrationRequest(BaseModel):
    """Request para cancelar una migración en curso."""
    reason: Optional[str] = Field(None, description="Motivo de la cancelación")


# ── Response schemas ──────────────────────────────────────────────

class MigrationNodeInfo(BaseModel):
    """Info resumida de un nodo en contexto de migración."""
    id: int
    name: str
    hostname: str
    status: str

    class Config:
        from_attributes = True


class MigrationJobResponse(BaseModel):
    """Respuesta detallada de un job de migración."""
    id: UUID
    deployment_id: int
    subdomain: str
    source_node_id: int
    target_node_id: int
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    state: str
    source_runtime_mode: Optional[str] = None
    target_runtime_mode: Optional[str] = None
    initiated_by: str
    error_log: Optional[str] = None
    preflight_result: Optional[Dict[str, Any]] = None
    filestore_size_bytes: Optional[int] = None
    filestore_synced_at: Optional[datetime] = None
    cutover_started_at: Optional[datetime] = None
    cutover_ended_at: Optional[datetime] = None
    cutover_duration_seconds: Optional[float] = None
    rollback_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MigrationJobListItem(BaseModel):
    """Item resumido para listados de jobs."""
    id: UUID
    subdomain: str
    state: str
    source_node_id: int
    target_node_id: int
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    initiated_by: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MigrationJobListResponse(BaseModel):
    """Lista paginada de jobs de migración."""
    success: bool = True
    data: List[MigrationJobListItem]
    meta: Dict[str, Any] = Field(default_factory=dict)


class MigrationStatusResponse(BaseModel):
    """Respuesta estándar SAJET para estado de migración."""
    success: bool = True
    data: Optional[MigrationJobResponse] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class MigrationStartResponse(BaseModel):
    """Respuesta al iniciar una migración."""
    success: bool = True
    data: MigrationJobResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# ── Helpers ───────────────────────────────────────────────────────

def job_to_response(job, source_node=None, target_node=None) -> MigrationJobResponse:
    """Convierte un TenantMigrationJob a MigrationJobResponse."""
    cutover_duration = None
    if job.cutover_started_at and job.cutover_ended_at:
        cutover_duration = (job.cutover_ended_at - job.cutover_started_at).total_seconds()

    return MigrationJobResponse(
        id=job.id,
        deployment_id=job.deployment_id,
        subdomain=job.subdomain,
        source_node_id=job.source_node_id,
        target_node_id=job.target_node_id,
        source_node_name=getattr(source_node, "name", None) or getattr(job.source_node, "name", None) if hasattr(job, "source_node") else None,
        target_node_name=getattr(target_node, "name", None) or getattr(job.target_node, "name", None) if hasattr(job, "target_node") else None,
        state=job.state.value if hasattr(job.state, "value") else str(job.state),
        source_runtime_mode=job.source_runtime_mode,
        target_runtime_mode=job.target_runtime_mode,
        initiated_by=job.initiated_by,
        error_log=job.error_log,
        preflight_result=job.preflight_result,
        filestore_size_bytes=job.filestore_size_bytes,
        filestore_synced_at=job.filestore_synced_at,
        cutover_started_at=job.cutover_started_at,
        cutover_ended_at=job.cutover_ended_at,
        cutover_duration_seconds=cutover_duration,
        rollback_reason=job.rollback_reason,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


def job_to_list_item(job) -> MigrationJobListItem:
    """Convierte un TenantMigrationJob a MigrationJobListItem."""
    return MigrationJobListItem(
        id=job.id,
        subdomain=job.subdomain,
        state=job.state.value if hasattr(job.state, "value") else str(job.state),
        source_node_id=job.source_node_id,
        target_node_id=job.target_node_id,
        source_node_name=getattr(job.source_node, "name", None) if hasattr(job, "source_node") else None,
        target_node_name=getattr(job.target_node, "name", None) if hasattr(job, "target_node") else None,
        initiated_by=job.initiated_by,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
