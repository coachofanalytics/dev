from django.test import TestCase
from pathlib import Path
from django.apps import apps


class MigrationAndConstraintsTests(TestCase):
    def test_migrations_exist_for_core_apps(self):
        # Determine project base reliably across different test invocation contexts
        resolved = Path(__file__).resolve()
        candidates = [resolved.parents[3], resolved.parents[2], resolved.parents[4] if len(resolved.parents) > 4 else resolved.parents[3]]
        base = None
        for cand in candidates:
            if (cand / 'manage.py').exists() or (cand / 'pyproject.toml').exists() or (cand / 'requirements.txt').exists():
                base = cand
                break
        if base is None:
            base = resolved.parents[3]
        apps_to_check = ['accounts', 'payments', 'marketplace', 'onboarding', 'kyc']
        for app in apps_to_check:
            migrations_dir = base / app / 'migrations'
            self.assertTrue(migrations_dir.exists(), f"Migrations missing for {app}")
            py_files = list(migrations_dir.glob('[0-9]*_*.py'))
            self.assertTrue(len(py_files) > 0, f"No migration files in {migrations_dir}")
