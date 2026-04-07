"""036 — Merge plan_governance_fair_use + infra_tunnels_reserved_subdomains

Revision ID: i6j4k9l0m789
Revises: b1d5e8f1a229, h5i3j4k5l678
Create Date: 2026-04-05

Une las dos ramas divergentes:
  - Branch A: b1d5e8f1a229 (029_plan_governance_fair_use)
  - Branch B: h5i3j4k5l678 (035_infra_tunnels_reserved_subdomains)
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'i6j4k9l0m789'
down_revision = ('b1d5e8f1a229', 'h5i3j4k5l678')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
