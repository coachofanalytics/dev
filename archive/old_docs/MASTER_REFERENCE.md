# CODA BUDGET SYSTEM - MASTER TECHNICAL REFERENCE
**Version 2.0 - Data-Driven Budget Platform**  
**Last Updated:** October 2, 2025  
**Status:** Phase 2 Complete, Phase 3 In Progress

---

## 📌 **QUICK CONTEXT** (Read This First)

### What We're Building:
A **data-driven budget system** that uses actual transaction data instead of guesses. The system learns from spending patterns and provides intelligent predictions.

### Core Philosophy:
**"Transactions are the source of truth"** - Everything flows from real spending data.

### Current State (October 2025):
- ✅ **Phase 1**: Data cleanup (95.6% categorized, dashboard bug fixed)
- ✅ **Phase 2**: Smart forms + AI predictions (intelligent categorization)
- 🚧 **Phase 3**: User drill-down views (budget category exploration)

---

## 🏗️ **SYSTEM ARCHITECTURE**

### Data Flow:
```
Transaction Entry (Smart Form)
    ↓
Auto-Categorization (AI Service)
    ↓
Transaction Database (Source of Truth)
    ↓
Budget Projections (Data Analysis)
    ↓
Dashboard Views (User Interface)
```

### Key Components:

#### 1. **Transaction System** (Source of Truth)
- **Model**: `Transaction` (`finance/models.py`)
- **Fields**: receiver, amount, category, subcategory, type (item), department, date
- **Total Records**: 366 transactions, $1.49M historical spending
- **Quality**: 95.6% categorized (350/366)

#### 2. **Smart Transaction Form** (Data Entry)
- **Form**: `SmartTransactionForm` (`finance/forms_improved.py`)
- **Template**: `smart_transaction_entry.html`
- **URL**: `/finance/transaction/smart-entry/`
- **Features**:
  - Receiver auto-complete with historical lookup
  - Category prediction based on receiver + amount + department
  - Cascading dropdowns: Category → Subcategory → Item
  - Real-time validation and warnings
  - Currency selection (enabled)

#### 3. **AI Prediction Service** (Intelligence)
- **Service**: `AIPredictionService` (`finance/services/ai_prediction_service.py`)
- **Capabilities**:
  - Predict category from receiver name (84% accuracy)
  - Suggest subcategory based on category selection
  - Recommend amount based on historical averages
  - Auto-fill description from patterns
- **Caching**: `AIPredictionCache` model stores learned patterns

#### 4. **Budget Models** (Planning)
- **Primary**: `Budget` model (266 active records, $837K total)
- **Projections**: `BudgetEstimateProjection` (13 AI-generated projections)
- **Categories**: `BudgetCategory` (14 categories) + `BudgetSubCategory` (subcategories)

#### 5. **Dashboard System** (Visualization)
- **Main**: `unified_budget_dashboard` (`views_unified_budget.py`)
- **URL**: `/finance/budget-dashboard/<company>/`
- **Tabs**: Overview, Estimation, Planning, Approvals, Analytics
- **Critical Fix**: Changed `Sum(qty)*Sum(price)` to `Sum(qty*price*cases)` (fixed 177x inflation bug)

---

## 💾 **DATABASE SCHEMA**

### Core Models:

```python
# Transaction (Source of Truth)
class Transaction(models.Model):
    sender = CharField                # Payer
    receiver = CharField              # Vendor/recipient
    vendor_supplier = ForeignKey      # Standardized vendor (future)
    phone = CharField
    department = ForeignKey           # Which department spent
    category = ForeignKey             # Primary category
    subcategory = ForeignKey          # Sub-category
    type = CharField                  # Item/service type
    amount = DecimalField             # USD amount
    currency = CharField              # Currency code
    qty = DecimalField                # Quantity
    transaction_cost = DecimalField   # Transaction fee
    transaction_date = DateTimeField
    payment_method = CharField
    description = TextField
    receipt_link = URLField
    location = CharField              # Office location (future)

# Budget (Planning)
class Budget(models.Model):
    company = ForeignKey
    department = ForeignKey
    category = ForeignKey
    subcategory = ForeignKey
    item_name = CharField
    quantity = DecimalField
    unit_price = DecimalField
    cases = DecimalField              # Multiplier
    budget_lead = ForeignKey
    date_from = DateField
    date_to = DateField
    is_active = BooleanField
    
    # Critical: total_amount calculation
    @property
    def total_amount(self):
        return (self.unit_price or 0) * (self.quantity or 0) * (self.cases or 1)

# BudgetEstimateProjection (AI-Generated Forecasts)
class BudgetEstimateProjection(models.Model):
    company = ForeignKey
    department = ForeignKey
    method = CharField                # "transaction_analysis", "historical_avg", etc.
    horizon = CharField               # "monthly", "quarterly", "yearly"
    estimates = JSONField             # {category_id: {monthly_avg, total_projection, confidence}}
    total_estimate = DecimalField
    status = CharField
    created_by = ForeignKey
    created_at = DateTimeField

# AIPredictionCache (Learning System)
class AIPredictionCache(models.Model):
    input_hash = CharField            # Hash of input parameters
    input_data = JSONField            # {receiver, department, amount}
    prediction = JSONField            # {category, subcategory, description}
    confidence = FloatField           # 0.0 - 1.0
    hit_count = IntegerField          # How many times reused
    last_used = DateTimeField
    is_validated = BooleanField       # User confirmed correct
```

---

## 🎯 **CRITICAL FIXES IMPLEMENTED**

### 1. **Dashboard Aggregation Bug** (Fixed Oct 2, 2025)
**Problem**: Budget totals inflated by 177x  
**Root Cause**: `Sum('quantity') * Sum('unit_price')` = wrong math  
**Solution**: `Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1))`  
**File**: `views_unified_budget.py` lines 164-174  
**Impact**: $148M → $837K (correct)

### 2. **Data Quality** (Improved from 60% → 95.6%)
**Problem**: 148 uncategorized transactions (40.4%)  
**Solution**: Built intelligent categorization engine  
**File**: `management/commands/categorize_transactions.py`  
**Rules**:
- KPLC → Utilities (electricity)
- Safaricom variations → IT/Software
- "boda" → Travel
- "salary" + amount range → Salaries
- 10 total categorization rules

### 3. **Smart Form Fields** (Oct 2, 2025)
**Problem**: Subcategory, Type, Currency fields not working  
**Solution**: Added explicit widgets with proper IDs  
**File**: `forms_improved.py`  
**Changes**:
- `subcategory`: Select widget with `id_subcategory`
- `type`: TextInput with datalist for autocomplete
- `currency`: Explicitly set `disabled=False`

### 4. **Admin 404** (Fixed Oct 2, 2025)
**Problem**: `/admin/finance/budgetestimateprojection/` → 404  
**Solution**: Registered models in admin  
**File**: `admin.py`  
**Registered**: BudgetEstimateProjection, Transaction, BudgetCategory, BudgetSubCategory

---

## 🔌 **API ENDPOINTS**

### Cascading Dropdown APIs:
```python
# Get subcategories for a category
GET /finance/api/subcategories/?category_id=5
Response: [{"id": 1, "name": "Electricity"}, ...]

# Get items for a subcategory
GET /finance/api/items/?subcategory_id=3
Response: [{"id": 1, "name": "Office Supplies"}, ...]

# Predict all fields from receiver
GET /finance/api/predict-all/?receiver=KPLC&department=3&amount=5000
Response: {
    "receiver_info": {"name": "KPLC", "transaction_count": 16, "avg_amount": 3242.88},
    "predictions": {
        "category_id": 5,
        "category_name": "Utilities",
        "subcategory_id": 12,
        "description": "Payment to KPLC",
        "estimated_amount": 4272.45,
        "confidence": 0.95
    }
}
```

### Budget APIs:
```python
# Get budget by category
GET /finance/api/budget-category/<category_id>/

# Get budget projections
GET /finance/api/budget-projections/

# Generate new projection
POST /finance/api/generate-projection/
Body: {"method": "transaction_analysis", "horizon": "yearly"}
```

---

## 📊 **DATA ANALYSIS INSIGHTS**

### Historical Spending (27 months, July 2022 - Oct 2024):
```
Total: $1,458,482 across 350 transactions

By Category:
1. Salaries/Wages:      $939K  (64.4%)  → Budget needed: $465K/year
2. Operational:         $183K  (12.6%)  → Budget needed: $91K/year
3. IT/Software:         $116K  (7.9%)   → Budget needed: $57K/year (NOT BUDGETED!)
4. Human Resources:     $88K   (6.0%)   → Budget needed: $43K/year
5. Utilities:           $52K   (3.6%)   → Budget needed: $26K/year

By Department:
1. HR:                  $1.11M (74.4%)  → 259 transactions
2. Management:          $111K  (7.6%)   → 47 transactions
3. Health:              $71K   (4.8%)   → 17 transactions
4. IT:                  $55K   (3.8%)   → 12 transactions

Monthly Average: $54,682
Annual Projection (with 10% growth): $721,949
Current Budget: $65,215 (1,007% increase needed!)
```

### Key Finding:
**The current budget is 11x too low.** Real spending is $722K/year, not $65K.

---

## 🛠️ **MANAGEMENT COMMANDS**

### Data Analysis:
```bash
# Full transaction analysis
python manage.py analyze_transaction_data

# Analyze uncategorized transactions
python manage.py analyze_uncategorized

# Generate budget projections from transaction data
python manage.py generate_budget_projections --months 12 --save
```

### Data Cleanup:
```bash
# Auto-categorize uncategorized transactions
python manage.py categorize_transactions --auto-assign

# Fix duplicate CodaBudget entries
python manage.py cleanup_duplicate_codabudgets

# Verify dashboard calculation fix
python manage.py verify_dashboard_fix
```

### AI/Predictions:
```bash
# Test AI prediction system
python manage.py test_ai_predictions --employee-id 74

# Test intelligent assignment
python manage.py test_intelligent_assignment --test-type=single
```

---

## 🎨 **USER INTERFACE**

### Main Entry Points:

1. **Budget Dashboard** (Main Hub)
   - URL: `/finance/budget-dashboard/coda/`
   - Tabs: Overview | Estimation | Planning | Approvals | Analytics
   - Features: Category drill-down, filtering, search

2. **Smart Transaction Entry** (Data Entry)
   - URL: `/finance/transaction/smart-entry/`
   - Features: Auto-complete, predictions, cascading dropdowns
   - Validation: Real-time, prevents bad data

3. **Category Detail** (Drill-Down - NEW!)
   - URL: `/finance/budget/coda/category/<id>/`
   - Shows: All items in category, transaction history, variance
   - Actions: Edit items, compare budget vs actual

4. **Item Edit** (Quick Edit - NEW!)
   - URL: `/finance/budget/item/<id>/edit/`
   - Features: Update quantity, price, description
   - AJAX: Can be inline or full page

### JavaScript Dependencies:
```html
<!-- Required in base template -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="{% static 'finance/js/budget-common.js' %}"></script>

<!-- In smart form template -->
<script>
// Initialize auto-complete
$('#id_receiver').on('blur', function() {
    triggerAutoFill();  // Calls /finance/api/predict-all/
});

// Initialize cascading dropdowns
$('#id_category').on('change', function() {
    loadSubcategories($(this).val());  // Calls /finance/api/subcategories/
});
</script>
```

---

## 🐛 **DEBUGGING GUIDE**

### Common Issues:

#### 1. Auto-fill Not Working
**Check Console For:**
```javascript
"=== SMART FORM INITIALIZING ==="  // Should appear on page load
"=== triggerAutoFill called ==="   // Should appear on receiver blur
"=== API SUCCESS ==="               // Should appear after API call
```

**If Missing:**
- jQuery not loaded → Check base template
- API 404 → Check URL routing
- API 500 → Check backend logs
- Fields not populating → Check field IDs match (id_category, id_subcategory)

#### 2. Cascading Dropdowns Not Working
**Check:**
1. Category change event binding: `$('#id_category').on('change')`
2. API endpoint works: `/finance/api/subcategories/?category_id=1`
3. Console shows: "CATEGORY CHANGE EVENT TRIGGERED"
4. Subcategory dropdown ID: `#id_subcategory` exists

#### 3. Dashboard Shows Wrong Totals
**Verify Fix:**
```python
# WRONG (causes 177x inflation):
Sum('quantity') * Sum('unit_price')

# CORRECT:
Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), output_field=DecimalField())
```

---

## 🚀 **DEPLOYMENT**

### Environment:
- **UAT**: `codamakutano.herokuapp.com`
- **Production**: `codatrainingapp.herokuapp.com`

### Deploy Command:
```bash
git add -A
git commit -m "Your message"
git push heroku 25.10_CODA_DEV_CM:main
```

### Post-Deployment Checklist:
```bash
# 1. Verify URL routing
heroku run "cd coda && python manage.py show_urls" --app codamakutano | grep finance

# 2. Run migrations
heroku run "cd coda && python manage.py migrate" --app codamakutano

# 3. Collect static files
heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano

# 4. Test critical paths
curl https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
curl https://codamakutano.herokuapp.com/finance/api/predict-all/?receiver=KPLC

# 5. Check data quality
heroku run "cd coda && python manage.py analyze_transaction_data" --app codamakutano
```

---

## 📁 **FILE STRUCTURE**

```
coda/finance/
├── models.py                      # All models (Transaction, Budget, etc.)
├── admin.py                       # Admin registrations (fixed Oct 2)
├── forms_improved.py              # Smart forms with validation
├── views_unified_budget.py        # Main dashboard (fixed aggregation)
├── views_budget_drilldown.py      # Category detail views (NEW Oct 2)
├── views_smart_transaction.py     # Transaction entry views
├── urls.py                        # URL routing
├── services/
│   └── ai_prediction_service.py   # AI predictions and caching
└── management/commands/
    ├── analyze_transaction_data.py     # Data analysis
    ├── categorize_transactions.py      # Auto-categorization
    ├── generate_budget_projections.py  # Budget forecasting
    └── verify_dashboard_fix.py         # Validation
```

---

## 🎓 **DEVELOPMENT WORKFLOW**

### Adding New Feature:
1. **Analyze Data**: What does transaction data tell us?
2. **Create Model** (if needed): Add to `models.py`
3. **Build Service**: Logic in `services/`
4. **Create View**: In appropriate `views_*.py`
5. **Add URL**: In `urls.py`
6. **Create Template**: In `templates/finance/`
7. **Write Tests**: Management command or unit test
8. **Deploy to UAT**: Test with real data
9. **Document**: Update this file

### Testing Cycle:
```bash
# Local testing
python manage.py test_feature
python manage.py runserver
# Test at http://localhost:8000

# UAT testing
git push heroku main
heroku run "cd coda && python manage.py test_feature" --app codamakutano
# Test at https://codamakutano.herokuapp.com
```

---

## 📈 **METRICS & MONITORING**

### Key Metrics:
- **Data Quality**: 95.6% categorized (target: 100%)
- **Budget Accuracy**: Fixed 177x inflation, now correct
- **Prediction Accuracy**: 84% for auto-categorization
- **User Adoption**: Track smart form usage vs old form

### Monitoring Commands:
```bash
# Daily data quality check
python manage.py analyze_transaction_data

# Weekly categorization audit
python manage.py analyze_uncategorized

# Monthly budget projection update
python manage.py generate_budget_projections --save
```

---

## 🔮 **FUTURE ROADMAP**

### Phase 3 (Current):
- ✅ Admin model registration
- ✅ Form field fixes
- ✅ User drill-down views
- 🚧 Make categories clickable in dashboard
- 🚧 Budget vs Actual comparison view

### Phase 4 (Planned):
- Bank integration (import transactions from CSV/API)
- Vendor lookup table (standardize receiver names)
- Location field separation (Matunda/Makutano)
- Automated reconciliation

### Phase 5 (Future):
- Real-time AI predictions (external API like OpenAI)
- Forecasting with seasonality detection
- Automated budget proposals
- Mobile app integration

---

## 🆘 **SUPPORT**

### Common Questions:

**Q: Why is my transaction not auto-categorized?**  
A: Check if receiver name matches existing patterns. Run `analyze_uncategorized` to see why.

**Q: How do I add a new category?**  
A: Add via Django admin `/admin/finance/budgetcategory/`. Updates cascade automatically.

**Q: Dashboard totals seem wrong?**  
A: Verify the aggregation fix is deployed. Run `verify_dashboard_fix` command.

**Q: Smart form not predicting?**  
A: Open browser console (F12) and check for JavaScript errors. Should see "API SUCCESS" message.

---

**This is the single source of truth for CODA Budget System technical documentation.**  
**Always refer to this file when onboarding new developers or troubleshooting issues.**

*Last Updated: October 2, 2025*  
*Maintained by: CODA Development Team*

