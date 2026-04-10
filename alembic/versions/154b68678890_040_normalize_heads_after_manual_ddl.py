"""040 normalize heads after manual ddl

Revision ID: 154b68678890
Revises: i6j7k8l9m012, m9n0p1q2r678
Create Date: 2026-04-10 05:54:01.208066

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '154b68678890'
down_revision: Union[str, None] = ('i6j7k8l9m012', 'm9n0p1q2r678')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
