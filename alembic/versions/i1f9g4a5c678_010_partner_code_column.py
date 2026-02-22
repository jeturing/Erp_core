"""010 - Add partner_code column to partners table

- New column: partner_code (String(20), unique, indexed, nullable)
- Auto-generate codes for existing partners: P-XXXX format

Revision ID: i1f9g4a5c678
Revises: h0e8f3a4b567
Create Date: 2026-02-23
"""
from alembic import op
import sqlalchemy as sa
import secrets
import string

# revision identifiers
revision = 'i1f9g4a5c678'
down_revision = 'h0e8f3a4b567'
branch_labels = None
depends_on = None


def _generate_code():
    """Genera un código de partner único: P-XXXX (4 alfanuméricos uppercase)."""
    chars = string.ascii_uppercase + string.digits
    return "P-" + "".join(secrets.choice(chars) for _ in range(4))


def upgrade() -> None:
    # Add column without unique constraint first
    op.add_column('partners', sa.Column('partner_code', sa.String(20), nullable=True))

    # Generate codes for existing partners
    conn = op.get_bind()
    partners = conn.execute(sa.text("SELECT id FROM partners")).fetchall()
    used_codes = set()
    for row in partners:
        code = _generate_code()
        while code in used_codes:
            code = _generate_code()
        used_codes.add(code)
        conn.execute(
            sa.text("UPDATE partners SET partner_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    # Now add unique index
    op.create_index('ix_partners_partner_code', 'partners', ['partner_code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_partners_partner_code', table_name='partners')
    op.drop_column('partners', 'partner_code')
