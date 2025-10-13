# Transaction System - Implementation

## Data Model

### Transaction Model
**Location:** `coda/finance/models/core.py`

```python
class Transaction(models.Model):
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    vendor_supplier = models.ForeignKey(User, related_name='transactions_as_vendor')
    category = models.ForeignKey('BudgetCategory', null=True)
    subcategory = models.ForeignKey('BudgetSubcategory', null=True)
    type = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50)
    company = models.ForeignKey('Company')
    department = models.ForeignKey('Department', null=True)
```

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

