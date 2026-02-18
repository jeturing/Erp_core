"""001_epic1_all_new_tables_and_billing_mode

Revision ID: e8deb7b3f057
Revises: 4cdf70375180
Create Date: 2026-02-18

Epic 1: BillingMode + all new tables for épicas 1-10.
Uses raw SQL with DO $$ blocks for IF NOT EXISTS on enums (PostgreSQL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8deb7b3f057'
down_revision: Union[str, None] = '4cdf70375180'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_if_not_exists(name: str, values: list[str]):
    """Create PostgreSQL enum type if it doesn't exist."""
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({vals});
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def upgrade() -> None:
    # ── 1. Create all enum types ──
    _create_enum_if_not_exists('billingmode', [
        'JETURING_DIRECT_SUBSCRIPTION', 'PARTNER_DIRECT',
        'PARTNER_PAYS_FOR_CLIENT', 'LEGACY_IMPORTED'])
    _create_enum_if_not_exists('invoiceissuer', ['JETURING', 'PARTNER'])
    _create_enum_if_not_exists('collectortype', [
        'STRIPE_DIRECT', 'STRIPE_CONNECT', 'PARTNER_EXTERNAL'])
    _create_enum_if_not_exists('payertype', ['CLIENT', 'PARTNER'])
    _create_enum_if_not_exists('seateventtype', [
        'USER_CREATED', 'USER_DEACTIVATED', 'USER_REACTIVATED',
        'FIRST_LOGIN', 'HWM_SNAPSHOT'])
    _create_enum_if_not_exists('invoicestatus', [
        'draft', 'issued', 'paid', 'overdue', 'void', 'credited'])
    _create_enum_if_not_exists('invoicetype', [
        'SUBSCRIPTION', 'SETUP', 'ADDON', 'INTERCOMPANY', 'CREDIT_NOTE'])
    _create_enum_if_not_exists('settlementstatus', [
        'draft', 'pending_approval', 'approved', 'transferred', 'disputed'])
    _create_enum_if_not_exists('workorderstatus', [
        'requested', 'approved', 'in_progress', 'completed', 'rejected', 'cancelled'])
    _create_enum_if_not_exists('plantype', ['basic', 'pro', 'enterprise'])
    _create_enum_if_not_exists('billingscenario', ['jeturing_collects', 'partner_collects'])
    _create_enum_if_not_exists('partnerstatus', ['pending', 'active', 'suspended', 'terminated'])
    _create_enum_if_not_exists('leadstatus', [
        'new', 'contacted', 'qualified', 'in_qualification', 'proposal', 'won',
        'tenant_requested', 'provisioning_running', 'tenant_ready', 'invoiced',
        'active', 'suspended', 'closed', 'lost', 'invalid'])
    _create_enum_if_not_exists('commissionstatus', [
        'pending', 'approved', 'paid', 'disputed', 'offset'])
    _create_enum_if_not_exists('quotationstatus', [
        'draft', 'sent', 'accepted', 'rejected', 'expired', 'invoiced'])
    _create_enum_if_not_exists('servicecategory', [
        'saas_platform', 'saas_support', 'core_financiero', 'vciso',
        'soc', 'cloud_devops', 'payments_pos'])

    # ── 2. Create tables (all use IF NOT EXISTS via raw SQL) ──

    op.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        display_name VARCHAR(100) NOT NULL,
        description TEXT,
        base_price FLOAT NOT NULL DEFAULT 0,
        price_per_user FLOAT NOT NULL DEFAULT 0,
        included_users INTEGER NOT NULL DEFAULT 1,
        max_users INTEGER DEFAULT 0,
        max_domains INTEGER DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'USD',
        stripe_price_id VARCHAR(100),
        stripe_product_id VARCHAR(100),
        features TEXT,
        is_active BOOLEAN DEFAULT true,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS service_catalog (
        id SERIAL PRIMARY KEY,
        category servicecategory NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        unit VARCHAR(50) NOT NULL,
        price_monthly FLOAT NOT NULL,
        price_max FLOAT,
        is_addon BOOLEAN DEFAULT false,
        requires_service_id INTEGER REFERENCES service_catalog(id),
        min_quantity INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT true,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS partners (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER UNIQUE REFERENCES customers(id),
        company_name VARCHAR(200) NOT NULL,
        legal_name VARCHAR(200),
        tax_id VARCHAR(50),
        contact_name VARCHAR(150),
        contact_email VARCHAR(150) NOT NULL,
        phone VARCHAR(50),
        country VARCHAR(100),
        address TEXT,
        billing_scenario billingscenario DEFAULT 'jeturing_collects',
        commission_rate FLOAT DEFAULT 50.0,
        margin_cap FLOAT DEFAULT 30.0,
        status partnerstatus DEFAULT 'pending',
        portal_access BOOLEAN DEFAULT true,
        stripe_account_id VARCHAR(100),
        stripe_onboarding_complete BOOLEAN DEFAULT false,
        stripe_charges_enabled BOOLEAN DEFAULT false,
        contract_signed_at TIMESTAMP,
        contract_reference VARCHAR(100),
        notes TEXT,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER NOT NULL REFERENCES partners(id),
        company_name VARCHAR(200) NOT NULL,
        contact_name VARCHAR(150),
        contact_email VARCHAR(150),
        phone VARCHAR(50),
        country VARCHAR(100),
        status leadstatus DEFAULT 'new',
        notes TEXT,
        estimated_monthly_value FLOAT DEFAULT 0,
        converted_customer_id INTEGER REFERENCES customers(id),
        converted_at TIMESTAMP,
        lost_reason VARCHAR(200),
        registered_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS commissions (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER NOT NULL REFERENCES partners(id),
        subscription_id INTEGER REFERENCES subscriptions(id),
        lead_id INTEGER REFERENCES leads(id),
        period_start TIMESTAMP NOT NULL,
        period_end TIMESTAMP NOT NULL,
        gross_revenue FLOAT DEFAULT 0,
        net_revenue FLOAT DEFAULT 0,
        deductions_json TEXT,
        partner_amount FLOAT DEFAULT 0,
        jeturing_amount FLOAT DEFAULT 0,
        status commissionstatus DEFAULT 'pending',
        paid_at TIMESTAMP,
        payment_reference VARCHAR(100),
        notes TEXT,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS quotations (
        id SERIAL PRIMARY KEY,
        quote_number VARCHAR(20) UNIQUE NOT NULL,
        created_by_partner_id INTEGER REFERENCES partners(id),
        created_by_admin BOOLEAN DEFAULT false,
        customer_id INTEGER REFERENCES customers(id),
        prospect_name VARCHAR(200),
        prospect_email VARCHAR(150),
        prospect_company VARCHAR(200),
        prospect_phone VARCHAR(50),
        lines_json TEXT,
        subtotal FLOAT DEFAULT 0,
        partner_margin FLOAT DEFAULT 0,
        total_monthly FLOAT DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'USD',
        status quotationstatus DEFAULT 'draft',
        valid_until TIMESTAMP,
        notes TEXT,
        terms TEXT,
        sent_at TIMESTAMP,
        accepted_at TIMESTAMP,
        rejected_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS module_catalog (
        id SERIAL PRIMARY KEY,
        technical_name VARCHAR(150) UNIQUE NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        description TEXT,
        category VARCHAR(100),
        version VARCHAR(20) DEFAULT '17.0.1.0',
        is_core BOOLEAN DEFAULT false,
        partner_allowed BOOLEAN DEFAULT true,
        price_monthly FLOAT DEFAULT 0,
        requires_module_id INTEGER REFERENCES module_catalog(id),
        is_active BOOLEAN DEFAULT true,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS module_packages (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) UNIQUE NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        description TEXT,
        plan_type plantype,
        base_price_monthly FLOAT DEFAULT 0,
        is_default BOOLEAN DEFAULT false,
        is_active BOOLEAN DEFAULT true,
        module_list JSONB,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS module_package_items (
        id SERIAL PRIMARY KEY,
        package_id INTEGER NOT NULL REFERENCES module_packages(id) ON DELETE CASCADE,
        module_id INTEGER NOT NULL REFERENCES module_catalog(id) ON DELETE CASCADE,
        is_optional BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT now(),
        CONSTRAINT uq_package_module UNIQUE (package_id, module_id)
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS seat_events (
        id SERIAL PRIMARY KEY,
        subscription_id INTEGER NOT NULL REFERENCES subscriptions(id),
        event_type seateventtype NOT NULL,
        odoo_user_id INTEGER,
        odoo_login VARCHAR(150),
        user_count_after INTEGER NOT NULL,
        is_billable BOOLEAN DEFAULT false,
        grace_expires_at TIMESTAMP,
        source VARCHAR(50) DEFAULT 'webhook',
        metadata_json JSONB,
        created_at TIMESTAMP DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_seat_events_created_at ON seat_events(created_at);
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS seat_high_water (
        id SERIAL PRIMARY KEY,
        subscription_id INTEGER NOT NULL REFERENCES subscriptions(id),
        period_date TIMESTAMP NOT NULL,
        hwm_count INTEGER NOT NULL,
        stripe_qty_updated BOOLEAN DEFAULT false,
        stripe_qty_updated_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT now(),
        CONSTRAINT uq_sub_period UNIQUE (subscription_id, period_date)
    );
    CREATE INDEX IF NOT EXISTS ix_seat_hwm_sub_date ON seat_high_water(subscription_id, period_date);
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY,
        invoice_number VARCHAR(30) UNIQUE NOT NULL,
        subscription_id INTEGER REFERENCES subscriptions(id),
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        partner_id INTEGER REFERENCES partners(id),
        invoice_type invoicetype DEFAULT 'SUBSCRIPTION',
        billing_mode billingmode,
        issuer invoiceissuer DEFAULT 'JETURING',
        subtotal FLOAT DEFAULT 0,
        tax_amount FLOAT DEFAULT 0,
        total FLOAT DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'USD',
        lines_json JSONB,
        stripe_invoice_id VARCHAR(100),
        stripe_payment_intent_id VARCHAR(100),
        status invoicestatus DEFAULT 'draft',
        issued_at TIMESTAMP,
        paid_at TIMESTAMP,
        due_date TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS settlement_periods (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER NOT NULL REFERENCES partners(id),
        period_start TIMESTAMP NOT NULL,
        period_end TIMESTAMP NOT NULL,
        gross_revenue FLOAT DEFAULT 0,
        net_revenue FLOAT DEFAULT 0,
        jeturing_share FLOAT DEFAULT 0,
        partner_share FLOAT DEFAULT 0,
        offset_amount FLOAT DEFAULT 0,
        final_partner_payout FLOAT DEFAULT 0,
        status settlementstatus DEFAULT 'draft',
        approved_by VARCHAR(100),
        transfer_reference VARCHAR(200),
        transferred_at TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now(),
        CONSTRAINT uq_partner_period UNIQUE (partner_id, period_start)
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS settlement_lines (
        id SERIAL PRIMARY KEY,
        settlement_id INTEGER NOT NULL REFERENCES settlement_periods(id) ON DELETE CASCADE,
        subscription_id INTEGER REFERENCES subscriptions(id),
        invoice_id INTEGER REFERENCES invoices(id),
        description VARCHAR(300) NOT NULL,
        gross_amount FLOAT DEFAULT 0,
        stripe_fee FLOAT DEFAULT 0,
        refunds FLOAT DEFAULT 0,
        chargebacks FLOAT DEFAULT 0,
        net_amount FLOAT DEFAULT 0,
        jeturing_amount FLOAT DEFAULT 0,
        partner_amount FLOAT DEFAULT 0,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS infra_assets (
        id SERIAL PRIMARY KEY,
        subscription_id INTEGER REFERENCES subscriptions(id),
        asset_type VARCHAR(50) NOT NULL,
        asset_reference VARCHAR(200) NOT NULL,
        monthly_cost FLOAT DEFAULT 0,
        is_billable BOOLEAN DEFAULT true,
        metadata_json JSONB,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_runs (
        id SERIAL PRIMARY KEY,
        period_start TIMESTAMP NOT NULL,
        period_end TIMESTAMP NOT NULL,
        stripe_total FLOAT DEFAULT 0,
        local_total FLOAT DEFAULT 0,
        discrepancy FLOAT DEFAULT 0,
        discrepancy_details JSONB,
        status VARCHAR(20) DEFAULT 'completed',
        run_by VARCHAR(100) DEFAULT 'cron',
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS work_orders (
        id SERIAL PRIMARY KEY,
        order_number VARCHAR(30) UNIQUE NOT NULL,
        subscription_id INTEGER REFERENCES subscriptions(id),
        customer_id INTEGER REFERENCES customers(id),
        partner_id INTEGER REFERENCES partners(id),
        work_type VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        parameters_json JSONB,
        status workorderstatus DEFAULT 'requested',
        requested_by VARCHAR(150) NOT NULL,
        approved_by VARCHAR(150),
        completed_by VARCHAR(150),
        requested_at TIMESTAMP DEFAULT now(),
        approved_at TIMESTAMP,
        completed_at TIMESTAMP,
        result_json JSONB,
        notes TEXT,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(50) NOT NULL,
        actor_id INTEGER,
        actor_username VARCHAR(150),
        actor_role VARCHAR(50),
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        resource VARCHAR(200),
        action VARCHAR(100),
        status VARCHAR(20) DEFAULT 'success',
        details JSONB,
        created_at TIMESTAMP DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events(event_type);
    CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events(created_at);
    CREATE INDEX IF NOT EXISTS ix_audit_type_created ON audit_events(event_type, created_at);
    CREATE INDEX IF NOT EXISTS ix_audit_actor_created ON audit_events(actor_username, created_at);
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS partner_branding_profiles (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER UNIQUE NOT NULL REFERENCES partners(id),
        brand_name VARCHAR(200),
        logo_url VARCHAR(500),
        favicon_url VARCHAR(500),
        primary_color VARCHAR(7) DEFAULT '#4F46E5',
        secondary_color VARCHAR(7) DEFAULT '#7C3AED',
        support_email VARCHAR(200),
        support_url VARCHAR(500),
        custom_css TEXT,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)

    # ── 3. ALTER subscriptions: add billing columns ──
    for col, typedef, default in [
        ('billing_mode', 'billingmode', "'JETURING_DIRECT_SUBSCRIPTION'"),
        ('invoice_issuer', 'invoiceissuer', "'JETURING'"),
        ('collector', 'collectortype', "'STRIPE_DIRECT'"),
        ('payer_type', 'payertype', "'CLIENT'"),
        ('owner_partner_id', 'INTEGER REFERENCES partners(id)', None),
        ('package_id', 'INTEGER REFERENCES module_packages(id)', None),
    ]:
        op.execute(f"""
            DO $$ BEGIN
                ALTER TABLE subscriptions ADD COLUMN {col} {typedef};
            EXCEPTION
                WHEN duplicate_column THEN null;
            END $$;
        """)
        if default:
            op.execute(f"UPDATE subscriptions SET {col} = {default} WHERE {col} IS NULL")


def downgrade() -> None:
    for col in ['package_id', 'owner_partner_id', 'payer_type', 'collector', 'invoice_issuer', 'billing_mode']:
        op.execute(f"ALTER TABLE subscriptions DROP COLUMN IF EXISTS {col}")

    for table in [
        'partner_branding_profiles', 'audit_events', 'work_orders',
        'reconciliation_runs', 'infra_assets', 'settlement_lines',
        'settlement_periods', 'invoices', 'seat_high_water', 'seat_events',
        'module_package_items', 'module_packages', 'module_catalog',
        'quotations', 'commissions', 'leads', 'partners',
        'service_catalog', 'plans',
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    for etype in [
        'workorderstatus', 'settlementstatus', 'invoicetype', 'invoicestatus',
        'seateventtype', 'payertype', 'collectortype', 'invoiceissuer', 'billingmode',
        'servicecategory', 'quotationstatus', 'commissionstatus', 'leadstatus',
        'partnerstatus', 'billingscenario',
    ]:
        op.execute(f"DROP TYPE IF EXISTS {etype}")
