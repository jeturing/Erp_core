"""019 add last_password_changed_at to customers

Revision ID: r0o8p4s5t567
Revises: q9n7p3r4s456
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'r0o8p4s5t567'
down_revision = 'q9n7p3r4s456'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'customers',
        sa.Column('last_password_changed_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column('customers', 'last_password_changed_at')
