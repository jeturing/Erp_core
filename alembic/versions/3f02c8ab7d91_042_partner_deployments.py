"""042 partner deployments

Revision ID: 3f02c8ab7d91
Revises: 154b68678890
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f02c8ab7d91"
down_revision: Union[str, Sequence[str], None] = "154b68678890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_deployments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("tenant_deployment_id", sa.Integer(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=True),
        sa.Column("contact_email", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("country_code", sa.String(length=10), nullable=True),
        sa.Column("subdomain", sa.String(length=100), nullable=False),
        sa.Column("plan_name", sa.String(length=50), nullable=False, server_default="basic"),
        sa.Column("user_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("billing_mode", sa.String(length=60), nullable=False, server_default="partner_direct"),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("blueprint_package_name", sa.String(length=150), nullable=True),
        sa.Column("blueprint_package_id", sa.Integer(), nullable=True),
        sa.Column("package_snapshot", sa.JSON(), nullable=True),
        sa.Column("kpis_json", sa.JSON(), nullable=True),
        sa.Column("checklist_json", sa.JSON(), nullable=True),
        sa.Column("event_log", sa.JSON(), nullable=True),
        sa.Column("current_phase", sa.String(length=40), nullable=False, server_default="strategy"),
        sa.Column("current_week", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="tenant_requested"),
        sa.Column("provisioning_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("invoice_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("handoff_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("tenant_url", sa.String(length=255), nullable=True),
        sa.Column("admin_login", sa.String(length=200), nullable=True),
        sa.Column("admin_password", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_ready_at", sa.DateTime(), nullable=True),
        sa.Column("invoiced_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_deployment_id"], ["tenant_deployments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["blueprint_package_id"], ["module_packages.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_partner_deployments_partner_id", "partner_deployments", ["partner_id"])
    op.create_index("ix_partner_deployments_lead_id", "partner_deployments", ["lead_id"])
    op.create_index("ix_partner_deployments_customer_id", "partner_deployments", ["customer_id"])
    op.create_index("ix_partner_deployments_subscription_id", "partner_deployments", ["subscription_id"])
    op.create_index("ix_partner_deployments_tenant_deployment_id", "partner_deployments", ["tenant_deployment_id"])
    op.create_index("ix_partner_deployments_invoice_id", "partner_deployments", ["invoice_id"])
    op.create_index("ix_partner_deployments_subdomain", "partner_deployments", ["subdomain"])
    op.create_index("ix_partner_deployments_status", "partner_deployments", ["status"])
    op.create_index("ix_partner_deployments_partner_status", "partner_deployments", ["partner_id", "status"])
    op.create_index("ix_partner_deployments_partner_phase", "partner_deployments", ["partner_id", "current_phase"])


def downgrade() -> None:
    op.drop_index("ix_partner_deployments_partner_phase", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_partner_status", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_status", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_subdomain", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_invoice_id", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_tenant_deployment_id", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_subscription_id", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_customer_id", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_lead_id", table_name="partner_deployments")
    op.drop_index("ix_partner_deployments_partner_id", table_name="partner_deployments")
    op.drop_table("partner_deployments")
