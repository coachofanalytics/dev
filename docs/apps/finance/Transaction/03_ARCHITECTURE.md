# Transaction System - Architecture

**Last Updated:** October 22, 2025  
**Purpose:** System design, data models, and technical architecture for transaction management

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│           USER INTERFACE LAYER                   │
│  ┌─────────────┐         ┌──────────────┐      │
│  │Smart Entry  │         │  Transaction │      │
│  │    Form     │         │     List     │      │
│  └─────────────┘         └──────────────┘      │
└──────────┬──────────────────────┬───────────────┘
           │                      │
           ▼                      ▼
┌────────────────────────────────────────────────┐
│              VIEW LAYER                         │
│  ┌──────────────┐      ┌──────────────┐       │
│  │ smart_       │      │ transaction_ │       │
│  │ transaction  │      │ list         │       │
│  └──────────────┘      └──────────────┘       │
└──────────┬──────────────────────┬──────────────┘
           │                      │
           ▼                      ▼
┌────────────────────────────────────────────────┐
│           SERVICE LAYER                         │
│  ┌────────────────┐    ┌─────────────────┐    │
│  │ AIPrediction   │    │ Categorization  │    │
│  │ Service        │    │ Service         │    │
│  └────────────────┘    └─────────────────┘    │
└──────────┬──────────────────────┬──────────────┘
           │                      │
           ▼                      ▼
┌────────────────────────────────────────────────┐
│              MODEL LAYER                        │
│  ┌────────────┐  ┌────────────┐               │
│  │Transaction │  │  Budget    │               │
│  │            │  │  Category  │               │
│  └────────────┘  └────────────┘               │
└────────────────────────────────────────────────┘
```

---

## 📊 DATA MODEL

### Transaction (Core Model)
**Table:** `finance_transaction`  
**Purpose:** Single source of truth for all financial data

**Schema:**
```sql
CREATE TABLE finance_transaction (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(255),
    receiver VARCHAR(255),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'KES',
    transaction_date TIMESTAMP NOT NULL,
    description TEXT,
    payment_method VARCHAR(50),
    
    category_id INTEGER REFERENCES finance_budgetcategory(id),
    subcategory_id INTEGER REFERENCES finance_budgetsubcategory(id),
    department_id INTEGER REFERENCES main_department(id),
    company_id INTEGER REFERENCES main_company(id),
    
    is_categorized BOOLEAN DEFAULT FALSE,
    categorization_confidence DECIMAL(3,2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transaction_category ON finance_transaction(category_id);
CREATE INDEX idx_transaction_date ON finance_transaction(transaction_date);
CREATE INDEX idx_transaction_company ON finance_transaction(company_id);
```

---

### AIPredictionCache (Performance Optimization)
**Table:** `finance_aipredictioncache`  
**Purpose:** Cache AI predictions for fast lookup

**Schema:**
```sql
CREATE TABLE finance_aipredictioncache (
    id SERIAL PRIMARY KEY,
    input_hash VARCHAR(64) UNIQUE,
    input_data JSONB,
    prediction JSONB,
    confidence DECIMAL(3,2),
    hit_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    is_validated BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_prediction_hash ON finance_aipredictioncache(input_hash);
CREATE INDEX idx_prediction_confidence ON finance_aipredictioncache(confidence);
```

---

## 🔄 DATA FLOW

### Transaction Entry Flow:

```
1. User Opens Smart Entry Form
           ↓
2. Enters Receiver Name
           ↓
3. [AJAX] Call AI Prediction API
   GET /finance/api/predict-all/?receiver=KPLC
           ↓
4. AI Service Checks Cache
   • If cached: Return instantly (10ms)
   • If not: Analyze historical (100ms)
           ↓
5. Return Predictions
   {category: "Utilities", confidence: 0.95}
           ↓
6. Auto-fill Form Fields
   • Category dropdown auto-selected
   • Subcategory filtered & selected
   • Typical amount suggested
           ↓
7. User Reviews/Adjusts
           ↓
8. Submit Transaction
           ↓
9. Save to Database
   • is_categorized = TRUE
   • categorization_confidence = 0.95
           ↓
10. Update AI Cache
    • Validate prediction if user kept it
    • Update hit_count
```

---

### Auto-Categorization Flow:

```
1. [Cron Job] Runs Nightly
   python manage.py categorize_transactions
           ↓
2. Fetch Uncategorized Transactions
   WHERE is_categorized = FALSE
           ↓
3. For Each Transaction:
           ↓
4. Apply Categorization Rules (Priority Order)
   a. Exact vendor match
   b. Keyword match (description)
   c. Amount pattern
   d. Department default
           ↓
5. If Match Found (confidence >0.8):
   • Set category/subcategory
   • Set is_categorized = TRUE
   • Set confidence score
           ↓
6. If No Match (confidence <0.8):
   • Flag for manual review
   • Log for improvement
           ↓
7. Save Updates
           ↓
8. Generate Report
   • X transactions categorized
   • Y remaining
   • Success rate: Z%
```

---

## 🔧 TECHNOLOGY STACK

**Backend:**
- Django 4.x ORM
- Python 3.9+
- PostgreSQL 13+

**Frontend:**
- jQuery 3.6.0 for AJAX
- Bootstrap 4.5 for UI
- No heavy frameworks (keep simple)

**AI/ML:**
- Rule-based system (Phase 1-2)
- Pattern matching & keyword analysis
- Future: scikit-learn for ML (Phase 3)

**Caching:**
- Django cache framework
- AIPredictionCache model for AI predictions
- Redis planned for session caching

---

## 🎯 DESIGN DECISIONS

### Decision 1: Rule-Based vs ML-Only
**Chosen:** Hybrid (rules + AI)  
**Reason:**
- Limited transaction volume (561 records)
- Rules work well for common vendors
- AI fills gaps for unknown patterns
- 84% accuracy with simple approach

### Decision 2: Real-Time vs Batch Categorization
**Chosen:** Both  
**Reason:**
- Real-time for smart form (user experience)
- Batch for existing uncategorized (efficiency)
- Best of both worlds

### Decision 3: Cache Predictions
**Chosen:** Yes (AIPredictionCache model)  
**Reason:**
- Same vendors queried repeatedly
- 95% cache hit rate
- 10x faster response (10ms vs 100ms)

---

## 📚 RELATED DOCUMENTATION

**See Also:**
- `01_ANALYSIS.md` - Problem statement
- `02_REQUIREMENTS.md` - Functional requirements
- `04_IMPLEMENTATION.md` - Code details
- `05_TESTING.md` - Test scenarios
- `06_MAINTENANCE.md` - Known issues

---

**Last Updated:** October 22, 2025


