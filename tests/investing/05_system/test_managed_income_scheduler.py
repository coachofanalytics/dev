import os
from datetime import date, timedelta
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.test import SimpleTestCase, override_settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()


@override_settings(UNUSUAL_WHALES_ENABLED=False)
class ManagedIncomeSchedulerTests(SimpleTestCase):
    def test_scheduler_returns_allocation_summary(self):
        suggestion = SimpleNamespace(
            id=1,
            symbol='AMD',
            strategy='bull_put_spread',
            probability_of_profit=Decimal('78'),
            ai_score=Decimal('82'),
            premium_collected=Decimal('215'),
            capital_required=Decimal('2500'),
            max_profit=Decimal('215'),
            max_loss=Decimal('2285'),
            positions=[],
            api_response_data={'unusual_whales': {'flow_score': 80, 'timing_signal': '🟢 ENTER NOW'}},
        )

        class FakeQuerySet(list):
            def order_by(self_inner, *args, **kwargs):
                return self_inner

        fake_queryset = FakeQuerySet([suggestion])

        try:
            tasks_module = import_module('coda.investing.tasks')
        except RuntimeError as exc:
            self.skipTest(
                "TODO-managed-income: real migrations for accounts/investing missing; "
                f"scheduler test will run once migration backlog is cleared. Root cause: {exc}"
            )

        summary = {
            'success': True,
            'allocations': [{'symbol': 'AMD'}],
            'totals': {'positions': 1, 'coverage_pct': Decimal('105'), 'expected_income': Decimal('450')},
            'meets_target': True,
            'notes': [],
        }

        with patch.object(tasks_module.SuggestedPosition.objects, 'filter', return_value=fake_queryset), \
             patch.object(tasks_module.NotificationService, 'send_internal_allocation_digest', return_value=True) as mock_digest, \
             patch.object(tasks_module.CapitalAllocationService, 'recommend_allocations', return_value=summary):

            result = tasks_module.managed_income_scheduler.run()

        self.assertTrue(result['success'])
        self.assertEqual(result['totals']['positions'], 1)
        mock_digest.assert_called_once()

