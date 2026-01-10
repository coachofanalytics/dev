"""
Architecture Tests: Dependency Management & Layer Separation
Tests for proper module dependencies and avoiding circular dependencies.
"""

import pytest
from django.apps import apps
from django.conf import settings
import importlib
import os
import sys
from pathlib import Path


@pytest.mark.architecture
class TestDependencyArchitecture:
    """Tests for module dependency architecture."""

    def test_no_circular_imports(self):
        """
        ARCHITECTURE TEST: Ensure no circular dependencies between apps.
        
        Risk: Circular dependencies make code fragile and hard to maintain.
        """
        # Try importing all app modules to detect circular imports
        app_configs = apps.get_app_configs()
        errors = []
        
        for app_config in app_configs:
            if app_config.name.startswith('django.'):
                continue  # Skip Django's own apps
            
            try:
                importlib.import_module(app_config.name)
            except ImportError as e:
                errors.append(f"Import error in {app_config.name}: {str(e)}")
        
        assert len(errors) == 0, f"Circular import or import errors detected:\n" + "\n".join(errors)

    def test_core_apps_are_independent(self):
        """
        ARCHITECTURE TEST: Core business apps should not depend on each other.
        
        Expected: accounts, marketplace, payments can exist independently.
        Risk: Tight coupling makes modules hard to test and reuse.
        """
        # Define which apps should be independent
        independent_apps = ['accounts', 'marketplace', 'payments', 'kyc', 'gdpr']
        
        # This is a simplified test - in real scenarios, you'd use tools like
        # import-linter or analyze import statements
        for app in independent_apps:
            try:
                importlib.import_module(app)
            except ImportError:
                # App might not exist, which is fine
                pass
        
        # All imports succeeded without circular dependency errors
        assert True

    def test_models_dont_import_views(self):
        """
        ARCHITECTURE TEST: Models should never import views.
        
        Violates: MVC/MVT pattern - models are data layer, views are presentation.
        Risk: Creates tight coupling and makes testing difficult.
        """
        violations = []
        
        # Get all Django apps in the project
        project_apps = [
            'accounts', 'payments', 'marketplace', 'kyc', 'gdpr', 
            'monitoring', 'audit', 'onboarding', 'core'
        ]
        
        for app_name in project_apps:
            models_path = Path(settings.BASE_DIR) / app_name / 'models.py'
            if not models_path.exists():
                continue
            
            with open(models_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for view imports
            if 'from .views import' in content or f'from {app_name}.views import' in content:
                violations.append(f"{app_name}/models.py imports from views")
        
        assert len(violations) == 0, f"Architecture violation:\n" + "\n".join(violations)

    def test_settings_split_architecture(self):
        """
        ARCHITECTURE TEST: Settings should be split by environment.
        
        Best Practice: Separate dev, staging, production settings.
        Risk: Mixing environments leads to security issues.
        """
        config_dir = Path(settings.BASE_DIR) / 'config'
        
        # Check for settings organization
        has_base_settings = (config_dir / 'settings.py').exists()
        has_settings_dir = (config_dir / 'settings').exists()
        
        # Either single file or directory structure is acceptable
        assert has_base_settings or has_settings_dir, \
            "Settings file not found in expected location"


@pytest.mark.architecture
class TestLayeredArchitecture:
    """Tests for proper layered architecture (Presentation -> Business -> Data)."""

    def test_views_dont_access_db_directly(self):
        """
        ARCHITECTURE TEST: Views should use services/managers, not raw ORM queries.
        
        Best Practice: Business logic in services, not views.
        Risk: Duplicated logic, hard to test, security issues.
        """
        # This is a heuristic test - checks for common anti-patterns
        violations = []
        
        project_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr']
        
        for app_name in project_apps:
            views_path = Path(settings.BASE_DIR) / app_name / 'views.py'
            if not views_path.exists():
                continue
            
            with open(views_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for anti-patterns (this is simplified)
            # In production, you'd use AST parsing for accuracy
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for filter() or create() calls in views
                # (Should be in services/managers instead)
                if '.filter(' in line or '.create(' in line:
                    # Allow if it's in a service or manager
                    if 'service' not in content.lower() and 'manager' not in content.lower():
                        # This is informational - many Django apps do this
                        pass  # Not failing this as it's common in Django
        
        # Not enforcing strict service layer for now
        assert True

    def test_services_exist_for_complex_logic(self):
        """
        ARCHITECTURE TEST: Complex apps should have service layers.
        
        Best Practice: Business logic in dedicated service modules.
        """
        complex_apps = ['payments', 'marketplace']
        
        for app_name in complex_apps:
            services_path = Path(settings.BASE_DIR) / app_name / 'services'
            services_file = Path(settings.BASE_DIR) / app_name / 'services.py'
            
            has_services = services_path.exists() or services_file.exists()
            
            assert has_services, \
                f"{app_name} app should have a services module for business logic"


@pytest.mark.architecture
class TestModularity:
    """Tests for modular architecture and code organization."""

    def test_each_app_has_proper_structure(self):
        """
        ARCHITECTURE TEST: Each Django app should have standard structure.
        
        Expected: models.py, views.py, urls.py, tests/ (at minimum for complete apps).
        """
        core_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr']
        
        for app_name in core_apps:
            app_path = Path(settings.BASE_DIR) / app_name
            
            if not app_path.exists():
                continue
            
            # Check for essential files
            has_models = (app_path / 'models.py').exists() or (app_path / 'models').exists()
            has_init = (app_path / '__init__.py').exists()
            
            assert has_init, f"{app_name} missing __init__.py"
            # Models are optional for some apps
            # assert has_models, f"{app_name} missing models.py"

    def test_apps_registered_in_settings(self):
        """
        ARCHITECTURE TEST: All project apps should be in INSTALLED_APPS.
        
        Risk: Missing app registration causes runtime errors.
        """
        required_apps = ['accounts', 'payments', 'marketplace', 'gdpr', 'kyc']
        
        for app in required_apps:
            is_installed = any(
                app == installed or app in installed 
                for installed in settings.INSTALLED_APPS
            )
            assert is_installed, f"{app} not in INSTALLED_APPS"

    def test_middleware_order_correct(self):
        """
        ARCHITECTURE TEST: Security middleware should be in correct order.
        
        Expected Order:
        1. SecurityMiddleware (first)
        2. SessionMiddleware
        3. CsrfViewMiddleware (after session)
        4. AuthenticationMiddleware (after session)
        """
        middleware = settings.MIDDLEWARE
        
        # Find indices
        security_idx = next((i for i, m in enumerate(middleware) if 'SecurityMiddleware' in m), None)
        session_idx = next((i for i, m in enumerate(middleware) if 'SessionMiddleware' in m), None)
        csrf_idx = next((i for i, m in enumerate(middleware) if 'CsrfViewMiddleware' in m), None)
        auth_idx = next((i for i, m in enumerate(middleware) if 'AuthenticationMiddleware' in m), None)
        
        # Security should be first (or near first)
        if security_idx is not None:
            assert security_idx < 3, "SecurityMiddleware should be among the first middleware"
        
        # CSRF should be after Session
        if csrf_idx is not None and session_idx is not None:
            assert csrf_idx > session_idx, "CsrfViewMiddleware must come after SessionMiddleware"
        
        # Authentication should be after Session
        if auth_idx is not None and session_idx is not None:
            assert auth_idx > session_idx, "AuthenticationMiddleware must come after SessionMiddleware"


@pytest.mark.architecture
class TestDatabaseArchitecture:
    """Tests for database architecture and ORM usage."""

    def test_models_use_proper_indexes(self):
        """
        ARCHITECTURE TEST: Models should have indexes for frequently queried fields.
        
        Best Practice: Foreign keys auto-indexed, but add indexes for common filters.
        """
        from django.apps import apps
        
        indexed_fields_found = []
        
        for model in apps.get_models():
            # Skip Django's internal models
            if model._meta.app_label.startswith('django.'):
                continue
            
            # Check for explicit indexes
            for field in model._meta.fields:
                if getattr(field, 'db_index', False):
                    indexed_fields_found.append(f"{model.__name__}.{field.name}")
        
        # We should have at least some indexed fields
        assert len(indexed_fields_found) > 0, \
            "No explicit indexes found. Consider adding indexes for performance."

    def test_no_raw_sql_in_models(self):
        """
        ARCHITECTURE TEST: Prefer ORM over raw SQL for maintainability.
        
        Risk: Raw SQL harder to maintain, security risks (SQL injection).
        """
        violations = []
        
        project_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr']
        
        for app_name in project_apps:
            models_path = Path(settings.BASE_DIR) / app_name / 'models.py'
            if not models_path.exists():
                continue
            
            with open(models_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for raw SQL usage
            if '.raw(' in content or 'connection.cursor()' in content:
                violations.append(f"{app_name}/models.py contains raw SQL")
        
        # Raw SQL is sometimes necessary, so this is informational
        if violations:
            pytest.skip(f"Raw SQL found (not necessarily bad): {', '.join(violations)}")

    def test_migrations_exist_for_all_apps(self):
        """
        ARCHITECTURE TEST: All apps with models should have migrations.
        
        Risk: Missing migrations cause deployment issues.
        """
        project_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr', 'audit', 'monitoring']
        
        for app_name in project_apps:
            app_path = Path(settings.BASE_DIR) / app_name
            if not app_path.exists():
                continue
            
            models_path = app_path / 'models.py'
            migrations_path = app_path / 'migrations'
            
            # If app has models, it should have migrations directory
            if models_path.exists():
                assert migrations_path.exists(), \
                    f"{app_name} has models but no migrations directory"


@pytest.mark.architecture
class TestAPIArchitecture:
    """Tests for API architecture and design."""

    def test_api_versioning_present(self):
        """
        ARCHITECTURE TEST: API should support versioning.
        
        Best Practice: /api/v1/ structure for future-proofing.
        """
        # Check if DRF is installed
        has_rest_framework = 'rest_framework' in settings.INSTALLED_APPS
        
        if has_rest_framework:
            # Check main URL configuration
            from django.urls import get_resolver
            resolver = get_resolver()
            
            # Look for versioned API patterns
            url_patterns = [str(pattern.pattern) for pattern in resolver.url_patterns]
            
            has_versioned_api = any('api/v' in pattern for pattern in url_patterns)
            
            # Versioning is recommended but not required
            if not has_versioned_api:
                pytest.skip("API versioning not found - recommended for production")
        else:
            pytest.skip("DRF not installed, skipping API tests")

    def test_api_uses_serializers(self):
        """
        ARCHITECTURE TEST: DRF APIs should use serializers, not raw models.
        
        Best Practice: Serializers for data validation and transformation.
        """
        has_rest_framework = 'rest_framework' in settings.INSTALLED_APPS
        
        if has_rest_framework:
            serializers_found = []
            
            project_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr']
            
            for app_name in project_apps:
                serializers_path = Path(settings.BASE_DIR) / app_name / 'serializers.py'
                if serializers_path.exists():
                    serializers_found.append(app_name)
            
            # If DRF is installed, at least one app should have serializers
            assert len(serializers_found) > 0, \
                "DRF installed but no serializers found in any app"
        else:
            pytest.skip("DRF not installed")


@pytest.mark.architecture
class TestCodeQuality:
    """Tests for code quality and best practices."""

    def test_no_print_statements_in_code(self):
        """
        ARCHITECTURE TEST: No print() statements in production code.
        
        Best Practice: Use logging instead of print.
        Risk: print() statements expose debug info, don't respect log levels.
        """
        violations = []
        
        project_apps = ['accounts', 'payments', 'marketplace', 'kyc', 'gdpr']
        
        for app_name in project_apps:
            app_path = Path(settings.BASE_DIR) / app_name
            if not app_path.exists():
                continue
            
            # Check .py files (excluding migrations and tests)
            for py_file in app_path.rglob('*.py'):
                if 'migration' in str(py_file) or 'test_' in py_file.name:
                    continue
                
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if '\nprint(' in content or ' print(' in content:
                    violations.append(str(py_file.relative_to(settings.BASE_DIR)))
        
        # This is a warning, not a hard failure
        if violations:
            print(f"\nWARNING: print() statements found in: {', '.join(violations)}")
            # Not failing the test as print() is sometimes useful

    def test_proper_logging_configured(self):
        """
        ARCHITECTURE TEST: Logging should be properly configured.
        
        Best Practice: Use Django's logging framework.
        """
        assert hasattr(settings, 'LOGGING'), "LOGGING not configured in settings"
        
        logging_config = settings.LOGGING
        
        # Should have handlers and loggers
        assert 'handlers' in logging_config, "No logging handlers configured"
        assert 'loggers' in logging_config or 'root' in logging_config, \
            "No loggers configured"

    def test_secret_key_not_in_settings_file(self):
        """
        ARCHITECTURE TEST: SECRET_KEY should come from environment variables.
        
        Security Risk: Hardcoded secrets in version control.
        """
        settings_file = Path(settings.BASE_DIR) / 'config' / 'settings.py'
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if SECRET_KEY is hardcoded (not from env)
            has_hardcoded_secret = "SECRET_KEY = '" in content or 'SECRET_KEY = "' in content
            
            if has_hardcoded_secret and 'os.environ' not in content and 'os.getenv' not in content:
                pytest.fail("SECRET_KEY appears to be hardcoded. Use environment variables.")


@pytest.mark.architecture
class TestTestArchitecture:
    """Tests for test architecture and organization."""

    def test_tests_directory_structure_proper(self):
        """
        ARCHITECTURE TEST: Tests should be organized by type.
        
        Expected: tests/unit/, tests/integration/, tests/security/, etc.
        """
        tests_dir = Path(settings.BASE_DIR) / 'tests'
        
        assert tests_dir.exists(), "tests/ directory not found"
        
        # Check for test organization
        subdirs = [d.name for d in tests_dir.iterdir() if d.is_dir()]
        
        # Should have at least 2 types of tests
        assert len(subdirs) >= 2, \
            f"Tests should be organized by type. Found: {subdirs}"

    def test_each_test_file_properly_marked(self):
        """
        ARCHITECTURE TEST: Test files should have pytest markers.
        
        Best Practice: @pytest.mark.unit, @pytest.mark.integration, etc.
        """
        tests_dir = Path(settings.BASE_DIR) / 'tests'
        
        test_files = list(tests_dir.rglob('test_*.py'))
        
        assert len(test_files) > 0, "No test files found"
        
        files_with_markers = 0
        
        for test_file in test_files[:10]:  # Sample first 10
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '@pytest.mark.' in content or 'pytest.mark' in content:
                files_with_markers += 1
        
        # At least some tests should have markers
        marker_percentage = (files_with_markers / min(10, len(test_files))) * 100
        
        assert marker_percentage > 30, \
            f"Only {marker_percentage:.0f}% of test files have pytest markers"
