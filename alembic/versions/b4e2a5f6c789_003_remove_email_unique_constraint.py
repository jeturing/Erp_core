"""003_remove_email_unique_constraint

Múltiples tenants comparten el mismo admin login Odoo (admin@sajet.us),
por lo que email no puede ser UNIQUE en customers.

Revision ID: b4e2a5f6c789
Revises: a3f1c2d4e567
Create Date: 2026-02-19
"""
from alembic import op

# revision identifiers
revision = 'b4e2a5f6c789'
down_revision = 'a3f1c2d4e567'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the unique constraint on customers.email
    # The index name created by SQLAlchemy is ix_customers_email
    op.drop_index('ix_customers_email', table_name='customers')
    # Re-create as non-unique index for performance
    op.create_index('ix_customers_email', 'customers', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_customers_email', table_name='customers')
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
