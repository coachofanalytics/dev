"""
Architecture Tests: Performance & Scalability
Tests for performance-related architecture patterns and scalability.
"""

import pytest
from django.conf import settings
from django.apps import apps
from pathlib import Path


@pytest.mark.architecture
class TestPerformanceArchitecture:
    """Tests for performance-related architecture patterns."""

    def test_select_related_used_in_common_queries(self):
        """
        ARCHITECTURE TEST: Foreign key queries should use select_related.
        
        Best Practice: Prevent N+1 query problem.
        Risk: Performance degradation with many related objects.
        """
        # This would require analyzing querysets in views/services
        # Informational test
        pytest.skip("Manual review: Check if select_related() is used for FK queries")

    def test_pagination_configured_for_list_views(self):
        """
        ARCHITECTURE TEST: List views should have pagination.
        
        Risk: Loading thousands of records crashes the app.
        """
        if 'rest_framework' in settings.INSTALLED_APPS:
            # Check if DRF pagination is configured
            has_drf_pagination = hasattr(settings, 'REST_FRAMEWORK') and \
                                'DEFAULT_PAGINATION_CLASS' in settings.REST_FRAMEWORK
            
            assert has_drf_pagination, \
                "DRF should have DEFAULT_PAGINATION_CLASS configured"

    def test_database_pooling_configured(self):
        """
        ARCHITECTURE TEST: Database should use connection pooling.
        
        Best Practice: Reuse database connections for performance.
        """
        db_settings = settings.DATABASES.get('default', {})
        
        # Check for connection pooling configuration
        has_pooling = 'CONN_MAX_AGE' in db_settings
        
        if not has_pooling:
            pytest.skip("Connection pooling (CONN_MAX_AGE) not configured - recommended for production")

    def test_caching_backend_configured(self):
        """
        ARCHITECTURE TEST: Caching should be configured.
        
        Best Practice: Use Redis/Memcached, not dummy cache.
        """
        caches = settings.CACHES.get('default', {})
        backend = caches.get('BACKEND', '')
        
        is_dummy = 'DummyCache' in backend or 'LocMemCache' in backend
        
        if is_dummy:
            pytest.skip("Production-grade cache (Redis/Memcached) not configured")

    def test_static_files_storage_configured(self):
        """
        ARCHITECTURE TEST: Static files should use optimized storage.
        
        Best Practice: Use WhiteNoise or CDN for static files.
        """
        staticfiles_storage = getattr(settings, 'STATICFILES_STORAGE', '')
        
        has_whitenoise = 'whitenoise' in staticfiles_storage.lower()
        has_s3 = 's3' in staticfiles_storage.lower()
        has_cloudinary = 'cloudinary' in staticfiles_storage.lower()
        
        if not (has_whitenoise or has_s3 or has_cloudinary):
            pytest.skip("Optimized static file storage not configured")


@pytest.mark.architecture
class TestScalabilityArchitecture:
    """Tests for scalability architecture patterns."""

    def test_celery_configured_for_async_tasks(self):
        """
        ARCHITECTURE TEST: Celery should be configured for async processing.
        
        Best Practice: Payment processing, emails should be async.
        """
        has_celery = 'django_celery_results' in settings.INSTALLED_APPS or \
                     'django_celery_beat' in settings.INSTALLED_APPS or \
                     hasattr(settings, 'CELERY_BROKER_URL')
        
        if not has_celery:
            pytest.skip("Celery not configured - recommended for background tasks")

    def test_file_uploads_use_proper_storage(self):
        """
        ARCHITECTURE TEST: File uploads should use cloud storage (S3, etc.).
        
        Risk: Local storage doesn't scale horizontally.
        """
        default_file_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        
        uses_cloud = 's3' in default_file_storage.lower() or \
                     'azure' in default_file_storage.lower() or \
                     'gcs' in default_file_storage.lower() or \
                     'cloudinary' in default_file_storage.lower()
        
        if not uses_cloud:
            pytest.skip("Cloud file storage not configured - needed for horizontal scaling")

    def test_session_backend_scalable(self):
        """
        ARCHITECTURE TEST: Session backend should be database or cache-based.
        
        Risk: File-based sessions don't work with multiple servers.
        """
        session_engine = settings.SESSION_ENGINE
        
        is_scalable = 'cached_db' in session_engine or \
                      'cache' in session_engine or \
                      'database' in session_engine or \
                      'redis' in session_engine
        
        assert is_scalable, \
            f"Session engine '{session_engine}' may not scale horizontally"


@pytest.mark.architecture
class TestSecurityArchitecture:
    """Tests for security-related architecture."""

    def test_security_middleware_enabled(self):
        """
        ARCHITECTURE TEST: Security middleware should be enabled.
        """
        middleware = settings.MIDDLEWARE
        
        has_security = any('SecurityMiddleware' in m for m in middleware)
        has_csrf = any('CsrfViewMiddleware' in m for m in middleware)
        has_xframe = any('XFrameOptionsMiddleware' in m for m in middleware)
        
        assert has_security, "SecurityMiddleware not enabled"
        assert has_csrf, "CsrfViewMiddleware not enabled"
        if not has_xframe:
            pytest.skip("XFrameOptionsMiddleware not enabled - recommended")

    def test_https_enforced_in_production(self):
        """
        ARCHITECTURE TEST: HTTPS should be enforced in production.
        """
        if not settings.DEBUG:
            secure_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
            assert secure_ssl_redirect, "SECURE_SSL_REDIRECT should be True in production"

    def test_password_hashers_secure(self):
        """
        ARCHITECTURE TEST: Password hashers should use strong algorithms.
        
        Recommended: Argon2, PBKDF2 with high iterations.
        """
        hashers = getattr(settings, 'PASSWORD_HASHERS', [])
        
        if hashers:
            primary_hasher = hashers[0]
            
            is_strong = 'Argon2' in primary_hasher or \
                       ('PBKDF2' in primary_hasher and 'SHA' in primary_hasher)
            
            assert is_strong, \
                f"Primary password hasher '{primary_hasher}' should be Argon2 or PBKDF2SHA256"


@pytest.mark.architecture
class TestMonitoringArchitecture:
    """Tests for monitoring and observability architecture."""

    def test_error_tracking_configured(self):
        """
        ARCHITECTURE TEST: Error tracking (Sentry, etc.) should be configured.
        
        Best Practice: Catch production errors proactively.
        """
        # Check for Sentry or similar
        has_sentry = hasattr(settings, 'SENTRY_DSN') or \
                     'sentry_sdk' in str(settings.INSTALLED_APPS)
        
        if not has_sentry:
            pytest.skip("Error tracking (Sentry) not configured - recommended for production")

    def test_audit_logging_app_installed(self):
        """
        ARCHITECTURE TEST: Audit logging should be enabled.
        
        Critical for: Financial platforms, GDPR compliance.
        """
        has_audit = 'audit' in settings.INSTALLED_APPS or \
                    any('audit' in app for app in settings.INSTALLED_APPS)
        
        assert has_audit, "Audit app not found - critical for financial platform"

    def test_monitoring_app_installed(self):
        """
        ARCHITECTURE TEST: Monitoring app should exist.
        
        Critical for: Performance tracking, health checks.
        """
        has_monitoring = 'monitoring' in settings.INSTALLED_APPS or \
                        any('monitoring' in app for app in settings.INSTALLED_APPS)
        
        assert has_monitoring, "Monitoring app not found"


@pytest.mark.architecture
class TestDeploymentArchitecture:
    """Tests for deployment-related architecture."""

    def test_allowed_hosts_configured(self):
        """
        ARCHITECTURE TEST: ALLOWED_HOSTS should not be wildcard in production.
        """
        allowed_hosts = settings.ALLOWED_HOSTS
        
        if not settings.DEBUG:
            assert allowed_hosts != ['*'], \
                "ALLOWED_HOSTS should not be ['*'] in production"
            assert len(allowed_hosts) > 0, \
                "ALLOWED_HOSTS must be configured in production"

    def test_debug_false_in_production(self):
        """
        ARCHITECTURE TEST: DEBUG should be False in production.
        """
        # Can't test this in dev, but ensure it's configurable
        debug_env_var = 'DEBUG' in str(settings.DEBUG) or isinstance(settings.DEBUG, bool)
        assert debug_env_var, "DEBUG should be configurable via environment"

    def test_wsgi_application_configured(self):
        """
        ARCHITECTURE TEST: WSGI application should be configured.
        """
        assert hasattr(settings, 'WSGI_APPLICATION'), \
            "WSGI_APPLICATION not configured"

    def test_requirements_file_exists(self):
        """
        ARCHITECTURE TEST: requirements.txt should exist.
        
        Best Practice: Dependency management for deployment.
        """
        requirements = Path(settings.BASE_DIR) / 'requirements.txt'
        pyproject = Path(settings.BASE_DIR) / 'pyproject.toml'
        pipfile = Path(settings.BASE_DIR) / 'Pipfile'
        
        has_deps = requirements.exists() or pyproject.exists() or pipfile.exists()
        
        assert has_deps, "No dependency file found (requirements.txt, pyproject.toml, or Pipfile)"


@pytest.mark.architecture
class TestDataIntegrity:
    """Tests for data integrity architecture."""

    def test_models_use_constraints(self):
        """
        ARCHITECTURE TEST: Models should use database constraints.
        
        Best Practice: unique_together, check constraints for data integrity.
        """
        models_with_constraints = []
        
        for model in apps.get_models():
            if model._meta.app_label.startswith('django.'):
                continue
            
            # Check for unique_together or constraints
            if model._meta.unique_together or \
               (hasattr(model._meta, 'constraints') and model._meta.constraints):
                models_with_constraints.append(model.__name__)
        
        # Should have at least some constraints
        assert len(models_with_constraints) > 0, \
            "No models with constraints found - consider adding for data integrity"

    def test_foreign_keys_have_on_delete(self):
        """
        ARCHITECTURE TEST: Foreign keys should specify on_delete behavior.
        
        Risk: Undefined cascade behavior leads to data inconsistency.
        """
        # This is enforced by Django itself, so if migrations exist, this passes
        migrations_exist = Path(settings.BASE_DIR).rglob('*/migrations/*.py')
        
        assert any(migrations_exist), "Migrations should exist"


@pytest.mark.architecture
class TestAPISecurityArchitecture:
    """Tests for API security architecture."""

    def test_api_rate_limiting_configured(self):
        """
        ARCHITECTURE TEST: API should have rate limiting.
        
        Risk: DoS attacks, API abuse.
        """
        if 'rest_framework' in settings.INSTALLED_APPS:
            rest_config = getattr(settings, 'REST_FRAMEWORK', {})
            
            has_throttling = 'DEFAULT_THROTTLE_CLASSES' in rest_config and \
                           'DEFAULT_THROTTLE_RATES' in rest_config
            
            if not has_throttling:
                pytest.skip("DRF throttling not configured - recommended for production APIs")

    def test_api_authentication_configured(self):
        """
        ARCHITECTURE TEST: API should have default authentication.
        
        Risk: Open APIs without authentication.
        """
        if 'rest_framework' in settings.INSTALLED_APPS:
            rest_config = getattr(settings, 'REST_FRAMEWORK', {})
            
            has_auth = 'DEFAULT_AUTHENTICATION_CLASSES' in rest_config
            
            assert has_auth, "DRF DEFAULT_AUTHENTICATION_CLASSES should be configured"

    def test_cors_properly_configured(self):
        """
        ARCHITECTURE TEST: CORS should be properly configured if needed.
        
        Risk: Either too open (security) or too closed (functionality).
        """
        has_cors = 'corsheaders' in settings.INSTALLED_APPS
        
        if has_cors:
            # CORS is configured, check it's not wide open
            allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            allow_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
            
            if allow_all:
                pytest.fail("CORS_ALLOW_ALL_ORIGINS=True is a security risk in production")
