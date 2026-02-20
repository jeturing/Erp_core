"""004_add_plan_quota_fields

Phase 2 — Resource Quotas: Agrega columnas de cuota al modelo Plan.
  - max_storage_mb: Almacenamiento en MB (0=ilimitado)
  - max_websites: Websites Odoo (default 1)
  - max_companies: Multi-company (default 1)
  - max_backups: Backups retenidos (0=ilimitado)
  - max_api_calls_day: API calls diarias (0=ilimitado)

Revision ID: c5f3b6d7e890
Revises: b4e2a5f6c789
Create Date: 2025-07-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'c5f3b6d7e890'
down_revision = 'b4e2a5f6c789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('plans', sa.Column('max_storage_mb', sa.Integer(), server_default='0', nullable=True))
    op.add_column('plans', sa.Column('max_websites', sa.Integer(), server_default='1', nullable=True))
    op.add_column('plans', sa.Column('max_companies', sa.Integer(), server_default='1', nullable=True))
    op.add_column('plans', sa.Column('max_backups', sa.Integer(), server_default='0', nullable=True))
    op.add_column('plans', sa.Column('max_api_calls_day', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    op.drop_column('plans', 'max_api_calls_day')
    op.drop_column('plans', 'max_backups')
    op.drop_column('plans', 'max_companies')
    op.drop_column('plans', 'max_websites')
    op.drop_column('plans', 'max_storage_mb')
