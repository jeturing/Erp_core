"""
Seed del catálogo de servicios SAJET — Tabla de precios oficial
Ejecutar: python -m app.scripts.seed_catalog
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.database import SessionLocal, ServiceCatalogItem, ServiceCategory

CATALOG_ITEMS = [
    # ── SAAS PLATFORM ──
    {"category": "saas_platform", "name": "Servidor base SaaS (10GB, 24/7)", "unit": "Por servidor", "price_monthly": 160, "sort_order": 1},
    {"category": "saas_platform", "name": "Usuario SaaS", "unit": "Por usuario", "price_monthly": 40, "sort_order": 2},

    # ── SAAS SUPPORT ──
    {"category": "saas_support", "name": "Soporte básico por ticket", "description": "Incluido con servidor base", "unit": "Incluido", "price_monthly": 0, "sort_order": 10},
    {"category": "saas_support", "name": "Soporte Professional", "unit": "Por cuenta", "price_monthly": 399, "sort_order": 11},
    {"category": "saas_support", "name": "Soporte Enterprise", "unit": "Por cuenta", "price_monthly": 699, "sort_order": 12},

    # ── CORE FINANCIERO ──
    {"category": "core_financiero", "name": "Servidor Core Financiero", "unit": "Por servidor", "price_monthly": 400, "sort_order": 20},
    {"category": "core_financiero", "name": "Operación y gestión Core", "unit": "Por cuenta", "price_monthly": 200, "sort_order": 21},
    {"category": "core_financiero", "name": "Usuario Core Financiero", "unit": "Por usuario", "price_monthly": 40, "sort_order": 22},

    # ── vCISO ──
    {"category": "vciso", "name": "vCISO Essential", "unit": "Por cuenta", "price_monthly": 2000, "sort_order": 30},
    {"category": "vciso", "name": "vCISO Professional", "unit": "Por cuenta", "price_monthly": 3500, "sort_order": 31},
    {"category": "vciso", "name": "vCISO Enterprise", "unit": "Por cuenta", "price_monthly": 5000, "price_max": 7500, "sort_order": 32},

    # ── SOC (requiere vCISO) ──
    {"category": "soc", "name": "SOC ≤250 assets", "unit": "Por bloque", "price_monthly": 2500, "is_addon": True, "sort_order": 40},
    {"category": "soc", "name": "SOC 251–500 assets", "unit": "Por bloque", "price_monthly": 4000, "is_addon": True, "sort_order": 41},
    {"category": "soc", "name": "SOC 501–750 assets", "unit": "Por bloque", "price_monthly": 5500, "is_addon": True, "sort_order": 42},
    {"category": "soc", "name": "SOC 751–1000 assets", "unit": "Por bloque", "price_monthly": 7000, "is_addon": True, "sort_order": 43},
    {"category": "soc", "name": "SOC +250 assets adicionales", "unit": "Por bloque", "price_monthly": 1500, "is_addon": True, "sort_order": 44},

    # ── CLOUD & DEVOPS ──
    {"category": "cloud_devops", "name": "Cloud & DevOps managed", "unit": "Por cuenta", "price_monthly": 350, "price_max": 650, "sort_order": 50},

    # ── PAYMENTS / POS ──
    {"category": "payments_pos", "name": "Payment operations (POS/Gateway)", "unit": "Por cuenta", "price_monthly": 75, "price_max": 150, "sort_order": 60},
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(ServiceCatalogItem).count()
        if existing > 0:
            print(f"Catálogo ya tiene {existing} items. Saltando seed.")
            return

        for item_data in CATALOG_ITEMS:
            cat = ServiceCategory(item_data.pop("category"))
            item = ServiceCatalogItem(category=cat, **item_data)
            db.add(item)

        db.commit()
        print(f"✅ {len(CATALOG_ITEMS)} servicios insertados en el catálogo")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding catalog: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
