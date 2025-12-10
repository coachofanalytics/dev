"""
Run a single Django test module with settings configured.

Usage:
    python scripts/run_single_django_test.py tests.payment.integration.test_mpesa_stk_callback

This script sets `DJANGO_SETTINGS_MODULE` to `config.settings`, calls
`django.setup()` and runs the specified unittest module. It helps run
individual Django TestCase modules outside of `manage.py test` when test
discovery/import issues occur.
"""
import os
import sys
import importlib
import unittest

# Ensure project root is on sys.path for module discovery
sys.path.insert(0, os.getcwd())


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/run_single_django_test.py <dotted_test_module>')
        return 2

    test_module = sys.argv[1]

    # Ensure we use project settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django
    django.setup()

    # Import the test module and run it
    # Try import by dotted module name first. If it fails, fall back to
    # loading the test file by filesystem path (useful when packages are
    # not importable via a plain module import).
    module = None
    try:
        module = importlib.import_module(test_module)
    except Exception:
        # Construct a filesystem path for the dotted module
        path_parts = test_module.split('.')
        file_path = os.path.join(os.getcwd(), *path_parts) + '.py'
        if not os.path.exists(file_path):
            print('Failed to import test module and file not found:', file_path)
            raise

        from importlib.machinery import SourceFileLoader
        module = SourceFileLoader(test_module, file_path).load_module()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
