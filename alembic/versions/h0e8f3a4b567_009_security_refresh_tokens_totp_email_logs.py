"""009 - Security: refresh_tokens table, totp columns on customer/partner, email_logs table

- New table: refresh_tokens (persistent JWT refresh token storage)
- New table: email_logs (transactional email history)
- New columns on customers: totp_secret, totp_enabled, totp_backup_codes, totp_backup_codes_used
- New columns on partners: totp_secret, totp_enabled, totp_backup_codes, totp_backup_codes_used

Revision ID: h0e8f3a4b567
Revises: g9d7e2f3a456
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'h0e8f3a4b567'
down_revision = 'g9d7e2f3a456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── refresh_tokens table ──────────────────────────────────────────────────
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_username', 'refresh_tokens', ['username'], unique=False)

    # ── email_logs table ──────────────────────────────────────────────────────
    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('email_type', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='sent'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=True),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_logs_recipient', 'email_logs', ['recipient'], unique=False)

    # ── TOTP columns on customers ─────────────────────────────────────────────
    op.add_column('customers', sa.Column('totp_secret', sa.String(length=64), nullable=True))
    op.add_column('customers', sa.Column('totp_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('customers', sa.Column('totp_backup_codes', sa.Text(), nullable=True))
    op.add_column('customers', sa.Column('totp_backup_codes_used', sa.Text(), nullable=True))

    # ── TOTP columns on partners ──────────────────────────────────────────────
    op.add_column('partners', sa.Column('totp_secret', sa.String(length=64), nullable=True))
    op.add_column('partners', sa.Column('totp_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('partners', sa.Column('totp_backup_codes', sa.Text(), nullable=True))
    op.add_column('partners', sa.Column('totp_backup_codes_used', sa.Text(), nullable=True))


def downgrade() -> None:
    # TOTP columns
    op.drop_column('partners', 'totp_backup_codes_used')
    op.drop_column('partners', 'totp_backup_codes')
    op.drop_column('partners', 'totp_enabled')
    op.drop_column('partners', 'totp_secret')
    op.drop_column('customers', 'totp_backup_codes_used')
    op.drop_column('customers', 'totp_backup_codes')
    op.drop_column('customers', 'totp_enabled')
    op.drop_column('customers', 'totp_secret')
    # Tables
    op.drop_index('ix_email_logs_recipient', table_name='email_logs')
    op.drop_table('email_logs')
    op.drop_index('ix_refresh_tokens_username', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
