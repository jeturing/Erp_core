"""023 multi-node tenant deployment fields

Revision ID: v4w2x8y9z012
Revises: u3r1s7w8x890
Create Date: 2026-03-28

Agrega campos multi-nodo a tenant_deployments:
  - active_node_id / desired_node_id (FK → proxmox_nodes)
  - runtime_mode (shared_pool / dedicated_service)
  - routing_mode (node_proxy / direct_service)
  - backend_host, http_port, chat_port
  - service_name, addons_overlay_path
  - migration_state (idle → completed/failed)
  - last_healthcheck_at

Backfill: todos los deployments existentes reciben:
  - active_node_id = id del nodo con host que matchee ODOO_PRIMARY_IP o CT105_IP
  - runtime_mode = shared_pool
  - routing_mode = node_proxy
  - backend_host = IP del nodo primario (de env o default 10.10.10.100)
  - http_port = 8080, chat_port = 8072
  - migration_state = idle
"""
import os
from alembic import op
import sqlalchemy as sa

revision = 'v4w2x8y9z012'
down_revision = 'u3r1s7w8x890'
branch_labels = None
depends_on = None

# Resolver IP del nodo primario desde env (misma lógica que config.py)
_ODOO_DB_HOST = os.getenv("ODOO_DB_HOST", "10.10.10.137")
_ODOO_PRIMARY_IP = os.getenv("ODOO_PRIMARY_IP", os.getenv("CT105_IP", _ODOO_DB_HOST if _ODOO_DB_HOST != "10.10.10.137" else "10.10.10.100"))


def upgrade() -> None:
    # ── 1. Crear tipos ENUM en PostgreSQL ─────────────────────────────
    runtime_mode_enum = sa.Enum('shared_pool', 'dedicated_service', name='runtimemode')
    routing_mode_enum = sa.Enum('node_proxy', 'direct_service', name='routingmode')
    migration_state_enum = sa.Enum(
        'idle', 'queued', 'preflight', 'preparing_target', 'warming_target',
        'cutover', 'verifying', 'rollback', 'completed', 'failed',
        name='migrationstate'
    )
    runtime_mode_enum.create(op.get_bind(), checkfirst=True)
    routing_mode_enum.create(op.get_bind(), checkfirst=True)
    migration_state_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Agregar columnas a tenant_deployments ──────────────────────
    op.add_column('tenant_deployments', sa.Column(
        'active_node_id', sa.Integer(),
        sa.ForeignKey('proxmox_nodes.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.add_column('tenant_deployments', sa.Column(
        'desired_node_id', sa.Integer(),
        sa.ForeignKey('proxmox_nodes.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.add_column('tenant_deployments', sa.Column(
        'runtime_mode', runtime_mode_enum,
        nullable=False, server_default='shared_pool'
    ))
    op.add_column('tenant_deployments', sa.Column(
        'routing_mode', routing_mode_enum,
        nullable=False, server_default='node_proxy'
    ))
    op.add_column('tenant_deployments', sa.Column(
        'backend_host', sa.String(100), nullable=True
    ))
    op.add_column('tenant_deployments', sa.Column(
        'http_port', sa.Integer(), nullable=True, server_default='8080'
    ))
    op.add_column('tenant_deployments', sa.Column(
        'chat_port', sa.Integer(), nullable=True, server_default='8072'
    ))
    op.add_column('tenant_deployments', sa.Column(
        'service_name', sa.String(150), nullable=True
    ))
    op.add_column('tenant_deployments', sa.Column(
        'addons_overlay_path', sa.String(500), nullable=True
    ))
    op.add_column('tenant_deployments', sa.Column(
        'migration_state', migration_state_enum,
        nullable=False, server_default='idle'
    ))
    op.add_column('tenant_deployments', sa.Column(
        'last_healthcheck_at', sa.DateTime(), nullable=True
    ))

    # ── 3. Índice en active_node_id ───────────────────────────────────
    op.create_index('ix_tenant_deployments_active_node_id', 'tenant_deployments', ['active_node_id'])

    # ── 4. Backfill: asignar nodo primario a deployments existentes ───
    # Buscar el id del ProxmoxNode cuyo host matchee la IP primaria
    conn = op.get_bind()

    # Intentar encontrar el nodo primario por IP (columna = hostname)
    result = conn.execute(sa.text(
        "SELECT id FROM proxmox_nodes WHERE hostname = :ip LIMIT 1"
    ), {"ip": _ODOO_PRIMARY_IP})
    row = result.fetchone()
    primary_node_id = row[0] if row else None

    if primary_node_id:
        conn.execute(sa.text(
            "UPDATE tenant_deployments SET "
            "  active_node_id = :node_id, "
            "  backend_host = :ip, "
            "  http_port = 8080, "
            "  chat_port = 8072 "
            "WHERE active_node_id IS NULL"
        ), {"node_id": primary_node_id, "ip": _ODOO_PRIMARY_IP})
    else:
        # Si no hay nodo registrado, al menos llenar backend_host con la IP
        conn.execute(sa.text(
            "UPDATE tenant_deployments SET "
            "  backend_host = :ip, "
            "  http_port = 8080, "
            "  chat_port = 8072 "
            "WHERE backend_host IS NULL"
        ), {"ip": _ODOO_PRIMARY_IP})


def downgrade() -> None:
    op.drop_index('ix_tenant_deployments_active_node_id', 'tenant_deployments')

    op.drop_column('tenant_deployments', 'last_healthcheck_at')
    op.drop_column('tenant_deployments', 'migration_state')
    op.drop_column('tenant_deployments', 'addons_overlay_path')
    op.drop_column('tenant_deployments', 'service_name')
    op.drop_column('tenant_deployments', 'chat_port')
    op.drop_column('tenant_deployments', 'http_port')
    op.drop_column('tenant_deployments', 'backend_host')
    op.drop_column('tenant_deployments', 'routing_mode')
    op.drop_column('tenant_deployments', 'runtime_mode')
    op.drop_column('tenant_deployments', 'desired_node_id')
    op.drop_column('tenant_deployments', 'active_node_id')

    # Eliminar tipos ENUM
    sa.Enum(name='migrationstate').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='routingmode').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='runtimemode').drop(op.get_bind(), checkfirst=True)
