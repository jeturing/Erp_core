"""034 developer portal apps and agreement workflow

Revision ID: g4h2i3j4k567
Revises: f3g7h1i2j456
Create Date: 2026-04-01

Creates tables for Developer Portal Agreement Flow:
- developer_apps: Apps registered in the developer portal (like Uber's Developer Dashboard)
- developer_agreement_flows: Multi-stage agreement tracking (generate→pending→viewed→in_review→signed)
Extends enums: AgreementType + developer_agreement, AgreementTarget + developer
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "g4h2i3j4k567"
down_revision = "f3g7h1i2j456"
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Extend AgreementType enum ──
    op.execute("ALTER TYPE agreementtype ADD VALUE IF NOT EXISTS 'developer_agreement'")
    op.execute("ALTER TYPE agreementtype ADD VALUE IF NOT EXISTS 'marketplace_nda'")
    op.execute("COMMIT")  # enums need commit before use

    # ── 2. Extend AgreementTarget enum ──
    op.execute("ALTER TYPE agreementtarget ADD VALUE IF NOT EXISTS 'developer'")
    op.execute("COMMIT")

    # ── 3. Create developer_apps table ──
    op.create_table(
        "developer_apps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("api_suite", sa.String(100), nullable=False, server_default="eats_marketplace"),
        sa.Column("app_mode", sa.String(20), nullable=False, server_default="test"),  # test | production
        sa.Column("status", sa.String(50), nullable=False, server_default="created"),
        # Statuses: created → org_linked → agreements_pending → sandbox_granted → verification_requested → verified → rejected
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_by", sa.String(150), nullable=True),
        sa.Column("organization_name", sa.String(200), nullable=True),
        sa.Column("organization_linked", sa.Boolean(), server_default="false"),
        sa.Column("sandbox_access", sa.Boolean(), server_default="false"),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("access_token", sa.String(500), nullable=True),
        sa.Column("client_id", sa.String(200), nullable=True),
        sa.Column("client_secret", sa.String(500), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),  # JSON string for extra config
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_developer_apps_partner_id", "developer_apps", ["partner_id"])
    op.create_index("ix_developer_apps_customer_id", "developer_apps", ["customer_id"])
    op.create_index("ix_developer_apps_status", "developer_apps", ["status"])

    # ── 4. Create developer_agreement_flows table ──
    op.create_table(
        "developer_agreement_flows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("app_id", sa.Integer(), sa.ForeignKey("developer_apps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("agreement_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("signed_agreement_id", sa.Integer(), sa.ForeignKey("signed_agreements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="generated"),
        # Statuses: generated → pending → viewed → in_review → signed | rejected
        sa.Column("generated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("pdf_preview_path", sa.String(500), nullable=True),
        sa.Column("reviewer_id", sa.String(150), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_dev_agreement_flows_app_id", "developer_agreement_flows", ["app_id"])
    op.create_index("ix_dev_agreement_flows_status", "developer_agreement_flows", ["status"])

    # ── 5. Seed: Developer Portal NDA template ──
    op.execute("""
        INSERT INTO agreement_templates (agreement_type, target, title, version, html_content, is_active, is_required, sort_order, created_by, created_at, updated_at)
        VALUES (
            'developer_agreement', 'developer',
            'Acuerdo de Confidencialidad — Portal de Desarrollo Sajet',
            '1.0',
            '<h2>Acuerdo de Confidencialidad y No Divulgación (NDA)</h2>
<h3>Portal de Desarrollo — Sajet ERP Platform</h3>
<p>Fecha de vigencia: {{date}}</p>
<hr/>

<p>Este Acuerdo de Confidencialidad y No Divulgación (<strong>"Acuerdo"</strong>) se celebra entre:</p>

<p><strong>Jeturing SRL</strong> ("Parte Divulgadora"), con domicilio en República Dominicana, operadora de la plataforma SaaS Sajet ERP (sajet.us).</p>

<p><strong>{{signer_name}}</strong> {{signer_company}} ("Parte Receptora"), identificado con el correo electrónico {{signer_email}}.</p>

<h3>1. Definición de Información Confidencial</h3>
<p>Se considera "Información Confidencial" toda información técnica, comercial, financiera, operativa o de cualquier otra naturaleza que la Parte Divulgadora comparta con la Parte Receptora a través del Portal de Desarrollo de Sajet, incluyendo pero no limitado a:</p>
<ul>
<li>APIs, endpoints, documentación técnica y especificaciones</li>
<li>Credenciales de acceso, tokens, claves de API (sandbox y producción)</li>
<li>Arquitectura del sistema, bases de datos y esquemas</li>
<li>Código fuente, bibliotecas y herramientas internas</li>
<li>Datos de clientes, partners y tenants de la plataforma</li>
<li>Estrategias comerciales, precios y planes de negocio</li>
<li>Información sobre vulnerabilidades, seguridad y auditorías</li>
</ul>

<h3>2. Obligaciones de la Parte Receptora</h3>
<p>La Parte Receptora se compromete a:</p>
<ul>
<li>Mantener la confidencialidad de toda Información Confidencial recibida</li>
<li>No divulgar, publicar, reproducir ni compartir la Información Confidencial con terceros sin autorización escrita previa</li>
<li>Utilizar la Información Confidencial únicamente para los fines del desarrollo e integración autorizada con la plataforma Sajet</li>
<li>Implementar medidas de seguridad razonables para proteger la Información Confidencial</li>
<li>Notificar inmediatamente a la Parte Divulgadora sobre cualquier acceso no autorizado o brecha de seguridad</li>
<li>No realizar ingeniería inversa, descompilación o cualquier intento de acceder al código fuente no proporcionado</li>
</ul>

<h3>3. Uso de APIs y Credenciales</h3>
<p>La Parte Receptora reconoce que:</p>
<ul>
<li>Las credenciales de API son personales e intransferibles</li>
<li>El acceso sandbox es exclusivo para desarrollo y pruebas</li>
<li>Cualquier uso indebido de las APIs resultará en la revocación inmediata del acceso</li>
<li>Los rate limits y cuotas de uso deben ser respetados en todo momento</li>
<li>No se permite el scraping, crawling o extracción masiva de datos no autorizada</li>
</ul>

<h3>4. Propiedad Intelectual</h3>
<p>Toda la Información Confidencial, APIs, documentación y herramientas proporcionadas a través del Portal de Desarrollo son y permanecen propiedad exclusiva de Jeturing SRL. Este Acuerdo no otorga ningún derecho de propiedad intelectual sobre los mismos.</p>

<h3>5. Vigencia</h3>
<p>Este Acuerdo tiene una vigencia de <strong>dos (2) años</strong> a partir de la fecha de firma, y las obligaciones de confidencialidad permanecen vigentes por tres (3) años adicionales después de su terminación.</p>

<h3>6. Consecuencias del Incumplimiento</h3>
<p>El incumplimiento de este Acuerdo podrá resultar en:</p>
<ul>
<li>Revocación inmediata del acceso al Portal de Desarrollo y todas las APIs</li>
<li>Suspensión de la cuenta de partner o developer</li>
<li>Acciones legales por daños y perjuicios según la legislación de República Dominicana</li>
<li>Notificación a las autoridades competentes en caso de incidentes de seguridad</li>
</ul>

<h3>7. Ley Aplicable</h3>
<p>Este Acuerdo se rige por las leyes de la República Dominicana. Cualquier controversia será sometida a la jurisdicción de los tribunales de Santo Domingo.</p>

<hr/>
<p style="font-size:12px;color:#888;">Documento generado electrónicamente por la plataforma Sajet ERP — sajet.us<br/>Hash de integridad y firma digital adjuntos al momento de la firma.</p>',
            true, true, 10, 'system',
            NOW(), NOW()
        )
    """)


def downgrade():
    op.drop_table("developer_agreement_flows")
    op.drop_table("developer_apps")
    # Note: PostgreSQL does not support removing enum values
