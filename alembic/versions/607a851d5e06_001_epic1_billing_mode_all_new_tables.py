"""001_epic1_billing_mode_all_new_tables

Revision ID: 607a851d5e06
Revises: 4cdf70375180
Create Date: 2026-02-18 20:33:23.500936

Creates all new tables and adds billing_mode columns to subscriptions.
Tables already in DB: customers, subscriptions, stripe_events, custom_domains,
    proxmox_nodes, lxc_containers, tenant_deployments, resource_metrics, system_config
Tables to CREATE: plans, service_catalog, partners, leads, commissions, quotations,
    module_catalog, module_packages, module_package_items, seat_events, seat_high_water,
    invoices, settlement_periods, settlement_lines, infra_assets, reconciliation_runs,
    work_orders, audit_events, partner_branding_profiles
ALTER: subscriptions (add billing_mode, invoice_issuer, collector, payer_type,
    owner_partner_id, package_id)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '607a851d5e06'
down_revision: Union[str, None] = '4cdf70375180'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create enum types ──
    billingmode = sa.Enum('JETURING_DIRECT_SUBSCRIPTION', 'PARTNER_DIRECT', 'PARTNER_PAYS_FOR_CLIENT', 'LEGACY_IMPORTED', name='billingmode')
    billingmode.create(op.get_bind(), checkfirst=True)

    invoiceissuer = sa.Enum('JETURING', 'PARTNER', name='invoiceissuer')
    invoiceissuer.create(op.get_bind(), checkfirst=True)

    collectortype = sa.Enum('STRIPE_DIRECT', 'STRIPE_CONNECT', 'PARTNER_EXTERNAL', name='collectortype')
    collectortype.create(op.get_bind(), checkfirst=True)

    payertype = sa.Enum('CLIENT', 'PARTNER', name='payertype')
    payertype.create(op.get_bind(), checkfirst=True)

    seateventtype = sa.Enum('USER_CREATED', 'USER_DEACTIVATED', 'USER_REACTIVATED', 'FIRST_LOGIN', 'HWM_SNAPSHOT', name='seateventtype')
    seateventtype.create(op.get_bind(), checkfirst=True)

    invoicestatus = sa.Enum('draft', 'issued', 'paid', 'overdue', 'void', 'credited', name='invoicestatus')
    invoicestatus.create(op.get_bind(), checkfirst=True)

    invoicetype = sa.Enum('SUBSCRIPTION', 'SETUP', 'ADDON', 'INTERCOMPANY', 'CREDIT_NOTE', name='invoicetype')
    invoicetype.create(op.get_bind(), checkfirst=True)

    settlementstatus = sa.Enum('draft', 'pending_approval', 'approved', 'transferred', 'disputed', name='settlementstatus')
    settlementstatus.create(op.get_bind(), checkfirst=True)

    workorderstatus = sa.Enum('requested', 'approved', 'in_progress', 'completed', 'rejected', 'cancelled', name='workorderstatus')
    workorderstatus.create(op.get_bind(), checkfirst=True)

    plantype = sa.Enum('basic', 'pro', 'enterprise', name='plantype')
    plantype.create(op.get_bind(), checkfirst=True)

    billingscenario = sa.Enum('jeturing_collects', 'partner_collects', name='billingscenario')
    billingscenario.create(op.get_bind(), checkfirst=True)

    partnerstatus = sa.Enum('pending', 'active', 'suspended', 'terminated', name='partnerstatus')
    partnerstatus.create(op.get_bind(), checkfirst=True)

    leadstatus = sa.Enum('new', 'contacted', 'qualified', 'in_qualification', 'proposal', 'won', 'tenant_requested', 'provisioning_running', 'tenant_ready', 'invoiced', 'active', 'suspended', 'closed', 'lost', 'invalid', name='leadstatus')
    leadstatus.create(op.get_bind(), checkfirst=True)

    commissionstatus = sa.Enum('pending', 'approved', 'paid', 'disputed', 'offset', name='commissionstatus')
    commissionstatus.create(op.get_bind(), checkfirst=True)

    quotationstatus = sa.Enum('draft', 'sent', 'accepted', 'rejected', 'expired', 'invoiced', name='quotationstatus')
    quotationstatus.create(op.get_bind(), checkfirst=True)

    servicecategory = sa.Enum('saas_platform', 'saas_support', 'core_financiero', 'vciso', 'soc', 'cloud_devops', 'payments_pos', name='servicecategory')
    servicecategory.create(op.get_bind(), checkfirst=True)

    # ── plans ──
    op.create_table('plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('base_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('price_per_user', sa.Float(), nullable=False, server_default='0'),
        sa.Column('included_users', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_users', sa.Integer(), server_default='0'),
        sa.Column('max_domains', sa.Integer(), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('stripe_price_id', sa.String(100)),
        sa.Column('stripe_product_id', sa.String(100)),
        sa.Column('features', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── service_catalog ──
    op.create_table('service_catalog',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category', servicecategory, nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('price_monthly', sa.Float(), nullable=False),
        sa.Column('price_max', sa.Float()),
        sa.Column('is_addon', sa.Boolean(), server_default='false'),
        sa.Column('requires_service_id', sa.Integer(), sa.ForeignKey('service_catalog.id')),
        sa.Column('min_quantity', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── partners ──
    op.create_table('partners',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), unique=True),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('legal_name', sa.String(200)),
        sa.Column('tax_id', sa.String(50)),
        sa.Column('contact_name', sa.String(150)),
        sa.Column('contact_email', sa.String(150), nullable=False),
        sa.Column('phone', sa.String(50)),
        sa.Column('country', sa.String(100)),
        sa.Column('address', sa.Text()),
        sa.Column('billing_scenario', billingscenario, server_default='jeturing_collects'),
        sa.Column('commission_rate', sa.Float(), server_default='50.0'),
        sa.Column('margin_cap', sa.Float(), server_default='30.0'),
        sa.Column('status', partnerstatus, server_default='pending'),
        sa.Column('portal_access', sa.Boolean(), server_default='true'),
        sa.Column('stripe_account_id', sa.String(100)),
        sa.Column('stripe_onboarding_complete', sa.Boolean(), server_default='false'),
        sa.Column('stripe_charges_enabled', sa.Boolean(), server_default='false'),
        sa.Column('contract_signed_at', sa.DateTime()),
        sa.Column('contract_reference', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── leads ──
    op.create_table('leads',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('contact_name', sa.String(150)),
        sa.Column('contact_email', sa.String(150)),
        sa.Column('phone', sa.String(50)),
        sa.Column('country', sa.String(100)),
        sa.Column('status', leadstatus, server_default='new'),
        sa.Column('notes', sa.Text()),
        sa.Column('estimated_monthly_value', sa.Float(), server_default='0'),
        sa.Column('converted_customer_id', sa.Integer(), sa.ForeignKey('customers.id')),
        sa.Column('converted_at', sa.DateTime()),
        sa.Column('lost_reason', sa.String(200)),
        sa.Column('registered_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── commissions ──
    op.create_table('commissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id')),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id')),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('gross_revenue', sa.Float(), server_default='0'),
        sa.Column('net_revenue', sa.Float(), server_default='0'),
        sa.Column('deductions_json', sa.Text()),
        sa.Column('partner_amount', sa.Float(), server_default='0'),
        sa.Column('jeturing_amount', sa.Float(), server_default='0'),
        sa.Column('status', commissionstatus, server_default='pending'),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('payment_reference', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── quotations ──
    op.create_table('quotations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quote_number', sa.String(20), unique=True, nullable=False),
        sa.Column('created_by_partner_id', sa.Integer(), sa.ForeignKey('partners.id')),
        sa.Column('created_by_admin', sa.Boolean(), server_default='false'),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id')),
        sa.Column('prospect_name', sa.String(200)),
        sa.Column('prospect_email', sa.String(150)),
        sa.Column('prospect_company', sa.String(200)),
        sa.Column('prospect_phone', sa.String(50)),
        sa.Column('lines_json', sa.Text()),
        sa.Column('subtotal', sa.Float(), server_default='0'),
        sa.Column('partner_margin', sa.Float(), server_default='0'),
        sa.Column('total_monthly', sa.Float(), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('status', quotationstatus, server_default='draft'),
        sa.Column('valid_until', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('terms', sa.Text()),
        sa.Column('sent_at', sa.DateTime()),
        sa.Column('accepted_at', sa.DateTime()),
        sa.Column('rejected_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── module_catalog ──
    op.create_table('module_catalog',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('technical_name', sa.String(150), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(100)),
        sa.Column('version', sa.String(20), server_default='17.0.1.0'),
        sa.Column('is_core', sa.Boolean(), server_default='false'),
        sa.Column('partner_allowed', sa.Boolean(), server_default='true'),
        sa.Column('price_monthly', sa.Float(), server_default='0'),
        sa.Column('requires_module_id', sa.Integer(), sa.ForeignKey('module_catalog.id')),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── module_packages ──
    op.create_table('module_packages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(150), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('plan_type', plantype),
        sa.Column('base_price_monthly', sa.Float(), server_default='0'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('module_list', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── module_package_items ──
    op.create_table('module_package_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('module_packages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.Integer(), sa.ForeignKey('module_catalog.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_optional', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('package_id', 'module_id', name='uq_package_module'),
    )

    # ── seat_events ──
    op.create_table('seat_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('event_type', seateventtype, nullable=False),
        sa.Column('odoo_user_id', sa.Integer()),
        sa.Column('odoo_login', sa.String(150)),
        sa.Column('user_count_after', sa.Integer(), nullable=False),
        sa.Column('is_billable', sa.Boolean(), server_default='false'),
        sa.Column('grace_expires_at', sa.DateTime()),
        sa.Column('source', sa.String(50), server_default='webhook'),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_seat_events_created_at', 'seat_events', ['created_at'])

    # ── seat_high_water ──
    op.create_table('seat_high_water',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('period_date', sa.DateTime(), nullable=False),
        sa.Column('hwm_count', sa.Integer(), nullable=False),
        sa.Column('stripe_qty_updated', sa.Boolean(), server_default='false'),
        sa.Column('stripe_qty_updated_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('subscription_id', 'period_date', name='uq_sub_period'),
    )
    op.create_index('ix_seat_hwm_sub_date', 'seat_high_water', ['subscription_id', 'period_date'])

    # ── invoices ──
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('invoice_number', sa.String(30), unique=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id')),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id')),
        sa.Column('invoice_type', invoicetype, server_default='SUBSCRIPTION'),
        sa.Column('billing_mode', billingmode),
        sa.Column('issuer', invoiceissuer, server_default='JETURING'),
        sa.Column('subtotal', sa.Float(), server_default='0'),
        sa.Column('tax_amount', sa.Float(), server_default='0'),
        sa.Column('total', sa.Float(), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('lines_json', sa.JSON()),
        sa.Column('stripe_invoice_id', sa.String(100)),
        sa.Column('stripe_payment_intent_id', sa.String(100)),
        sa.Column('status', invoicestatus, server_default='draft'),
        sa.Column('issued_at', sa.DateTime()),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── settlement_periods ──
    op.create_table('settlement_periods',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('gross_revenue', sa.Float(), server_default='0'),
        sa.Column('net_revenue', sa.Float(), server_default='0'),
        sa.Column('jeturing_share', sa.Float(), server_default='0'),
        sa.Column('partner_share', sa.Float(), server_default='0'),
        sa.Column('offset_amount', sa.Float(), server_default='0'),
        sa.Column('final_partner_payout', sa.Float(), server_default='0'),
        sa.Column('status', settlementstatus, server_default='draft'),
        sa.Column('approved_by', sa.String(100)),
        sa.Column('transfer_reference', sa.String(200)),
        sa.Column('transferred_at', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('partner_id', 'period_start', name='uq_partner_period'),
    )

    # ── settlement_lines ──
    op.create_table('settlement_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('settlement_id', sa.Integer(), sa.ForeignKey('settlement_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id')),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id')),
        sa.Column('description', sa.String(300), nullable=False),
        sa.Column('gross_amount', sa.Float(), server_default='0'),
        sa.Column('stripe_fee', sa.Float(), server_default='0'),
        sa.Column('refunds', sa.Float(), server_default='0'),
        sa.Column('chargebacks', sa.Float(), server_default='0'),
        sa.Column('net_amount', sa.Float(), server_default='0'),
        sa.Column('jeturing_amount', sa.Float(), server_default='0'),
        sa.Column('partner_amount', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── infra_assets ──
    op.create_table('infra_assets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id')),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('asset_reference', sa.String(200), nullable=False),
        sa.Column('monthly_cost', sa.Float(), server_default='0'),
        sa.Column('is_billable', sa.Boolean(), server_default='true'),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── reconciliation_runs ──
    op.create_table('reconciliation_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('stripe_total', sa.Float(), server_default='0'),
        sa.Column('local_total', sa.Float(), server_default='0'),
        sa.Column('discrepancy', sa.Float(), server_default='0'),
        sa.Column('discrepancy_details', sa.JSON()),
        sa.Column('status', sa.String(20), server_default='completed'),
        sa.Column('run_by', sa.String(100), server_default='cron'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── work_orders ──
    op.create_table('work_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_number', sa.String(30), unique=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id')),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id')),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id')),
        sa.Column('work_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('parameters_json', sa.JSON()),
        sa.Column('status', workorderstatus, server_default='requested'),
        sa.Column('requested_by', sa.String(150), nullable=False),
        sa.Column('approved_by', sa.String(150)),
        sa.Column('completed_by', sa.String(150)),
        sa.Column('requested_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('result_json', sa.JSON()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── audit_events ──
    op.create_table('audit_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.Integer()),
        sa.Column('actor_username', sa.String(150)),
        sa.Column('actor_role', sa.String(50)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('resource', sa.String(200)),
        sa.Column('action', sa.String(100)),
        sa.Column('status', sa.String(20), server_default='success'),
        sa.Column('details', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'])
    op.create_index('ix_audit_type_created', 'audit_events', ['event_type', 'created_at'])
    op.create_index('ix_audit_actor_created', 'audit_events', ['actor_username', 'created_at'])

    # ── partner_branding_profiles ──
    op.create_table('partner_branding_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), unique=True, nullable=False),
        sa.Column('brand_name', sa.String(200)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('favicon_url', sa.String(500)),
        sa.Column('primary_color', sa.String(7), server_default='#4F46E5'),
        sa.Column('secondary_color', sa.String(7), server_default='#7C3AED'),
        sa.Column('support_email', sa.String(200)),
        sa.Column('support_url', sa.String(500)),
        sa.Column('custom_css', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── ALTER subscriptions: add billing columns ──
    op.add_column('subscriptions', sa.Column('billing_mode', billingmode))
    op.add_column('subscriptions', sa.Column('invoice_issuer', invoiceissuer))
    op.add_column('subscriptions', sa.Column('collector', collectortype))
    op.add_column('subscriptions', sa.Column('payer_type', payertype))
    op.add_column('subscriptions', sa.Column('owner_partner_id', sa.Integer(), sa.ForeignKey('partners.id')))
    op.add_column('subscriptions', sa.Column('package_id', sa.Integer(), sa.ForeignKey('module_packages.id')))

    # Set defaults on existing rows
    op.execute("UPDATE subscriptions SET billing_mode = 'JETURING_DIRECT_SUBSCRIPTION' WHERE billing_mode IS NULL")
    op.execute("UPDATE subscriptions SET invoice_issuer = 'JETURING' WHERE invoice_issuer IS NULL")
    op.execute("UPDATE subscriptions SET collector = 'STRIPE_DIRECT' WHERE collector IS NULL")
    op.execute("UPDATE subscriptions SET payer_type = 'CLIENT' WHERE payer_type IS NULL")


def downgrade() -> None:
    op.drop_column('subscriptions', 'package_id')
    op.drop_column('subscriptions', 'owner_partner_id')
    op.drop_column('subscriptions', 'payer_type')
    op.drop_column('subscriptions', 'collector')
    op.drop_column('subscriptions', 'invoice_issuer')
    op.drop_column('subscriptions', 'billing_mode')

    op.drop_table('partner_branding_profiles')
    op.drop_table('audit_events')
    op.drop_table('work_orders')
    op.drop_table('reconciliation_runs')
    op.drop_table('infra_assets')
    op.drop_table('settlement_lines')
    op.drop_table('settlement_periods')
    op.drop_table('invoices')
    op.drop_table('seat_high_water')
    op.drop_table('seat_events')
    op.drop_table('module_package_items')
    op.drop_table('module_packages')
    op.drop_table('module_catalog')
    op.drop_table('quotations')
    op.drop_table('commissions')
    op.drop_table('leads')
    op.drop_table('partners')
    op.drop_table('service_catalog')
    op.drop_table('plans')

    # Drop enum types
    for name in ['workorderstatus', 'settlementstatus', 'invoicetype', 'invoicestatus',
                 'seateventtype', 'payertype', 'collectortype', 'invoiceissuer', 'billingmode',
                 'servicecategory', 'quotationstatus', 'commissionstatus', 'leadstatus',
                 'partnerstatus', 'billingscenario', 'plantype']:
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
