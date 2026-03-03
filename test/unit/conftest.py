import os
import pytest

# Ensure tests use project settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    # Provide safe defaults for secrets and services during tests
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('DEBUG', 'False')
    monkeypatch.setenv('OPENAI_API_KEY', 'test')
    # Celery eager mode
    monkeypatch.setenv('CELERY_TASK_ALWAYS_EAGER', 'True')
    yield
