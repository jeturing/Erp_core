"""021 add partner branding fields

Revision ID: t2q0r6v7w789
Revises: s1p9q5u6v678
Create Date: 2026-03-27

Agrega campos de branding white-label al modelo Partner:
  - brand_name          : Nombre del partner en emails
  - brand_color_primary : Color primario (hex)
  - brand_color_accent  : Color accent (hex)
  - logo_url            : URL pública del logo
  - smtp_from_name      : Nombre "From" en email
  - smtp_from_email     : Email "From" si partner tiene SMTP propio
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 't2q0r6v7w789'
down_revision = 's1p9q5u6v678'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('partners', sa.Column('brand_name',          sa.String(200), nullable=True))
    op.add_column('partners', sa.Column('brand_color_primary', sa.String(10),  nullable=True))
    op.add_column('partners', sa.Column('brand_color_accent',  sa.String(10),  nullable=True))
    op.add_column('partners', sa.Column('logo_url',            sa.String(500), nullable=True))
    op.add_column('partners', sa.Column('smtp_from_name',      sa.String(200), nullable=True))
    op.add_column('partners', sa.Column('smtp_from_email',     sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('partners', 'smtp_from_email')
    op.drop_column('partners', 'smtp_from_name')
    op.drop_column('partners', 'logo_url')
    op.drop_column('partners', 'brand_color_accent')
    op.drop_column('partners', 'brand_color_primary')
    op.drop_column('partners', 'brand_name')
