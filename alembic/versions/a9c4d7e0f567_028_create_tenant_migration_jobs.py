"""028: create tenant_migration_jobs table

Revision ID: a9c4d7e0f567
Revises: z8b3c6d9e456
Create Date: 2026-03-29

Fase 2 — Migración live entre nodos:
  - Crea tabla tenant_migration_jobs para tracking de migraciones
  - UUID PK, FKs a tenant_deployments y proxmox_nodes
  - Estado usa MigrationState enum existente
  - JSON para preflight_result, timestamps para ventana de corte
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM

# revision identifiers
revision = "a9c4d7e0f567"
down_revision = "z8b3c6d9e456"
branch_labels = None
depends_on = None

# Referencia al enum que ya existe en PostgreSQL (creado en migración 023)
migration_state_enum = PG_ENUM(
    "idle", "queued", "preflight", "preparing_target",
    "warming_target", "cutover", "verifying", "rollback",
    "completed", "failed",
    name="migrationstate",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "tenant_migration_jobs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "deployment_id",
            sa.Integer,
            sa.ForeignKey("tenant_deployments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subdomain", sa.String(100), nullable=False),
        sa.Column(
            "source_node_id",
            sa.Integer,
            sa.ForeignKey("proxmox_nodes.id"),
            nullable=False,
        ),
        sa.Column(
            "target_node_id",
            sa.Integer,
            sa.ForeignKey("proxmox_nodes.id"),
            nullable=False,
        ),
        # Usa el enum 'migrationstate' que ya existe en PostgreSQL (creado en migración 023)
        sa.Column(
            "state",
            migration_state_enum,
            nullable=False,
            server_default="queued",
        ),
        sa.Column("source_runtime_mode", sa.String(30), server_default="shared_pool"),
        sa.Column("target_runtime_mode", sa.String(30), server_default="shared_pool"),
        sa.Column("initiated_by", sa.String(150), nullable=False),
        sa.Column("error_log", sa.Text, nullable=True),
        sa.Column("preflight_result", sa.JSON, nullable=True),
        sa.Column("filestore_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("filestore_synced_at", sa.DateTime, nullable=True),
        sa.Column("cutover_started_at", sa.DateTime, nullable=True),
        sa.Column("cutover_ended_at", sa.DateTime, nullable=True),
        sa.Column("rollback_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Índices para queries frecuentes
    op.create_index(
        "ix_migration_jobs_deployment_state",
        "tenant_migration_jobs",
        ["deployment_id", "state"],
    )
    op.create_index(
        "ix_migration_jobs_state",
        "tenant_migration_jobs",
        ["state"],
    )


def downgrade() -> None:
    op.drop_index("ix_migration_jobs_state")
    op.drop_index("ix_migration_jobs_deployment_state")
    op.drop_table("tenant_migration_jobs")
