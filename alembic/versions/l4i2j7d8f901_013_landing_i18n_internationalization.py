"""013 Landing page i18n internationalization — testimonials, sections, translations

Revision ID: l4i2j7d8f901
Revises: k3h1i6c7e890
Create Date: 2026-02-23

This migration:
1. Creates testimonials table (name, role, company, text, avatar_url, locale, created_at)
2. Creates landing_sections table (section_key, locale, title, content, meta_description, created_at)
3. Changes landing_sections unique constraint from (section_key) to (section_key, locale) composite
4. Creates translations table (key, locale, value, context, updated_at) for admin-managed CMS strings
5. Adds locale columns to partners and plans tables
6. Indexes for performance
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'l4i2j7d8f901'
down_revision = 'k3h1i6c7e890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. testimonials table ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS testimonials (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        role VARCHAR(150),
        company VARCHAR(200),
        text TEXT NOT NULL,
        avatar_url VARCHAR(500),
        locale VARCHAR(10) NOT NULL DEFAULT 'en',
        featured BOOLEAN DEFAULT FALSE NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_testimonials_locale ON testimonials(locale);
    CREATE INDEX IF NOT EXISTS ix_testimonials_featured ON testimonials(featured);
    """)

    # ── 2. landing_sections table (replacing partial schema from earlier) ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS landing_sections (
        id SERIAL PRIMARY KEY,
        section_key VARCHAR(100) NOT NULL,
        locale VARCHAR(10) NOT NULL DEFAULT 'en',
        title VARCHAR(300),
        content TEXT,
        meta_description VARCHAR(500),
        meta_keywords VARCHAR(300),
        og_title VARCHAR(300),
        og_description VARCHAR(500),
        og_image_url VARCHAR(500),
        structured_data JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(section_key, locale)
    );
    CREATE INDEX IF NOT EXISTS ix_landing_sections_key ON landing_sections(section_key);
    CREATE INDEX IF NOT EXISTS ix_landing_sections_locale ON landing_sections(locale);
    """)

    # ── 3. translations table — for admin-managed CMS strings beyond static i18n ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS translations (
        id SERIAL PRIMARY KEY,
        key VARCHAR(255) NOT NULL,
        locale VARCHAR(10) NOT NULL DEFAULT 'en',
        value TEXT NOT NULL,
        context VARCHAR(100),
        is_approved BOOLEAN DEFAULT FALSE NOT NULL,
        approved_by VARCHAR(150),
        created_by VARCHAR(150),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(key, locale)
    );
    CREATE INDEX IF NOT EXISTS ix_translations_key ON translations(key);
    CREATE INDEX IF NOT EXISTS ix_translations_locale ON translations(locale);
    CREATE INDEX IF NOT EXISTS ix_translations_context ON translations(context);
    """)

    # ── 4. Add locale columns to existing tables (if not present) ──
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE partners ADD COLUMN locale VARCHAR(10) DEFAULT 'en' NOT NULL;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$ BEGIN
        ALTER TABLE plans ADD COLUMN locale VARCHAR(10) DEFAULT 'en' NOT NULL;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """)

    # ── 5. Create ENUM for locale (optional, for stricter type checking) ──
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE locale_enum AS ENUM('en', 'es');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)

    # ── 6. Seed initial testimonials (Spanish + English) ──
    op.execute("""
    INSERT INTO testimonials (name, role, company, text, locale, featured, sort_order)
    VALUES 
    -- English testimonials
    ('María González', 'CFO', 'TechCorp Latino', 'SAJET ERP transformed how we manage our operations. The multi-company support is perfect for our growth trajectory.', 'en', TRUE, 1),
    ('Roberto Chen', 'COO', 'Logística Plus', 'From implementation to daily operations, the support team has been exceptional. This platform scales with us.', 'en', TRUE, 2),
    ('Carmela Rossi', 'Finance Manager', 'RetailHub Solutions', 'The reporting capabilities are incredible. We went from spreadsheets to real-time dashboards in weeks.', 'en', FALSE, 3),
    -- Spanish testimonials
    ('María González', 'Directora Financiera', 'TechCorp Latino', 'SAJET ERP transformó cómo manejamos nuestras operaciones. El soporte multi-compañía es perfecto para nuestro crecimiento.', 'es', TRUE, 1),
    ('Roberto Chen', 'Jefe de Operaciones', 'Logística Plus', 'Desde la implementación hasta las operaciones diarias, el equipo de soporte ha sido excepcional. Esta plataforma crece con nosotros.', 'es', TRUE, 2),
    ('Carmela Rossi', 'Gerente de Finanzas', 'RetailHub Solutions', 'Las capacidades de reportes son increíbles. Pasamos de hojas de cálculo a dashboards en tiempo real en semanas.', 'es', FALSE, 3)
    ON CONFLICT DO NOTHING;
    """)

    # ── 7. Seed initial landing sections (English + Spanish) ──
    op.execute("""
    INSERT INTO landing_sections (section_key, locale, title, meta_description, meta_keywords)
    VALUES 
    -- English sections
    ('hero', 'en', 'Modern ERP for Growing Latin American Businesses', 'SAJET ERP — Enterprise Resource Planning built for Latin America. Multi-company, multi-tenant, cloud-based.', 'ERP, enterprise resource planning, business software, Latin America'),
    ('features', 'en', 'Platform Capabilities', 'Comprehensive ERP features: Finance, Sales, Inventory, HR, Payments, Reporting. All in one platform.', 'ERP features, accounting software, inventory management'),
    ('how_it_works', 'en', 'How It Works', 'Simple onboarding. From sign-up to productive in days. Cloud-based setup with zero server maintenance.', 'ERP onboarding, cloud setup, implementation'),
    ('pricing', 'en', 'Simple, Transparent Pricing', 'Pay only for what you use. Scale from 1 user to enterprise. No hidden fees, no setup costs.', 'ERP pricing, business software costs'),
    ('partners', 'en', 'Partner Program', 'Earn recurring revenue. 50/50 revenue share with Jeturing. Become a reseller or implementation partner.', 'partner program, reseller opportunities'),
    -- Spanish sections
    ('hero', 'es', 'ERP Moderno para Empresas en Crecimiento de Latinoamérica', 'SAJET ERP — Sistema de Planificación de Recursos Empresariales diseñado para Latinoamérica. Multi-empresa, multi-tenant, basado en nube.', 'ERP, software empresarial, gestión de negocios, Latinoamérica'),
    ('features', 'es', 'Capacidades de la Plataforma', 'Características ERP completas: Finanzas, Ventas, Inventario, RRHH, Pagos, Reportes. Todo en una plataforma.', 'características ERP, software contable, gestión de inventario'),
    ('how_it_works', 'es', 'Cómo Funciona', 'Incorporación simple. De registro a productivo en días. Configuración basada en nube sin mantenimiento de servidores.', 'implementación ERP, configuración en la nube'),
    ('pricing', 'es', 'Precios Simples y Transparentes', 'Paga solo por lo que usas. Escala de 1 usuario a empresa. Sin cargos ocultos, sin costos de configuración.', 'precios ERP, costos de software empresarial'),
    ('partners', 'es', 'Programa de Asociados', 'Genera ingresos recurrentes. 50/50 de ingresos compartidos con Jeturing. Conviértete en revendedor o socio de implementación.', 'programa de asociados, oportunidades de reventa')
    ON CONFLICT DO NOTHING;
    """)

    # ── 8. Seed initial translations (CMS strings that will be edited via admin panel) ──
    op.execute("""
    INSERT INTO translations (key, locale, value, context, is_approved, created_by)
    VALUES 
    -- English CMS translations
    ('landing.hero.badge', 'en', '✨ Now Available in Spanish', 'landing', TRUE, 'system'),
    ('landing.seo.title', 'en', 'SAJET ERP — Modern Enterprise Resource Planning for Latin America', 'seo', TRUE, 'system'),
    ('landing.seo.description', 'en', 'Affordable, cloud-based ERP software for SMBs in Latin America. Finance, Sales, Inventory, HR, all in one platform.', 'seo', TRUE, 'system'),
    -- Spanish CMS translations
    ('landing.hero.badge', 'es', '✨ Ahora Disponible en Español', 'landing', TRUE, 'system'),
    ('landing.seo.title', 'es', 'SAJET ERP — Planificación de Recursos Empresariales Moderna para Latinoamérica', 'seo', TRUE, 'system'),
    ('landing.seo.description', 'es', 'Software ERP asequible y basado en nube para PYMEs en Latinoamérica. Finanzas, Ventas, Inventario, RRHH, todo en una plataforma.', 'seo', TRUE, 'system')
    ON CONFLICT DO NOTHING;
    """)

    # ── 9. Create indexes on translations for admin search ──
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_translations_approved ON translations(is_approved);
    CREATE INDEX IF NOT EXISTS ix_translations_updated ON translations(updated_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS translations CASCADE;")
    op.execute("DROP TABLE IF EXISTS landing_sections CASCADE;")
    op.execute("DROP TABLE IF EXISTS testimonials CASCADE;")
    op.execute("ALTER TABLE partners DROP COLUMN IF EXISTS locale;")
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS locale;")
    op.execute("DROP TYPE IF EXISTS locale_enum CASCADE;")
