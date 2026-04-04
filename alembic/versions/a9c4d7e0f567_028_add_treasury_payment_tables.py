"""028: add payout_requests, provider_accounts, payment_events tables

Revision ID: a9c4d7e0f567
Revises: z8b3c6d9e456
Create Date: 2026-04-03

Treasury & Payments persistence:
  - payout_requests: solicitudes de dispersión a proveedores vía Mercury
  - provider_accounts: cuentas bancarias de proveedores (con KYC)
  - payment_events: log de auditoría inmutable de eventos de pago
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a9c4d7e0f567"
down_revision = "z8b3c6d9e456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ──
    payout_status = postgresql.ENUM(
        "pending", "authorized", "processing", "completed", "failed", "canceled", "rejected",
        name="payoutstatus", create_type=False,
    )
    kyc_status = postgresql.ENUM(
        "pending", "approved", "rejected", "expired",
        name="kycstatus", create_type=False,
    )
    payout_status.create(op.get_bind(), checkfirst=True)
    kyc_status.create(op.get_bind(), checkfirst=True)

    # ── provider_accounts ──
    op.create_table(
        "provider_accounts",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("partner_id", sa.Integer, sa.ForeignKey("partners.id"), nullable=False, index=True),
        sa.Column("account_holder_name", sa.String(200), nullable=False),
        sa.Column("account_number_masked", sa.String(20), nullable=False),
        sa.Column("account_number_enc", sa.Text, nullable=True),
        sa.Column("routing_number", sa.String(20), nullable=False),
        sa.Column("account_type", sa.String(10), server_default="checking"),
        sa.Column("bank_name", sa.String(200), nullable=True),
        sa.Column("kyc_status", kyc_status, server_default="pending", index=True),
        sa.Column("kyc_verified_at", sa.DateTime, nullable=True),
        sa.Column("kyc_notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, onupdate=sa.func.now()),
    )

    # ── payout_requests ──
    op.create_table(
        "payout_requests",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("partner_id", sa.Integer, sa.ForeignKey("partners.id"), nullable=False, index=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("provider_account_id", sa.Integer, sa.ForeignKey("provider_accounts.id"), nullable=True),
        sa.Column("gross_amount", sa.Float, nullable=False),
        sa.Column("jeturing_commission_pct", sa.Float, server_default="15.0"),
        sa.Column("jeturing_commission", sa.Float, server_default="0"),
        sa.Column("mercury_fee", sa.Float, server_default="0"),
        sa.Column("net_amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("transfer_type", sa.String(10), server_default="ach"),
        sa.Column("mercury_transfer_id", sa.String(100), nullable=True, index=True),
        sa.Column("estimated_delivery", sa.DateTime, nullable=True),
        sa.Column("status", payout_status, server_default="pending", index=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("authorized_by", sa.String(150), nullable=True),
        sa.Column("authorized_at", sa.DateTime, nullable=True),
        sa.Column("executed_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("failed_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index("ix_payout_partner_status", "payout_requests", ["partner_id", "status"])
    op.create_index("ix_payout_created", "payout_requests", ["created_at"])

    # ── payment_events ──
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("payout_id", sa.Integer, sa.ForeignKey("payout_requests.id"), nullable=True),
        sa.Column("amount", sa.Float, nullable=True),
        sa.Column("metadata_json", postgresql.JSON, server_default="{}"),
        sa.Column("actor", sa.String(150), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_payment_events_type_time", "payment_events", ["event_type", "created_at"])


def downgrade() -> None:
    op.drop_table("payment_events")
    op.drop_table("payout_requests")
    op.drop_table("provider_accounts")

    op.execute("DROP TYPE IF EXISTS payoutstatus")
    op.execute("DROP TYPE IF EXISTS kycstatus")
