import os
import pytest
from django.conf import settings


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Ensure test environment variables are set and isolate external services."""
    monkeypatch.setenv('ENVIRONMENT', 'testing')
    # Avoid using real AWS/Redis/OpenAI etc.
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test')
    monkeypatch.setenv('AWS_STORAGE_BUCKET_NAME', 'test-bucket')
    monkeypatch.setenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    monkeypatch.setenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Minimal settings overrides
    settings.DEBUG = True
    # Use default allauth adapter to avoid missing custom adapter in tests
    try:
        settings.SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'
    except Exception:
        pass
