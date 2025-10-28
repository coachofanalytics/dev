# Heroku Platform API Integration - Implementation Guide
**Feature:** Platform-Wide Heroku Automation  
**Date:** October 28, 2025  
**Status:** 🔨 Implementation Guide

---

## 🚀 QUICK START (2 Hours to Basic Functionality)

### **Prerequisites:**
```bash
# 1. Install heroku3 Python library
pip install heroku3

# 2. Get your Heroku API key
heroku auth:token

# 3. Add to environment variables
# In .env or Heroku config:
HEROKU_API_KEY=your_api_key_here
```

### **Basic Implementation:**

```python
# Step 1: Create base service (30 minutes)
# File: coda/platform_services/__init__.py
__all__ = ['HerokuService', 'DatabaseService', 'DeploymentService']

# File: coda/platform_services/heroku_service.py
import heroku3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class HerokuService:
    def __init__(self):
        self.client = heroku3.from_key(settings.HEROKU_API_KEY)
    
    def list_apps(self):
        """List all your Heroku apps"""
        return [app.name for app in self.client.apps()]
    
    def get_app_info(self, app_name):
        """Get app details"""
        app = self.client.app(app_name)
        return {
            'name': app.name,
            'region': app.region.name,
            'stack': app.stack.name,
            'created_at': app.created_at
        }

# Test it:
service = HerokuService()
print(service.list_apps())  # Should show your apps!
```

---

## 📁 FILE STRUCTURE

```
coda/
├── platform_services/               # New directory
│   ├── __init__.py
│   ├── heroku_service.py           # Base service
│   ├── deployment_service.py       # Deployments
│   ├── database_service.py         # Backups & DB
│   ├── monitoring_service.py       # Health checks
│   ├── scaling_service.py          # Auto-scaling
│   ├── security_service.py         # Security audits
│   ├── models.py                   # HerokuApp, HerokuDeployment, etc.
│   ├── tasks.py                    # Celery tasks
│   ├── admin.py                    # Django admin
│   └── tests/
│       ├── test_heroku_service.py
│       ├── test_deployment_service.py
│       └── test_database_service.py
│
├── management/commands/
│   ├── heroku_deploy.py            # Deploy command
│   ├── heroku_backup.py            # Backup command
│   ├── heroku_health_check.py      # Health check command
│   └── heroku_security_audit.py    # Security audit command
│
└── coda_project/
    └── settings/
        └── heroku.py               # Heroku-specific settings
```

---

## 🔨 PHASE-BY-PHASE IMPLEMENTATION

### **PHASE 1: Foundation (Week 1) - 15 hours**

#### **Day 1-2: Base Service (5 hours)**

**File: `coda/platform_services/heroku_service.py`**

```python
import heroku3
from django.conf import settings
from django.core.cache import cache
import logging
import time

logger = logging.getLogger(__name__)

class HerokuService:
    """
    Base service for all Heroku API interactions
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.HEROKU_API_KEY
        if not self.api_key:
            raise ValueError("HEROKU_API_KEY not configured")
        self.client = heroku3.from_key(self.api_key)
    
    def _handle_api_call(self, func, *args, **kwargs):
        """
        Wrapper for all API calls
        Handles errors, logging, rate limiting
        """
        try:
            result = func(*args, **kwargs)
            logger.info(f"✅ Heroku API: {func.__name__} succeeded")
            return {'success': True, 'data': result}
        except heroku3.exceptions.RateLimitExceeded:
            logger.warning("⏱️ Rate limit exceeded, waiting 60s...")
            time.sleep(60)
            return self._handle_api_call(func, *args, **kwargs)
        except heroku3.exceptions.Unauthorized:
            logger.error("🔒 Unauthorized - check HEROKU_API_KEY")
            return {'success': False, 'error': 'Unauthorized'}
        except Exception as e:
            logger.error(f"❌ Heroku API error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_apps(self):
        """List all apps"""
        return self._handle_api_call(lambda: list(self.client.apps()))
    
    def get_app(self, app_name):
        """Get app details (cached for 5 min)"""
        cache_key = f'heroku_app_{app_name}'
        cached = cache.get(cache_key)
        if cached:
            return {'success': True, 'data': cached}
        
        result = self._handle_api_call(self.client.app, app_name)
        if result['success']:
            cache.set(cache_key, result['data'], 300)
        return result
    
    def get_config(self, app_name):
        """Get all config vars"""
        app = self.get_app(app_name)
        if not app['success']:
            return app
        return self._handle_api_call(lambda: dict(app['data'].config()))
    
    def set_config(self, app_name, key, value):
        """Set config var"""
        app = self.get_app(app_name)
        if not app['success']:
            return app
        
        result = self._handle_api_call(
            lambda: app['data'].config().update({key: value})
        )
        
        if result['success']:
            # Invalidate cache
            cache.delete(f'heroku_app_{app_name}')
            logger.info(f"✅ Set {key} for {app_name}")
        
        return result
```

**Test:**
```python
# Create tests/test_heroku_service.py
import pytest
from platform_services.heroku_service import HerokuService

def test_heroku_service_init():
    service = HerokuService()
    assert service.client is not None

def test_list_apps():
    service = HerokuService()
    result = service.list_apps()
    assert result['success'] == True
    assert len(result['data']) > 0

def test_get_app_info():
    service = HerokuService()
    result = service.get_app('codamakutano')  # UAT app
    assert result['success'] == True
    assert result['data'].name == 'codamakutano'
```

Run tests:
```bash
cd coda
pytest platform_services/tests/test_heroku_service.py -v
```

---

#### **Day 3-4: Database Service (6 hours)**

**File: `coda/platform_services/database_service.py`**

```python
from .heroku_service import HerokuService
from celery import shared_task
from django.utils import timezone
import requests
import os

class DatabaseService(HerokuService):
    """Database backup and management"""
    
    def _get_database_addon(self, app_name):
        """Get PostgreSQL addon for app"""
        app = self.get_app(app_name)
        if not app['success']:
            return app
        
        # Find postgres addon
        addons = app['data'].addons()
        postgres_addon = next((a for a in addons if 'postgres' in a.name), None)
        
        if not postgres_addon:
            return {'success': False, 'error': 'No PostgreSQL addon found'}
        
        return {'success': True, 'data': postgres_addon}
    
    def create_backup(self, app_name):
        """Create database backup"""
        addon = self._get_database_addon(app_name)
        if not addon['success']:
            return addon
        
        try:
            # Create backup using heroku postgres:backups:capture
            backup = addon['data'].backups.create()
            
            logger.info(f"✅ Backup created: {backup.id}")
            return {
                'success': True,
                'backup_id': backup.id,
                'created_at': timezone.now(),
                'app_name': app_name
            }
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_backups(self, app_name, limit=10):
        """List recent backups"""
        addon = self._get_database_addon(app_name)
        if not addon['success']:
            return addon
        
        try:
            backups = addon['data'].backups()[:limit]
            return {
                'success': True,
                'backups': [{
                    'id': b.id,
                    'created_at': b.created_at,
                    'size': b.size,
                    'status': b.status
                } for b in backups]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_backup(self, app_name, backup_id=None):
        """Download backup file"""
        addon = self._get_database_addon(app_name)
        if not addon['success']:
            return addon
        
        try:
            if not backup_id:
                # Get latest backup
                backups = addon['data'].backups()
                if not backups:
                    return {'success': False, 'error': 'No backups found'}
                backup = backups[0]
            else:
                backup = addon['data'].backups.get(backup_id)
            
            # Get download URL
            download_url = backup.download_url()
            
            # Download file
            response = requests.get(download_url, stream=True)
            filename = f"backup_{app_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.dump"
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Backup downloaded: {filename}")
            return {
                'success': True,
                'filename': filename,
                'size_mb': os.path.getsize(filename) / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"❌ Download failed: {str(e)}")
            return {'success': False, 'error': str(e)}
```

**Celery Task for Daily Backups:**

**File: `coda/platform_services/tasks.py`**

```python
from celery import shared_task
from .database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

@shared_task(name='platform_services.daily_backup')
def daily_backup_task(app_name='codatrainingapp'):
    """
    Daily backup task (runs at 2 AM)
    """
    logger.info(f"🔄 Starting daily backup for {app_name}...")
    
    service = DatabaseService()
    result = service.create_backup(app_name)
    
    if result['success']:
        logger.info(f"✅ Daily backup completed: {result['backup_id']}")
        
        # Optional: Download to local/Google Drive
        # download_result = service.download_backup(app_name, result['backup_id'])
        
        return {'status': 'success', 'backup_id': result['backup_id']}
    else:
        logger.error(f"❌ Daily backup failed: {result['error']}")
        # Send alert email/Slack
        return {'status': 'failed', 'error': result['error']}

@shared_task(name='platform_services.cleanup_old_backups')
def cleanup_old_backups_task(app_name='codatrainingapp', retention_days=30):
    """
    Clean up backups older than retention period
    """
    service = DatabaseService()
    backups = service.list_backups(app_name, limit=100)
    
    if not backups['success']:
        return backups
    
    deleted_count = 0
    for backup in backups['backups']:
        age_days = (timezone.now() - backup['created_at']).days
        if age_days > retention_days:
            # Delete backup
            deleted_count += 1
    
    logger.info(f"🗑️ Deleted {deleted_count} old backups")
    return {'status': 'success', 'deleted': deleted_count}
```

**Configure Celery Beat:**

**File: `coda/coda_project/settings/celery_settings.py`**

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-heroku-backup': {
        'task': 'platform_services.daily_backup',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': ('codatrainingapp',)  # Production app
    },
    'weekly-backup-cleanup': {
        'task': 'platform_services.cleanup_old_backups',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday 3 AM
        'args': ('codatrainingapp', 30)  # Keep 30 days
    },
}
```

---

#### **Day 5: Management Commands (4 hours)**

**File: `coda/platform_services/management/commands/heroku_backup.py`**

```python
from django.core.management.base import BaseCommand
from platform_services.database_service import DatabaseService

class Command(BaseCommand):
    help = 'Create Heroku database backup'
    
    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, default='codatrainingapp')
        parser.add_argument('--download', action='store_true')
    
    def handle(self, *args, **options):
        app_name = options['app']
        
        self.stdout.write(f"Creating backup for {app_name}...")
        
        service = DatabaseService()
        result = service.create_backup(app_name)
        
        if result['success']:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Backup created: {result['backup_id']}"
            ))
            
            if options['download']:
                self.stdout.write("Downloading backup...")
                download_result = service.download_backup(app_name, result['backup_id'])
                
                if download_result['success']:
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Downloaded: {download_result['filename']} "
                        f"({download_result['size_mb']:.1f} MB)"
                    ))
        else:
            self.stdout.write(self.style.ERROR(
                f"❌ Backup failed: {result['error']}"
            ))
```

**Usage:**
```bash
# Create backup
python manage.py heroku_backup --app codatrainingapp

# Create and download backup
python manage.py heroku_backup --app codatrainingapp --download

# List backups
python manage.py heroku_list_backups --app codatrainingapp
```

---

### **PHASE 2: Intelligence (Week 2-3) - 30 hours**

(Monitoring, Scaling, Predictive Analytics)

### **PHASE 3: Excellence (Week 4-6) - 30 hours**

(Security, Deployment Automation, Self-Healing)

---

## 🧪 TESTING REQUIREMENTS

### **Unit Tests:**
```python
# tests/test_database_service.py
import pytest
from platform_services.database_service import DatabaseService

@pytest.mark.django_db
def test_create_backup():
    service = DatabaseService()
    result = service.create_backup('codamakutano')  # UAT
    
    assert result['success'] == True
    assert 'backup_id' in result
    
@pytest.mark.django_db
def test_list_backups():
    service = DatabaseService()
    result = service.list_backups('codamakutano')
    
    assert result['success'] == True
    assert len(result['backups']) > 0
```

**Run tests:**
```bash
cd coda
pytest platform_services/tests/ -v
```

---

## 📋 IMPLEMENTATION CHECKLIST

### **Phase 1: Foundation**
- [ ] Install heroku3 library
- [ ] Create platform_services directory
- [ ] Implement HerokuService base class
- [ ] Implement DatabaseService
- [ ] Create Celery tasks for backups
- [ ] Configure Celery Beat schedule
- [ ] Create management commands
- [ ] Write unit tests
- [ ] Test in UAT environment

### **Phase 2: Intelligence**
- [ ] Implement MonitoringService
- [ ] Implement ScalingService
- [ ] Create health check tasks
- [ ] Create auto-scaling tasks
- [ ] Create management commands
- [ ] Write tests
- [ ] Deploy to UAT

### **Phase 3: Excellence**
- [ ] Implement SecurityService
- [ ] Implement DeploymentService
- [ ] Create security audit tasks
- [ ] Create deployment automation
- [ ] Self-healing capabilities
- [ ] Write comprehensive tests
- [ ] Deploy to Production

---

**Implementation Status:** Ready to begin  
**Estimated Time:** 6-8 weeks (part-time)  
**Next:** Begin Phase 1 implementation

