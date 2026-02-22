"""011 admin_users table

Revision ID: j2g0h5b6d789
Revises: i1f9g4a5c678
Create Date: 2026-02-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import bcrypt

# revision identifiers, used by Alembic.
revision = 'j2g0h5b6d789'
down_revision = 'i1f9g4a5c678'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Crear enum y tabla directamente con SQL para evitar conflictos de SQLAlchemy
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE adminuserrole AS ENUM ('admin', 'operator', 'viewer');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(200) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(200) NOT NULL,
            role adminuserrole NOT NULL DEFAULT 'admin',
            is_active BOOLEAN NOT NULL DEFAULT true,
            last_login_at TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now(),
            created_by VARCHAR(150)
        );
    """))

    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_admin_users_email ON admin_users (email);
    """))

    # Seed: crear usuario soc@jeturing.com y admin hardcodeado
    conn = op.get_bind()

    # Password: SecurePass2026!
    pw_hash = bcrypt.hashpw('SecurePass2026!'.encode(), bcrypt.gensalt()).decode()

    conn.execute(
        sa.text(
            "INSERT INTO admin_users (email, password_hash, display_name, role, is_active, created_by) "
            "VALUES (:email, :pw, :name, :role, true, :by)"
        ),
        {
            'email': 'soc@jeturing.com',
            'pw': pw_hash,
            'name': 'Jeturing SOC',
            'role': 'admin',
            'by': 'migration_011',
        }
    )

    # Admin principal también como registro en BD
    pw_hash_admin = bcrypt.hashpw('SecurePass2026!'.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        sa.text(
            "INSERT INTO admin_users (email, password_hash, display_name, role, is_active, created_by) "
            "VALUES (:email, :pw, :name, :role, true, :by)"
        ),
        {
            'email': 'admin@sajet.us',
            'pw': pw_hash_admin,
            'name': 'Admin Principal',
            'role': 'admin',
            'by': 'migration_011',
        }
    )


def downgrade() -> None:
    op.drop_index('ix_admin_users_email', table_name='admin_users')
    op.drop_table('admin_users')
    sa.Enum('admin', 'operator', 'viewer', name='adminuserrole').drop(op.get_bind(), checkfirst=True)
