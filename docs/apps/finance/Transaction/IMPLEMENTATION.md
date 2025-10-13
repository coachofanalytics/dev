# Transaction System - Implementation

## Data Model

### Transaction Model
**Location:** `coda/finance/models/core.py`

**Complete Schema:**
```python
class Transaction(models.Model):
    """
    Source of truth for all financial transactions
    
    Philosophy: "Transactions are the source of truth" - all budget 
    decisions flow from real spending data, not guesses.
    """
    # Parties
    sender = models.CharField(max_length=255)  # Payer
    receiver = models.CharField(max_length=255)  # Vendor/recipient
    vendor_supplier = models.ForeignKey(User, related_name='transactions_as_vendor')
    phone = models.CharField(max_length=20)
    
    # Organization
    department = models.ForeignKey('Department', null=True)
    company = models.ForeignKey('Company')
    
    # Categorization (Hierarchical)
    category = models.ForeignKey('BudgetCategory', null=True)
    subcategory = models.ForeignKey('BudgetSubcategory', null=True)
    type = models.CharField(max_length=100, blank=True)  # Item/service type
    
    # Financial Details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Transaction Details
    transaction_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50)
    description = models.TextField()
    receipt_link = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)  # Office location
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Historical Data (July 2022 - Oct 2024):**
- **Total Records:** 366 transactions
- **Total Value:** $1,458,482
- **Time Period:** 27 months
- **Data Quality:** 95.6% categorized (350/366)

**Source:** MASTER_REFERENCE.md

## AI Prediction Service

**Location:** `coda/finance/services/ai_prediction_service.py`

### Overview
Intelligent prediction system that learns from historical transaction patterns to suggest categorization and amounts.

**Capabilities:**
- Predict category from receiver name (84% accuracy)
- Suggest subcategory based on category selection
- Recommend amount based on historical averages
- Auto-fill description from patterns

**Caching:** Uses `AIPredictionCache` model to store learned patterns

### AIPredictionCache Model
```python
class AIPredictionCache(models.Model):
    """Stores learned prediction patterns for performance"""
    input_hash = models.CharField(max_length=64)  # Hash of input parameters
    input_data = models.JSONField()  # {receiver, department, amount}
    prediction = models.JSONField()  # {category, subcategory, description}
    confidence = models.FloatField()  # 0.0 - 1.0
    hit_count = models.IntegerField(default=0)  # Reuse tracking
    last_used = models.DateTimeField(auto_now=True)
    is_validated = models.BooleanField(default=False)  # User confirmed correct
```

### Prediction Algorithm:
1. **Extract keywords** from receiver name and description
2. **Match against historical** transactions (same receiver, similar amount)
3. **Weight by frequency** and recency (recent patterns weighted higher)
4. **Calculate confidence** based on match strength
5. **Return top 3 suggestions** with confidence scores
6. **Cache result** for future reuse

### API Endpoint:
```python
# Predict all fields from receiver
GET /finance/api/predict-all/?receiver=KPLC&department=3&amount=5000

Response: {
    "receiver_info": {
        "name": "KPLC",
        "transaction_count": 16,
        "avg_amount": 3242.88
    },
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

**Accuracy:** 84% for category prediction (tested on historical data)

## Auto-Categorization Engine

**Location:** `coda/finance/management/commands/categorize_transactions.py`

### Overview
Intelligent categorization system that automatically assigns categories to transactions based on pattern matching rules.

**Accuracy:** 84% successful auto-categorization  
**Impact:** Improved data quality from 40.4% → 95.6% categorized

### Complete Categorization Rules:
```python
CATEGORIZATION_RULES = {
    # Utilities
    'KPLC': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'Kenya Power': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'Nairobi Water': {'category': 'Utilities', 'subcategory': 'Water'},
    
    # IT & Communications
    'Safaricom': {'category': 'IT & Software', 'subcategory': 'Communications'},
    'Airtel': {'category': 'IT & Software', 'subcategory': 'Communications'},
    'Telkom': {'category': 'IT & Software', 'subcategory': 'Communications'},
    
    # Travel
    'boda': {'category': 'Travel', 'subcategory': 'Local Transport'},
    'uber': {'category': 'Travel', 'subcategory': 'Local Transport'},
    'taxi': {'category': 'Travel', 'subcategory': 'Local Transport'},
    'flight': {'category': 'Travel', 'subcategory': 'Air Travel'},
    
    # Salaries (amount-based)
    'salary': {'category': 'Salaries and Wages', 'amount_range': (10000, 100000)},
    'wages': {'category': 'Salaries and Wages'},
    'payroll': {'category': 'Salaries and Wages'},
    
    # Office & Supplies
    'office': {'category': 'Office Supplies'},
    'stationery': {'category': 'Office Supplies'},
    'printer': {'category': 'Office Supplies', 'subcategory': 'Equipment'},
    
    # Maintenance
    'repair': {'category': 'Maintenance and Repairs'},
    'maintenance': {'category': 'Maintenance and Repairs'},
    'plumber': {'category': 'Maintenance and Repairs', 'subcategory': 'Plumbing'},
    'electrician': {'category': 'Maintenance and Repairs', 'subcategory': 'Electrical'},
    
    # Training
    'training': {'category': 'Training and Development'},
    'workshop': {'category': 'Training and Development'},
    'seminar': {'category': 'Training and Development'},
    
    # Insurance & Taxes
    'insurance': {'category': 'Insurance'},
    'tax': {'category': 'Taxes'},
    'KRA': {'category': 'Taxes'},
    
    # Rent
    'rent': {'category': 'Rent'},
    'lease': {'category': 'Rent'},
}
```

### Usage:
```bash
# Auto-categorize all uncategorized transactions
python manage.py categorize_transactions --auto-assign

# Analyze what would be categorized (dry run)
python manage.py categorize_transactions --dry-run

# Force re-categorize all transactions
python manage.py categorize_transactions --force
```

### Results (Phase 1):
- **Before:** 147 uncategorized (40.4%)
- **After:** 16 uncategorized (4.4%)
- **Improvement:** 131 transactions auto-categorized
- **Time Saved:** ~3 hours of manual work

## Views

### Smart Transaction Entry
**URL:** `/finance/transaction/create/`
**View:** `views_smart_transaction.py::smart_transaction_entry`

Features:
- AJAX category prediction on description change
- Cascading dropdowns (category → subcategory → type)
- Vendor autocomplete
- Amount validation

### API Endpoints

**Cascading Dropdowns:**
```python
# Get subcategories for a category
GET /finance/api/subcategories/?category_id=5
Response: [
    {"id": 1, "name": "Electricity"},
    {"id": 2, "name": "Water"},
    ...
]

# Get types/items for a subcategory
GET /finance/api/items/?subcategory_id=3
Response: [
    {"id": 1, "name": "Office Supplies"},
    ...
]
```

**AI Predictions:**
```python
# Predict all fields from receiver (main prediction endpoint)
GET /finance/api/predict-all/?receiver=KPLC&department=3&amount=5000
Response: {
    "receiver_info": {
        "name": "KPLC",
        "transaction_count": 16,
        "avg_amount": 3242.88
    },
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

## Management Commands

### Data Analysis:
```bash
# Full transaction analysis (shows all metrics)
python manage.py analyze_transaction_data

# Analyze uncategorized transactions only
python manage.py analyze_uncategorized

# Generate budget projections from transaction data
python manage.py generate_budget_projections --months 12 --save
```

### Data Cleanup:
```bash
# Auto-categorize uncategorized transactions
python manage.py categorize_transactions --auto-assign

# Dry run (see what would be categorized)
python manage.py categorize_transactions --dry-run

# Force re-categorize all transactions
python manage.py categorize_transactions --force
```

### Testing:
```bash
# Test AI prediction system
python manage.py test_ai_predictions --employee-id 74

# Verify data quality improvements
python manage.py verify_data_quality
```

## Data Quality Metrics

### Current (Oct 2025):
- **95.6%** transactions categorized (350/366)
- **$1.49M** total dataset
- **366** total transactions
- **98%** have vendors
- **87%** have subcategories
- **84%** AI prediction accuracy

### Historical Progress:
- **Sept 30, 2025:** 40.4% categorized (147/366 uncategorized)
- **Oct 1, 2025:** 95.6% categorized (16/366 uncategorized)
- **Improvement:** 131 transactions auto-categorized in Phase 1

### Target:
- **99%+** categorization (ongoing)
- **<1%** uncategorized transactions

## Debugging Guide

### Issue: Auto-fill Not Working

**Check Browser Console For:**
```javascript
"=== SMART FORM INITIALIZING ==="  // Should appear on page load
"=== triggerAutoFill called ==="   // Should appear on receiver blur
"=== API SUCCESS ==="               // Should appear after API call
```

**If Missing:**
- jQuery not loaded → Check base template has jQuery 3.6.0
- API 404 → Check URL routing in `urls.py`
- API 500 → Check backend logs: `heroku logs --tail`
- Fields not populating → Check field IDs match (`id_category`, `id_subcategory`)

### Issue: Cascading Dropdowns Not Working

**Check:**
1. Category change event binding: `$('#id_category').on('change')`
2. API endpoint works: `/finance/api/subcategories/?category_id=1`
3. Console shows: "CATEGORY CHANGE EVENT TRIGGERED"
4. Subcategory dropdown ID: `#id_subcategory` exists
5. Response is valid JSON array

**Debug Steps:**
```javascript
// Test in browser console (F12)
$('#id_category').val()  // Should return category ID
$('#id_category').trigger('change')  // Manually trigger
// Check Network tab for API call
```

### Issue: Transaction Not Categorizing

**Check:**
1. Does receiver match any rule? (case-insensitive)
2. Is amount in expected range? (for amount-based rules)
3. Run dry-run to see: `python manage.py categorize_transactions --dry-run`
4. Check logs for why it was skipped

**Add New Rule:**
```python
# In categorize_transactions.py
CATEGORIZATION_RULES['new_vendor'] = {
    'category': 'Category Name',
    'subcategory': 'Subcategory Name'
}
```

---

**Last Updated:** October 13, 2025  
**Source:** MASTER_REFERENCE.md (complete integration)

