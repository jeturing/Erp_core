"""020 allow multiple custom domains per tenant

Revision ID: s1p9q5u6v678
Revises: r0o8p4s5t567
Create Date: 2026-03-27

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "s1p9q5u6v678"
down_revision = "r0o8p4s5t567"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE custom_domains
        DROP CONSTRAINT IF EXISTS custom_domains_sajet_subdomain_key
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_custom_domains_sajet
        ON custom_domains (sajet_subdomain)
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE custom_domains
        ADD CONSTRAINT custom_domains_sajet_subdomain_key UNIQUE (sajet_subdomain)
        """
    )
