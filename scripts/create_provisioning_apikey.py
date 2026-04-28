#!/usr/bin/env python3
"""
Create managed API key for provisioning.

This utility bypasses ORM to avoid enum corruption issues. Creates a fresh
managed API key (sk_live_*) with:
- Scope: admin (covers provisioning operations)
- Tier: enterprise
- Permissions: ["*"] (all operations, access level hierarchy enforced by gateway)
- Rate limits: 60 RPM, 10000 RPD

Usage:
    python3 scripts/create_provisioning_apikey.py

Output:
    Prints key_id and FULL_KEY (store securely). Use as X-API-Key header.

Notes:
    - Requires DATABASE_URL and SQLAlchemy session context
    - Deletes any existing row with same name before inserting
    - Full key includes secret_part; store it securely (only printed once)
    - Rotate quarterly for security best practices
"""

import os
import sys
sys.path.insert(0, "/opt/Erp_core")

import hashlib
import secrets
from sqlalchemy import text
from app.models.database import SessionLocal

KEY_NAME = "provisioning-public-2026"


def main():
    """Create provisioning API key with raw SQL insert."""
    db = SessionLocal()
    try:
        # 1. Clean any legacy row (including corrupt enums from previous attempts)
        db.execute(text("DELETE FROM api_keys WHERE name = :name OR scope::text = 'provisioning'"),
                   {"name": KEY_NAME})
        db.commit()

        # 2. Generate new key with format: sk_live_{prefix}_{secret_part}
        prefix = secrets.token_urlsafe(12).replace("-", "").replace("_", "")[:16]
        secret_part = secrets.token_urlsafe(24).replace("-", "").replace("_", "")[:32]
        key_id = f"sk_live_{prefix}"
        full_key = f"sk_live_{prefix}_{secret_part}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # 3. Raw INSERT to avoid enum issues
        db.execute(text("""
            INSERT INTO api_keys (
                key_id, key_hash, name, description,
                scope, tier, status, permissions,
                requests_per_minute, requests_per_day,
                created_at, updated_at
            ) VALUES (
                :key_id, :key_hash, :name, :desc,
                'admin'::apikeyscope, 'enterprise'::apikeytier, 'active'::apikeystatus,
                :perms,
                :rpm, :rpd,
                NOW(), NOW()
            )
        """), {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": KEY_NAME,
            "desc": "API key para flujo público de provisioning de tenants",
            "perms": '["*"]',
            "rpm": 60,
            "rpd": 10000,
        })
        db.commit()

        print("=" * 70)
        print("✅ API KEY CREADA")
        print("=" * 70)
        print(f"key_id   : {key_id}")
        print(f"FULL_KEY : {full_key}")
        print("=" * 70)
        print(f"\nHeader usage: X-API-Key: {full_key}")
        print("\n⚠️  STORE THIS KEY SECURELY. It won't be displayed again.")
        print("Rotate quarterly for security best practices.\n")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
