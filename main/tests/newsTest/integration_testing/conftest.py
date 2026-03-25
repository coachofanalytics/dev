"""
Pytest Configuration for Integration Tests
Centralized configuration for running integration tests
"""

import os
import django
from django.conf import settings


def pytest_configure():
    """Configure Django settings before running tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
    django.setup()
