"""029 plan governance fair use

Agrega campos de parametrización fair use y gobernanza de planes:
- customers.stock_sku_count
- customers.fair_use_enabled
- customers.last_usage_sync_at
- plans.quota_warning_percent
- plans.quota_recommend_percent
- plans.quota_block_percent
- plans.fair_use_new_customers_only
- partner_pricing_overrides.max_users_override
- partner_pricing_overrides.max_storage_mb_override
- partner_pricing_overrides.max_stock_sku_override

Clientes existentes quedan con fair_use_enabled = false.
Clientes nuevos usarán el default de aplicación definido en los flujos de alta.

Revision ID: b1d5e8f1a229
Revises: a9c4d7e0f128
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'b1d5e8f1a229'
down_revision = 'a9c4d7e0f128'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('customers', sa.Column('stock_sku_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('customers', sa.Column('fair_use_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('customers', sa.Column('last_usage_sync_at', sa.DateTime(), nullable=True))

    op.add_column('plans', sa.Column('quota_warning_percent', sa.Integer(), nullable=False, server_default='80'))
    op.add_column('plans', sa.Column('quota_recommend_percent', sa.Integer(), nullable=False, server_default='95'))
    op.add_column('plans', sa.Column('quota_block_percent', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('plans', sa.Column('fair_use_new_customers_only', sa.Boolean(), nullable=False, server_default=sa.true()))

    op.add_column('partner_pricing_overrides', sa.Column('max_users_override', sa.Integer(), nullable=True))
    op.add_column('partner_pricing_overrides', sa.Column('max_storage_mb_override', sa.Integer(), nullable=True))
    op.add_column('partner_pricing_overrides', sa.Column('max_stock_sku_override', sa.Integer(), nullable=True))

    op.execute("UPDATE customers SET fair_use_enabled = FALSE")


def downgrade() -> None:
    op.drop_column('partner_pricing_overrides', 'max_stock_sku_override')
    op.drop_column('partner_pricing_overrides', 'max_storage_mb_override')
    op.drop_column('partner_pricing_overrides', 'max_users_override')

    op.drop_column('plans', 'fair_use_new_customers_only')
    op.drop_column('plans', 'quota_block_percent')
    op.drop_column('plans', 'quota_recommend_percent')
    op.drop_column('plans', 'quota_warning_percent')

    op.drop_column('customers', 'last_usage_sync_at')
    op.drop_column('customers', 'fair_use_enabled')
    op.drop_column('customers', 'stock_sku_count')
