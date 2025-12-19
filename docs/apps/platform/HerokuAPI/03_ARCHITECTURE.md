# Heroku Platform API Integration - Architecture
**Feature:** Platform-Wide Heroku Automation  
**Date:** October 28, 2025  
**Status:** 🏗️ Architecture Design

---

## 🎯 ARCHITECTURAL PRINCIPLES

1. **Service-Based Architecture** - Modular, testable services
2. **Event-Driven** - Operations triggered by events (git push, schedule, alerts)
3. **Fail-Safe** - Graceful degradation, never break app
4. **Async-First** - Long operations run in background (Celery)
5. **Observable** - Comprehensive logging and monitoring
6. **Secure-by-Default** - API keys encrypted, audit trails

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      CODA PLATFORM                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Finance   │  │ Investing  │  │ AI Services│  ... apps │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
│        │               │               │                    │
│        └───────────────┴───────────────┘                    │
│                        │                                     │
│        ┌───────────────▼──────────────────────┐            │
│        │   Platform Services Layer            │            │
│        │  ┌────────────────────────────────┐ │            │
│        │  │   HerokuService (Base)         │ │            │
│        │  └────────────┬───────────────────┘ │            │
│        │               │                      │            │
│        │  ┌────────────┼────────────┐        │            │
│        │  │            │            │        │            │
│        │  ▼            ▼            ▼        │            │
│        │  Deployment  Database   Monitoring  │            │
│        │  Service     Service    Service     │            │
│        │              │                       │            │
│        │  ▼            ▼            ▼        │            │
│        │  Scaling    Security    Analytics   │            │
│        │  Service    Service     Service     │            │
│        └──────────────┬───────────────────────┘            │
└───────────────────────┼────────────────────────────────────┘
                        │
        ┌───────────────▼──────────────────┐
        │   Heroku Platform API            │
        │  (External Service)              │
        │                                  │
        │  - App Management                │
        │  - Database Operations           │
        │  - Dyno Scaling                  │
        │  - Config Management             │
        │  - Metrics & Monitoring          │
        └──────────────────────────────────┘
```

---

## 📦 COMPONENT ARCHITECTURE

### **1. Base Service Layer**

```python
# coda/platform_services/heroku_service.py

import heroku3
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class HerokuService:
    """
    Base service for all Heroku API interactions
    
    Provides:
    - API authentication
    - Rate limiting
    - Error handling
    - Logging
    - Caching
    """
    
    def __init__(self, api_key=None):
        """Initialize Heroku API client"""
        self.api_key = api_key or settings.HEROKU_API_KEY
        self.client = heroku3.from_key(self.api_key)
        
    def _handle_api_call(self, func, *args, **kwargs):
        """
        Wrapper for all API calls
        Handles errors, logging, rate limiting
        """
        try:
            result = func(*args, **kwargs)
            logger.info(f"Heroku API call successful: {func.__name__}")
            return {'success': True, 'data': result}
        except heroku3.exceptions.RateLimitExceeded:
            logger.warning("Heroku API rate limit exceeded, retrying...")
            time.sleep(60)
            return self._handle_api_call(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Heroku API call failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_app(self, app_name):
        """Get Heroku app object"""
        cache_key = f'heroku_app_{app_name}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = self._handle_api_call(self.client.app, app_name)
        if result['success']:
            cache.set(cache_key, result['data'], 300)  # 5 min cache
        return result
```

---

### **2. Deployment Service**

```python
# coda/platform_services/deployment_service.py

from .heroku_service import HerokuService
from celery import shared_task
import time

class DeploymentService(HerokuService):
    """
    Automated deployment management
    """
    
    def deploy(self, app_name, git_url, branch='main', 
               run_migrations=True, verify=True):
        """
        Full deployment workflow:
        1. Pre-deployment backup
        2. Deploy code
        3. Run migrations
        4. Verify deployment
        5. Rollback on failure
        """
        deployment_id = self._generate_deployment_id()
        
        try:
            # Step 1: Backup before deploy
            logger.info(f"[{deployment_id}] Creating pre-deployment backup...")
            from .database_service import DatabaseService
            db_service = DatabaseService()
            backup = db_service.create_backup(app_name)
            
            # Step 2: Deploy code
            logger.info(f"[{deployment_id}] Deploying code from {git_url}...")
            app = self.get_app(app_name)
            build = app['data'].builds.create({
                'source_blob': {
                    'url': git_url,
                    'version': branch
                }
            })
            
            # Wait for build to complete
            while build.status not in ['succeeded', 'failed']:
                time.sleep(5)
                build.refresh()
            
            if build.status == 'failed':
                raise Exception(f"Build failed: {build.output_stream_url}")
            
            # Step 3: Run migrations
            if run_migrations:
                logger.info(f"[{deployment_id}] Running migrations...")
                self._run_migrations(app_name)
            
            # Step 4: Verify deployment
            if verify:
                logger.info(f"[{deployment_id}] Verifying deployment...")
                verification = self._verify_deployment(app_name)
                if not verification['success']:
                    raise Exception(f"Verification failed: {verification['error']}")
            
            logger.info(f"[{deployment_id}] ✅ Deployment successful!")
            return {
                'success': True,
                'deployment_id': deployment_id,
                'build_id': build.id,
                'backup_id': backup['id']
            }
            
        except Exception as e:
            logger.error(f"[{deployment_id}] ❌ Deployment failed: {str(e)}")
            logger.info(f"[{deployment_id}] Rolling back...")
            self.rollback(app_name, backup['id'])
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e)
            }
```

---

### **3. Database Service**

```python
# coda/platform_services/database_service.py

from .heroku_service import HerokuService
from celery import shared_task
import requests
import os

class DatabaseService(HerokuService):
    """
    Database backup and management
    """
    
    @shared_task(name='heroku.create_daily_backup')
    def scheduled_backup(app_name):
        """
        Celery task for daily backups (2 AM)
        """
        service = DatabaseService()
        result = service.create_backup(app_name)
        
        if result['success']:
            # Verify backup
            verify_result = service.verify_backup_integrity(result['backup_id'])
            
            # Optionally download to Google Drive
            if settings.BACKUP_TO_GOOGLE_DRIVE:
                service._backup_to_google_drive(result['backup_id'])
        
        return result
    
    def create_backup(self, app_name):
        """Create manual backup"""
        app = self.get_app(app_name)
        if not app['success']:
            return app
        
        try:
            # Get database addon
            db_addon = self._get_database_addon(app_name)
            
            # Create backup
            backup = db_addon.backups.create()
            
            logger.info(f"Backup created: {backup.id}")
            return {
                'success': True,
                'backup_id': backup.id,
                'created_at': backup.created_at,
                'size_mb': backup.size
            }
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_backup_integrity(self, backup_id):
        """
        Verify backup can be restored
        Creates temporary app, restores backup, tests
        """
        temp_app_name = f'backup-test-{backup_id}'
        
        try:
            # Create temporary app
            temp_app = self.client.apps.create(name=temp_app_name)
            
            # Restore backup to temp app
            self.restore_backup(temp_app_name, backup_id)
            
            # Run basic queries to verify
            # (implementation depends on your schema)
            verification_ok = self._run_verification_queries(temp_app_name)
            
            # Clean up
            temp_app.delete()
            
            return {
                'success': True,
                'verified': verification_ok,
                'backup_id': backup_id
            }
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return {'success': False, 'error': str(e)}
```

---

### **4. Monitoring Service**

```python
# coda/platform_services/monitoring_service.py

from .heroku_service import HerokuService
from celery import shared_task
from django.utils import timezone
import statistics

class MonitoringService(HerokuService):
    """
    Performance monitoring and alerting
    """
    
    @shared_task(name='heroku.health_check')
    def scheduled_health_check(app_name):
        """
        Celery task for health checks (every 5 min)
        """
        service = MonitoringService()
        health = service.check_health(app_name)
        
        if not health['healthy']:
            # Send alerts
            service._send_alert(app_name, health)
        
        return health
    
    def check_health(self, app_name):
        """
        Comprehensive health check
        Returns health score 0-100
        """
        checks = {
            'response_time': self._check_response_time(app_name),
            'error_rate': self._check_error_rate(app_name),
            'memory_usage': self._check_memory_usage(app_name),
            'database_connections': self._check_database_connections(app_name),
            'dyno_status': self._check_dyno_status(app_name),
        }
        
        health_score = sum(c['score'] for c in checks.values()) / len(checks)
        
        return {
            'healthy': health_score >= 80,
            'health_score': health_score,
            'checks': checks,
            'timestamp': timezone.now()
        }
    
    def get_metrics(self, app_name, metric_name, period='1h'):
        """
        Get performance metrics from Heroku
        
        Available metrics:
        - router.latency.p50
        - router.latency.p95
        - router.latency.p99
        - router.requests
        - router.status.5xx
        - memory.quota
        - load.avg.1m
        """
        app = self.get_app(app_name)
        if not app['success']:
            return app
        
        try:
            metrics = app['data'].metrics(metric_name, period=period)
            
            return {
                'success': True,
                'metric': metric_name,
                'data': metrics,
                'summary': {
                    'min': min(metrics),
                    'max': max(metrics),
                    'avg': statistics.mean(metrics),
                    'p95': statistics.quantiles(metrics, n=20)[18]  # 95th percentile
                }
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            return {'success': False, 'error': str(e)}
```

---

### **5. Scaling Service**

```python
# coda/platform_services/scaling_service.py

from .heroku_service import HerokuService
from .monitoring_service import MonitoringService
from celery import shared_task
import math

class ScalingService(HerokuService):
    """
    Auto-scaling management
    """
    
    SCALING_RULES = {
        'night': {'hours': range(0, 6), 'web': 1, 'worker': 1},
        'business': {'hours': range(8, 18), 'web': 2, 'worker': 2},
        'month_end': {'days': [28, 29, 30, 31], 'web': 3, 'worker': 2},
    }
    
    @shared_task(name='heroku.auto_scale')
    def scheduled_auto_scale(app_name):
        """
        Celery task for time-based scaling (every 30 min)
        """
        service = ScalingService()
        result = service.time_based_scaling(app_name)
        return result
    
    def time_based_scaling(self, app_name):
        """
        Scale based on time of day
        """
        now = timezone.now()
        hour = now.hour
        day_of_month = now.day
        
        # Determine appropriate scaling
        if day_of_month in self.SCALING_RULES['month_end']['days']:
            target = self.SCALING_RULES['month_end']
        elif hour in self.SCALING_RULES['night']['hours']:
            target = self.SCALING_RULES['night']
        elif hour in self.SCALING_RULES['business']['hours']:
            target = self.SCALING_RULES['business']
        else:
            return {'success': True, 'action': 'no_change'}
        
        # Apply scaling
        current_web = self.get_dyno_count(app_name, 'web')
        current_worker = self.get_dyno_count(app_name, 'worker')
        
        if current_web != target['web']:
            self.scale_dynos(app_name, 'web', target['web'])
            logger.info(f"Scaled web dynos: {current_web} → {target['web']}")
        
        if current_worker != target['worker']:
            self.scale_dynos(app_name, 'worker', target['worker'])
            logger.info(f"Scaled worker dynos: {current_worker} → {target['worker']}")
        
        return {
            'success': True,
            'action': 'scaled',
            'from': {'web': current_web, 'worker': current_worker},
            'to': {'web': target['web'], 'worker': target['worker']}
        }
```

---

### **6. Security Service**

```python
# coda/platform_services/security_service.py

from .heroku_service import HerokuService
from celery import shared_task
from django.core.signing import Signer
import secrets

class SecurityService(HerokuService):
    """
    Security automation and auditing
    """
    
    @shared_task(name='heroku.security_audit')
    def scheduled_security_audit(app_name):
        """
        Celery task for security audits (hourly)
        """
        service = SecurityService()
        audit_result = service.audit_security(app_name)
        
        # Auto-remediate critical issues
        for finding in audit_result['findings']:
            if finding['severity'] == 'CRITICAL':
                service._auto_remediate(app_name, finding)
        
        return audit_result
    
    def audit_security(self, app_name):
        """
        Run comprehensive security audit
        """
        findings = []
        
        # Check 1: SSL enforcement
        if not self._verify_ssl_enforcement(app_name):
            findings.append({
                'severity': 'HIGH',
                'issue': 'SSL not fully enforced',
                'fix': 'Set SECURE_SSL_REDIRECT=True'
            })
        
        # Check 2: Secret key rotation
        secret_age = self._get_secret_age(app_name, 'SECRET_KEY')
        if secret_age > 90:  # days
            findings.append({
                'severity': 'MEDIUM',
                'issue': f'SECRET_KEY not rotated in {secret_age} days',
                'fix': 'Rotate SECRET_KEY'
            })
        
        # Check 3: Database encryption
        if not self._verify_database_encryption(app_name):
            findings.append({
                'severity': 'HIGH',
                'issue': 'Database not encrypted at rest',
                'fix': 'Upgrade to Heroku Shield'
            })
        
        return {
            'app_name': app_name,
            'findings': findings,
            'security_score': self._calculate_security_score(findings),
            'timestamp': timezone.now()
        }
```

---

## 🔄 DATA FLOW DIAGRAMS

### **Deployment Flow:**

```
GitHub Push
    ↓
GitHub Webhook
    ↓
CODA receives webhook
    ↓
DeploymentService.deploy() [async]
    ├── DatabaseService.create_backup()
    ├── Heroku API: Build app
    ├── Wait for build
    ├── Run migrations
    ├── VerifyDeployment
    └── Send notification
```

### **Auto-Scaling Flow:**

```
Celery Beat (every 30 min)
    ↓
ScalingService.scheduled_auto_scale()
    ├── Check time of day
    ├── Check performance metrics
    ├── Determine target dyno count
    ├── Scale if needed
    └── Log action
```

### **Backup Flow:**

```
Celery Beat (2 AM daily)
    ↓
DatabaseService.scheduled_backup()
    ├── Create Heroku backup
    ├── Wait for completion
    ├── Verify backup integrity
    ├── Download to Google Drive
    └── Clean up old backups (>30 days)
```

---

## 🔐 SECURITY ARCHITECTURE

### **API Key Management:**
```python
# Environment variables (never in code!)
HEROKU_API_KEY=user_api_key_here
HEROKU_OAUTH_TOKEN=oauth_token_here

# Encrypted storage
from django.core.signing import Signer
signer = Signer()
encrypted_key = signer.sign(api_key)
```

### **Audit Trail:**
```python
class HerokuOperation(models.Model):
    """Log all Heroku operations"""
    operation = models.CharField(max_length=100)  # 'deploy', 'scale', etc.
    app_name = models.CharField(max_length=100)
    performed_by = models.ForeignKey(User)
    timestamp = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField()
    result = models.JSONField()
    success = models.BooleanField()
```

---

## 📊 DATABASE SCHEMA

```python
# coda/platform_services/models.py

class HerokuApp(models.Model):
    """Track Heroku apps"""
    name = models.CharField(max_length=100, unique=True)
    environment = models.CharField(max_length=20)  # 'production', 'uat', 'review'
    heroku_id = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    last_deployed = models.DateTimeField(null=True)

class HerokuDeployment(models.Model):
    """Track deployments"""
    app = models.ForeignKey(HerokuApp, on_delete=models.CASCADE)
    deployment_id = models.CharField(max_length=100, unique=True)
    git_sha = models.CharField(max_length=40)
    deployed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    backup_id = models.CharField(max_length=100, blank=True)

class HerokuBackup(models.Model):
    """Track backups"""
    app = models.ForeignKey(HerokuApp, on_delete=models.CASCADE)
    backup_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    size_mb = models.IntegerField()
    verified = models.BooleanField(default=False)
    google_drive_url = models.URLField(blank=True)
```

---

## ✅ ARCHITECTURE DECISIONS

### **Decision 1: Celery for Async Operations**
**Rationale:** Long-running Heroku operations (deployments, backups) shouldn't block web requests  
**Alternative Considered:** Synchronous operations  
**Risk:** Web request timeouts  

### **Decision 2: Service-Based Architecture**
**Rationale:** Modular, testable, reusable across CODA apps  
**Alternative Considered:** Monolithic helper module  
**Risk:** Tight coupling  

### **Decision 3: Cache Heroku API Responses**
**Rationale:** Reduce API calls, improve performance  
**Alternative Considered:** Always call API  
**Risk:** Stale data (mitigated by 5-min TTL)  

---

**Architecture Designed:** October 28, 2025  
**Status:** ✅ **APPROVED FOR IMPLEMENTATION**  
**Next:** Proceed to implementation (04_IMPLEMENTATION.md)

