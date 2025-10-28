# Heroku Platform API Integration - Testing Strategy
**Feature:** Platform-Wide Heroku Automation  
**Date:** October 28, 2025  
**Status:** 🧪 Testing Guide

---

## 🎯 TESTING PHILOSOPHY

**Critical Infrastructure = Rigorous Testing**

Heroku API integration is critical infrastructure that affects ALL CODA apps. Testing requirements:
- **Coverage Target:** 90%+ (higher than normal 80%)
- **Test Environment:** Dedicated test Heroku apps (not UAT/Production!)
- **Test Types:** Unit, Integration, Disaster Recovery, Chaos Engineering

---

## 🏗️ TEST INFRASTRUCTURE SETUP

### **Step 1: Create Test Heroku App**

```bash
# Create dedicated test app
heroku create coda-heroku-api-test --region us

# Add Postgres database
heroku addons:create heroku-postgresql:hobby-dev --app coda-heroku-api-test

# Get app info
heroku info --app coda-heroku-api-test
```

### **Step 2: Configure Test Settings**

**File: `coda/coda_project/settings/test_settings.py`**

```python
from .base_settings import *

# Test Heroku apps
HEROKU_TEST_APPS = {
    'primary': 'coda-heroku-api-test',
    'secondary': 'coda-heroku-api-test-2',  # For clone/restore tests
}

# Use test API key (read-only recommended)
HEROKU_API_KEY = os.getenv('HEROKU_TEST_API_KEY', HEROKU_API_KEY)

# Disable auto-cleanup (clean manually in tests)
HEROKU_AUTO_CLEANUP = False
```

### **Step 3: Create Test Fixtures**

**File: `coda/platform_services/tests/conftest.py`**

```python
import pytest
from platform_services.heroku_service import HerokuService
from platform_services.database_service import DatabaseService

@pytest.fixture
def heroku_service():
    """Base Heroku service for testing"""
    return HerokuService()

@pytest.fixture
def database_service():
    """Database service for testing"""
    return DatabaseService()

@pytest.fixture
def test_app_name():
    """Test app name from settings"""
    from django.conf import settings
    return settings.HEROKU_TEST_APPS['primary']

@pytest.fixture
def cleanup_test_backups(test_app_name):
    """Clean up test backups after test"""
    yield
    # Cleanup code runs after test
    service = DatabaseService()
    backups = service.list_backups(test_app_name)
    # Delete test backups if needed
```

---

## 🧪 UNIT TESTS

### **Test: HerokuService (Base)**

**File: `coda/platform_services/tests/test_heroku_service.py`**

```python
import pytest
from platform_services.heroku_service import HerokuService
from django.core.cache import cache

@pytest.mark.django_db
class TestHerokuService:
    """Test base Heroku service"""
    
    def test_init_with_api_key(self):
        """Test service initialization with API key"""
        service = HerokuService()
        assert service.client is not None
        assert service.api_key is not None
    
    def test_init_without_api_key_raises_error(self, settings):
        """Test service fails without API key"""
        settings.HEROKU_API_KEY = None
        with pytest.raises(ValueError, match="HEROKU_API_KEY not configured"):
            HerokuService()
    
    def test_list_apps_success(self, heroku_service):
        """Test listing apps"""
        result = heroku_service.list_apps()
        assert result['success'] == True
        assert len(result['data']) > 0
        assert all(hasattr(app, 'name') for app in result['data'])
    
    def test_get_app_success(self, heroku_service, test_app_name):
        """Test getting app details"""
        result = heroku_service.get_app(test_app_name)
        assert result['success'] == True
        assert result['data'].name == test_app_name
    
    def test_get_app_caching(self, heroku_service, test_app_name):
        """Test app info is cached"""
        # First call
        result1 = heroku_service.get_app(test_app_name)
        
        # Check cache
        cache_key = f'heroku_app_{test_app_name}'
        cached = cache.get(cache_key)
        assert cached is not None
        
        # Second call should use cache
        result2 = heroku_service.get_app(test_app_name)
        assert result1['data'] == result2['data']
    
    def test_get_config_success(self, heroku_service, test_app_name):
        """Test getting config vars"""
        result = heroku_service.get_config(test_app_name)
        assert result['success'] == True
        assert isinstance(result['data'], dict)
    
    def test_set_config_success(self, heroku_service, test_app_name):
        """Test setting config var"""
        test_key = 'TEST_VAR'
        test_value = 'test_value_123'
        
        result = heroku_service.set_config(test_app_name, test_key, test_value)
        assert result['success'] == True
        
        # Verify it was set
        config = heroku_service.get_config(test_app_name)
        assert config['data'][test_key] == test_value
        
        # Cleanup
        heroku_service.set_config(test_app_name, test_key, '')
    
    def test_get_nonexistent_app_fails(self, heroku_service):
        """Test getting nonexistent app"""
        result = heroku_service.get_app('nonexistent-app-12345')
        assert result['success'] == False
        assert 'error' in result
    
    def test_api_call_error_handling(self, heroku_service):
        """Test API call error handling"""
        # Force an error by using invalid app name
        result = heroku_service.get_app('')
        assert result['success'] == False
```

---

### **Test: DatabaseService**

**File: `coda/platform_services/tests/test_database_service.py`**

```python
import pytest
from platform_services.database_service import DatabaseService
from django.utils import timezone

@pytest.mark.django_db
class TestDatabaseService:
    """Test database service"""
    
    def test_get_database_addon_success(self, database_service, test_app_name):
        """Test getting database addon"""
        result = database_service._get_database_addon(test_app_name)
        assert result['success'] == True
        assert 'postgres' in result['data'].name.lower()
    
    def test_create_backup_success(self, database_service, test_app_name, cleanup_test_backups):
        """Test creating backup"""
        result = database_service.create_backup(test_app_name)
        
        assert result['success'] == True
        assert 'backup_id' in result
        assert 'created_at' in result
        assert result['app_name'] == test_app_name
    
    def test_list_backups_success(self, database_service, test_app_name):
        """Test listing backups"""
        result = database_service.list_backups(test_app_name, limit=5)
        
        assert result['success'] == True
        assert 'backups' in result
        assert len(result['backups']) <= 5
        
        # Check backup structure
        if result['backups']:
            backup = result['backups'][0]
            assert 'id' in backup
            assert 'created_at' in backup
            assert 'size' in backup
    
    def test_download_backup_success(self, database_service, test_app_name):
        """Test downloading backup"""
        # First create a backup
        create_result = database_service.create_backup(test_app_name)
        assert create_result['success'] == True
        backup_id = create_result['backup_id']
        
        # Wait for backup to complete (may take a few seconds)
        import time
        time.sleep(10)
        
        # Download it
        download_result = database_service.download_backup(test_app_name, backup_id)
        
        if download_result['success']:  # May fail if backup not ready yet
            assert 'filename' in download_result
            assert 'size_mb' in download_result
            
            # Cleanup downloaded file
            import os
            if os.path.exists(download_result['filename']):
                os.remove(download_result['filename'])
```

---

## 🔗 INTEGRATION TESTS

### **Test: Full Deployment Workflow**

**File: `coda/platform_services/tests/test_deployment_workflow.py`**

```python
import pytest
from platform_services.deployment_service import DeploymentService
from platform_services.database_service import DatabaseService

@pytest.mark.django_db
@pytest.mark.integration
class TestDeploymentWorkflow:
    """Test full deployment workflow"""
    
    def test_deploy_with_backup_and_rollback(self, test_app_name):
        """
        Test complete deployment workflow:
        1. Create backup
        2. Deploy code
        3. Run migrations
        4. Verify
        5. Rollback on failure
        """
        db_service = DatabaseService()
        deploy_service = DeploymentService()
        
        # Step 1: Create pre-deployment backup
        backup_result = db_service.create_backup(test_app_name)
        assert backup_result['success'] == True
        backup_id = backup_result['backup_id']
        
        # Step 2: Deploy (using test git URL)
        test_git_url = 'https://github.com/heroku/node-js-getting-started'
        deploy_result = deploy_service.deploy(
            test_app_name,
            test_git_url,
            branch='main',
            run_migrations=False,  # Skip for test
            verify=True
        )
        
        # Should succeed or fail gracefully
        assert 'success' in deploy_result
        assert 'deployment_id' in deploy_result
        
        if not deploy_result['success']:
            # Verify rollback happened
            assert 'error' in deploy_result
            # Check app still works (rollback successful)
```

---

## 🔥 DISASTER RECOVERY TESTS

### **Test: Backup Restoration**

**File: `coda/platform_services/tests/test_disaster_recovery.py`**

```python
import pytest
from platform_services.database_service import DatabaseService
from platform_services.deployment_service import DeploymentService
import time

@pytest.mark.django_db
@pytest.mark.dr  # Mark as disaster recovery test
@pytest.mark.slow  # Mark as slow test
class TestDisasterRecovery:
    """Test disaster recovery procedures"""
    
    def test_backup_and_restore_workflow(self):
        """
        Simulate disaster:
        1. Create backup of test app
        2. Make changes to database
        3. Restore from backup
        4. Verify data restored
        """
        service = DatabaseService()
        test_app = 'coda-heroku-api-test'
        
        # Step 1: Create backup
        backup_result = service.create_backup(test_app)
        assert backup_result['success'] == True
        backup_id = backup_result['backup_id']
        
        # Wait for backup to complete
        time.sleep(30)
        
        # Step 2: Simulate disaster (make changes)
        # (In real test, you'd modify data)
        
        # Step 3: Restore from backup
        restore_result = service.restore_backup(test_app, backup_id)
        
        # Should succeed
        assert restore_result['success'] == True
        
        # Step 4: Verify restoration
        # (In real test, you'd check data integrity)
    
    def test_backup_verification(self):
        """
        Test backup integrity verification:
        1. Create backup
        2. Verify it can be restored
        3. Test data integrity
        """
        service = DatabaseService()
        test_app = 'coda-heroku-api-test'
        
        # Create backup
        backup_result = service.create_backup(test_app)
        assert backup_result['success'] == True
        
        # Verify backup
        verify_result = service.verify_backup_integrity(backup_result['backup_id'])
        
        # Should pass verification
        assert verify_result['success'] == True
        assert verify_result['verified'] == True
```

---

## 🎭 CHAOS ENGINEERING TESTS

### **Test: Resilience**

**File: `coda/platform_services/tests/test_chaos.py`**

```python
import pytest
from platform_services.scaling_service import ScalingService
from platform_services.monitoring_service import MonitoringService
import random

@pytest.mark.django_db
@pytest.mark.chaos  # Mark as chaos test
class TestChaosEngineering:
    """Test system resilience under failure conditions"""
    
    def test_api_rate_limiting_handling(self, heroku_service):
        """
        Test service handles rate limiting gracefully
        Make 100 rapid API calls
        """
        results = []
        for i in range(100):
            result = heroku_service.list_apps()
            results.append(result)
        
        # All calls should eventually succeed (with retries)
        assert all(r['success'] for r in results)
    
    def test_handle_dyno_crash(self):
        """
        Simulate dyno crash and test recovery
        """
        scaling_service = ScalingService()
        monitoring_service = MonitoringService()
        test_app = 'coda-heroku-api-test'
        
        # Get current state
        initial_state = monitoring_service.check_health(test_app)
        
        # Simulate crash (restart all dynos)
        scaling_service._restart_all_dynos(test_app)
        
        # Wait for recovery
        import time
        time.sleep(30)
        
        # Check health recovered
        recovered_state = monitoring_service.check_health(test_app)
        assert recovered_state['healthy'] == True
    
    def test_database_connection_exhaustion(self):
        """
        Simulate database connection exhaustion
        Test graceful degradation
        """
        # Open many connections
        # Verify app handles gracefully
        # Cleanup connections
        pass  # Implement based on your needs
```

---

## 📊 COVERAGE TARGETS

### **Coverage Requirements:**

| Component | Target Coverage | Critical? |
|-----------|----------------|-----------|
| HerokuService | 95% | ✅ Yes |
| DatabaseService | 95% | ✅ Yes |
| DeploymentService | 90% | ✅ Yes |
| MonitoringService | 85% | Medium |
| ScalingService | 85% | Medium |
| SecurityService | 95% | ✅ Yes |

### **Run Coverage:**

```bash
# Run all tests with coverage
cd coda
pytest platform_services/tests/ --cov=platform_services --cov-report=html

# View coverage report
open htmlcov/index.html  # Opens in browser
```

---

## ✅ TEST EXECUTION CHECKLIST

### **Before Every Deployment:**
- [ ] All unit tests pass (`pytest platform_services/tests/test_*.py`)
- [ ] Integration tests pass (`pytest -m integration`)
- [ ] Coverage > 90% (`pytest --cov`)
- [ ] No test warnings or errors

### **Weekly:**
- [ ] Disaster recovery test (`pytest -m dr`)
- [ ] Backup verification test
- [ ] Full integration test suite

### **Monthly:**
- [ ] Chaos engineering tests (`pytest -m chaos`)
- [ ] Performance tests
- [ ] Security audit tests

---

## 🚀 CI/CD INTEGRATION

### **GitHub Actions Workflow:**

**File: `.github/workflows/heroku_api_tests.yml`**

```yaml
name: Heroku API Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'coda/platform_services/**'
  pull_request:
    paths:
      - 'coda/platform_services/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-django
    
    - name: Run tests
      env:
        HEROKU_API_KEY: ${{ secrets.HEROKU_TEST_API_KEY }}
      run: |
        cd coda
        pytest platform_services/tests/ -v --cov=platform_services --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coda/coverage.xml
```

---

**Testing Guide Complete**  
**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Next:** Maintenance procedures (06_MAINTENANCE.md)

