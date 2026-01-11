# Sync Production Data to Local SQLite

Pull real production tier classifications and budget data to your local SQLite database for examination and testing.

## Why?

- 🔍 **Examine real tier classifications** from $1.49M dataset
- 🧪 **Test with actual categories** instead of mock data
- 💡 **See variance thresholds** calculated from real patterns
- 🚀 **Faster local development** with production-like data

## Prerequisites

1. Python virtual environment activated
2. `dj-database-url` installed: `pip install dj-database-url`
3. Production database URL from Heroku

## Step 1: Get Production Database URL

**Option A: From Heroku Dashboard**
- Go to: https://dashboard.heroku.com/apps/codatrainingapp/settings
- Click "Reveal Config Vars"
- Copy the `DATABASE_URL` value

**Option B: If you have Heroku CLI**
```bash
heroku config:get DATABASE_URL --app codatrainingapp
```

The URL looks like:
```
postgres://user:password@host.compute.amazonaws.com:5432/database
```

## Step 2: Run the Sync

**Option A: Pass URL as argument**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate

python scripts/pull_prod_data_to_local.py --database-url "postgres://..."
```

**Option B: Set environment variable**
```bash
export DATABASE_URL="postgres://..."
python scripts/pull_prod_data_to_local.py
```

## Step 3: Examine the Data

### In Django Shell
```bash
cd coda
python manage.py shell --settings=coda_project.coda_settings.local_settings
```

```python
from finance.models import BudgetCategory

# See all Tier A (Auto-Approve) categories
tier_a = BudgetCategory.objects.filter(approval_tier='A')
for cat in tier_a:
    print(f"{cat.name}: ${cat.typical_monthly_amount}/mo (±{cat.variance_threshold}%)")

# See Tier B (Priority-Based) categories
tier_b = BudgetCategory.objects.filter(approval_tier='B')
for cat in tier_b.order_by('-typical_monthly_amount'):
    print(f"{cat.name}: ${cat.typical_monthly_amount}/mo")

# Test auto-approval logic
from decimal import Decimal
rent = BudgetCategory.objects.get(name__icontains='rent')
should_approve, reason = rent.should_auto_approve(Decimal('2100.00'))
print(f"Should approve $2100? {should_approve} - {reason}")
```

### Run Local Server
```bash
python manage.py runserver --settings=coda_project.coda_settings.local_settings
```

Visit: http://localhost:8000/finance/tier-management/coda/

### Run Tests with Real Data
```bash
python manage.py test finance.tests.test_budget_tier_system --settings=coda_project.coda_settings.local_settings
```

## What Gets Synced?

- ✅ All 25 Budget Categories
- ✅ Tier classifications (A/B/C)
- ✅ Typical monthly amounts (from $1.49M analysis)
- ✅ Variance thresholds
- ✅ Recurring pattern flags
- ✅ Auto-approval enabled/disabled status
- ✅ Last analysis timestamps

## Example Output

```
🔄 Pulling Production Data to Local SQLite
📡 Source: ec2-xxx.compute.amazonaws.com
💾 Destination: Local SQLite (coda/db.sqlite3)

🔌 Connecting to production database...
✅ Connected to production

📥 Fetching Budget Categories from production...
✅ Fetched 25 categories

💾 Saving to local SQLite...
   + Rent (Tier A)
   + Salaries and Wages (Tier B)
   + IT and Software (Tier B)
   ...

✅ Saved 25 categories to local database

📊 Category Summary:
   Total: 25
   - Tier A: 1
   - Tier B: 5
   - Tier C: 19
   Auto-approval enabled: 1
   With transaction data: 13

🔍 Tier A Categories (Auto-Approve):
   - Rent: $2,000.00/mo (variance: 15%)

🔍 Top Tier B Categories (Priority-Based):
   - Salaries and Wages: $33,460.00/mo
   - IT and Software: $8,234.50/mo
   - Utilities: $5,678.90/mo

✅ Sync Complete!
```

## Troubleshooting

**Error: `dj-database-url` not found**
```bash
pip install dj-database-url
```

**Error: Connection timeout**
- Check your internet connection
- Verify the database URL is correct
- Check if Heroku database allows external connections

**Error: Permission denied**
- Make sure you have read access to production database
- Check if your IP is whitelisted in Heroku

## Safety Note

✅ **READ ONLY** - This script only reads from production, never writes  
✅ **LOCAL ONLY** - Data is saved to your local SQLite, not pushed anywhere  
✅ **NO RISK** - Production database is not modified in any way

---

**Created:** October 16, 2025  
**Purpose:** Enable local examination of Phase 2 tier classifications with real production data

