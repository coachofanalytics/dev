"""
Unit tests for platform_services services

Tests business logic, calculations, and service methods in isolation.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from platform_services.database_service import DatabaseService
from platform_services.heroku_service import HerokuService


class HerokuServiceTest(SimpleTestCase):
    """Tests for HerokuService core behaviour."""

    def tearDown(self):
        cache.clear()

    def test_initialization_without_heroku3_gracefully_handles_missing_dependency(self):
        """Service should not crash when heroku3 library is unavailable."""
        with patch("platform_services.heroku_service.heroku3", new=None):
            service = HerokuService(api_key="fake-key")
            self.assertIsNone(service.client)
            self.assertEqual(service.api_key, "fake-key")

    @override_settings(HEROKU_API_KEY="env-key")
    def test_initialization_uses_setting_when_api_key_not_provided(self):
        """Service should pull API key from Django settings when not passed explicitly."""
        with patch("platform_services.heroku_service.heroku3") as mock_heroku:
            mock_client = MagicMock()
            mock_heroku.from_key.return_value = mock_client
            service = HerokuService()
            self.assertEqual(service.api_key, "env-key")
            self.assertIs(service.client, mock_client)

    def test_get_app_returns_cached_value(self):
        """Cached app info should be returned without hitting API."""
        with patch("platform_services.heroku_service.heroku3") as mock_heroku:
            mock_client = MagicMock()
            mock_heroku.from_key.return_value = mock_client
            service = HerokuService(api_key="key")
            cache_key = "heroku_app_test-app"
            cache.set(cache_key, {"name": "cached"}, 30)
            result = service.get_app("test-app")
            self.assertTrue(result["success"])
            self.assertEqual(result["data"], {"name": "cached"})
            mock_client.app.assert_not_called()

    def test_get_config_returns_error_when_app_not_found(self):
        """get_config should bubble up get_app error responses."""
        service = HerokuService()
        with patch.object(service, "get_app", return_value={"success": False, "error": "missing"}):
            result = service.get_config("missing-app")
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "missing")

    def test_set_config_invalid_app_does_not_attempt_update(self):
        """set_config should not call update when app lookup fails."""
        service = HerokuService()
        with patch.object(service, "get_app", return_value={"success": False, "error": "missing"}) as mock_get_app:
            result = service.set_config("missing", "KEY", "value")
            self.assertFalse(result["success"])
            mock_get_app.assert_called_once()


class DatabaseServiceTest(SimpleTestCase):
    """Tests for DatabaseService header helpers."""

    def test_header_helpers_include_api_key(self):
        service = DatabaseService(api_key="header-key")
        heroku_headers = service._heroku_headers()
        postgres_headers = service._postgres_headers()

        self.assertIn("Authorization", heroku_headers)
        self.assertTrue(heroku_headers["Authorization"].endswith("header-key"))
        self.assertIn("Accept", heroku_headers)
        self.assertIn("application/vnd.heroku+json", heroku_headers["Accept"])

        self.assertIn("Authorization", postgres_headers)
        self.assertTrue(postgres_headers["Authorization"].endswith("header-key"))
        self.assertEqual(postgres_headers["Accept"], "application/json")

    def test_handle_api_call_without_client_returns_error(self):
        service = DatabaseService(api_key="no-client")
        # Force client to None to simulate missing initialization
        service.client = None
        result = service._handle_api_call(lambda: "data")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Heroku client not initialized")

    def test_handle_api_call_success(self):
        with patch("platform_services.heroku_service.heroku3") as mock_heroku:
            mock_client = MagicMock()
            mock_heroku.from_key.return_value = mock_client
            service = DatabaseService(api_key="key")
            service.client = mock_client
            mock_func = MagicMock(return_value=["app1", "app2"])
            result = service._handle_api_call(mock_func)
            self.assertTrue(result["success"])
            self.assertEqual(result["data"], ["app1", "app2"])
            mock_func.assert_called_once()
