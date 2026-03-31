"""033 create DSAM session monitoring tables

Revision ID: f3g7h1i2j456
Revises: e2f6g0b1c345
Create Date: 2026-07-15

Creates tables for Dynamic Session & Anti-Theft Monitor (DSAM):
- active_sessions: Snapshot de sesiones activas capturadas desde Redis
- session_security_rules: Reglas de seguridad configurables por tenant
- session_geo_events: Historial de accesos geográficos
- account_security_actions: Log de acciones de seguridad (playbook)
- tenant_session_configs: Configuración DSAM por tenant
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f3g7h1i2j456'
down_revision = 'e2f6g0b1c345'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ──
    session_rule_type = sa.Enum(
        'single_session', 'max_sessions', 'geo_restriction',
        'impossible_travel', 'ip_whitelist', 'time_restriction',
        name='sessionruletype',
    )
    session_action_type = sa.Enum(
        'session_terminated', 'account_locked', 'account_unlocked',
        'security_alert', 'impossible_travel_detected',
        'concurrent_session_blocked', 'rule_violation',
        name='sessionactiontype',
    )
    session_alert_severity = sa.Enum(
        'low', 'medium', 'high', 'critical',
        name='sessionalertseverity',
    )

    # ── active_sessions ──
    op.create_table(
        'active_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('redis_session_key', sa.String(255), unique=True, nullable=False),
        sa.Column('tenant_db', sa.String(100), nullable=False, index=True),
        sa.Column('odoo_uid', sa.Integer(), nullable=True),
        sa.Column('odoo_login', sa.String(150), nullable=True, index=True),
        sa.Column('user_display_name', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('geo_country', sa.String(100), nullable=True),
        sa.Column('geo_country_code', sa.String(3), nullable=True, index=True),
        sa.Column('geo_region', sa.String(100), nullable=True),
        sa.Column('geo_city', sa.String(100), nullable=True),
        sa.Column('geo_lat', sa.Float(), nullable=True),
        sa.Column('geo_lon', sa.Float(), nullable=True),
        sa.Column('session_start', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_polled_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_index('ix_active_sessions_tenant_user', 'active_sessions', ['tenant_db', 'odoo_login'])
    op.create_index('ix_active_sessions_country', 'active_sessions', ['geo_country_code'])
    op.create_index('ix_active_sessions_active', 'active_sessions', ['is_active', 'tenant_db'])

    # ── session_security_rules ──
    op.create_table(
        'session_security_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('rule_type', session_rule_type, nullable=False),
        sa.Column('tenant_db', sa.String(100), nullable=True, index=True),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('exempt_users', sa.JSON(), server_default='[]'),
        sa.Column('exempt_tenants', sa.JSON(), server_default='[]'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_sec_rules_type_tenant', 'session_security_rules', ['rule_type', 'tenant_db'])

    # ── session_geo_events ──
    op.create_table(
        'session_geo_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_db', sa.String(100), nullable=False, index=True),
        sa.Column('odoo_login', sa.String(150), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('geo_country', sa.String(100), nullable=True),
        sa.Column('geo_country_code', sa.String(3), nullable=True),
        sa.Column('geo_region', sa.String(100), nullable=True),
        sa.Column('geo_city', sa.String(100), nullable=True),
        sa.Column('geo_lat', sa.Float(), nullable=True),
        sa.Column('geo_lon', sa.Float(), nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('browser', sa.String(50), nullable=True),
        sa.Column('os_name', sa.String(50), nullable=True),
        sa.Column('event_at', sa.DateTime(), server_default=sa.func.now(), index=True),
    )
    op.create_index('ix_geo_events_user_time', 'session_geo_events', ['tenant_db', 'odoo_login', 'event_at'])
    op.create_index('ix_geo_events_country', 'session_geo_events', ['geo_country_code', 'event_at'])

    # ── account_security_actions ──
    op.create_table(
        'account_security_actions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('action_type', session_action_type, nullable=False),
        sa.Column('severity', session_alert_severity, server_default='medium'),
        sa.Column('tenant_db', sa.String(100), nullable=False, index=True),
        sa.Column('odoo_login', sa.String(150), nullable=True),
        sa.Column('odoo_uid', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('details', sa.JSON(), server_default='{}'),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_username', sa.String(150), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(150), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
    )
    op.create_index('ix_sec_actions_tenant_time', 'account_security_actions', ['tenant_db', 'created_at'])
    op.create_index('ix_sec_actions_type_sev', 'account_security_actions', ['action_type', 'severity'])
    op.create_index('ix_sec_actions_unresolved', 'account_security_actions', ['resolved', 'severity'])

    # ── tenant_session_configs ──
    op.create_table(
        'tenant_session_configs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_db', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('allow_multiple_sessions', sa.Boolean(), default=False),
        sa.Column('max_concurrent_sessions', sa.Integer(), default=1),
        sa.Column('enforce_geo_restrictions', sa.Boolean(), default=False),
        sa.Column('enforce_impossible_travel', sa.Boolean(), default=True),
        sa.Column('allowed_countries', sa.JSON(), server_default='[]'),
        sa.Column('session_timeout_minutes', sa.Integer(), default=480),
        sa.Column('notify_on_new_device', sa.Boolean(), default=True),
        sa.Column('seat_audit_enabled', sa.Boolean(), default=True),
        sa.Column('last_seat_audit_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('tenant_session_configs')
    op.drop_table('account_security_actions')
    op.drop_table('session_geo_events')
    op.drop_table('session_security_rules')
    op.drop_table('active_sessions')
    sa.Enum(name='sessionruletype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sessionactiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sessionalertseverity').drop(op.get_bind(), checkfirst=True)
