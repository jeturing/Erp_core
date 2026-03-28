"""025 merge email addon branch with admin pct161 head

Revision ID: x6z1c4m8n222
Revises: k012updateadminpct161, w5x3y9z0a123
Create Date: 2026-03-28

No-op merge revision para dejar un único head en Alembic.
"""

from alembic import op


revision = "x6z1c4m8n222"
down_revision = ("k012updateadminpct161", "w5x3y9z0a123")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
