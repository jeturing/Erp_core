"""030 fix custom_domains sajet_subdomain index

Revision ID: c1d4e7f8g901
Revises: b0d5e8f1a678
Create Date: 2026-03-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "c1d4e7f8g901"
down_revision = "b0d5e8f1a678"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP INDEX IF EXISTS ix_custom_domains_sajet_subdomain")
    op.execute("DROP INDEX IF EXISTS idx_custom_domains_sajet")
    op.execute(
        """
        ALTER TABLE custom_domains
        DROP CONSTRAINT IF EXISTS custom_domains_sajet_subdomain_key
        """
    )
    op.create_index(
        "ix_custom_domains_sajet_subdomain",
        "custom_domains",
        ["sajet_subdomain"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_custom_domains_sajet_subdomain", table_name="custom_domains")
    op.create_index(
        "ix_custom_domains_sajet_subdomain",
        "custom_domains",
        ["sajet_subdomain"],
        unique=True,
    )
