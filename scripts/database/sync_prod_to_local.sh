#!/bin/bash
# Sync Production Data to Local SQLite
# Downloads tier classifications and budget data from production for local examination

set -e  # Exit on error

echo "🔄 Syncing Production Data to Local SQLite"
echo "=========================================="

# Configuration
PROD_APP="codatrainingapp"  # Production Heroku app
LOCAL_SETTINGS="coda_project.coda_settings.local_settings"
DATA_DIR="/tmp/coda_prod_sync"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create data directory
mkdir -p $DATA_DIR
cd "$(dirname "$0")/.."  # Go to project root

echo -e "\n${BLUE}📡 Source:${NC} ${PROD_APP}.herokuapp.com"
echo -e "${BLUE}💾 Destination:${NC} Local SQLite (coda/db.sqlite3)"

# Step 1: Export Budget Categories from Production
echo -e "\n${YELLOW}Step 1: Exporting Budget Categories...${NC}"
heroku run "cd coda && python manage.py dumpdata finance.BudgetCategory --indent=2 --natural-foreign --natural-primary" --app $PROD_APP > $DATA_DIR/budget_categories.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Exported Budget Categories${NC}"
else
    echo -e "❌ Failed to export categories"
    exit 1
fi

# Step 2: Create local database with migrations
echo -e "\n${YELLOW}Step 2: Setting up local SQLite database...${NC}"
cd coda

# Run migrations to create schema
python manage.py migrate --settings=$LOCAL_SETTINGS

echo -e "${GREEN}✅ Database schema created${NC}"

# Step 3: Load data into local database
echo -e "\n${YELLOW}Step 3: Loading production data...${NC}"
python manage.py loaddata $DATA_DIR/budget_categories.json --settings=$LOCAL_SETTINGS

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Data loaded successfully${NC}"
else
    echo -e "❌ Failed to load data"
    exit 1
fi

# Step 4: Show summary
echo -e "\n${YELLOW}Step 4: Data Summary${NC}"
python manage.py shell --settings=$LOCAL_SETTINGS <<EOF
from finance.models import BudgetCategory

total = BudgetCategory.objects.count()
tier_a = BudgetCategory.objects.filter(approval_tier='A').count()
tier_b = BudgetCategory.objects.filter(approval_tier='B').count()
tier_c = BudgetCategory.objects.filter(approval_tier='C').count()
auto_enabled = BudgetCategory.objects.filter(auto_approve_enabled=True).count()
with_data = BudgetCategory.objects.exclude(typical_monthly_amount__isnull=True).count()

print(f"\n📊 Budget Categories Synced:")
print(f"   Total: {total}")
print(f"   - Tier A (Auto-Approve): {tier_a}")
print(f"   - Tier B (Priority-Based): {tier_b}")
print(f"   - Tier C (Strategic): {tier_c}")
print(f"   Auto-approval enabled: {auto_enabled}")
print(f"   With transaction data: {with_data}")

print("\n🔍 Tier A Categories (Auto-Approve):")
for cat in BudgetCategory.objects.filter(approval_tier='A'):
    print(f"   - {cat.name}: \${cat.typical_monthly_amount or 0:.2f}/mo (variance: {cat.variance_threshold}%)")

print("\n🔍 Tier B Categories (Priority-Based):")
for cat in BudgetCategory.objects.filter(approval_tier='B')[:5]:
    print(f"   - {cat.name}: \${cat.typical_monthly_amount or 0:.2f}/mo")
EOF

echo -e "\n${GREEN}✅ Sync Complete!${NC}"
echo -e "\n${BLUE}💡 Next Steps:${NC}"
echo "   1. Examine tier classifications:"
echo "      python manage.py shell --settings=$LOCAL_SETTINGS"
echo ""
echo "   2. Run tier management UI locally:"
echo "      python manage.py runserver --settings=$LOCAL_SETTINGS"
echo "      Visit: http://localhost:8000/finance/tier-management/coda/"
echo ""
echo "   3. Test auto-approval logic with real categories:"
echo "      python manage.py test finance.tests.test_budget_tier_system --settings=$LOCAL_SETTINGS"
echo ""
echo "   4. Re-run tier classification on local data:"
echo "      python manage.py classify_budget_category_tiers --analyze"

