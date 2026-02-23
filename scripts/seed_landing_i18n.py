#!/usr/bin/env python3
"""
Seed script for landing page i18n content.
Populates testimonials, landing_sections, and translations tables.

Usage:
    python scripts/seed_landing_i18n.py

Requirements:
    - Database schema created (via alembic upgrade head)
    - SQLALCHEMY_DATABASE_URL environment variable set or in config.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.database import (
    SessionLocal, Testimonial, LandingSection, Translation, Base, engine
)

# Fix encoding for Unicode characters in DB queries
import sqlalchemy
if hasattr(engine, 'pool'):
    @sqlalchemy.event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.set_client_encoding('UTF8')


def seed_testimonials(db):
    """Seed initial testimonials in English and Spanish."""
    print("[*] Seeding testimonials...")
    
    testimonials_data = [
        # English testimonials
        {
            "name": "María González",
            "role": "CFO",
            "company": "TechCorp Latino",
            "text": "SAJET ERP transformed how we manage our operations. The multi-company support is perfect for our growth trajectory.",
            "locale": "en",
            "featured": True,
            "sort_order": 1,
        },
        {
            "name": "Roberto Chen",
            "role": "COO",
            "company": "Logística Plus",
            "text": "From implementation to daily operations, the support team has been exceptional. This platform scales with us.",
            "locale": "en",
            "featured": True,
            "sort_order": 2,
        },
        {
            "name": "Carmela Rossi",
            "role": "Finance Manager",
            "company": "RetailHub Solutions",
            "text": "The reporting capabilities are incredible. We went from spreadsheets to real-time dashboards in weeks.",
            "locale": "en",
            "featured": False,
            "sort_order": 3,
        },
        # Spanish testimonials
        {
            "name": "María González",
            "role": "Directora Financiera",
            "company": "TechCorp Latino",
            "text": "SAJET ERP transformó cómo manejamos nuestras operaciones. El soporte multi-compañía es perfecto para nuestro crecimiento.",
            "locale": "es",
            "featured": True,
            "sort_order": 1,
        },
        {
            "name": "Roberto Chen",
            "role": "Jefe de Operaciones",
            "company": "Logística Plus",
            "text": "Desde la implementación hasta las operaciones diarias, el equipo de soporte ha sido excepcional. Esta plataforma crece con nosotros.",
            "locale": "es",
            "featured": True,
            "sort_order": 2,
        },
        {
            "name": "Carmela Rossi",
            "role": "Gerente de Finanzas",
            "company": "RetailHub Solutions",
            "text": "Las capacidades de reportes son increíbles. Pasamos de hojas de cálculo a dashboards en tiempo real en semanas.",
            "locale": "es",
            "featured": False,
            "sort_order": 3,
        },
    ]
    
    count = 0
    for data in testimonials_data:
        # Check if testimonial already exists
        existing = db.query(Testimonial).filter(
            Testimonial.name == data["name"],
            Testimonial.locale == data["locale"],
        ).first()
        
        if not existing:
            testimonial = Testimonial(**data)
            db.add(testimonial)
            count += 1
        else:
            print(f"  - Testimonial '{data['name']}' ({data['locale']}) already exists, skipping")
    
    db.commit()
    print(f"  ✓ Added {count} testimonials")


def seed_landing_sections(db):
    """Seed initial landing section metadata (title, meta_description, etc.)."""
    print("[*] Seeding landing sections...")
    
    sections_data = [
        # English sections
        {
            "section_key": "hero",
            "locale": "en",
            "title": "Modern ERP for Growing Latin American Businesses",
            "meta_description": "SAJET ERP — Enterprise Resource Planning built for Latin America. Multi-company, multi-tenant, cloud-based.",
            "meta_keywords": "ERP, enterprise resource planning, business software, Latin America",
            "og_title": "SAJET ERP — Modern Enterprise Resource Planning for Latin America",
            "og_description": "Affordable, cloud-based ERP software for SMBs in Latin America. Finance, Sales, Inventory, HR, all in one platform.",
        },
        {
            "section_key": "features",
            "locale": "en",
            "title": "Platform Capabilities",
            "meta_description": "Comprehensive ERP features: Finance, Sales, Inventory, HR, Payments, Reporting. All in one platform.",
            "meta_keywords": "ERP features, accounting software, inventory management",
        },
        {
            "section_key": "how_it_works",
            "locale": "en",
            "title": "How It Works",
            "meta_description": "Simple onboarding. From sign-up to productive in days. Cloud-based setup with zero server maintenance.",
            "meta_keywords": "ERP onboarding, cloud setup, implementation",
        },
        {
            "section_key": "pricing",
            "locale": "en",
            "title": "Simple, Transparent Pricing",
            "meta_description": "Pay only for what you use. Scale from 1 user to enterprise. No hidden fees, no setup costs.",
            "meta_keywords": "ERP pricing, business software costs",
        },
        {
            "section_key": "partners",
            "locale": "en",
            "title": "Partner Program",
            "meta_description": "Earn recurring revenue. 50/50 revenue share with Jeturing. Become a reseller or implementation partner.",
            "meta_keywords": "partner program, reseller opportunities",
        },
        {
            "section_key": "value_prop",
            "locale": "en",
            "title": "Why SAJET ERP",
            "meta_description": "One source of truth for your business. Built-in multi-company support. No servers to manage.",
            "meta_keywords": "ERP benefits, business efficiency",
        },
        # Spanish sections
        {
            "section_key": "hero",
            "locale": "es",
            "title": "ERP Moderno para Empresas en Crecimiento de Latinoamérica",
            "meta_description": "SAJET ERP — Sistema de Planificación de Recursos Empresariales diseñado para Latinoamérica. Multi-empresa, multi-tenant, basado en nube.",
            "meta_keywords": "ERP, software empresarial, gestión de negocios, Latinoamérica",
            "og_title": "SAJET ERP — Planificación de Recursos Empresariales Moderna para Latinoamérica",
            "og_description": "Software ERP asequible y basado en nube para PYMEs en Latinoamérica. Finanzas, Ventas, Inventario, RRHH, todo en una plataforma.",
        },
        {
            "section_key": "features",
            "locale": "es",
            "title": "Capacidades de la Plataforma",
            "meta_description": "Características ERP completas: Finanzas, Ventas, Inventario, RRHH, Pagos, Reportes. Todo en una plataforma.",
            "meta_keywords": "características ERP, software contable, gestión de inventario",
        },
        {
            "section_key": "how_it_works",
            "locale": "es",
            "title": "Cómo Funciona",
            "meta_description": "Incorporación simple. De registro a productivo en días. Configuración basada en nube sin mantenimiento de servidores.",
            "meta_keywords": "implementación ERP, configuración en la nube",
        },
        {
            "section_key": "pricing",
            "locale": "es",
            "title": "Precios Simples y Transparentes",
            "meta_description": "Paga solo por lo que usas. Escala de 1 usuario a empresa. Sin cargos ocultos, sin costos de configuración.",
            "meta_keywords": "precios ERP, costos de software empresarial",
        },
        {
            "section_key": "partners",
            "locale": "es",
            "title": "Programa de Asociados",
            "meta_description": "Genera ingresos recurrentes. 50/50 de ingresos compartidos con Jeturing. Conviértete en revendedor o socio de implementación.",
            "meta_keywords": "programa de asociados, oportunidades de reventa",
        },
        {
            "section_key": "value_prop",
            "locale": "es",
            "title": "Por Qué SAJET ERP",
            "meta_description": "Una fuente única de verdad para tu negocio. Soporte multi-compañía integrado. Sin servidores que gestionar.",
            "meta_keywords": "beneficios ERP, eficiencia empresarial",
        },
    ]
    
    count = 0
    for data in sections_data:
        # Check if section already exists
        existing = db.query(LandingSection).filter(
            LandingSection.section_key == data["section_key"],
            LandingSection.locale == data["locale"],
        ).first()
        
        if not existing:
            section = LandingSection(**data)
            db.add(section)
            count += 1
        else:
            print(f"  - Section '{data['section_key']}' ({data['locale']}) already exists, skipping")
    
    db.commit()
    print(f"  ✓ Added {count} landing sections")


def seed_translations(db):
    """Seed admin-manageable translation strings."""
    print("[*] Seeding translations...")
    
    translations_data = [
        # English CMS translations
        {
            "key": "landing.hero.badge",
            "locale": "en",
            "value": "✨ Now Available in Spanish",
            "context": "landing",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "landing.seo.title",
            "locale": "en",
            "value": "SAJET ERP — Modern Enterprise Resource Planning for Latin America",
            "context": "seo",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "landing.seo.description",
            "locale": "en",
            "value": "Affordable, cloud-based ERP software for SMBs in Latin America. Finance, Sales, Inventory, HR, all in one platform.",
            "context": "seo",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "footer.copyright",
            "locale": "en",
            "value": "© 2026 Jeturing SRL. All rights reserved.",
            "context": "footer",
            "is_approved": True,
            "created_by": "system",
        },
        # Spanish CMS translations
        {
            "key": "landing.hero.badge",
            "locale": "es",
            "value": "✨ Ahora Disponible en Español",
            "context": "landing",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "landing.seo.title",
            "locale": "es",
            "value": "SAJET ERP — Planificación de Recursos Empresariales Moderna para Latinoamérica",
            "context": "seo",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "landing.seo.description",
            "locale": "es",
            "value": "Software ERP asequible y basado en nube para PYMEs en Latinoamérica. Finanzas, Ventas, Inventario, RRHH, todo en una plataforma.",
            "context": "seo",
            "is_approved": True,
            "created_by": "system",
        },
        {
            "key": "footer.copyright",
            "locale": "es",
            "value": "© 2026 Jeturing SRL. Todos los derechos reservados.",
            "context": "footer",
            "is_approved": True,
            "created_by": "system",
        },
    ]
    
    count = 0
    for data in translations_data:
        # Check if translation already exists
        existing = db.query(Translation).filter(
            Translation.key == data["key"],
            Translation.locale == data["locale"],
        ).first()
        
        if not existing:
            translation = Translation(**data)
            db.add(translation)
            count += 1
        else:
            print(f"  - Translation '{data['key']}' ({data['locale']}) already exists, skipping")
    
    db.commit()
    print(f"  ✓ Added {count} translations")


def main():
    """Main seed function."""
    print("\n" + "="*60)
    print("  SAJET ERP Landing Page i18n Seed Script")
    print("="*60 + "\n")
    
    try:
        db = SessionLocal()
        
        # Seed testimonials
        seed_testimonials(db)
        
        # Seed landing sections
        seed_landing_sections(db)
        
        # Seed translations
        seed_translations(db)
        
        db.close()
        
        print("\n" + "="*60)
        print("  ✓ Seeding completed successfully!")
        print("="*60 + "\n")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
