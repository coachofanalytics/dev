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

Analyzes description text and historical patterns to suggest:
- Most likely category
- Most likely subcategory
- Typical amount for this transaction type

**Algorithm:**
1. Extract keywords from description
2. Match against historical transactions
3. Weight by frequency and recency
4. Return top 3 suggestions with confidence scores

## Auto-Categorization Engine

**Location:** `coda/finance/management/commands/categorize_transactions.py`

**Rules:**
```python
CATEGORIZATION_RULES = {
    'KPLC': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'Safaricom': {'category': 'IT & Software', 'subcategory': 'Communications'},
    'boda': {'category': 'Travel', 'subcategory': 'Local Transport'},
    # ... 20+ more rules
}
```

**Run:** `python manage.py categorize_transactions`

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
- `GET /finance/api/subcategories/{category_id}/` - Get subcategories
- `GET /finance/api/types/{subcategory_id}/` - Get types

**AI Predictions:**
- `POST /finance/api/predict-category/` - Get category suggestions

## Data Quality Metrics

Current (Oct 2025):
- **95.6%** transactions categorized
- **$1.49M** total dataset
- **98%** have vendors
- **87%** have subcategories

---

**Last Updated:** October 13, 2025

