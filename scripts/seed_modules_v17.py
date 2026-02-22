#!/usr/bin/env python3
"""
Seed: lee /opt/extra-addons/V17 e importa al module_catalog.
Crea paquetes de industria. Sin referencias a Odoo de cara al cliente.
Uso: python3 scripts/seed_modules_v17.py
"""
import os
import sys
import ast
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.database import SessionLocal, ModuleCatalog, ModulePackage, ModulePackageItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ADDONS_PATH = "/opt/extra-addons/V17"

CATEGORY_MAP = {
    # Plataforma base
    "web": "Plataforma", "portal": "Plataforma", "dynamic_odoo": "Plataforma",
    "queue_job": "Plataforma", "document_management_system": "Plataforma",
    # Jeturing exclusivos
    "jeturing_branding": "Jeturing", "jeturing_iframe_app_manager": "Jeturing",
    "jeturing_finance_core": "Finanzas", "jeturing_e_nfc": "Finanzas",
    # CRM y Ventas
    "crm_dashboard": "CRM y Ventas", "kw_crm_lead_search_panel": "CRM y Ventas",
    "sale_mini_dashboard": "CRM y Ventas", "sale_report_generator": "CRM y Ventas",
    "pways_commission_mgmt": "CRM y Ventas", "acs_commission": "CRM y Ventas",
    "product_warranty_management_odoo": "CRM y Ventas",
    # Punto de Venta
    "point_of_sale": "Punto de Venta", "pos_sale": "Punto de Venta",
    "pos_posagent": "Punto de Venta", "bi_pos_stripe_payment": "Punto de Venta",
    "barcode_scanning_sale_purchase": "Punto de Venta", "pos_refund_password": "Punto de Venta",
    "pos_kitchen_screen_odoo": "Punto de Venta", "adm_pos_kitchen_screen": "Punto de Venta",
    "pos_takeaway": "Punto de Venta", "table_reservation_in_pos": "Punto de Venta",
    "table_reservation_on_website": "Punto de Venta",
    # Finanzas
    "accounting_pdf_reports": "Finanzas", "invoice_multi_approval": "Finanzas",
    "account_payment_approval": "Finanzas", "om_account_accountant": "Finanzas",
    "om_fiscal_year": "Finanzas", "om_account_followup": "Finanzas",
    "om_account_daily_reports": "Finanzas", "om_recurring_payments": "Finanzas",
    "invoice_design": "Finanzas", "base_account_budget": "Finanzas",
    "om_account_budget": "Finanzas", "om_account_asset": "Finanzas",
    "om_account_bank_statement_import": "Finanzas", "automatic_invoice_and_post": "Finanzas",
    "bill_digitization": "Finanzas", "dynamic_accounts_report": "Finanzas",
    # RRHH
    "ohrms_core": "RRHH y Nómina", "hr_payroll_community": "RRHH y Nómina",
    "hr_payroll_account_community": "RRHH y Nómina", "ohrms_loan": "RRHH y Nómina",
    "ohrms_salary_advance": "RRHH y Nómina", "hrms_dashboard": "RRHH y Nómina",
    "hr_employee_shift": "RRHH y Nómina", "hr_vacation_mngmt": "RRHH y Nómina",
    "hr_employee_transfer": "RRHH y Nómina", "hr_employee_updation": "RRHH y Nómina",
    "hr_leave_request_aliasing": "RRHH y Nómina", "hr_multi_company": "RRHH y Nómina",
    "hr_reminder": "RRHH y Nómina", "hr_resignation": "RRHH y Nómina",
    "hr_reward_warning": "RRHH y Nómina", "advance_hr_attendance_dashboard": "RRHH y Nómina",
    "oh_employee_creation_from_user": "RRHH y Nómina",
    "oh_employee_documents_expiry": "RRHH y Nómina", "employee_documents_expiry": "RRHH y Nómina",
    "ohrms_loan_accounting": "RRHH y Nómina",
    # Soporte y CX
    "odoo_website_helpdesk": "Soporte y CX", "lt_helpdesk_esign": "Soporte y CX",
    "enhanced_survey_management": "Soporte y CX", "customer_product_qrcode": "Soporte y CX",
    # Omnicanal
    "us_multichat": "Omnicanal", "us_messenger": "Omnicanal",
    "whatsapp_mail_messaging": "Omnicanal", "whatsapp_redirect": "Omnicanal",
    "sh_whatsapp_integration": "Omnicanal", "odoo_twilio_sms": "Omnicanal",
    "aos_whatsapp": "Omnicanal", "website_floating_whatsapp_icon": "Omnicanal",
    # Analítica
    "advanced_dynamic_dashboard": "Analítica", "activity_dashboard_mngmnt": "Analítica",
    "google_analytics_odoo": "Analítica", "excel_report_designer": "Analítica",
    "inventory_advanced_reports": "Analítica",
    # Verticales
    "hotel_management_odoo": "Hotelería", "front_office_management": "Hotelería",
    "base_hospital_management": "Salud", "medical_lab_management": "Salud",
    "education_university_management": "Educación",
    "event_management": "Eventos", "event_ticket_qr_scanner": "Eventos",
    "venue_booking_management": "Eventos",
    "gym_mgmt_system": "Fitness y Bienestar", "salon_management": "Fitness y Bienestar",
    "website_subscription_package": "Fitness y Bienestar",
    "odoo_parking_management": "Movilidad", "fleet_rental": "Movilidad",
    "advanced_fleet_rental": "Movilidad", "fleet_rental_dashboard": "Movilidad",
    "fleet_vehicle_inspection_management": "Movilidad",
    # SaaS Ops (Jeturing-only)
    "odoo_saas_kit": "SaaS Ops", "cetmix_tower": "SaaS Ops", "odoo_rest": "SaaS Ops",
    # Temas
    "theme_shopping": "Temas", "theme_the_chef": "Temas", "theme_voltro": "Temas",
    "muk_web_theme": "Temas", "spiffy_theme_backend": "Temas",
    "vista_backend_theme": "Temas", "clarity_backend_theme_bits": "Temas",
    "os_pwa_backend": "Temas", "web_login_styles": "Temas",
    # Herramientas
    "geolocation_map_widget": "Herramientas", "image_capture_upload_widget": "Herramientas",
    "odoo_menu_management": "Herramientas", "odoo_database_restore_manager": "Herramientas",
    # IA y Telefonía
    "hia_chatgpt_integration": "IA", "3cxcrm": "Telefonía",
}

# Módulos restringidos a Jeturing (partner_allowed=False)
JETURING_ONLY = {
    "jeturing_branding", "jeturing_iframe_app_manager",
    "odoo_saas_kit", "cetmix_tower", "odoo_rest",
    "odoo_database_restore_manager",
}
# Módulos base del sistema (is_core=True)
CORE_MODULES = {"web", "portal", "dynamic_odoo", "queue_job", "document_management_system"}

# Paquetes de industria
INDUSTRY_PACKAGES = [
    {
        "name": "pkg_restaurantes",
        "display_name": "🍽️ Restaurantes y Dark Kitchens",
        "description": "Punto de venta con pantalla de cocina, reservas de mesa, takeaway y pedidos en línea.",
        "module_list": ["web", "portal", "point_of_sale", "pos_sale", "pos_kitchen_screen_odoo",
                        "table_reservation_in_pos", "table_reservation_on_website", "pos_takeaway",
                        "us_multichat", "advanced_dynamic_dashboard"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_hoteleria",
        "display_name": "🏨 Hotelería y Alojamiento",
        "description": "Gestión de hotel, recepción, eventos y finanzas integradas.",
        "module_list": ["web", "portal", "hotel_management_odoo", "front_office_management",
                        "event_management", "jeturing_finance_core", "accounting_pdf_reports", "point_of_sale"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_salud",
        "display_name": "🏥 Salud y Clínicas",
        "description": "Gestión clínica, laboratorio, documentos, facturación y comunicación.",
        "module_list": ["web", "portal", "base_hospital_management", "medical_lab_management",
                        "document_management_system", "jeturing_finance_core",
                        "odoo_website_helpdesk", "us_multichat"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_educacion",
        "display_name": "🎓 Educación e Institutos",
        "description": "Campus virtual, eventos, encuestas, facturación y comunicación omnicanal.",
        "module_list": ["web", "portal", "education_university_management", "event_management",
                        "enhanced_survey_management", "jeturing_finance_core",
                        "crm_dashboard", "us_multichat"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_fitness",
        "display_name": "💪 Gimnasios y Fitness",
        "description": "Membresías, suscripciones online, punto de venta y omnicanal.",
        "module_list": ["web", "portal", "gym_mgmt_system", "website_subscription_package",
                        "point_of_sale", "crm_dashboard", "us_multichat"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_belleza",
        "display_name": "💅 Belleza, Spa y Barbería",
        "description": "Agenda online, citas, punto de venta y CRM.",
        "module_list": ["web", "portal", "salon_management", "table_reservation_on_website",
                        "point_of_sale", "crm_dashboard", "us_multichat", "advanced_dynamic_dashboard"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_flotas",
        "display_name": "🚗 Flotas y Rent-a-Car",
        "description": "Alquiler de vehículos, inspección, dashboard de flota y finanzas.",
        "module_list": ["web", "portal", "fleet_rental", "advanced_fleet_rental",
                        "fleet_rental_dashboard", "fleet_vehicle_inspection_management",
                        "jeturing_finance_core", "crm_dashboard"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_eventos",
        "display_name": "🎪 Eventos y Venues",
        "description": "Reservas, gestión de eventos, ticket QR y punto de venta.",
        "module_list": ["web", "portal", "venue_booking_management", "event_management",
                        "event_ticket_qr_scanner", "point_of_sale", "crm_dashboard", "us_multichat"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_parking",
        "display_name": "🅿️ Parking y Operaciones",
        "description": "Gestión de parqueaderos, códigos de barra, POS y omnicanal.",
        "module_list": ["web", "portal", "odoo_parking_management", "barcode_scanning_sale_purchase",
                        "point_of_sale", "jeturing_finance_core", "us_multichat"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_retail",
        "display_name": "🛍️ Retail Omnicanal",
        "description": "Tienda física + web, garantías de producto, analítica y soporte.",
        "module_list": ["web", "portal", "point_of_sale", "crm_dashboard", "sale_mini_dashboard",
                        "product_warranty_management_odoo", "theme_shopping",
                        "advanced_dynamic_dashboard", "us_multichat", "odoo_website_helpdesk"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_servicios_profesionales",
        "display_name": "💼 Servicios Profesionales y BPO",
        "description": "Finanzas, cobros recurrentes, diseño de facturas y gestión de personal.",
        "module_list": ["web", "portal", "jeturing_finance_core", "om_recurring_payments",
                        "invoice_design", "om_account_daily_reports",
                        "ohrms_core", "odoo_website_helpdesk", "crm_dashboard"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_core_basico",
        "display_name": "⚙️ Configuración Base",
        "description": "Plataforma base sin módulos adicionales. Configurable posteriormente.",
        "module_list": ["web", "portal"],
        "partner_allowed": True,
    },
    {
        "name": "pkg_saas_ops",
        "display_name": "🔧 SaaS Ops (Solo Jeturing)",
        "description": "Operación SaaS, gestión de servidores y API REST. Exclusivo Jeturing Inc.",
        "module_list": ["web", "portal", "odoo_saas_kit", "cetmix_tower", "odoo_rest",
                        "crm_dashboard", "jeturing_finance_core"],
        "partner_allowed": False,
    },
]


def read_manifest(dir_path: str) -> dict:
    mp = os.path.join(dir_path, "__manifest__.py")
    if not os.path.exists(mp):
        return {}
    try:
        with open(mp, "r", encoding="utf-8") as f:
            return ast.literal_eval(f.read())
    except Exception:
        return {}


def clean_name(dirname: str) -> str:
    """Quita sufijo de versión: crm_dashboard-17.0.1.0.1 → crm_dashboard"""
    return dirname.split("-")[0]


def seed_modules(db):
    if not os.path.exists(ADDONS_PATH):
        logger.error(f"Ruta no encontrada: {ADDONS_PATH}")
        return

    added = updated = skipped = 0
    for dirname in sorted(os.listdir(ADDONS_PATH)):
        full_path = os.path.join(ADDONS_PATH, dirname)
        if not os.path.isdir(full_path):
            continue
        technical_name = clean_name(dirname)
        manifest = read_manifest(full_path)
        if not manifest:
            skipped += 1
            continue

        display_name = manifest.get("name", technical_name.replace("_", " ").title())
        description_raw = manifest.get("summary", manifest.get("description", ""))
        description = str(description_raw)[:500] if description_raw else None
        version = manifest.get("version", "17.0.1.0")
        category = CATEGORY_MAP.get(technical_name, manifest.get("category", "General"))
        is_core = technical_name in CORE_MODULES
        partner_allowed = technical_name not in JETURING_ONLY

        existing = db.query(ModuleCatalog).filter(
            ModuleCatalog.technical_name == technical_name
        ).first()

        if existing:
            existing.display_name = display_name
            existing.version = version
            if not existing.category:
                existing.category = category
            updated += 1
        else:
            db.add(ModuleCatalog(
                technical_name=technical_name,
                display_name=display_name,
                description=description,
                category=category,
                version=version,
                is_core=is_core,
                partner_allowed=partner_allowed,
                price_monthly=0,
                is_active=True,
            ))
            added += 1

    db.commit()
    logger.info(f"✅ Módulos: {added} nuevos, {updated} actualizados, {skipped} sin manifest")


def seed_packages(db):
    added = skipped = 0
    for pd in INDUSTRY_PACKAGES:
        if db.query(ModulePackage).filter(ModulePackage.name == pd["name"]).first():
            skipped += 1
            continue
        pkg = ModulePackage(
            name=pd["name"],
            display_name=pd["display_name"],
            description=pd["description"],
            is_default=False,
            is_active=True,
            module_list=pd["module_list"],
        )
        db.add(pkg)
        db.flush()
        for tn in pd["module_list"]:
            m = db.query(ModuleCatalog).filter(
                ModuleCatalog.technical_name == tn
            ).first()
            if m:
                db.add(ModulePackageItem(
                    package_id=pkg.id,
                    module_id=m.id,
                    is_optional=False,
                ))
        added += 1

    db.commit()
    logger.info(f"✅ Paquetes: {added} creados, {skipped} ya existían")


if __name__ == "__main__":
    logger.info("🚀 Iniciando seed de módulos V17...")
    db = SessionLocal()
    try:
        seed_modules(db)
        seed_packages(db)
        logger.info("✅ Seed completado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en seed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
