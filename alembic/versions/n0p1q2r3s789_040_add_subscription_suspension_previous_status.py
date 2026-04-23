"""add subscription suspension_previous_status

Revision ID: n0p1q2r3s789
Revises: 154b68678890
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n0p1q2r3s789"
down_revision: Union[str, Sequence[str], None] = "154b68678890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("suspension_previous_status", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "suspension_previous_status")
