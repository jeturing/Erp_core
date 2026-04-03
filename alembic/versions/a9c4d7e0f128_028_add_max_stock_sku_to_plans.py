"""028 add max_stock_sku to plans

Agrega campo max_stock_sku a la tabla plans para limitar la cantidad de
SKUs únicos con stock real permitidos por plan (0 = ilimitado).

Revision ID: a9c4d7e0f128
Revises: g4h2i3j4k567
Create Date: 2026-04-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a9c4d7e0f128'
down_revision = 'g4h2i3j4k567'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'plans',
        sa.Column('max_stock_sku', sa.Integer(), nullable=False, server_default='0'),
    )
    # Valores iniciales por plan:
    #   basic      → 500 SKUs
    #   pro        → 2000 SKUs
    #   enterprise → 0 (ilimitado)
    op.execute("""
        UPDATE plans SET max_stock_sku = CASE
            WHEN name = 'basic'      THEN 500
            WHEN name = 'pro'        THEN 2000
            WHEN name = 'enterprise' THEN 0
            ELSE 0
        END
    """)


def downgrade() -> None:
    op.drop_column('plans', 'max_stock_sku')
