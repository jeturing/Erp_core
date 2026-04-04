"""035 — Crear tablas infra_tunnels y reserved_subdomains.

Separa la semántica de túneles de infraestructura de los deployments de tenants
y agrega configuración dinámica de subdominios reservados para filtrar el
auto-registro agresivo del db_watcher y get_all_tenants_from_servers().

Revision ID: h5i3j4k5l678
Revises: g4h2i3j4k567
Create Date: 2026-04-04

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'h5i3j4k5l678'
down_revision = 'g4h2i3j4k567'
branch_labels = None
depends_on = None

# Subdominios reservados iniciales — infraestructura conocida de Jeturing
INITIAL_RESERVED = [
    ("api", "API gateway / reserved namespace", "reserved"),
    ("admin", "Admin panel namespace", "reserved"),
    ("www", "WWW redirect", "reserved"),
    ("mail", "Email service", "service"),
    ("smtp", "SMTP relay", "service"),
    ("ftp", "FTP (legacy)", "reserved"),
    ("n8n", "N8n workflow automation", "service"),
    ("segrd", "SEGRD security platform", "infrastructure"),
    ("grafana", "Grafana monitoring", "service"),
    ("prometheus", "Prometheus metrics", "service"),
    ("glitchtip", "GlitchTip error monitoring", "service"),
    ("sentry", "Sentry error monitoring alias", "service"),
    ("wazuh", "Wazuh SIEM/SOC", "infrastructure"),
    ("thehive", "TheHive SOAR", "infrastructure"),
    ("cortex", "Cortex analyzers", "infrastructure"),
    ("pentagi", "PentAGI pentesting AI", "infrastructure"),
    ("ollama", "Ollama LLM", "service"),
    ("minio", "MinIO S3 storage", "service"),
    ("redis", "Redis cache", "service"),
    ("nextcloud", "Nextcloud files", "service"),
    ("gitea", "Gitea git server", "service"),
    ("keycloak", "Keycloak IAM", "service"),
    ("auth0", "Auth0 IAM", "service"),
    ("erp_core_db", "ERP Core database interna", "system"),
    ("postgres", "PostgreSQL system DB", "system"),
    ("template_tenant", "Template BD para clonado", "system"),
    ("root", "PostgreSQL root DB", "system"),
]


def upgrade() -> None:
    # ── infra_tunnels ──
    op.create_table(
        'infra_tunnels',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('cloudflare_tunnel_id', sa.String(100), nullable=True),
        sa.Column('cloudflare_zone_id', sa.String(100), nullable=True),
        sa.Column('domain', sa.String(200), nullable=False),
        sa.Column('hostname_pattern', sa.String(200), nullable=True),
        sa.Column('target_pct', sa.Integer, nullable=True),
        sa.Column('target_url', sa.String(300), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # ── reserved_subdomains ──
    op.create_table(
        'reserved_subdomains',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('subdomain', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('reason', sa.String(300), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='infrastructure'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # ── Seed datos iniciales ──
    reserved_table = sa.table(
        'reserved_subdomains',
        sa.column('subdomain', sa.String),
        sa.column('reason', sa.String),
        sa.column('category', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime),
    )
    op.bulk_insert(reserved_table, [
        {
            'subdomain': subdomain,
            'reason': reason,
            'category': category,
            'is_active': True,
            'created_at': datetime.utcnow(),
        }
        for subdomain, reason, category in INITIAL_RESERVED
    ])

    # ── Seed infra tunnels conocidos ──
    tunnels_table = sa.table(
        'infra_tunnels',
        sa.column('name', sa.String),
        sa.column('domain', sa.String),
        sa.column('hostname_pattern', sa.String),
        sa.column('target_pct', sa.Integer),
        sa.column('target_url', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('description', sa.Text),
        sa.column('created_at', sa.DateTime),
    )
    op.bulk_insert(tunnels_table, [
        {
            'name': 'sajet-pct105',
            'domain': 'sajet.us',
            'hostname_pattern': '*.sajet.us',
            'target_pct': 105,
            'target_url': 'http://localhost:8069',
            'is_active': True,
            'description': 'Tunnel principal Odoo 17 multi-tenant',
            'created_at': datetime.utcnow(),
        },
        {
            'name': 'sajet-pct160',
            'domain': 'sajet.us',
            'hostname_pattern': 'sajet.us',
            'target_pct': 160,
            'target_url': 'https://localhost:443',
            'is_active': True,
            'description': 'Tunnel SAJET ERP Core orquestador',
            'created_at': datetime.utcnow(),
        },
        {
            'name': 'segrd-pct154',
            'domain': 'segrd.com',
            'hostname_pattern': '*.segrd.com',
            'target_pct': 154,
            'target_url': 'http://localhost:8080',
            'is_active': True,
            'description': 'Tunnel SEGRD Stack (FOREN+AXION+VIGIL+ORBIA)',
            'created_at': datetime.utcnow(),
        },
        {
            'name': 'jeturing-pct161',
            'domain': 'jeturing.com',
            'hostname_pattern': 'jeturing.com',
            'target_pct': 161,
            'target_url': 'http://localhost:8069',
            'is_active': True,
            'description': 'Tunnel Odoo 19 corporativo Jeturing',
            'created_at': datetime.utcnow(),
        },
    ])


def downgrade() -> None:
    op.drop_table('reserved_subdomains')
    op.drop_table('infra_tunnels')
