"""005 - Partner portal auth fields + onboarding status

Revision ID: d6a4b7c8e901
Revises: c5f3b6d7e890
Create Date: 2026-02-21

Adds:
- partners.password_hash       → Credenciales propias del partner
- partners.portal_email        → Email de login del portal (puede diferir de contact_email)
- partners.onboarding_step     → Paso actual del onboarding wizard
- partners.onboarding_completed_at → Timestamp de onboarding completado
- partners.stripe_connect_return_url → URL de retorno post-KYC
- partners.last_login_at       → Último login
- partners.login_count         → Contador de logins
- partners.invited_at          → Fecha de invitación
- partners.invited_by          → Admin que invitó
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'd6a4b7c8e901'
down_revision = 'c5f3b6d7e890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Partner auth & portal fields
    op.add_column('partners', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('partners', sa.Column('portal_email', sa.String(200), nullable=True))
    op.add_column('partners', sa.Column('onboarding_step', sa.Integer(), server_default='0', nullable=False))
    op.add_column('partners', sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True))
    op.add_column('partners', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.add_column('partners', sa.Column('login_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('partners', sa.Column('invited_at', sa.DateTime(), nullable=True))
    op.add_column('partners', sa.Column('invited_by', sa.String(150), nullable=True))

    # Index for portal login lookups
    op.create_index('ix_partners_portal_email', 'partners', ['portal_email'], unique=True)
    op.create_index('ix_partners_contact_email', 'partners', ['contact_email'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_partners_contact_email', table_name='partners')
    op.drop_index('ix_partners_portal_email', table_name='partners')
    op.drop_column('partners', 'invited_by')
    op.drop_column('partners', 'invited_at')
    op.drop_column('partners', 'login_count')
    op.drop_column('partners', 'last_login_at')
    op.drop_column('partners', 'onboarding_completed_at')
    op.drop_column('partners', 'onboarding_step')
    op.drop_column('partners', 'portal_email')
    op.drop_column('partners', 'password_hash')
