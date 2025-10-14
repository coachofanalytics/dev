# Investor Schema Mismatch Issue

**Date:** October 13, 2025  
**Error:** `ProgrammingError: column investing_investor_information.contract_submitted_date does not exist`  
**Location:** `/finance/pay/` view

---

## 🔍 **ROOT CAUSE**

### **The Problem:**
The `Investor_Information` model inherits from `ContractBase`, which defines `contract_submitted_date` field. However, the production database table doesn't have this column.

### **Why This Happened:**

1. **Model Inheritance Changed:**
   ```python
   class Investor_Information(ContractBase, DocumentMixin, StatusMixin):
       # ContractBase provides: contract_submitted_date, company_rep, client_signature, etc.
   ```

2. **Database Out of Sync:**
   - Migration `0001_initial.py` creates table WITH `contract_submitted_date`
   - But production database was created BEFORE `ContractBase` was introduced
   - OR migrations weren't run after refactoring

3. **Query Triggers Error:**
   ```python
   # Line 2149 in finance/views.py
   payment_info = (
       Investor_Information.objects.filter(investor=request.user.id)
       .order_by("-contract_date")
       .first()
   )
   ```
   Django ORM tries to SELECT all fields including `contract_submitted_date`, but column doesn't exist.

---

## ⚡ **QUICK FIX (Applied)**

### **Graceful Error Handling:**
```python
except:
    try:
        payment_info = (
            Investor_Information.objects.filter(investor=request.user.id)
            .order_by("-contract_date")
            .first()
        )
    except Exception as e:
        # Handle case where Investor_Information table schema is outdated
        print(f"Error fetching investor info: {e}")
        payment_info = None
```

**What This Does:**
- ✅ Prevents 500 error
- ✅ App continues to function
- ✅ Logs the error for investigation
- ⚠️ Investor payment info won't display (but won't crash)

---

## 🎯 **PROPER FIX (Required)**

### **Run Missing Migrations:**

**Step 1: Check Current State**
```bash
heroku run "cd coda && python manage.py showmigrations investing" --app codamakutano
```

**Step 2: Check What's Missing**
```bash
# Compare local migrations vs production
heroku run "cd coda && python manage.py migrate investing --plan" --app codamakutano
```

**Step 3: Run Migrations**
```bash
heroku run "cd coda && python manage.py migrate investing" --app codamakutano
```

**Step 4: Verify**
```bash
# Check table schema
heroku pg:psql --app codamakutano
\d investing_investor_information
\q
```

---

## 📊 **Expected Changes**

When migrations run, these columns will be added to `investing_investor_information`:

```sql
ALTER TABLE investing_investor_information 
ADD COLUMN contract_submitted_date TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE investing_investor_information 
ADD COLUMN company_rep VARCHAR(255);

ALTER TABLE investing_investor_information 
ADD COLUMN client_signature VARCHAR(100);

-- Plus other fields from ContractBase, DocumentMixin, StatusMixin
```

---

## 🔄 **Migration Strategy**

### **Option 1: Run Now (Recommended)**
- ✅ Low risk (adds columns, doesn't modify existing data)
- ✅ Non-breaking (new columns have defaults)
- ✅ Quick (< 1 second for small table)

### **Option 2: Create New Migration**
If current migrations don't align, create a new one:

```bash
cd coda
python manage.py makemigrations investing
# Review the migration file
python manage.py migrate investing
```

---

## ⚠️ **IMPACT ANALYSIS**

### **Current State (With Quick Fix):**
- ✅ App doesn't crash
- ❌ Investor payment info not displayed
- ⚠️ Any code relying on `contract_submitted_date` will fail silently

### **After Proper Fix:**
- ✅ App fully functional
- ✅ Investor payment info displays correctly
- ✅ All ContractBase fields available
- ✅ No more schema mismatches

---

## 📝 **Related Issues**

This is similar to the admin config mismatch issues we fixed earlier:
- **LoanProduct:** Admin referenced non-existent fields
- **LoanApplication:** Admin referenced non-existent fields  
- **Investor_Information:** Model references non-existent columns

**Pattern:** Code/models are ahead of database schema.

**Solution:** Always run migrations after model changes!

---

## ✅ **ACTION ITEMS**

### **Immediate (Done):**
- [x] Apply quick fix to prevent crashes
- [x] Document the issue
- [x] Commit and deploy

### **Next Steps (To Do):**
- [ ] Run migrations on UAT: `heroku run "cd coda && python manage.py migrate investing" --app codamakutano`
- [ ] Verify table schema matches model
- [ ] Test `/finance/pay/` endpoint
- [ ] Remove try-except workaround (once migrations run)
- [ ] Add to deployment checklist: "Always run migrations"

---

## 🎓 **LESSON LEARNED**

**Always run migrations after:**
1. Model field changes
2. Model inheritance changes
3. Adding mixins with fields
4. Refactoring model structure

**Check Before Deploying:**
```bash
# Check for pending migrations
python manage.py showmigrations

# Check for model/DB mismatches
python manage.py makemigrations --check --dry-run
```

---

**Status:** Quick fix deployed ✅  
**Next:** Run proper migrations in UAT ⏳  
**Priority:** Medium (app works, but feature broken)

