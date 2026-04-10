"""039 add api key audit logs

Revision ID: m9n0p1q2r678
Revises: k8l6m1n2o345
Create Date: 2026-04-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "m9n0p1q2r678"
down_revision: Union[str, Sequence[str], None] = "k8l6m1n2o345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_key_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key_id", sa.String(length=32), nullable=False),
        sa.Column("auth_mode", sa.String(length=32), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=16), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False, server_default=sa.text("200")),
        sa.Column("reject_reason", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_api_key_audit_logs_key_id", "api_key_audit_logs", ["key_id"], unique=False)
    op.create_index("ix_api_key_audit_logs_auth_mode", "api_key_audit_logs", ["auth_mode"], unique=False)
    op.create_index("ix_api_key_audit_logs_reject_reason", "api_key_audit_logs", ["reject_reason"], unique=False)
    op.create_index("ix_api_key_audit_logs_created_at", "api_key_audit_logs", ["created_at"], unique=False)
    op.create_index("idx_api_key_audit_key_time", "api_key_audit_logs", ["key_id", "created_at"], unique=False)
    op.create_index("idx_api_key_audit_status_time", "api_key_audit_logs", ["status_code", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_api_key_audit_status_time", table_name="api_key_audit_logs")
    op.drop_index("idx_api_key_audit_key_time", table_name="api_key_audit_logs")
    op.drop_index("ix_api_key_audit_logs_created_at", table_name="api_key_audit_logs")
    op.drop_index("ix_api_key_audit_logs_reject_reason", table_name="api_key_audit_logs")
    op.drop_index("ix_api_key_audit_logs_auth_mode", table_name="api_key_audit_logs")
    op.drop_index("ix_api_key_audit_logs_key_id", table_name="api_key_audit_logs")
    op.drop_table("api_key_audit_logs")
