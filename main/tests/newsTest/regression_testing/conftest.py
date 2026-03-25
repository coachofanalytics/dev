"""
Pytest Configuration for Regression Tests
Centralized configuration for running regression tests
"""

import os
import django
from django.conf import settings


def pytest_configure():
    """Configure Django settings before running tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
    django.setup()
