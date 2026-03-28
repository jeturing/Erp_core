"""024 add service metadata and customer addons

Revision ID: w5x3y9z0a123
Revises: v4w2x8y9z012
Create Date: 2026-03-28

Agrega soporte comercial para servicios adicionales:
  - service_code + metadata_json en service_catalog
  - customer_addon_subscriptions para compras desde portales
"""
from alembic import op
import sqlalchemy as sa

revision = 'w5x3y9z0a123'
down_revision = 'v4w2x8y9z012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('service_catalog', sa.Column('service_code', sa.String(length=100), nullable=True))
    op.add_column('service_catalog', sa.Column('metadata_json', sa.JSON(), nullable=True))
    op.create_index('ix_service_catalog_service_code', 'service_catalog', ['service_code'])

    op.create_table(
        'customer_addon_subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id', ondelete='SET NULL'), nullable=True),
        sa.Column('catalog_item_id', sa.Integer(), sa.ForeignKey('service_catalog.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_monthly', sa.Float(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('service_code', sa.String(length=100), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('acquired_via', sa.String(length=50), nullable=False, server_default='tenant_portal'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('last_invoiced_year', sa.Integer(), nullable=True),
        sa.Column('last_invoiced_month', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_customer_addon_customer', 'customer_addon_subscriptions', ['customer_id'])
    op.create_index('ix_customer_addon_subscription', 'customer_addon_subscriptions', ['subscription_id'])
    op.create_index('ix_customer_addon_partner', 'customer_addon_subscriptions', ['partner_id'])
    op.create_index('ix_customer_addon_catalog_item', 'customer_addon_subscriptions', ['catalog_item_id'])
    op.create_index('ix_customer_addon_status', 'customer_addon_subscriptions', ['status'])
    op.create_index('ix_customer_addon_service_code', 'customer_addon_subscriptions', ['service_code'])


def downgrade() -> None:
    op.drop_index('ix_customer_addon_service_code', table_name='customer_addon_subscriptions')
    op.drop_index('ix_customer_addon_status', table_name='customer_addon_subscriptions')
    op.drop_index('ix_customer_addon_catalog_item', table_name='customer_addon_subscriptions')
    op.drop_index('ix_customer_addon_partner', table_name='customer_addon_subscriptions')
    op.drop_index('ix_customer_addon_subscription', table_name='customer_addon_subscriptions')
    op.drop_index('ix_customer_addon_customer', table_name='customer_addon_subscriptions')
    op.drop_table('customer_addon_subscriptions')

    op.drop_index('ix_service_catalog_service_code', table_name='service_catalog')
    op.drop_column('service_catalog', 'metadata_json')
    op.drop_column('service_catalog', 'service_code')
