"""038 — Email rate limiting overrides en partner_pricing_overrides

Revision ID: k8l6m1n2o345
Revises: j7k5l0m1n234
Create Date: 2026-04-08 00:00:00.000000

Agrega 4 columnas email override a partner_pricing_overrides:
  - max_emails_monthly_override
  - email_rate_per_minute_override
  - email_rate_per_hour_override
  - email_rate_per_day_override
"""
from alembic import op
import sqlalchemy as sa

revision = "k8l6m1n2o345"
down_revision = "j7k5l0m1n234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("partner_pricing_overrides") as batch_op:
        batch_op.add_column(
            sa.Column("max_emails_monthly_override", sa.Integer(), nullable=True,
                      comment="Override cuota mensual email, NULL=usar plan, 0=ilimitado")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_minute_override", sa.Integer(), nullable=True,
                      comment="Override emails/min, NULL=usar plan")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_hour_override", sa.Integer(), nullable=True,
                      comment="Override emails/hora, NULL=usar plan")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_day_override", sa.Integer(), nullable=True,
                      comment="Override emails/día, NULL=usar plan")
        )


def downgrade() -> None:
    with op.batch_alter_table("partner_pricing_overrides") as batch_op:
        batch_op.drop_column("email_rate_per_day_override")
        batch_op.drop_column("email_rate_per_hour_override")
        batch_op.drop_column("email_rate_per_minute_override")
        batch_op.drop_column("max_emails_monthly_override")
