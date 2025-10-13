# Transaction Model Migration Plan

## Current Situation

**Problem:** The current Transaction model was hastily aligned to match the existing database schema, which has inconsistent field types and naming. This was a temporary fix to get the View Details button working.

**Solution:** Replace with the proper production Transaction model which has:
- Proper ForeignKey relationships
- Better field naming
- Clearer choices
- Business logic (total_payment property)

---

## Comparison: Current vs Production Model

### Current Model (Temporary Fix)
```python
class Transaction(models.Model):
    sender = models.CharField(max_length=200)  # ❌ Should be ForeignKey
    receiver = models.CharField(max_length=200)  # ✅ OK
    phone = models.CharField(max_length=20)  # ✅ OK
    type = models.CharField(max_length=20)  # ⚠️ No choices
    sender_id = models.CharField(max_length=20)  # ❌ Duplicate/confusing
    department_id = models.CharField(max_length=20)  # ❌ Should be ForeignKey
    subcategory_id = models.CharField(max_length=20)  # ❌ Should be ForeignKey
    category_id = models.CharField(max_length=20)  # ❌ Should be ForeignKey
    vendor_supplier_id = models.CharField(max_length=200)  # ❌ Should be ForeignKey
    # ... many other inconsistent fields
```

### Production Model (Proper Structure)
```python
class Transaction(models.Model):
    sender = models.ForeignKey(User, ...)  # ✅ Proper relationship
    vendor_supplier = models.ForeignKey(User, ...)  # ✅ Proper relationship
    receiver = models.CharField(max_length=100)  # ✅ OK
    phone = models.CharField(max_length=50)  # ✅ OK
    department = models.ForeignKey(Department, ...)  # ✅ Proper relationship
    category = models.ForeignKey(BudgetCategory, ...)  # ✅ Proper relationship
    subcategory = models.ForeignKey(BudgetSubCategory, ...)  # ✅ Proper relationship
    type = models.CharField(choices=CAT_CHOICES)  # ✅ With choices
    payment_method = models.CharField(choices=PAY_CHOICES)  # ✅ With choices
    # ... clean, consistent structure
```

---

## Migration Strategy

### Option 1: Clean Slate (RECOMMENDED if data is not critical)
**Best if:** Development/staging environment, or data can be re-imported

1. **Backup existing data**
2. **Drop and recreate table with proper structure**
3. **Re-import data with proper relationships**

**Pros:**
- Clean, proper database schema
- No legacy issues
- Proper foreign key constraints

**Cons:**
- Requires data migration/re-import
- Some downtime

### Option 2: Gradual Migration (SAFER for production)
**Best if:** Production environment with critical data

1. **Create new fields alongside old ones**
2. **Migrate data gradually**
3. **Update code to use new fields**
4. **Remove old fields**

**Pros:**
- No data loss
- Minimal downtime
- Rollback possible

**Cons:**
- More complex
- Temporary database bloat
- Multiple deployment steps

---

## Recommended Approach: Clean Slate Migration

### Step 1: Backup Current Data

```bash
# Export current transactions
python manage.py shell -c "
import json
from finance.models import Transaction

transactions = Transaction.objects.all().values()
with open('transaction_backup.json', 'w') as f:
    json.dump(list(transactions), f, default=str, indent=2)

print(f'Backed up {len(transactions)} transactions')
"
```

### Step 2: Update Model Definition

Replace current Transaction model in `coda/finance/models/core.py` with:

```python
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

class Transaction(models.Model):
    """
    Production-ready Transaction model with proper relationships
    """
    # Category Choices
    CAT_CHOICES = [
        ("Salary", "Salary"),
        ("Health", "Health"),
        ("Transport", "Transport"),
        ("Food_Accomodation", "Food & Accomodation"),
        ("Internet_Airtime", "Internet & Airtime"),
        ("Recruitment", "Recruitment"),
        ("Labour", "Labour"),
        ("Management", "Management"),
        ("Electricity", "Electricity"),
        ("Construction", "Construction"),
        ("Other", "Other"),
    ]
    
    # Payment Method Choices
    PAY_CHOICES = [
        ("Cash", "Cash"),
        ("Mpesa", "Mpesa"),
        ("Check", "Check"),
        ("Other", "Other"),
    ]
    
    # User Relationships
    sender = models.ForeignKey(
        User,
        verbose_name=_("sender"),
        related_name="sent_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"is_staff": True, "is_active": True},
    )
    
    vendor_supplier = models.ForeignKey(
        User,
        verbose_name=_("vendor_supplier"),
        related_name="vendor_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True) & (Q(is_staff=True) | Q(category=6)),
    )
    
    receiver = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    
    # Department & Category Relationships
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    category = models.ForeignKey(
        'BudgetCategory',
        on_delete=models.CASCADE,
        related_name="transactions",
        blank=True,
        null=True
    )
    
    subcategory = models.ForeignKey(
        'BudgetSubCategory',
        on_delete=models.CASCADE,
        related_name="transactions",
        blank=True,
        null=True
    )
    
    # Transaction Details
    type = models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default="Other",
    )
    
    transaction_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    
    qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=1
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    transaction_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        null=True
    )
    
    payment_method = models.CharField(
        max_length=25,
        choices=PAY_CHOICES,
        default="Other",
    )
    
    # Computed Property
    @property
    def total_payment(self):
        """Calculate total payment amount"""
        if self.amount and self.qty:
            return self.amount * self.qty
        return self.amount or 0
    
    def get_absolute_url(self):
        return reverse("finance:transaction-detail", kwargs={"pk": self.pk})
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-transaction_date"]
    
    def __str__(self):
        return f"Transaction #{self.id} - {self.type}"
```

### Step 3: Create Migration

```bash
# Create new migration
python manage.py makemigrations finance

# This will create a migration to:
# 1. Drop old fields (sender_id, department_id, etc.)
# 2. Add proper ForeignKey fields
# 3. Update field definitions
```

### Step 4: Apply Migration (LOCAL FIRST!)

```bash
# Apply migration in local development
python manage.py migrate finance

# Verify migration worked
python manage.py shell -c "
from finance.models import Transaction
print(f'Transaction model ready: {Transaction._meta.get_fields()}')
"
```

### Step 5: Import Data with Proper Relationships

```python
# Create migration script: import_transactions.py
import json
from django.core.management.base import BaseCommand
from finance.models import Transaction, BudgetCategory, BudgetSubCategory
from accounts.models import Department, CustomerUser as User

class Command(BaseCommand):
    help = 'Import transactions with proper relationships'
    
    def handle(self, *args, **kwargs):
        with open('transaction_backup.json', 'r') as f:
            transactions = json.load(f)
        
        for t_data in transactions:
            # Map old data to new structure
            transaction = Transaction.objects.create(
                # Map sender_id to sender ForeignKey
                sender_id=t_data.get('sender_id'),
                
                # Map category_id to category ForeignKey
                category_id=t_data.get('category_id'),
                
                # Map subcategory_id to subcategory ForeignKey
                subcategory_id=t_data.get('subcategory_id'),
                
                # Map department_id to department ForeignKey
                department_id=t_data.get('department_id'),
                
                # Direct field mappings
                receiver=t_data.get('receiver'),
                phone=t_data.get('phone'),
                type=t_data.get('type', 'Other'),
                transaction_date=t_data.get('transaction_date'),
                receipt_link=t_data.get('receipt_link'),
                qty=t_data.get('qty', 1),
                amount=t_data.get('amount'),
                transaction_cost=t_data.get('transaction_cost', 0),
                description=t_data.get('description'),
                payment_method=t_data.get('payment_method', 'Other'),
            )
        
        self.stdout.write(self.style.SUCCESS(f'Imported {len(transactions)} transactions'))
```

### Step 6: Update Views to Use New Model

**Update drilldown.py:**
```python
# OLD (current)
recent_transactions = Transaction.objects.filter(subcategory=subcategory.id)

# NEW (with proper ForeignKey)
recent_transactions = Transaction.objects.filter(
    subcategory=subcategory
).select_related('sender', 'category', 'department')
```

**Update templates:**
```html
<!-- OLD (current) -->
{{ transaction.sender }}  <!-- This is CharField -->

<!-- NEW (with proper ForeignKey) -->
{{ transaction.sender.username }}  <!-- Access User object -->
{{ transaction.sender.get_full_name }}
```

### Step 7: Test Thoroughly

```bash
# Run comprehensive tests
python manage.py test finance

# Test View Details button
# Login: http://127.0.0.1:8000/accounts/login/
# Dashboard: http://127.0.0.1:8000/finance/budget-dashboard/coda/
# Click View Details on any category

# Verify all fields display correctly
# Verify relationships work
# Verify total_payment calculation
```

---

## Update Required Files

### Files to Update:

1. **coda/finance/models/core.py**
   - Replace Transaction model with production version

2. **coda/finance/views/budget/drilldown.py**
   - Update queries to use ForeignKey relationships
   - Update select_related() calls

3. **coda/finance/templates/finance/budgets/budget_category_detail.html**
   - Update template to access ForeignKey fields correctly
   - Use `transaction.sender.username` not `transaction.sender`

4. **coda/finance/admin.py**
   - Update TransactionAdmin to use proper field names
   - Add filter by sender, department, category

5. **coda/finance/forms_improved.py**
   - Update SmartTransactionForm to use new model fields
   - Add proper widgets for ForeignKey fields

---

## Benefits of Migration

### Before (Current State):
- ❌ Mixed CharField and ForeignKey types
- ❌ Confusing field names (sender + sender_id)
- ❌ No data validation
- ❌ No choices for type/payment_method
- ❌ No business logic (total_payment)
- ❌ Hard to query relationships

### After (Production Model):
- ✅ Proper ForeignKey relationships
- ✅ Clear, consistent field names
- ✅ Proper Django ORM usage
- ✅ Choices for type/payment_method
- ✅ Business logic (total_payment property)
- ✅ Easy to query with select_related/prefetch_related
- ✅ Proper database constraints

---

## Risks & Mitigation

### Risk 1: Data Loss
**Mitigation:**
- Backup before migration
- Test in local/staging first
- Export data as JSON
- Have rollback plan

### Risk 2: Broken Views
**Mitigation:**
- Update all views simultaneously
- Test each view after update
- Use comprehensive testing guide

### Risk 3: Foreign Key Constraint Errors
**Mitigation:**
- Verify all referenced IDs exist
- Handle null/invalid references
- Use SET_NULL for non-critical FKs

---

## Timeline

### Phase 1: Preparation (Day 1)
- [x] Document current state
- [ ] Backup production data
- [ ] Create migration plan

### Phase 2: Local Testing (Day 2)
- [ ] Update model locally
- [ ] Create and apply migrations
- [ ] Test all views and templates
- [ ] Verify data integrity

### Phase 3: Staging Deployment (Day 3)
- [ ] Deploy to staging
- [ ] Run migrations on staging
- [ ] Import data to staging
- [ ] Comprehensive testing

### Phase 4: Production Deployment (Day 4)
- [ ] Backup production database
- [ ] Deploy to production
- [ ] Run migrations
- [ ] Monitor for errors
- [ ] Verify all functionality

---

## Decision

**Recommendation:** Proceed with Clean Slate Migration

**Reason:**
1. Current model is a temporary fix
2. Production model is much cleaner
3. Proper relationships enable better features
4. Early enough in development to change

**Next Steps:**
1. Get user approval
2. Backup current data
3. Update model definition
4. Create and test migrations locally
5. Deploy to staging
6. Deploy to production

---

*Created: October 11, 2025*  
*Part of CODA Development Project*
