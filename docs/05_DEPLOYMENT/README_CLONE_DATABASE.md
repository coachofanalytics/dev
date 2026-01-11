# Clone Production Database to Local

Create an **exact copy** of production PostgreSQL database locally for safe development, testing, and learning.

## 🎯 Why Clone the Entire Database?

### **Before (Just Budget Categories):**
- ❌ Missing relationships between tables
- ❌ Can't test complex queries
- ❌ Don't see real data patterns
- ❌ Migrations untested on prod-like data

### **After (Full Database Clone):**
- ✅ **Complete production structure** - all tables, relationships, indexes, constraints
- ✅ **Real data patterns** - actual user data, transactions, budgets ($1.49M dataset)
- ✅ **Safe testing** - test migrations, queries, features without risk
- ✅ **Learn production** - understand how data is actually structured
- ✅ **Catch issues early** - find problems before they hit production
- ✅ **Realistic performance testing** - test with production data volumes

## 🚀 Quick Start

### **Prerequisites:**
1. **PostgreSQL installed locally**
   ```bash
   # macOS
   brew install postgresql@14
   brew services start postgresql@14
   
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo service postgresql start
   ```

2. **Heroku CLI installed** (if not already)
   ```bash
   brew install heroku/brew/heroku
   heroku login
   ```

### **Run the Clone:**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
chmod +x scripts/clone_prod_database.sh
./scripts/clone_prod_database.sh
```

Choose **Option 1: Full PostgreSQL clone**

## 📋 What Happens During Clone?

### **Step 1: Create Heroku Backup**
- Heroku creates a new backup of production database
- Happens on Heroku servers (no downtime)
- Usually takes 1-5 minutes depending on size

### **Step 2: Download Backup**
- Downloads `.dump` file to `/tmp/coda_prod_latest.dump`
- Compressed PostgreSQL backup format
- Contains all tables, data, indexes, constraints

### **Step 3: Prepare Local Database**
- Creates new PostgreSQL database: `coda_prod_clone`
- Drops existing if you confirm
- Fresh, clean database ready for restore

### **Step 4: Restore Backup**
- Runs `pg_restore` to load production data
- Restores all tables, data, relationships
- Creates indexes and constraints
- May show warnings (normal for permission issues)

### **Step 5: Configure Django**
- Creates `local_prod_clone_settings.py`
- Points Django to cloned database
- Sets up local development settings

## 🎁 What You Get

After cloning, you have an **exact snapshot** of production:

### **All Tables:**
```sql
-- Finance tables
finance_transaction (all $1.49M in transactions)
finance_budgetcategory (with tier classifications)
finance_budgetrequest (all budget requests)
finance_budget (all budgets)
finance_payment_information
finance_payment_history
... and 100+ more tables

-- User tables
accounts_customeruser (all users)
accounts_department
accounts_loginhistory

-- Management tables
management_task
management_taskhistory
management_meetings

-- And everything else!
```

### **All Data:**
- 📊 **Transactions:** $1,458,482.32 over 27 months
- 👥 **Users:** All production users (with passwords hashed)
- 💼 **Budgets:** All budget requests and approvals
- 🎯 **Tier Classifications:** All calculated tier data
- 📈 **Historical Data:** Complete audit trails
- 🔗 **Relationships:** All foreign keys intact

### **All Structure:**
- ✅ Indexes for performance
- ✅ Constraints for data integrity
- ✅ Sequences for auto-increment
- ✅ Triggers (if any)
- ✅ Views (if any)

## 💡 How to Use the Clone

### **1. Django Shell (Explore Data)**
```bash
cd coda
python manage.py shell --settings=coda_project.coda_settings.local_prod_clone_settings
```

```python
from finance.models import BudgetCategory, Transaction, BudgetRequest
from accounts.models import CustomerUser
from decimal import Decimal

# See real tier classifications
tier_a = BudgetCategory.objects.filter(approval_tier='A')
for cat in tier_a:
    print(f"{cat.name}: ${cat.typical_monthly_amount}/mo")

# See real transactions
trans = Transaction.objects.all()[:10]
for t in trans:
    print(f"{t.transaction_date}: {t.description} - ${t.amount}")

# See real budget requests
requests = BudgetRequest.objects.filter(status='approved')[:10]
for req in requests:
    print(f"Request #{req.id}: {req.purpose} - ${req.amount}")

# Count everything
print(f"\nTotal Transactions: {Transaction.objects.count()}")
print(f"Total Budget Requests: {BudgetRequest.objects.count()}")
print(f"Total Users: {CustomerUser.objects.count()}")
```

### **2. Run Django Server (UI Testing)**
```bash
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings
```

**Visit these URLs with REAL data:**
- http://localhost:8000/finance/tier-management/coda/
- http://localhost:8000/finance/budget-dashboard/coda/
- http://localhost:8000/finance/budget-requests/

**Test features with production data!**

### **3. SQL Queries (Deep Dive)**
```bash
psql coda_prod_clone
```

```sql
-- See all tables
\dt

-- Describe a table
\d+ finance_budgetcategory

-- Real queries
SELECT approval_tier, COUNT(*), 
       SUM(typical_monthly_amount) as total_monthly
FROM finance_budgetcategory 
GROUP BY approval_tier;

-- See transaction patterns
SELECT 
    category_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM finance_transaction
GROUP BY category_id
ORDER BY total_amount DESC
LIMIT 10;

-- See budget request patterns
SELECT status, COUNT(*), AVG(amount)
FROM finance_budgetrequest
GROUP BY status;
```

### **4. Test Migrations Safely**
```bash
# Create a new migration
python manage.py makemigrations --settings=coda_project.coda_settings.local_prod_clone_settings

# Test it on production data!
python manage.py migrate --settings=coda_project.coda_settings.local_prod_clone_settings

# If it works here, it'll work in production
```

### **5. Test New Features**
```python
# Test auto-approval with real categories
from finance.models import BudgetCategory, BudgetRequest
from finance.services.smart_approval_service import SmartApprovalService

# Get real Rent category
rent = BudgetCategory.objects.get(name__icontains='rent')

# Test with different amounts
service = SmartApprovalService()
print(rent.should_auto_approve(Decimal('2000')))  # Typical
print(rent.should_auto_approve(Decimal('2200')))  # Slight increase
print(rent.should_auto_approve(Decimal('3000')))  # Exceeds variance
```

### **6. Performance Testing**
```bash
# Test queries on production volume
python manage.py shell --settings=coda_project.coda_settings.local_prod_clone_settings
```

```python
import time
from finance.models import Transaction

# Test query performance
start = time.time()
result = Transaction.objects.filter(
    transaction_date__year=2024,
    amount__gt=1000
).select_related('category').count()
print(f"Query took: {time.time() - start:.3f}s")
print(f"Found: {result} transactions")
```

## 🔄 Refreshing the Clone

Production changes daily. To get latest data:

```bash
# Simply re-run the clone script
./scripts/clone_prod_database.sh
```

**How often to refresh:**
- 📅 **Weekly:** For active development
- 📅 **Before major changes:** To test with latest data
- 📅 **After prod updates:** To sync new features

## 🛡️ Safety & Privacy

### **✅ Safe:**
- Clone is READ from production (no writes)
- Local database is completely isolated
- Changes to clone don't affect production
- Can drop/recreate clone anytime

### **⚠️ Sensitive Data:**
- Contains real production data (user emails, amounts, etc.)
- Keep local database secure
- Don't commit database files to git
- Don't share database dumps publicly

### **🔒 Password Hashing:**
- User passwords are hashed (Django default)
- Can't see original passwords
- Safe to work with user data

## 📊 Database Size Examples

**Typical CODA Production Database:**
- Size: ~100-500 MB (depending on data)
- Tables: ~150 tables
- Transactions: 366 records ($1.49M)
- Users: Varies
- Download time: 30-60 seconds
- Restore time: 1-2 minutes

## 🐛 Troubleshooting

### **Error: PostgreSQL not installed**
```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### **Error: Heroku CLI not found**
```bash
brew install heroku/brew/heroku
heroku login
```

### **Error: Permission denied to create database**
```bash
# Give your user permission
createuser -s $USER
```

### **Error: Database exists**
- Script will ask if you want to drop it
- Or manually: `dropdb coda_prod_clone`

### **Warnings during restore**
- Some warnings are normal (permissions, ownership)
- Data is still restored correctly
- Check with: `psql coda_prod_clone -c "\dt"`

## 🎯 Use Cases

### **1. Learning Production Structure**
```sql
-- See how tables are related
\d+ finance_budgetrequest

-- See indexes
\di

-- See constraints
\d+ finance_transaction
```

### **2. Testing Phase 2 with Real Data**
- Test tier classifications on actual categories
- Test auto-approval with real amounts
- Test variance checking with real patterns

### **3. Debugging Production Issues**
- Reproduce bugs with actual data
- Test fixes before deploying
- Understand data patterns causing issues

### **4. Performance Optimization**
- Test query performance on real volumes
- Optimize slow queries
- Test indexes

### **5. Training & Demos**
- Show real system behavior
- Train new developers
- Demo features with real data

## 🆚 Comparison

| Feature | Partial Sync | Full Clone |
|---------|-------------|------------|
| **Speed** | Fast (seconds) | Slow (minutes) |
| **Size** | Small (~1 MB) | Large (~100-500 MB) |
| **Tables** | 1-2 tables | All 150+ tables |
| **Data** | Budget categories only | Everything |
| **Relationships** | ❌ Missing | ✅ Complete |
| **Testing** | Limited | Comprehensive |
| **Use Case** | Quick checks | Full development |

**Recommendation:** Use **Full Clone** for serious development and testing

## 📝 Summary

**Before running code on production, test it on the clone:**

```bash
# 1. Clone production
./scripts/clone_prod_database.sh

# 2. Test your changes
cd coda
python manage.py shell --settings=coda_project.coda_settings.local_prod_clone_settings

# 3. Run migrations
python manage.py migrate --settings=coda_project.coda_settings.local_prod_clone_settings

# 4. Test features
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# 5. If everything works on clone → safe to deploy to production!
```

---

**Created:** October 16, 2025  
**Purpose:** Safe local development with production-identical database  
**Benefit:** Catch issues before they hit production 🛡️

