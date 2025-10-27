# CODA Testing Strategy

**Date:** October 23, 2025  
**Purpose:** Reduce production errors and improve deployment confidence

---

## 🎯 TESTING PHILOSOPHY

### Current Problem:
- Testing directly against production database
- No automated tests
- Errors discovered by users
- Manual fixes required each time

### Goal:
- Catch errors before they reach users
- Automated test suite
- Separate test environment
- Confidence in deployments

---

## 🏗️ TESTING PYRAMID

```
        /\
       /  \  E2E Tests (Few)
      /____\
     /      \  Integration Tests (Some)
    /________\
   /          \  Unit Tests (Many)
  /__________\
```

### 1. Unit Tests (70%)
- Test individual functions/methods
- Fast execution
- Easy to maintain
- Catch logic errors early

### 2. Integration Tests (20%)
- Test multiple components together
- Database interactions
- Form validation
- Signal chains

### 3. End-to-End Tests (10%)
- Test complete user flows
- Browser automation
- Real user scenarios
- Slowest but most realistic

---

## 📋 TESTING LEVELS

### Level 1: Pre-Commit Tests (Fastest)
**Run before every git commit**

```bash
# Linting
black coda/ --check
ruff check coda/

# Type checking
mypy coda/

# Quick unit tests
pytest tests/unit/ -v
```

### Level 2: Pre-Push Tests (Fast)
**Run before pushing to GitHub**

```bash
# All unit tests
pytest tests/unit/ -v

# Model tests
pytest tests/models/ -v

# Form validation tests
pytest tests/forms/ -v

# Check migrations
python manage.py makemigrations --check --dry-run
```

### Level 3: CI/CD Tests (Medium)
**Run automatically on GitHub push**

```bash
# All tests
pytest tests/ -v --cov

# Database migrations
python manage.py migrate --check

# Static file collection
python manage.py collectstatic --noinput --dry-run

# URL resolution
python manage.py show_urls
```

### Level 4: Staging Tests (Slow)
**Run in staging environment before production**

```bash
# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# Load testing
locust -f tests/load/locustfile.py

# Security scanning
bandit -r coda/
```

---

## 🔧 TESTING TOOLS SETUP

### 1. Install Testing Dependencies

```bash
# In requirements.txt add:
pytest==7.4.0
pytest-django==4.5.2
pytest-cov==4.1.0
factory-boy==3.3.0
faker==19.3.0
selenium==4.12.0
locust==2.15.1
```

```bash
pip install -r requirements.txt
```

### 2. Configure pytest

Create `pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = coda_project.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
```

### 3. Create Test Database Settings

Create `coda/coda_project/coda_settings/test_settings.py`:
```python
from .base_settings import *

# Use SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory for speed
    }
}

# Disable migrations for tests (use --create-db for real migrations)
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

# MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug
DEBUG = False

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

---

## 📝 EXAMPLE TEST STRUCTURE

### tests/
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── factories.py             # Test data factories
│
├── unit/                    # Fast, isolated tests
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_forms.py
│   ├── test_services.py
│   └── test_utils.py
│
├── integration/             # Component integration
│   ├── __init__.py
│   ├── test_views.py
│   ├── test_signals.py
│   └── test_api.py
│
├── e2e/                     # End-to-end flows
│   ├── __init__.py
│   ├── test_user_flows.py
│   └── test_payment_flow.py
│
└── fixtures/                # Test data
    ├── users.json
    ├── departments.json
    └── food_items.json
```

---

## 🧪 EXAMPLE TESTS

### 1. Unit Test Example

`tests/unit/test_food_models.py`:
```python
import pytest
from decimal import Decimal
from django.utils import timezone
from finance.models import Food, FoodInventory, Supplier
from main.models import Department

@pytest.mark.django_db
class TestFoodModel:
    def test_food_creation(self):
        """Test creating a food item"""
        food = Food.objects.create(
            name="Rice",
            category="grains",
            current_unit_price=Decimal("5.00"),
            currency="USD",
            unit_of_measurement="kg"
        )
        assert food.name == "Rice"
        assert food.current_unit_price == Decimal("5.00")
    
    def test_food_total_amount(self):
        """Test total_amount property"""
        food = Food.objects.create(
            name="Sugar",
            current_unit_price=Decimal("2.50"),
            currency="USD"
        )
        assert food.total_amount == Decimal("2.50")


@pytest.mark.django_db
class TestFoodInventory:
    def test_inventory_status_updates(self, food_item, department):
        """Test that inventory status updates correctly"""
        inventory = FoodInventory.objects.create(
            food_item=food_item,
            location=department,
            quantity=Decimal("10.0"),
            reorder_level=Decimal("5.0")
        )
        
        # Should be in stock
        inventory.update_status()
        assert inventory.status == 'in_stock'
        
        # Reduce to low stock
        inventory.quantity = Decimal("4.0")
        inventory.update_status()
        assert inventory.status == 'low_stock'
        
        # Reduce to out of stock
        inventory.quantity = Decimal("0.0")
        inventory.update_status()
        assert inventory.status == 'out_of_stock'
```

### 2. Integration Test Example

`tests/integration/test_food_signals.py`:
```python
import pytest
from decimal import Decimal
from django.utils import timezone
from finance.models import (
    Food, FoodInventory, FoodPurchaseTransaction,
    FoodConsumptionLog, Transaction
)

@pytest.mark.django_db
class TestFoodSignals:
    def test_purchase_creates_transaction(self, food_item, supplier, user):
        """Test that purchasing food creates a Transaction"""
        purchase = FoodPurchaseTransaction.objects.create(
            food_item=food_item,
            quantity=Decimal("10.0"),
            unit_price=Decimal("5.00"),
            currency="USD",
            supplier=supplier,
            purchased_by=user
        )
        
        # Signal should have created Transaction
        assert purchase.transaction is not None
        assert purchase.transaction.amount == Decimal("5.00")
        assert purchase.transaction.qty == Decimal("10.0")
    
    def test_consumption_updates_inventory(self, inventory, user):
        """Test that logging consumption updates inventory"""
        original_quantity = inventory.quantity
        
        log = FoodConsumptionLog.objects.create(
            inventory=inventory,
            quantity_consumed=Decimal("2.0"),
            recorded_by=user
        )
        
        # Refresh inventory from DB
        inventory.refresh_from_db()
        
        # Quantity should be reduced
        assert inventory.quantity == original_quantity - Decimal("2.0")
```

### 3. View Test Example

`tests/integration/test_food_views.py`:
```python
import pytest
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
class TestFoodDashboard:
    def test_dashboard_loads(self, client, user):
        """Test that food dashboard loads"""
        client.force_login(user)
        response = client.get(reverse('finance:food:dashboard'))
        
        assert response.status_code == 200
        assert 'Food Inventory Dashboard' in response.content.decode()
    
    def test_dashboard_shows_low_stock_alerts(
        self, client, user, low_stock_inventory
    ):
        """Test that low stock items appear in alerts"""
        client.force_login(user)
        response = client.get(reverse('finance:food:dashboard'))
        
        assert 'Low Stock Alerts' in response.content.decode()
        assert low_stock_inventory.food_item.name in response.content.decode()
```

---

## 🏭 TEST FIXTURES (conftest.py)

`tests/conftest.py`:
```python
import pytest
from decimal import Decimal
from django.utils import timezone
from accounts.models import CustomerUser
from main.models import Department
from finance.models import Food, FoodInventory, Supplier

@pytest.fixture
def user(db):
    """Create a test user"""
    return CustomerUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def department(db):
    """Create a test department"""
    return Department.objects.create(
        name='Test Department',
        slug='test-dept'
    )

@pytest.fixture
def supplier(db):
    """Create a test supplier"""
    return Supplier.objects.create(
        name='Test Supplier',
        email='supplier@example.com',
        phone='+254712345678'
    )

@pytest.fixture
def food_item(db, supplier):
    """Create a test food item"""
    return Food.objects.create(
        name='Test Rice',
        category='grains',
        current_unit_price=Decimal("5.00"),
        currency='USD',
        unit_of_measurement='kg',
        current_supplier=supplier
    )

@pytest.fixture
def inventory(db, food_item, department):
    """Create a test inventory"""
    return FoodInventory.objects.create(
        food_item=food_item,
        location=department,
        quantity=Decimal("50.0"),
        reorder_level=Decimal("10.0"),
        reorder_quantity=Decimal("30.0")
    )

@pytest.fixture
def low_stock_inventory(db, food_item, department):
    """Create a low stock inventory"""
    return FoodInventory.objects.create(
        food_item=food_item,
        location=department,
        quantity=Decimal("5.0"),  # Below reorder level
        reorder_level=Decimal("10.0"),
        reorder_quantity=Decimal("30.0")
    )
```

---

## 🚀 RUNNING TESTS

### Local Development

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_food_models.py

# Run tests with coverage
pytest --cov=finance --cov-report=html

# Run fast tests only (skip slow)
pytest -m "not slow"

# Run with verbose output
pytest -vv

# Run and stop on first failure
pytest -x
```

### CI/CD (GitHub Actions)

Create `.github/workflows/tests.yml`:
```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd coda
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 🔍 PRE-DEPLOYMENT CHECKLIST

### Before Every Deployment:

```bash
# 1. Run linters
black coda/ --check
ruff check coda/

# 2. Run tests
pytest -v

# 3. Check migrations
cd coda
python manage.py makemigrations --check --dry-run

# 4. Check for model/DB mismatches
python manage.py check

# 5. Verify URLs
python manage.py show_urls | grep finance

# 6. Test critical paths manually
# - Login
# - Dashboard loads
# - Forms submit
# - Admin accessible
```

---

## 🛡️ SAFETY IMPROVEMENTS

### 1. Separate Environments

```python
# In local_settings.py
ENVIRONMENT = 'development'
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 2. Database Synchronization Script

Create `scripts/sync_prod_to_local.py`:
```python
"""
Sync production database structure to local for testing
WITHOUT copying actual data
"""
import subprocess

def sync_schema():
    # Export schema only (no data)
    subprocess.run([
        'pg_dump',
        '--schema-only',
        '--no-owner',
        '--no-privileges',
        'production_db_url',
        '-f', 'schema.sql'
    ])
    
    # Import to local
    subprocess.run([
        'psql',
        'local_db',
        '-f', 'schema.sql'
    ])
    
    print("✅ Schema synced from production to local")
```

### 3. Model Validation Script

Create `scripts/validate_models.py`:
```python
"""
Validate that models match database schema
"""
from django.core.management import call_command
from django.db import connection

def validate_schema():
    # Check for missing migrations
    call_command('makemigrations', '--check', '--dry-run')
    
    # Check for model/DB mismatches
    with connection.cursor() as cursor:
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables in database")
        
        # For each table, check columns
        for table in tables:
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            columns = cursor.fetchall()
            print(f"✅ {table}: {len(columns)} columns")
```

---

## 📊 TESTING METRICS

### Track These Metrics:

1. **Test Coverage**
   - Aim for >80% overall
   - Critical paths should be 100%

2. **Test Execution Time**
   - Unit tests: <1 second each
   - Integration: <5 seconds each
   - E2E: <30 seconds each

3. **Failure Rate**
   - Pre-commit: Should catch 70%+ of issues
   - CI/CD: Should catch 20%+ of remaining
   - Production: <5% should reach users

---

## 🎯 IMMEDIATE ACTION PLAN

### Week 1: Foundation
1. ✅ Install pytest and dependencies
2. ✅ Create test_settings.py
3. ✅ Write 10 unit tests for Food models
4. ✅ Set up conftest.py with fixtures

### Week 2: Coverage
1. ✅ Write integration tests for signals
2. ✅ Write view tests for all food endpoints
3. ✅ Add form validation tests
4. ✅ Reach 50% test coverage

### Week 3: Automation
1. ✅ Set up GitHub Actions CI/CD
2. ✅ Create pre-commit hooks
3. ✅ Document testing workflow
4. ✅ Train team on running tests

### Week 4: Refinement
1. ✅ Add E2E tests for critical flows
2. ✅ Optimize test execution time
3. ✅ Reach 80% test coverage
4. ✅ Make tests mandatory for deployment

---

## 💡 BEST PRACTICES

### DO:
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Use fixtures for test data
- ✅ Test edge cases
- ✅ Mock external services
- ✅ Run tests before committing

### DON'T:
- ❌ Test against production DB
- ❌ Write tests that depend on each other
- ❌ Skip writing tests to "save time"
- ❌ Test framework code (Django itself)
- ❌ Make tests too complex
- ❌ Ignore failing tests

---

## 🔄 TESTING WORKFLOW

```
Developer writes code
  ↓
Run pre-commit tests (fast)
  ↓ [All pass?]
Commit code
  ↓
Push to GitHub
  ↓
CI/CD runs full test suite
  ↓ [All pass?]
Deploy to staging
  ↓
Run integration tests on staging
  ↓ [All pass?]
Deploy to production
  ↓
Monitor for errors
```

---

## 📞 SUPPORT

**Questions?** Reference:
- Django Testing Docs: https://docs.djangoproject.com/en/stable/topics/testing/
- pytest-django: https://pytest-django.readthedocs.io/
- This document: `docs/TESTING_STRATEGY.md`

---

**Last Updated:** October 23, 2025  
**Owner:** CODA Development Team  
**Review Cycle:** Monthly

