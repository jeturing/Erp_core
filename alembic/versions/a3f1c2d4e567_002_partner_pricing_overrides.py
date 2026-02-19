"""002_partner_pricing_overrides

Add partner_pricing_overrides table and supportlevel enum.
Enables differentiated pricing per partner (e.g., Techeels partner SMB rates).

Revision ID: a3f1c2d4e567
Revises: e8deb7b3f057
Create Date: 2026-02-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a3f1c2d4e567'
down_revision = 'e8deb7b3f057'
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(name, values):
    """Creates a PostgreSQL ENUM type if it doesn't already exist."""
    op.execute(f"""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
            CREATE TYPE {name} AS ENUM ({', '.join(f"'{v}'" for v in values)});
        END IF;
    END$$;
    """)


def upgrade() -> None:
    # 1. Create supportlevel enum
    _create_enum_if_not_exists('supportlevel', [
        'helpdesk_only', 'priority', 'dedicated'
    ])

    # 2. Create partner_pricing_overrides table
    op.execute("""
    CREATE TABLE IF NOT EXISTS partner_pricing_overrides (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER NOT NULL REFERENCES partners(id) ON DELETE CASCADE,
        plan_name VARCHAR(50) NOT NULL,

        -- Price overrides (NULL = use global plan value)
        base_price_override FLOAT,
        price_per_user_override FLOAT,
        included_users_override INTEGER,

        -- Partner-specific rates
        setup_fee FLOAT DEFAULT 0,
        customization_hourly_rate FLOAT,
        support_level supportlevel DEFAULT 'helpdesk_only',
        ecf_passthrough BOOLEAN DEFAULT false,
        ecf_monthly_cost FLOAT,

        -- Metadata
        label VARCHAR(100),
        notes TEXT,
        is_active BOOLEAN DEFAULT true,
        valid_from TIMESTAMP,
        valid_until TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),

        CONSTRAINT uq_partner_plan_override UNIQUE (partner_id, plan_name)
    );
    """)

    # 3. Create index for fast lookups
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_partner_pricing_partner_plan
    ON partner_pricing_overrides(partner_id, plan_name);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS partner_pricing_overrides CASCADE;")
    op.execute("DROP TYPE IF EXISTS supportlevel;")
