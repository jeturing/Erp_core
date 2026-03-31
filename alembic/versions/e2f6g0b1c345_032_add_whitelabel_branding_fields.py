"""032 add white-label branding fields to partners and branding profiles

Revision ID: e2f6g0b1c345
Revises: d1e5f9a0b234
Create Date: 2025-07-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2f6g0b1c345'
down_revision = 'd1e5f9a0b234'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- partners table ---
    op.add_column(
        'partners',
        sa.Column('white_label_enabled', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'partners',
        sa.Column(
            'brand_profile_id',
            sa.Integer(),
            sa.ForeignKey('partner_branding_profiles.id', ondelete='SET NULL'),
            nullable=True
        )
    )
    op.create_index(
        'ix_partners_brand_profile_id',
        'partners',
        ['brand_profile_id']
    )

    # --- partner_branding_profiles table ---
    op.add_column(
        'partner_branding_profiles',
        sa.Column('portal_url', sa.String(500), nullable=True)
    )
    op.add_column(
        'partner_branding_profiles',
        sa.Column('custom_domain', sa.String(255), nullable=True)
    )
    op.add_column(
        'partner_branding_profiles',
        sa.Column('terms_url', sa.String(500), nullable=True)
    )
    op.add_column(
        'partner_branding_profiles',
        sa.Column('privacy_url', sa.String(500), nullable=True)
    )
    op.create_unique_constraint(
        'uq_partner_branding_profiles_custom_domain',
        'partner_branding_profiles',
        ['custom_domain']
    )


def downgrade() -> None:
    # --- partner_branding_profiles table ---
    op.drop_constraint(
        'uq_partner_branding_profiles_custom_domain',
        'partner_branding_profiles',
        type_='unique'
    )
    op.drop_column('partner_branding_profiles', 'privacy_url')
    op.drop_column('partner_branding_profiles', 'terms_url')
    op.drop_column('partner_branding_profiles', 'custom_domain')
    op.drop_column('partner_branding_profiles', 'portal_url')

    # --- partners table ---
    op.drop_index('ix_partners_brand_profile_id', table_name='partners')
    op.drop_column('partners', 'brand_profile_id')
    op.drop_column('partners', 'white_label_enabled')
