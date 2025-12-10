"""
Programmatic runner for the `tests/payment` suite.

This script sets up Django's test environment and test databases using
`DiscoverRunner`, then loads test modules directly from file paths and
executes them. This avoids test discovery import issues that can occur
when the `tests` package name conflicts or when dotted labels fail.

Usage (from project root, with venv activated):
    python scripts/run_payment_tests.py

The script will run all `test_*.py` files under `tests/payment`.
"""
import os
import sys
import django
import unittest
import importlib.util
from django.conf import settings


def discover_test_files(start_dir):
    """Yield absolute paths to test files under start_dir matching test_*.py."""
    for root, dirs, files in os.walk(start_dir):
        for f in files:
            if f.startswith('test_') and f.endswith('.py'):
                yield os.path.join(root, f)


def load_module_from_path(path, module_name=None):
    """Import a module from a file path with a unique module name."""
    module_name = module_name or f"tests_payment_file_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    BASE_DIR = Path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    tests_dir = os.path.join(BASE_DIR, 'tests', 'payment')

    if not os.path.isdir(tests_dir):
        print(f"Tests directory not found: {tests_dir}")
        sys.exit(1)

    # Ensure project root is on sys.path
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    # Create lightweight package entries for `tests` and `tests.payment` so
    # modules that import using `from tests.payment...` succeed when we load
    # individual files by path.
    import types
    tests_pkg_path = os.path.join(BASE_DIR, 'tests')
    payment_pkg_path = os.path.join(tests_pkg_path, 'payment')
    if 'tests' not in sys.modules:
        tests_pkg = types.ModuleType('tests')
        tests_pkg.__path__ = [tests_pkg_path]
        sys.modules['tests'] = tests_pkg
    if 'tests.payment' not in sys.modules:
        payment_pkg = types.ModuleType('tests.payment')
        payment_pkg.__path__ = [payment_pkg_path]
        sys.modules['tests.payment'] = payment_pkg

    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    # Use DiscoverRunner to create test DBs and manage environment
    from django.test.runner import DiscoverRunner

    test_runner = DiscoverRunner(verbosity=1, interactive=False)
    test_runner.setup_test_environment()
    old_config = test_runner.setup_databases()

    try:
        loader = unittest.TestLoader()
        master_suite = unittest.TestSuite()

        for path in discover_test_files(tests_dir):
            print(f"Loading tests from {path}")
            module = load_module_from_path(path)
            suite = loader.loadTestsFromModule(module)
            master_suite.addTests(suite)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(master_suite)

        if not result.wasSuccessful():
            sys.exit(2)

    finally:
        test_runner.teardown_databases(old_config)
        test_runner.teardown_test_environment()


if __name__ == '__main__':
    main()
