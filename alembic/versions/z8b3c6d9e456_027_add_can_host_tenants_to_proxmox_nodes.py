"""027: add can_host_tenants to proxmox_nodes + fix atenea-odoo status

Revision ID: z8b3c6d9e456
Revises: y7a2b5c8d345
Create Date: 2026-03-29

Fase 1 Multi-Nodo:
  - Agrega columna can_host_tenants (BOOLEAN DEFAULT false) a proxmox_nodes
  - Backfill: true para nodos donde is_database_node = false
  - Fix: atenea-odoo (CT105, 10.10.10.100) -> status = online (sirve 4 deployments productivos)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "z8b3c6d9e456"
down_revision = "y7a2b5c8d345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Agregar columna can_host_tenants
    op.add_column(
        "proxmox_nodes",
        sa.Column(
            "can_host_tenants",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # 2. Backfill: nodos que NO son de BD pueden hospedar tenants
    op.execute(
        """
        UPDATE proxmox_nodes
        SET can_host_tenants = true
        WHERE is_database_node = false
        """
    )

    # 3. Fix: atenea-odoo a online (sirve los 4 deployments productivos)
    op.execute(
        """
        UPDATE proxmox_nodes
        SET status = 'online'
        WHERE hostname = '10.10.10.100'
          AND status = 'offline'
        """
    )


def downgrade() -> None:
    op.drop_column("proxmox_nodes", "can_host_tenants")
