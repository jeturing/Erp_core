"""Migration: Add max_domains to plans + Stripe Connect columns to partners"""
from app.models.database import _get_engine
from sqlalchemy import text, inspect

engine = _get_engine()
inspector = inspect(engine)

# Add max_domains to plans
existing_cols = [c["name"] for c in inspector.get_columns("plans")]
with engine.connect() as conn:
    if "max_domains" not in existing_cols:
        conn.execute(text("ALTER TABLE plans ADD COLUMN max_domains INTEGER DEFAULT 0"))
        conn.commit()
        print("✅ Added max_domains to plans")
    else:
        print("⏭️ max_domains already exists in plans")

# Add stripe columns to partners
partner_cols = [c["name"] for c in inspector.get_columns("partners")]
with engine.connect() as conn:
    if "stripe_account_id" not in partner_cols:
        conn.execute(text("ALTER TABLE partners ADD COLUMN stripe_account_id VARCHAR(100)"))
        conn.execute(text("ALTER TABLE partners ADD COLUMN stripe_onboarding_complete BOOLEAN DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE partners ADD COLUMN stripe_charges_enabled BOOLEAN DEFAULT FALSE"))
        conn.commit()
        print("✅ Added Stripe Connect columns to partners")
    else:
        print("⏭️ Stripe columns already exist in partners")

# Set default max_domains for existing plans
with engine.connect() as conn:
    conn.execute(text("UPDATE plans SET max_domains = 0 WHERE name = 'basic'"))
    conn.execute(text("UPDATE plans SET max_domains = 1 WHERE name = 'pro'"))
    conn.execute(text("UPDATE plans SET max_domains = -1 WHERE name = 'enterprise'"))
    conn.commit()
    print("✅ Updated max_domains: basic=0, pro=1, enterprise=unlimited(-1)")

print("\n🎉 Migration complete!")
