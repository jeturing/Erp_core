"""022 add postal email usage table

Revision ID: u3r1s7w8x890
Revises: t2q0r6v7w789
Create Date: 2026-03-27

Crea la tabla postal_email_usage para:
  - Tracking de emails enviados por tenant via Postal
  - Cálculo de costo por envío (USD por email)
  - Base para billing de uso de correo electrónico
"""
from alembic import op
import sqlalchemy as sa

revision = 'u3r1s7w8x890'
down_revision = 't2q0r6v7w789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'postal_email_usage',
        sa.Column('id',                   sa.Integer(),    primary_key=True, index=True),
        sa.Column('tenant_subdomain',     sa.String(100),  nullable=False),
        sa.Column('customer_id',          sa.Integer(),    sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_year',          sa.Integer(),    nullable=False),
        sa.Column('period_month',         sa.Integer(),    nullable=False),
        sa.Column('emails_sent',          sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('emails_delivered',     sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('emails_bounced',       sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('emails_failed',        sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('cost_per_email',       sa.Float(),      nullable=False, server_default='0.00020'),
        sa.Column('total_cost_usd',       sa.Float(),      nullable=False, server_default='0.0'),
        sa.Column('postal_server_token',  sa.String(50),   nullable=True),
        sa.Column('last_synced_at',       sa.DateTime(),   nullable=True),
        sa.Column('is_billed',            sa.Boolean(),    nullable=False, server_default='false'),
        sa.Column('billed_at',            sa.DateTime(),   nullable=True),
        sa.Column('notes',                sa.Text(),       nullable=True),
        sa.Column('created_at',           sa.DateTime(),   server_default=sa.func.now()),
        sa.Column('updated_at',           sa.DateTime(),   server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_postal_email_usage_tenant',  'postal_email_usage', ['tenant_subdomain'])
    op.create_unique_constraint(
        'uq_postal_usage_tenant_period',
        'postal_email_usage',
        ['tenant_subdomain', 'period_year', 'period_month']
    )


def downgrade() -> None:
    op.drop_constraint('uq_postal_usage_tenant_period', 'postal_email_usage', type_='unique')
    op.drop_index('ix_postal_email_usage_tenant', 'postal_email_usage')
    op.drop_table('postal_email_usage')
