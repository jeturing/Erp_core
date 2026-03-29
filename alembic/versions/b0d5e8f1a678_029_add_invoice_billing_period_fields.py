"""029: add invoice billing period fields

Revision ID: b0d5e8f1a678
Revises: a9c4d7e0f567
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa


revision = "b0d5e8f1a678"
down_revision = "a9c4d7e0f567"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("billing_period_key", sa.String(length=80), nullable=True))
    op.add_column("invoices", sa.Column("period_start", sa.DateTime(), nullable=True))
    op.add_column("invoices", sa.Column("period_end", sa.DateTime(), nullable=True))
    op.create_index("ix_invoices_billing_period_key", "invoices", ["billing_period_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_invoices_billing_period_key", table_name="invoices")
    op.drop_column("invoices", "period_end")
    op.drop_column("invoices", "period_start")
    op.drop_column("invoices", "billing_period_key")
