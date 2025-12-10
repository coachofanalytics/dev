"""
Run each `tests/payment` test file one-by-one with environment loaded from `.env`.

This script:
- Loads environment variables from the project's `.env` file (if present) into
  the current process (only in-memory; it does not modify files or commit secrets).
- Runs each `test_*.py` under `tests/payment` separately. For each file it:
  - Sets up Django test environment and databases
  - Runs tests in that file
  - Tears down the databases

Usage (with venv activated):
    python scripts/run_payment_tests_with_env.py --all

This will run integration tests too (they will use the credentials from `.env`).
"""
import os
import sys
import django
import argparse
import importlib.util
import unittest


def load_dotenv(path):
    """Read simple KEY=VALUE lines from a .env file and set in os.environ.

    Ignores comments and empty lines. Values are not exported to disk.
    """
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # Do not override existing environment variables unless empty
            if os.environ.get(key) in (None, ''):
                os.environ[key] = val


def discover_test_files(start_dir):
    for root, dirs, files in os.walk(start_dir):
        for f in sorted(files):
            if f.startswith('test_') and f.endswith('.py'):
                yield os.path.join(root, f)


def load_module_from_path(path):
    spec = importlib.util.spec_from_file_location(f"testmod_{abs(hash(path))}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tests_in_file(path):
    print('\n' + '=' * 80)
    print(f"Running tests in {path}")

    # Setup Django test env for this file
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1, interactive=False)
    runner.setup_test_environment()
    old_config = runner.setup_databases()

    try:
        module = load_module_from_path(path)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner_out = unittest.TextTestRunner(verbosity=2).run(suite)
        ok = runner_out.wasSuccessful()
        print(f"Result for {os.path.basename(path)}: {'OK' if ok else 'FAIL'}")
        return ok
    finally:
        runner.teardown_databases(old_config)
        runner.teardown_test_environment()


def main():
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)

    # Ensure project root is on path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Make `tests` and `tests.payment` importable for modules that use
    # `from tests.payment...` imports when we load files by path.
    import types
    tests_pkg_path = os.path.join(project_root, 'tests')
    payment_pkg_path = os.path.join(tests_pkg_path, 'payment')
    if 'tests' not in sys.modules:
        tests_pkg = types.ModuleType('tests')
        tests_pkg.__path__ = [tests_pkg_path]
        sys.modules['tests'] = tests_pkg
    if 'tests.payment' not in sys.modules:
        payment_pkg = types.ModuleType('tests.payment')
        payment_pkg.__path__ = [payment_pkg_path]
        sys.modules['tests.payment'] = payment_pkg

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    tests_dir = os.path.join(project_root, 'tests', 'payment')
    if not os.path.isdir(tests_dir):
        print('No tests/payment directory found')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='Run all test files one-by-one')
    args = parser.parse_args()

    files = list(discover_test_files(tests_dir))
    if not files:
        print('No test files found')
        sys.exit(0)

    failed = []
    for path in files:
        ok = run_tests_in_file(path)
        if not ok:
            failed.append(path)

    print('\n' + '=' * 80)
    if failed:
        print('Some test files failed:')
        for f in failed:
            print('-', f)
        sys.exit(2)
    print('All test files passed')


if __name__ == '__main__':
    main()
