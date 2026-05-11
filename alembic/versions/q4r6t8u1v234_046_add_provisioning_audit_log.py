"""046 add provisioning audit log

Revision ID: q4r6t8u1v234
Revises: p1q2r3s4t901
Create Date: 2026-05-11
"""
from typing import Sequence, Union

from alembic import op  # type: ignore[reportMissingImports]
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "q4r6t8u1v234"
down_revision: Union[str, Sequence[str], None] = "p1q2r3s4t901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provisioning_audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subdomain", sa.String(length=100), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="internal"),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="started"),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_provisioning_audit_log_id", "provisioning_audit_log", ["id"], unique=False)
    op.create_index("ix_provisioning_audit_log_trace_id", "provisioning_audit_log", ["trace_id"], unique=False)
    op.create_index("ix_provisioning_audit_log_subdomain", "provisioning_audit_log", ["subdomain"], unique=False)
    op.create_index("ix_provisioning_audit_log_customer_id", "provisioning_audit_log", ["customer_id"], unique=False)
    op.create_index("ix_provisioning_audit_log_subscription_id", "provisioning_audit_log", ["subscription_id"], unique=False)
    op.create_index("ix_provisioning_audit_log_action", "provisioning_audit_log", ["action"], unique=False)
    op.create_index("ix_provisioning_audit_log_status", "provisioning_audit_log", ["status"], unique=False)
    op.create_index("ix_provisioning_audit_log_created_at", "provisioning_audit_log", ["created_at"], unique=False)

    op.create_index(
        "ix_provisioning_audit_subdomain_created",
        "provisioning_audit_log",
        ["subdomain", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_provisioning_audit_trace_created",
        "provisioning_audit_log",
        ["trace_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_provisioning_audit_status_created",
        "provisioning_audit_log",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_provisioning_audit_status_created", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_trace_created", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_subdomain_created", table_name="provisioning_audit_log")

    op.drop_index("ix_provisioning_audit_log_created_at", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_status", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_action", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_subscription_id", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_customer_id", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_subdomain", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_trace_id", table_name="provisioning_audit_log")
    op.drop_index("ix_provisioning_audit_log_id", table_name="provisioning_audit_log")

    op.drop_table("provisioning_audit_log")
