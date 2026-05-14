"""Migration for DGII Data Service models."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # Tabla: dgii_rnc_cache
    op.create_table(
        'dgii_rnc_cache',
        sa.Column('rnc_number', sa.String(11), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'not_found', 'suspended', name='rncstatus'), 
                  nullable=False, server_default='not_found'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ttl_expires', sa.DateTime(), nullable=False),
        sa.Column('update_count', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('rnc_number'),
        sa.UniqueConstraint('rnc_number')
    )
    op.create_index('ix_dgii_rnc_cache_ttl', 'dgii_rnc_cache', ['ttl_expires'])
    op.create_index('ix_dgii_rnc_cache_status', 'dgii_rnc_cache', ['status'])
    op.create_index('ix_dgii_rnc_cache_rnc_number', 'dgii_rnc_cache', ['rnc_number'])
    
    # Tabla: dgii_validation_log
    op.create_table(
        'dgii_validation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(3), nullable=False),
        sa.Column('ncf', sa.String(13), nullable=True),
        sa.Column('amount', sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column('is_valid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('issues_found', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_codes', postgresql.JSON(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('validated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dgii_validation_log_company_id', 'dgii_validation_log', ['company_id'])
    op.create_index('ix_dgii_validation_log_ncf', 'dgii_validation_log', ['ncf'])
    op.create_index('ix_dgii_validation_log_validated_at', 'dgii_validation_log', ['validated_at'])
    
    # Tabla: dgii_data_service_config
    op.create_table(
        'dgii_data_service_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('rnc_api_url', sa.String(255), nullable=True),
        sa.Column('rnc_api_key', sa.String(255), nullable=True),
        sa.Column('cache_ttl_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('cache_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('auto_enrich_partner', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('auto_fix_common_errors', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reject_duplicate_ncf', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id')
    )


def downgrade():
    op.drop_table('dgii_data_service_config')
    op.drop_table('dgii_validation_log')
    op.drop_type('rncstatus')
    op.drop_table('dgii_rnc_cache')
