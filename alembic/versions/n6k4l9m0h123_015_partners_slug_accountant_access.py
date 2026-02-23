"""015 Add partners.slug and accountant_tenant_access table

Revision ID: n6k4l9m0h123
Revises: m5j3k8l9g012
Create Date: 2026-02-23 02:35:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'n6k4l9m0h123'
down_revision = 'm5j3k8l9g012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── partners.slug ──
    op.add_column('partners', sa.Column('slug', sa.String(100), nullable=True))
    op.create_index('ix_partners_slug', 'partners', ['slug'], unique=True)

    # ── accountant_tenant_access table ──
    # The enum type 'accountantaccesslevel' already exists in the DB (created by model metadata).
    # Use sa.VARCHAR and a CHECK constraint instead to avoid duplication errors.
    op.create_table(
        'accountant_tenant_access',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('accountant_id', sa.Integer(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_level', sa.VARCHAR(20), server_default='readonly'),
        sa.Column('granted_by', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.UniqueConstraint('accountant_id', 'tenant_id', name='uq_accountant_tenant'),
    )
    op.create_index('ix_accountant_tenant_access_id', 'accountant_tenant_access', ['id'])


def downgrade() -> None:
    op.drop_table('accountant_tenant_access')
    sa.Enum('readonly', 'readwrite', 'full', name='accountantaccesslevel').drop(op.get_bind(), checkfirst=True)
    op.drop_index('ix_partners_slug', table_name='partners')
    op.drop_column('partners', 'slug')
