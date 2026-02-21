"""007 - Onboarding config table

Table for admin-configurable onboarding flow: steps, visible plans,
portal menu, welcome texts, account management flags and e-CF countries.

Revision ID: f8c6d1e2a345
Revises: e7b5c9d0f123
Create Date: 2025-06-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'f8c6d1e2a345'
down_revision = 'e7b5c9d0f123'
branch_labels = None
depends_on = None

DEFAULT_STEPS = '[{"step":0,"key":"password","label":"Contraseña","required":true,"visible":true,"condition":null},{"step":1,"key":"profile","label":"Perfil","required":true,"visible":true,"condition":null},{"step":2,"key":"ecf","label":"Fiscal (RD)","required":false,"visible":true,"condition":{"country_in":["DO"]}},{"step":3,"key":"confirm","label":"Confirmación","required":true,"visible":true,"condition":null}]'
DEFAULT_PLANS = '["basic","pro","enterprise"]'
DEFAULT_MENU  = '[{"key":"dashboard","label":"Mi Cuenta","icon":"User","visible":true,"order":1},{"key":"billing","label":"Facturación","icon":"CreditCard","visible":true,"order":2},{"key":"domains","label":"Dominios","icon":"Globe","visible":true,"order":3},{"key":"support","label":"Soporte","icon":"HelpCircle","visible":true,"order":4},{"key":"settings","label":"Ajustes","icon":"Settings","visible":true,"order":5}]'
DEFAULT_ECF   = '["DO"]'


def upgrade() -> None:
    op.create_table(
        'onboarding_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('config_key', sa.String(100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False, server_default='Onboarding Principal'),
        sa.Column('steps_config', sa.JSON(), nullable=False, server_default=DEFAULT_STEPS),
        sa.Column('visible_plans', sa.JSON(), nullable=False, server_default=DEFAULT_PLANS),
        sa.Column('portal_menu', sa.JSON(), nullable=False, server_default=DEFAULT_MENU),
        sa.Column('welcome_title', sa.String(300), server_default='¡Bienvenido a Sajet ERP!'),
        sa.Column('welcome_subtitle', sa.String(500), server_default='Configure su cuenta para comenzar.'),
        sa.Column('allow_plan_change', sa.Boolean(), server_default='true'),
        sa.Column('allow_cancel', sa.Boolean(), server_default='true'),
        sa.Column('allow_email_change', sa.Boolean(), server_default='false'),
        sa.Column('show_invoices', sa.Boolean(), server_default='true'),
        sa.Column('show_usage', sa.Boolean(), server_default='true'),
        sa.Column('ecf_countries', sa.JSON(), nullable=False, server_default=DEFAULT_ECF),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('onboarding_config')
