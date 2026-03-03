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
import sys
from pathlib import Path

# Ensure the project root (parent of 'dev') is on sys.path so imports like
# `import dev.finance` resolve correctly. conftest.py is at dev/test/conftest.py
# so parents[2] == project root (C:\...\DC48k_Train)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

# Use our test Django settings for pytest-django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test.test_settings')

import django

def pytest_configure():
    # Configure Django for tests
    django.setup()
