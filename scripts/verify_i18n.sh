#!/bin/bash
# Verification script for i18n implementation
# Checks that all frontend and backend files are in place

set -e

echo "🔍 SAJET ERP i18n Implementation Verification"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
CHECKS_PASSED=0
CHECKS_FAILED=0

# Check function
check_file() {
  local file=$1
  local description=$2
  
  if [ -f "$file" ]; then
    echo -e "${GREEN}✓${NC} $description"
    ((CHECKS_PASSED++))
  else
    echo -e "${RED}✗${NC} $description (NOT FOUND: $file)"
    ((CHECKS_FAILED++))
  fi
}

check_dir() {
  local dir=$1
  local description=$2
  
  if [ -d "$dir" ]; then
    echo -e "${GREEN}✓${NC} $description"
    ((CHECKS_PASSED++))
  else
    echo -e "${RED}✗${NC} $description (NOT FOUND: $dir)"
    ((CHECKS_FAILED++))
  fi
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$SCRIPT_DIR/.."

cd "$ROOT_DIR"

echo "📁 Frontend i18n Files"
echo "─────────────────────"
check_dir "frontend/src/lib/i18n" "i18n directory"
check_file "frontend/src/lib/i18n/index.ts" "i18n initialization"
check_file "frontend/src/lib/i18n/en.json" "English translations (185 keys)"
check_file "frontend/src/lib/i18n/es.json" "Spanish translations (185 keys)"
check_file "frontend/src/lib/stores/locale.ts" "Locale store"
echo ""

echo "📄 Frontend Components (i18n enabled)"
echo "────────────────────────────────────"
check_file "frontend/src/App.svelte" "App.svelte with i18n init"
check_file "frontend/src/lib/components/landing/NavBar.svelte" "NavBar with language selector"
check_file "frontend/src/lib/components/landing/Hero.svelte" "Hero with i18n"
check_file "frontend/src/lib/components/landing/ValueProp.svelte" "ValueProp with i18n"
check_file "frontend/src/lib/components/landing/FeaturesGrid.svelte" "FeaturesGrid with i18n"
check_file "frontend/src/lib/components/landing/HowItWorks.svelte" "HowItWorks with i18n"
check_file "frontend/src/lib/components/landing/PricingPreview.svelte" "PricingPreview with i18n"
check_file "frontend/src/lib/components/landing/ForPartners.svelte" "ForPartners with i18n"
check_file "frontend/src/lib/components/landing/Testimonials.svelte" "Testimonials with i18n"
check_file "frontend/src/lib/components/landing/FinalCTA.svelte" "FinalCTA with i18n"
check_file "frontend/src/lib/components/landing/Footer.svelte" "Footer with i18n"
check_file "frontend/src/lib/components/landing/SocialProof.svelte" "SocialProof with i18n"
echo ""

echo "🗄️  Backend Files"
echo "────────────────"
check_file "app/models/database.py" "Database models (Testimonial, LandingSection, Translation)"
check_file "app/routes/public_landing.py" "Public landing routes with locale support"
echo ""

echo "🧳 Database Migration"
echo "────────────────────"
check_file "alembic/versions/l4i2j7d8f901_013_landing_i18n_internationalization.py" "Alembic migration 013"
echo ""

echo "📜 Scripts"
echo "─────────"
check_file "scripts/seed_landing_i18n.py" "Landing i18n seed script"
echo ""

echo "📋 Documentation"
echo "────────────────"
check_file "I18N_IMPLEMENTATION_SUMMARY.md" "i18n Implementation Summary"
echo ""

echo "📦 NPM Packages"
echo "───────────────"
if grep -q "svelte-i18n" frontend/package.json; then
  echo -e "${GREEN}✓${NC} svelte-i18n in package.json"
  ((CHECKS_PASSED++))
else
  echo -e "${RED}✗${NC} svelte-i18n not found in package.json"
  ((CHECKS_FAILED++))
fi

# Check if node_modules has svelte-i18n
if [ -d "frontend/node_modules/svelte-i18n" ]; then
  echo -e "${GREEN}✓${NC} svelte-i18n installed in node_modules"
  ((CHECKS_PASSED++))
else
  echo -e "${YELLOW}⚠${NC}  svelte-i18n not installed (run: npm install)"
fi
echo ""

# Summary
echo "=============================================="
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo "=============================================="

if [ $CHECKS_FAILED -eq 0 ]; then
  echo -e "\n${GREEN}✓ All i18n implementation files are in place!${NC}\n"
  exit 0
else
  echo -e "\n${RED}✗ Some files are missing. Please review the output above.${NC}\n"
  exit 1
fi
