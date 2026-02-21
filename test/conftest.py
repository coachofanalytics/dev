import os
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
