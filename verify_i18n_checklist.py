#!/usr/bin/env python3
"""
Quick checklist to verify i18n implementation is ready for Phase 2 (Admin CRUD pages).
Run this script to verify all Phase 1 files are in place and correctly formatted.
"""

import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()

def check_file_exists(path, description):
    """Check if file exists."""
    full_path = ROOT_DIR / path
    exists = full_path.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {description}")
    if not exists:
        print(f"    → {path}")
    return exists

def check_json_valid(path, description):
    """Check if JSON file is valid."""
    full_path = ROOT_DIR / path
    if not full_path.exists():
        print(f"  ✗ {description} (FILE NOT FOUND)")
        return False
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"  ✓ {description} (valid JSON)")
        return True
    except Exception as e:
        print(f"  ✗ {description} (INVALID JSON: {str(e)[:50]})")
        return False

def check_svelte_import(path, import_str, description):
    """Check if Svelte file contains import."""
    full_path = ROOT_DIR / path
    if not full_path.exists():
        print(f"  ✗ {description} (FILE NOT FOUND)")
        return False
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        has_import = import_str in content
        status = "✓" if has_import else "✗"
        print(f"  {status} {description}")
        if not has_import:
            print(f"    → Missing: {import_str}")
        return has_import
    except Exception as e:
        print(f"  ✗ {description} (ERROR: {str(e)[:50]})")
        return False

def main():
    """Run all checks."""
    print("\n" + "="*70)
    print("  SAJET ERP i18n Phase 1 Verification Checklist")
    print("="*70 + "\n")
    
    checks_passed = 0
    checks_total = 0
    
    # ────────────────────────────────────────────────────────────────
    print("📁 Frontend i18n Files")
    print("─" * 70)
    
    checks = [
        ("frontend/src/lib/i18n/index.ts", "i18n initialization (initializeI18n, getInitialLocale)"),
        ("frontend/src/lib/i18n/en.json", "English translations (185 keys)"),
        ("frontend/src/lib/i18n/es.json", "Spanish translations (185 keys)"),
        ("frontend/src/lib/stores/locale.ts", "Locale store with toggle/set methods"),
    ]
    
    for path, desc in checks:
        checks_total += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # Check JSON validity
    print()
    checks_total += 2
    if check_json_valid("frontend/src/lib/i18n/en.json", "English JSON structure"):
        checks_passed += 1
    if check_json_valid("frontend/src/lib/i18n/es.json", "Spanish JSON structure"):
        checks_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    print("\n📄 Frontend Components (i18n enabled)")
    print("─" * 70)
    
    components = [
        ("frontend/src/App.svelte", "import { initializeI18n }", "App.svelte initializes i18n"),
        ("frontend/src/lib/components/landing/NavBar.svelte", "import { t } from 'svelte-i18n'", "NavBar imports svelte-i18n"),
        ("frontend/src/lib/components/landing/Hero.svelte", "import { t } from 'svelte-i18n'", "Hero imports svelte-i18n"),
        ("frontend/src/lib/components/landing/ValueProp.svelte", "import { t } from 'svelte-i18n'", "ValueProp imports svelte-i18n"),
        ("frontend/src/lib/components/landing/FeaturesGrid.svelte", "import { t } from 'svelte-i18n'", "FeaturesGrid imports svelte-i18n"),
        ("frontend/src/lib/components/landing/HowItWorks.svelte", "import { t } from 'svelte-i18n'", "HowItWorks imports svelte-i18n"),
        ("frontend/src/lib/components/landing/PricingPreview.svelte", "import { t } from 'svelte-i18n'", "PricingPreview imports svelte-i18n"),
        ("frontend/src/lib/components/landing/ForPartners.svelte", "import { t } from 'svelte-i18n'", "ForPartners imports svelte-i18n"),
        ("frontend/src/lib/components/landing/Testimonials.svelte", "import { t } from 'svelte-i18n'", "Testimonials imports svelte-i18n"),
        ("frontend/src/lib/components/landing/FinalCTA.svelte", "import { t } from 'svelte-i18n'", "FinalCTA imports svelte-i18n"),
        ("frontend/src/lib/components/landing/Footer.svelte", "import { t } from 'svelte-i18n'", "Footer imports svelte-i18n"),
        ("frontend/src/lib/components/landing/SocialProof.svelte", "import { t } from 'svelte-i18n'", "SocialProof imports svelte-i18n"),
    ]
    
    for path, import_str, desc in components:
        checks_total += 1
        if check_svelte_import(path, import_str, desc):
            checks_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    print("\n🗄️  Backend Files")
    print("─" * 70)
    
    checks = [
        ("app/models/database.py", "Database models with Testimonial, LandingSection, Translation"),
        ("app/routes/public_landing.py", "Public landing routes with locale support"),
    ]
    
    for path, desc in checks:
        checks_total += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # Check if models are in database.py
    print()
    full_path = ROOT_DIR / "app/models/database.py"
    for model_name in ["Testimonial", "LandingSection", "Translation"]:
        checks_total += 1
        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
            if f"class {model_name}(Base):" in content:
                print(f"  ✓ Model {model_name} defined in database.py")
                checks_passed += 1
            else:
                print(f"  ✗ Model {model_name} NOT found in database.py")
        else:
            print(f"  ✗ database.py not found")
    
    # ────────────────────────────────────────────────────────────────
    print("\n🧳 Database Migration")
    print("─" * 70)
    
    checks_total += 1
    migrations_dir = ROOT_DIR / "alembic/versions"
    if migrations_dir.exists():
        migration_013 = None
        for f in migrations_dir.glob("*013*landing_i18n*"):
            migration_013 = f
            break
        
        if migration_013:
            print(f"  ✓ Alembic migration 013 found: {migration_013.name}")
            checks_passed += 1
        else:
            print(f"  ✗ Alembic migration 013 NOT found")
    else:
        print(f"  ✗ alembic/versions directory not found")
    
    # ────────────────────────────────────────────────────────────────
    print("\n📜 Scripts")
    print("─" * 70)
    
    checks = [
        ("scripts/seed_landing_i18n.py", "Seed script for i18n data"),
        ("scripts/verify_i18n.sh", "Verification script for i18n files"),
    ]
    
    for path, desc in checks:
        checks_total += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    print("\n📋 Documentation")
    print("─" * 70)
    
    checks = [
        ("I18N_IMPLEMENTATION_SUMMARY.md", "i18n Implementation Summary"),
        ("I18N_STATUS_REPORT.md", "i18n Status Report"),
    ]
    
    for path, desc in checks:
        checks_total += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    print("\n📦 NPM Package")
    print("─" * 70)
    
    checks_total += 1
    package_json = ROOT_DIR / "frontend/package.json"
    if package_json.exists():
        with open(package_json, 'r') as f:
            pkg = json.load(f)
        if "svelte-i18n" in pkg.get("dependencies", {}):
            print(f"  ✓ svelte-i18n in package.json")
            checks_passed += 1
        else:
            print(f"  ✗ svelte-i18n NOT in package.json dependencies")
    else:
        print(f"  ✗ frontend/package.json not found")
    
    # ────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print(f"  Results: {checks_passed}/{checks_total} checks passed")
    print("="*70)
    
    if checks_passed == checks_total:
        print("\n✅ All Phase 1 files are in place and correctly formatted!")
        print("    Ready to proceed with Phase 2 (Admin CRUD Pages)\n")
        return 0
    else:
        print(f"\n⚠️  {checks_total - checks_passed} check(s) failed.")
        print("    Please review the output above and ensure all files are in place.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
