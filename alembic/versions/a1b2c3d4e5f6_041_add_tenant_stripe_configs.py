"""041_add_tenant_stripe_configs

Revision ID: a1b2c3d4e5f6
Revises: 154b68678890
Create Date: 2026-04-24 18:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '154b68678890'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tenant_stripe_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(),
                  sa.ForeignKey('tenant_deployments.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('stripe_mode', sa.String(20)),
        sa.Column('stripe_account_count', sa.Integer(), default=0),
        sa.Column('stripe_account_type', sa.String(20)),
        sa.Column('connect_country', sa.String(2)),
        sa.Column('terminal_routing', sa.String(20), default='connect'),
        sa.Column('terminal_max_devices', sa.Integer(), default=0),
        sa.Column('feature_flags', sa.JSON(), nullable=True),
        sa.Column('fee_rules_count', sa.Integer(), default=0),
        sa.Column('last_transaction_at', sa.DateTime(), nullable=True),
        sa.Column('transactions_30d', sa.Integer(), default=0),
        sa.Column('transfers_30d_cents', sa.BigInteger(), default=0),
        sa.Column('refunds_30d_cents', sa.BigInteger(), default=0),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('tenant_id', 'source', name='uq_tenant_source'),
    )
    op.create_index('ix_tenant_stripe_configs_tenant', 'tenant_stripe_configs', ['tenant_id'])
    op.create_index('ix_tenant_stripe_configs_source', 'tenant_stripe_configs', ['source'])


def downgrade():
    op.drop_index('ix_tenant_stripe_configs_source', table_name='tenant_stripe_configs')
    op.drop_index('ix_tenant_stripe_configs_tenant', table_name='tenant_stripe_configs')
    op.drop_table('tenant_stripe_configs')
