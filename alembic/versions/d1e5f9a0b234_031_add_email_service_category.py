"""031 add email_service to ServiceCategory enum

Revision ID: d1e5f9a0b234
Revises: c1d4e7f8g901
Create Date: 2025-07-11

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd1e5f9a0b234'
down_revision = 'c1d4e7f8g901'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add enum values
    op.execute("ALTER TYPE servicecategory ADD VALUE IF NOT EXISTS 'email_service'")


def downgrade() -> None:
    # PostgreSQL no soporta eliminar valores de enum de forma nativa.
    # Requeriría recrear el tipo completo. Se deja como no-op por seguridad.
    pass
