"""008 - work_orders blueprint fields

Adds blueprint_package_id, selected_modules, approved_modules,
rejected_modules and tenant credential fields for provisioning workflow.

Revision ID: g9d7e2f3a456
Revises: f8c6d1e2a345
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'g9d7e2f3a456'
down_revision = 'f8c6d1e2a345'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('work_orders', sa.Column('blueprint_package_id', sa.Integer(), nullable=True))
    op.add_column('work_orders', sa.Column('selected_modules', sa.JSON(), nullable=True))
    op.add_column('work_orders', sa.Column('approved_modules', sa.JSON(), nullable=True))
    op.add_column('work_orders', sa.Column('rejected_modules', sa.JSON(), nullable=True))
    op.add_column('work_orders', sa.Column('tenant_admin_email', sa.String(200), nullable=True))
    op.add_column('work_orders', sa.Column('tenant_admin_password', sa.String(200), nullable=True))
    op.add_column('work_orders', sa.Column('tenant_user_email', sa.String(200), nullable=True))
    op.add_column('work_orders', sa.Column('tenant_user_password', sa.String(200), nullable=True))
    try:
        op.create_foreign_key(
            'fk_work_orders_blueprint',
            'work_orders', 'module_packages',
            ['blueprint_package_id'], ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint('fk_work_orders_blueprint', 'work_orders', type_='foreignkey')
    except Exception:
        pass
    for col in [
        'tenant_user_password', 'tenant_user_email', 'tenant_admin_password',
        'tenant_admin_email', 'rejected_modules', 'approved_modules',
        'selected_modules', 'blueprint_package_id',
    ]:
        try:
            op.drop_column('work_orders', col)
        except Exception:
            pass
