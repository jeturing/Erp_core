"""037 — Email rate limiting: plan fields + email_rate_limit_windows table

Revision ID: j7k5l0m1n234
Revises: c3e7f0a1b234
Create Date: 2026-04-07 00:00:00.000000

Agrega:
  1. 4 columnas en `plans`: max_emails_monthly, email_rate_per_minute,
     email_rate_per_hour, email_rate_per_day
  2. Tabla `email_rate_limit_windows` para ventanas deslizantes de rate limiting
     por tenant (minute / hour / day).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "j7k5l0m1n234"
down_revision = "c3e7f0a1b234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Columnas nuevas en plans ─────────────────────────────────────────
    with op.batch_alter_table("plans") as batch_op:
        batch_op.add_column(
            sa.Column("max_emails_monthly", sa.Integer(), nullable=True,
                      server_default="5000",
                      comment="Cuota mensual total de emails, 0=ilimitado")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_minute", sa.Integer(), nullable=True,
                      server_default="20",
                      comment="Máx emails por minuto (O365=30, Gmail~20)")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_hour", sa.Integer(), nullable=True,
                      server_default="500",
                      comment="Máx emails por hora (O365~600, Gmail~100)")
        )
        batch_op.add_column(
            sa.Column("email_rate_per_day", sa.Integer(), nullable=True,
                      server_default="2000",
                      comment="Máx emails por día (O365=10000, Gmail=2000)")
        )

    # ── 2. Tabla de ventanas deslizantes ────────────────────────────────────
    window_type_enum = sa.Enum("minute", "hour", "day",
                               name="ratelimitwindowtype")
    window_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_rate_limit_windows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_subdomain", sa.String(100), nullable=False),
        sa.Column("window_type", window_type_enum, nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end",   sa.DateTime(), nullable=False),
        sa.Column("emails_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )

    # Índices
    op.create_index(
        "ix_email_rate_limit_windows_tenant_subdomain",
        "email_rate_limit_windows", ["tenant_subdomain"]
    )
    op.create_index(
        "ix_email_rate_limit_windows_window_start",
        "email_rate_limit_windows", ["window_start"]
    )
    op.create_index(
        "ix_email_ratelimit_tenant_type",
        "email_rate_limit_windows", ["tenant_subdomain", "window_type"]
    )

    # Unique constraint
    op.create_unique_constraint(
        "uq_ratelimit_window_tenant_type_start",
        "email_rate_limit_windows",
        ["tenant_subdomain", "window_type", "window_start"],
    )


def downgrade() -> None:
    # Drop tabla de ventanas
    op.drop_table("email_rate_limit_windows")

    window_type_enum = sa.Enum("minute", "hour", "day",
                               name="ratelimitwindowtype")
    window_type_enum.drop(op.get_bind(), checkfirst=True)

    # Drop columnas de plans
    with op.batch_alter_table("plans") as batch_op:
        batch_op.drop_column("email_rate_per_day")
        batch_op.drop_column("email_rate_per_hour")
        batch_op.drop_column("email_rate_per_minute")
        batch_op.drop_column("max_emails_monthly")
