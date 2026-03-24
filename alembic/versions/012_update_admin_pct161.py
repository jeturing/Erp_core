"""012 update admin password for PCT161

Revision ID: k012updateadminpct161
Revises: j2g0h5b6d789
Create Date: 2026-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import bcrypt

# revision identifiers, used by Alembic.
revision = 'k012updateadminpct161'
down_revision = 'j2g0h5b6d789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Nuevo password solicitado por el equipo (PCT 161)
    plain_pw = '321Abcd'
    pw_hash = bcrypt.hashpw(plain_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 1) Intentar actualizar por id=2 (requisito explícito)
    res = conn.execute(
        sa.text("UPDATE admin_users SET password_hash = :pw, updated_at = NOW() WHERE id = 2"),
        {'pw': pw_hash}
    )

    if getattr(res, 'rowcount', 0) == 0:
        # 2) Si no hay fila con id=2, intentar actualizar por email
        res2 = conn.execute(
            sa.text("UPDATE admin_users SET password_hash = :pw, updated_at = NOW() WHERE email = :email"),
            {'pw': pw_hash, 'email': 'admin@sajet.us'}
        )

        if getattr(res2, 'rowcount', 0) == 0:
            # 3) Si no existe, insertar nuevo registro con id=2
            conn.execute(
                sa.text(
                    "INSERT INTO admin_users (id, email, password_hash, display_name, role, is_active, created_by) "
                    "VALUES (:id, :email, :pw, :name, 'admin', true, :by)"
                ),
                {
                    'id': 2,
                    'email': 'admin@sajet.us',
                    'pw': pw_hash,
                    'name': 'Admin Principal PCT161',
                    'by': 'migration_012_pct161',
                }
            )


def downgrade() -> None:
    conn = op.get_bind()
    # Restaurar a una contraseña conocida por migración previa (no reversible exactamente)
    pw_hash = bcrypt.hashpw('SecurePass2026!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn.execute(
        sa.text("UPDATE admin_users SET password_hash = :pw, updated_at = NOW() WHERE email = :email"),
        {'pw': pw_hash, 'email': 'admin@sajet.us'}
    )
