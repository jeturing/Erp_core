"""014 Add missing columns to plans and customers tables

plans: is_public, is_highlighted, trial_days, annual_discount_percent
customers: is_accountant, accountant_firm_name

Revision ID: m5j3k8l9g012
Revises: l4i2j7d8f901
Create Date: 2026-02-23 02:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'm5j3k8l9g012'
down_revision = 'l4i2j7d8f901'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Plans table ──
    op.add_column('plans', sa.Column('is_public', sa.Boolean(), server_default='true', nullable=True))
    op.add_column('plans', sa.Column('is_highlighted', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('plans', sa.Column('trial_days', sa.Integer(), server_default='14', nullable=True))
    op.add_column('plans', sa.Column('annual_discount_percent', sa.Float(), server_default='20', nullable=True))

    # ── Customers table ──
    op.add_column('customers', sa.Column('is_accountant', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('customers', sa.Column('accountant_firm_name', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('customers', 'accountant_firm_name')
    op.drop_column('customers', 'is_accountant')
    op.drop_column('plans', 'annual_discount_percent')
    op.drop_column('plans', 'trial_days')
    op.drop_column('plans', 'is_highlighted')
    op.drop_column('plans', 'is_public')
