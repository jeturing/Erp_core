"""036 — Sistema de capacidad dinámica por nodo.

Agrega umbrales configurables de capacidad (CPU, RAM, disco) a proxmox_nodes,
campos de policy Odoo (tenant_ram_mb, system_overhead_mb, max_tenants,
storage_type), y tabla node_capacity_alerts para historial de alertas de
infraestructura separadas de las alertas de plan/tenant.

Revision ID: i6j7k8l9m012
Revises: h5i3j4k5l678
Create Date: 2026-04-06

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'i6j7k8l9m012'
down_revision = 'h5i3j4k5l678'
branch_labels = None
depends_on = None


def upgrade():
    # ── proxmox_nodes: umbrales de capacidad ──────────────────────────────
    op.add_column('proxmox_nodes', sa.Column(
        'cpu_threshold_warning', sa.Float(), server_default='70', nullable=False))
    op.add_column('proxmox_nodes', sa.Column(
        'cpu_threshold_critical', sa.Float(), server_default='90', nullable=False))
    op.add_column('proxmox_nodes', sa.Column(
        'ram_threshold_warning', sa.Float(), server_default='75', nullable=False))
    op.add_column('proxmox_nodes', sa.Column(
        'ram_threshold_critical', sa.Float(), server_default='90', nullable=False))
    op.add_column('proxmox_nodes', sa.Column(
        'storage_threshold_warning', sa.Float(), server_default='70', nullable=False))
    op.add_column('proxmox_nodes', sa.Column(
        'storage_threshold_critical', sa.Float(), server_default='85', nullable=False))

    # ── proxmox_nodes: política de capacidad Odoo ─────────────────────────
    op.add_column('proxmox_nodes', sa.Column(
        'tenant_ram_mb', sa.Integer(), server_default='800', nullable=False,
        comment='RAM estimada por tenant Odoo (MB)'))
    op.add_column('proxmox_nodes', sa.Column(
        'system_overhead_mb', sa.Integer(), server_default='1200', nullable=False,
        comment='RAM reservada para sistema (PG, Nginx, systemd) (MB)'))
    op.add_column('proxmox_nodes', sa.Column(
        'max_tenants_override', sa.Integer(), nullable=True,
        comment='Límite fijo de tenants (override del cálculo dinámico)'))
    op.add_column('proxmox_nodes', sa.Column(
        'storage_type', sa.String(20), server_default='loop', nullable=False,
        comment='Tipo de storage: loop, zfs, lvm, dir'))
    op.add_column('proxmox_nodes', sa.Column(
        'io_max_tenants', sa.Integer(), server_default='8', nullable=False,
        comment='Máx tenants por límite I/O del storage'))
    op.add_column('proxmox_nodes', sa.Column(
        'auto_drain', sa.Boolean(), server_default='false', nullable=False,
        comment='Si true, deja de aceptar tenants al superar umbral crítico'))
    op.add_column('proxmox_nodes', sa.Column(
        'capacity_score', sa.Float(), server_default='0', nullable=False,
        comment='Score calculado: 0-100, mayor = más capacidad'))
    op.add_column('proxmox_nodes', sa.Column(
        'stagger_delay_sec', sa.Integer(), server_default='12', nullable=False,
        comment='Delay entre arranques de tenants (segundos)'))

    # ── node_capacity_alerts ──────────────────────────────────────────────
    op.create_table(
        'node_capacity_alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('node_id', sa.Integer(),
                  sa.ForeignKey('proxmox_nodes.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('alert_type', sa.String(50), nullable=False,
                  comment='capacity_warning, capacity_critical, auto_drain, scale_out, io_limit'),
        sa.Column('severity', sa.String(20), nullable=False,
                  comment='warning, critical, info'),
        sa.Column('metric_name', sa.String(50), nullable=False,
                  comment='cpu, ram, storage, tenants, io, score'),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_nca_active_node', 'node_capacity_alerts',
                    ['node_id', 'is_active'])


def downgrade():
    op.drop_table('node_capacity_alerts')

    cols_to_drop = [
        'cpu_threshold_warning', 'cpu_threshold_critical',
        'ram_threshold_warning', 'ram_threshold_critical',
        'storage_threshold_warning', 'storage_threshold_critical',
        'tenant_ram_mb', 'system_overhead_mb', 'max_tenants_override',
        'storage_type', 'io_max_tenants', 'auto_drain', 'capacity_score',
        'stagger_delay_sec',
    ]
    for col in cols_to_drop:
        op.drop_column('proxmox_nodes', col)
