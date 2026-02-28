"""016 add segrd roles to adminuserrole

Revision ID: o7l5n1p2q234
Revises: n6k4l9m0h123
Create Date: 2026-02-28 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "o7l5n1p2q234"
down_revision: Union[str, None] = "n6k4l9m0h123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'adminuserrole'
                  AND e.enumlabel = 'segrd-admin'
            ) THEN
                ALTER TYPE adminuserrole ADD VALUE 'segrd-admin';
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'adminuserrole'
                  AND e.enumlabel = 'segrd-user'
            ) THEN
                ALTER TYPE adminuserrole ADD VALUE 'segrd-user';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without recreating the type.
    # Keep downgrade as no-op to avoid destructive enum rewrites in production.
    pass
