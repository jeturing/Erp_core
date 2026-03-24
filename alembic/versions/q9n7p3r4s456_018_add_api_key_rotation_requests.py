"""018 — Add api_key_rotation_requests table

Revision ID: q9n7p3r4s456
Revises: p8m6o2q3r345
Create Date: 2025-07-08
"""
from alembic import op
import sqlalchemy as sa

revision = "q9n7p3r4s456"
down_revision = "p8m6o2q3r345"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Enum para status de solicitud de rotación
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE apikeyrotationstatus AS ENUM ('pending','approved','rejected','expired'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$"
    ))

    op.create_table(
        "api_key_rotation_requests",
        sa.Column("id",          sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id",      sa.String(32),  nullable=False),
        sa.Column("tenant_id",   sa.Integer(), sa.ForeignKey("tenant_deployments.id"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("verify_token", sa.String(64), nullable=False),
        sa.Column("status",      sa.Text(), nullable=False, server_default="pending"),
        sa.Column("requested_by_email", sa.String(255), nullable=False),
        sa.Column("support_user_id",    sa.Integer(), nullable=True),
        sa.Column("reason",      sa.Text(), nullable=True),
        sa.Column("reject_note", sa.Text(), nullable=True),
        sa.Column("created_at",  sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at",  sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_unique_constraint("uq_rotation_verify_token", "api_key_rotation_requests", ["verify_token"])
    op.create_index("idx_rotation_req_key_status", "api_key_rotation_requests", ["key_id", "status"])
    op.create_index("idx_rotation_req_tenant",     "api_key_rotation_requests", ["tenant_id", "status"])


def downgrade():
    op.drop_table("api_key_rotation_requests")
    op.execute("DROP TYPE IF EXISTS apikeyrotationstatus")
