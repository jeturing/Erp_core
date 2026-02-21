"""006 - Customer onboarding + RD e-CF fields

Adds onboarding flow tracking and Dominican Republic electronic invoicing
(e-CF / Comprobantes Fiscales Electrónicos) fields to the customers table.

Revision ID: e7b5c9d0f123
Revises: d6a4b7c8e901
Create Date: 2025-06-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7b5c9d0f123'
down_revision = 'd6a4b7c8e901'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Customer onboarding tracking ──
    op.add_column('customers', sa.Column('onboarding_step', sa.Integer(), server_default='0', nullable=False))
    op.add_column('customers', sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True))
    op.add_column('customers', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('customers', sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=True))

    # ── Dominican Republic e-CF fields ──
    op.add_column('customers', sa.Column('requires_ecf', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('customers', sa.Column('ecf_rnc', sa.String(length=20), nullable=True))           # RNC / Cédula
    op.add_column('customers', sa.Column('ecf_business_name', sa.String(length=250), nullable=True)) # Razón social fiscal
    op.add_column('customers', sa.Column('ecf_establishment_type', sa.String(length=50), nullable=True))  # persona_fisica, persona_juridica, zona_franca
    op.add_column('customers', sa.Column('ecf_ncf_series', sa.String(length=20), nullable=True))     # Serie NCF autorizada (B01, B02, B14, B15, etc.)
    op.add_column('customers', sa.Column('ecf_environment', sa.String(length=20), server_default='test_ecf', nullable=True))  # test_ecf, production
    op.add_column('customers', sa.Column('ecf_certificate_expiry', sa.DateTime(), nullable=True))    # Vencimiento del certificado digital DGII
    op.add_column('customers', sa.Column('ecf_authorized_sequences', sa.Text(), nullable=True))      # JSON: rangos de secuencias autorizadas por DGII


def downgrade() -> None:
    op.drop_column('customers', 'ecf_authorized_sequences')
    op.drop_column('customers', 'ecf_certificate_expiry')
    op.drop_column('customers', 'ecf_environment')
    op.drop_column('customers', 'ecf_ncf_series')
    op.drop_column('customers', 'ecf_establishment_type')
    op.drop_column('customers', 'ecf_business_name')
    op.drop_column('customers', 'ecf_rnc')
    op.drop_column('customers', 'requires_ecf')
    op.drop_column('customers', 'partner_id')
    op.drop_column('customers', 'country')
    op.drop_column('customers', 'onboarding_completed_at')
    op.drop_column('customers', 'onboarding_step')
