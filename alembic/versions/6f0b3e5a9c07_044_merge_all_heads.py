"""044 merge all heads

Revision ID: 6f0b3e5a9c07
Revises: 5e9a2b1c3d04, a1b2c3d4e5f6, n0p1q2r3s789
Create Date: 2026-05-04
"""
from typing import Sequence, Union

revision: str = "6f0b3e5a9c07"
down_revision: Union[str, Sequence[str]] = ("5e9a2b1c3d04", "a1b2c3d4e5f6", "n0p1q2r3s789")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
