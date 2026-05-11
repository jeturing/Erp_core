"""045 subscription special discounts

Revision ID: p1q2r3s4t901
Revises: 6f0b3e5a9c07
Create Date: 2026-05-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p1q2r3s4t901"
down_revision: Union[str, Sequence[str], None] = "6f0b3e5a9c07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("discount_pct", sa.Float(), nullable=False, server_default="0"))
    op.add_column("subscriptions", sa.Column("discount_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("subscriptions", sa.Column("discount_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("subscriptions", "discount_reason")
    op.drop_column("subscriptions", "discount_amount")
    op.drop_column("subscriptions", "discount_pct")
