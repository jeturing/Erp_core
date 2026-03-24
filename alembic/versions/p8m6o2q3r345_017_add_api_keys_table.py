"""017 — Add api_keys and api_key_usage_logs tables

Revision ID: p8m6o2q3r345
Revises: o7l5n1p2q234
Create Date: 2025-07-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "p8m6o2q3r345"
down_revision = "o7l5n1p2q234"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ─── Enums (IF NOT EXISTS via SQL directo) ───────────────
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE apikeystatus AS ENUM ('active','revoked','expired','rotating'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE apikeyscope AS ENUM ('read_only','read_write','admin','custom'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE apikeytier AS ENUM ('free','standard','pro','enterprise'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$"
    ))

    # ─── Tabla principal ─────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id",          sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id",      sa.String(32),  nullable=False),
        sa.Column("key_hash",    sa.String(128), nullable=False),
        sa.Column("name",        sa.String(255), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),

        # Ownership
        sa.Column("tenant_id",   sa.Integer(), sa.ForeignKey("tenant_deployments.id"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"),          nullable=True),
        sa.Column("created_by",  sa.Integer(), nullable=True),

        # Estado / scope / tier  (usamos sa.Text + cast para reusar enums ya creados)
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("scope",  sa.Text(), nullable=False, server_default="read_only"),
        sa.Column("tier",   sa.Text(), nullable=False, server_default="standard"),

        # Permisos
        sa.Column("permissions",          sa.JSON(), nullable=False, server_default="[]"),

        # Rate limit overrides
        sa.Column("requests_per_minute",  sa.Integer(), nullable=True),
        sa.Column("requests_per_day",     sa.Integer(), nullable=True),
        sa.Column("monthly_quota_tokens", sa.Integer(), nullable=True),

        # Contadores
        sa.Column("usage_today",        sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usage_this_month",   sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_requests",     sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at",       sa.DateTime(), nullable=True),
        sa.Column("last_used_ip",       sa.String(45), nullable=True),

        # Ciclo de vida
        sa.Column("expires_at",          sa.DateTime(), nullable=True),
        sa.Column("created_at",          sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",          sa.DateTime(), nullable=True),
        sa.Column("rotated_at",          sa.DateTime(), nullable=True),
        sa.Column("rotation_old_key_id", sa.String(32), nullable=True),

        # Metadata
        sa.Column("tags",     sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
    )

    op.create_index("uq_api_keys_key_id", "api_keys", ["key_id"], unique=True)
    op.create_index("idx_api_keys_status_tier",   "api_keys", ["status", "tier"])
    op.create_index("idx_api_keys_customer",      "api_keys", ["customer_id", "status"])
    op.create_index("idx_api_keys_tenant",        "api_keys", ["tenant_id", "status"])

    # ─── Tabla de logs de uso ─────────────────────────────────
    op.create_table(
        "api_key_usage_logs",
        sa.Column("id",            sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id",        sa.String(32),  nullable=False),
        sa.Column("hour_bucket",   sa.DateTime(),  nullable=False),
        sa.Column("request_count", sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("token_count",   sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("error_count",   sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("endpoint",      sa.String(255), nullable=True),
        sa.Column("ip_address",    sa.String(45),  nullable=True),
    )

    op.create_unique_constraint(
        "uq_usage_key_hour_endpoint",
        "api_key_usage_logs",
        ["key_id", "hour_bucket", "endpoint"],
    )
    op.create_index("idx_usage_key_bucket", "api_key_usage_logs", ["key_id", "hour_bucket"])


def downgrade():
    op.drop_table("api_key_usage_logs")
    op.drop_table("api_keys")

    op.execute("DROP TYPE IF EXISTS apikeytier")
    op.execute("DROP TYPE IF EXISTS apikeyscope")
    op.execute("DROP TYPE IF EXISTS apikeystatus")
