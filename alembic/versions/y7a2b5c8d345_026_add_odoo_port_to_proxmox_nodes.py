"""026 add odoo_port to proxmox_nodes

Revision ID: y7a2b5c8d345
Revises: x6z1c4m8n222
Create Date: 2026-03-29

Agrega columna odoo_port a proxmox_nodes para soportar nodos Odoo
con puertos distintos (ej: CT105=8069, PCT161=8089).

Backfill:
  - vmid=105 → odoo_port=8069
  - vmid=161 → odoo_port=8089
  - Todos los demás → 8069 (default)
"""
from alembic import op
import sqlalchemy as sa

revision = 'y7a2b5c8d345'
down_revision = 'x6z1c4m8n222'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('proxmox_nodes', sa.Column(
        'odoo_port', sa.Integer(), nullable=True, server_default='8069'
    ))

    # Backfill puertos conocidos
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE proxmox_nodes SET odoo_port = 8069 WHERE odoo_port IS NULL"
    ))
    conn.execute(sa.text(
        "UPDATE proxmox_nodes SET odoo_port = 8089 WHERE vmid = 161"
    ))


def downgrade() -> None:
    op.drop_column('proxmox_nodes', 'odoo_port')
