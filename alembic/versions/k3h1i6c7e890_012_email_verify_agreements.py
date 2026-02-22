"""012 email verification tokens + agreement templates + partner agreements

Revision ID: k3h1i6c7e890
Revises: j2g0h5b6d789
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'k3h1i6c7e890'
down_revision = 'j2g0h5b6d789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. email_verification_tokens ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS email_verification_tokens (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        token VARCHAR(10) NOT NULL,
        token_hash VARCHAR(64) NOT NULL,
        user_type VARCHAR(30) NOT NULL DEFAULT 'tenant',
        user_id INTEGER,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        is_used BOOLEAN DEFAULT FALSE NOT NULL,
        used_at TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_evt_token_hash ON email_verification_tokens(token_hash);
    CREATE INDEX IF NOT EXISTS ix_evt_email ON email_verification_tokens(email);
    CREATE INDEX IF NOT EXISTS ix_evt_expires ON email_verification_tokens(expires_at);
    """)

    # ── 2. admin_users: add require_email_verify column ──
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE admin_users ADD COLUMN require_email_verify BOOLEAN DEFAULT FALSE NOT NULL;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """)

    # ── 3. agreement_templates — editable NDA/TOS templates ──
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE agreementtype AS ENUM ('nda', 'service_agreement', 'terms_of_service', 'privacy_policy');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE agreementtarget AS ENUM ('partner', 'customer', 'both');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS agreement_templates (
        id SERIAL PRIMARY KEY,
        agreement_type agreementtype NOT NULL DEFAULT 'nda',
        target agreementtarget NOT NULL DEFAULT 'partner',
        title VARCHAR(300) NOT NULL,
        version VARCHAR(20) NOT NULL DEFAULT '1.0',
        html_content TEXT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE NOT NULL,
        is_required BOOLEAN DEFAULT TRUE NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_by VARCHAR(150),
        updated_by VARCHAR(150),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE UNIQUE INDEX IF NOT EXISTS uq_agreement_type_version
        ON agreement_templates(agreement_type, target, version);
    """)

    # ── 4. signed_agreements — signed instances ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS signed_agreements (
        id SERIAL PRIMARY KEY,
        template_id INTEGER NOT NULL REFERENCES agreement_templates(id),
        partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
        customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
        signer_name VARCHAR(200) NOT NULL,
        signer_email VARCHAR(255) NOT NULL,
        signer_title VARCHAR(150),
        signer_company VARCHAR(200),
        signature_data TEXT NOT NULL,
        signature_type VARCHAR(20) DEFAULT 'typed' NOT NULL,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        document_hash VARCHAR(64) NOT NULL,
        pdf_path VARCHAR(500),
        signed_at TIMESTAMP DEFAULT NOW() NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_sa_partner ON signed_agreements(partner_id);
    CREATE INDEX IF NOT EXISTS ix_sa_customer ON signed_agreements(customer_id);
    CREATE INDEX IF NOT EXISTS ix_sa_template ON signed_agreements(template_id);
    """)

    # ── 5. Seed default NDA template for partners ──
    op.execute("""
    INSERT INTO agreement_templates (agreement_type, target, title, version, html_content, is_active, is_required, sort_order, created_by)
    VALUES (
        'nda', 'partner',
        'Acuerdo de Confidencialidad y No Divulgación (NDA)',
        '1.0',
        '<h2 style="text-align:center;color:#1a1a1a;">ACUERDO DE CONFIDENCIALIDAD<br>Y NO DIVULGACIÓN</h2>
<p style="text-align:center;color:#666;font-size:13px;">Jeturing SRL — Partner Agreement</p>
<hr style="border-color:#e5e5e5;">

<p>Este Acuerdo de Confidencialidad y No Divulgación (en adelante, el "<strong>Acuerdo</strong>") se celebra entre:</p>

<p><strong>PARTE DIVULGADORA:</strong> Jeturing SRL, sociedad organizada bajo las leyes de República Dominicana, con domicilio en Santo Domingo (en adelante, "<strong>Jeturing</strong>").</p>

<p><strong>PARTE RECEPTORA:</strong> {{signer_company}}, representada por {{signer_name}}, con correo electrónico {{signer_email}} (en adelante, el "<strong>Partner</strong>").</p>

<h3>1. DEFINICIONES</h3>
<p>"<strong>Información Confidencial</strong>" significa toda información técnica, comercial, financiera, operativa o de cualquier naturaleza que sea divulgada por Jeturing al Partner, incluyendo pero no limitándose a: código fuente, arquitectura de sistemas, datos de clientes, estrategias comerciales, precios, planes de negocio y cualquier material marcado como confidencial.</p>

<h3>2. OBLIGACIONES DEL PARTNER</h3>
<p>El Partner se compromete a:</p>
<ul>
<li>Mantener estricta confidencialidad sobre toda Información Confidencial recibida.</li>
<li>No divulgar, publicar, copiar o transferir la Información Confidencial a terceros sin consentimiento previo y por escrito de Jeturing.</li>
<li>Utilizar la Información Confidencial exclusivamente para los fines comerciales acordados en el Partnership Agreement.</li>
<li>Implementar medidas de seguridad razonables para proteger la Información Confidencial.</li>
<li>Notificar inmediatamente a Jeturing ante cualquier divulgación no autorizada.</li>
</ul>

<h3>3. EXCEPCIONES</h3>
<p>No se considerará Información Confidencial aquella que:</p>
<ul>
<li>Sea de dominio público al momento de su divulgación.</li>
<li>El Partner pueda demostrar que ya la poseía antes de recibirla de Jeturing.</li>
<li>Sea obtenida lícitamente de un tercero sin obligación de confidencialidad.</li>
<li>Sea requerida por orden judicial o autoridad competente.</li>
</ul>

<h3>4. PROPIEDAD INTELECTUAL</h3>
<p>La divulgación de Información Confidencial no otorga al Partner ningún derecho de propiedad intelectual sobre la misma. Todos los derechos permanecen con Jeturing.</p>

<h3>5. VIGENCIA</h3>
<p>Este Acuerdo entrará en vigor en la fecha de firma y permanecerá vigente por un período de <strong>tres (3) años</strong> a partir de la última divulgación de Información Confidencial.</p>

<h3>6. INCUMPLIMIENTO</h3>
<p>El incumplimiento de este Acuerdo facultará a Jeturing a tomar las acciones legales correspondientes, incluyendo la terminación inmediata del Partnership Agreement y la reclamación de daños y perjuicios.</p>

<h3>7. LEY APLICABLE</h3>
<p>Este Acuerdo se regirá por las leyes de República Dominicana. Cualquier disputa será sometida a los tribunales competentes de Santo Domingo.</p>

<hr style="border-color:#e5e5e5;">
<p style="font-size:12px;color:#999;">Fecha de firma: {{date}} | IP: {{ip_address}}</p>',
        TRUE, TRUE, 1, 'system'
    )
    ON CONFLICT DO NOTHING;
    """)

    # ── 6. Seed default service agreement for partners ──
    op.execute("""
    INSERT INTO agreement_templates (agreement_type, target, title, version, html_content, is_active, is_required, sort_order, created_by)
    VALUES (
        'service_agreement', 'partner',
        'Acuerdo Global de Partnership — Servicios',
        '1.0',
        '<h2 style="text-align:center;color:#1a1a1a;">ACUERDO GLOBAL DE PARTNERSHIP</h2>
<p style="text-align:center;color:#666;font-size:13px;">Jeturing SRL — Términos de Servicio para Partners</p>
<hr style="border-color:#e5e5e5;">

<p>Este Acuerdo de Servicio se celebra entre <strong>Jeturing SRL</strong> y <strong>{{signer_company}}</strong>, representada por <strong>{{signer_name}}</strong>.</p>

<h3>1. OBJETO</h3>
<p>Jeturing otorga al Partner una licencia no exclusiva para comercializar los servicios de la plataforma SAJET ERP, bajo los términos establecidos en este acuerdo.</p>

<h3>2. MODELO DE INGRESOS</h3>
<p>El modelo de reparto de ingresos será <strong>50/50</strong> sobre los Ingresos Netos generados por los clientes referidos por el Partner.</p>
<ul>
<li><strong>Ingresos Netos</strong>: Monto bruto cobrado menos comisiones de procesador de pago, reembolsos y contracargos.</li>
<li>Las liquidaciones se realizarán mensualmente.</li>
</ul>

<h3>3. OBLIGACIONES DEL PARTNER</h3>
<ul>
<li>Registrar todos los prospectos en el Portal de Partners antes del cierre comercial.</li>
<li>Mantener un margen máximo de 30% sobre el precio base al cliente final.</li>
<li>Completar la verificación KYC de Stripe Connect para recibir pagos.</li>
<li>Brindar soporte de primer nivel a sus clientes referidos.</li>
</ul>

<h3>4. OBLIGACIONES DE JETURING</h3>
<ul>
<li>Proveer la plataforma SAJET ERP con disponibilidad del 99.5% mensual.</li>
<li>Realizar las liquidaciones mensuales en los primeros 10 días hábiles.</li>
<li>Soporte técnico de segundo y tercer nivel.</li>
<li>Actualizaciones y mantenimiento de la plataforma.</li>
</ul>

<h3>5. VIGENCIA Y TERMINACIÓN</h3>
<p>Este acuerdo tiene vigencia indefinida y puede ser terminado por cualquiera de las partes con <strong>30 días</strong> de aviso previo por escrito.</p>

<hr style="border-color:#e5e5e5;">
<p style="font-size:12px;color:#999;">Fecha de firma: {{date}} | IP: {{ip_address}}</p>',
        TRUE, TRUE, 2, 'system'
    )
    ON CONFLICT DO NOTHING;
    """)

    # ── 7. Seed default TOS for customers ──
    op.execute("""
    INSERT INTO agreement_templates (agreement_type, target, title, version, html_content, is_active, is_required, sort_order, created_by)
    VALUES (
        'terms_of_service', 'customer',
        'Términos y Condiciones de Servicio — Cliente',
        '1.0',
        '<h2 style="text-align:center;color:#1a1a1a;">TÉRMINOS Y CONDICIONES DE SERVICIO</h2>
<p style="text-align:center;color:#666;font-size:13px;">Plataforma SAJET ERP — Jeturing SRL</p>
<hr style="border-color:#e5e5e5;">

<p>Al utilizar los servicios de la plataforma SAJET ERP, <strong>{{signer_company}}</strong> (el "<strong>Cliente</strong>"), representado por <strong>{{signer_name}}</strong>, acepta los siguientes términos:</p>

<h3>1. SERVICIO</h3>
<p>Jeturing SRL proveerá acceso a la plataforma SAJET ERP bajo el plan contratado, incluyendo hosting, mantenimiento y soporte técnico según el nivel del plan.</p>

<h3>2. DATOS Y PRIVACIDAD</h3>
<ul>
<li>Los datos del Cliente son propiedad exclusiva del Cliente.</li>
<li>Jeturing no accederá a los datos del Cliente excepto para soporte técnico autorizado.</li>
<li>Se realizarán backups automáticos según el plan contratado.</li>
</ul>

<h3>3. FACTURACIÓN</h3>
<ul>
<li>La facturación es mensual y recurrente según el plan contratado.</li>
<li>El precio se calcula como: precio base + (usuarios adicionales × precio por usuario).</li>
<li>Los pagos se procesan a través de Stripe.</li>
</ul>

<h3>4. CANCELACIÓN</h3>
<p>El Cliente puede cancelar su suscripción en cualquier momento. Los datos se mantendrán por 30 días después de la cancelación.</p>

<hr style="border-color:#e5e5e5;">
<p style="font-size:12px;color:#999;">Fecha de aceptación: {{date}} | IP: {{ip_address}}</p>',
        TRUE, TRUE, 1, 'system'
    )
    ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS signed_agreements CASCADE;")
    op.execute("DROP TABLE IF EXISTS agreement_templates CASCADE;")
    op.execute("DROP TABLE IF EXISTS email_verification_tokens CASCADE;")
    op.execute("ALTER TABLE admin_users DROP COLUMN IF EXISTS require_email_verify;")
    op.execute("DROP TYPE IF EXISTS agreementtype CASCADE;")
    op.execute("DROP TYPE IF EXISTS agreementtarget CASCADE;")
