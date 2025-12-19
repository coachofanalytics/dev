import unittest
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

try:
    from coda.investing.models import ManagedTradingAccount, TradingRule, TradingActivity
    INVESTING_MODELS_IMPORT_ERROR = None
except RuntimeError as exc:  # pragma: no cover - legacy pending migrations
    ManagedTradingAccount = TradingRule = TradingActivity = None
    INVESTING_MODELS_IMPORT_ERROR = exc


@unittest.skipIf(
    INVESTING_MODELS_IMPORT_ERROR is not None,
    f"Skipping until legacy investing models are migratable: {INVESTING_MODELS_IMPORT_ERROR}",
)
class AccountLimitControlsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            email='staff@example.com',
            password='pass1234',
            is_staff=True,
            is_superuser=True,
        )
        self.account_manager = User.objects.create_user(
            email='manager@example.com',
            password='pass1234',
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='pass1234',
        )

        self.account = ManagedTradingAccount.objects.create(
            client=self.client_user,
            account_number='CODA-TEST-001',
            account_name='Test Managed Account',
            account_manager=self.account_manager,
            initial_capital=Decimal('30000'),
            current_balance=Decimal('30000'),
            cash_available=Decimal('25000'),
            cash_reserved=Decimal('0'),
            high_water_mark=Decimal('30000'),
            status='active',
            trading_enabled=True,
        )

        TradingRule.objects.create(
            managed_account=self.account,
            rule_name='Per-position cap',
            rule_type='position_size_percentage',
            rule_config={'max_percentage_per_position': '2.0'},
        )
        TradingRule.objects.create(
            managed_account=self.account,
            rule_name='Absolute cap',
            rule_type='position_limit',
            rule_config={'max_position_size': '600'},
        )

    def test_account_limits_exposed_in_context(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('investing:suggested_positions_list'))
        self.assertEqual(response.status_code, 200)

        account_limits = response.context['account_limits']
        key = str(self.account.id)
        self.assertIn(key, account_limits)
        limit_payload = account_limits[key]

        self.assertAlmostEqual(limit_payload['max_percentage'], 2.0)
        self.assertAlmostEqual(limit_payload['effective_max_dollar'], 600.0)

    def test_update_account_position_limit_updates_rules(self):
        self.client.force_login(self.staff)

        account = ManagedTradingAccount.objects.create(
            client=self.client_user,
            account_number='CODA-TEST-002',
            account_name='Adjustable Account',
            account_manager=self.account_manager,
            initial_capital=Decimal('25000'),
            current_balance=Decimal('25000'),
            cash_available=Decimal('20000'),
            cash_reserved=Decimal('0'),
            high_water_mark=Decimal('25000'),
            status='active',
            trading_enabled=True,
        )

        response = self.client.post(
            reverse('investing:update_account_position_limit'),
            {
                'account_id': account.id,
                'max_percentage': '3.5',
                'max_absolute': '800',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('investing:suggested_positions_list'))

        pct_rule = TradingRule.objects.get(
            managed_account=account,
            rule_type='position_size_percentage',
        )
        abs_rule = TradingRule.objects.get(
            managed_account=account,
            rule_type='position_limit',
        )

        self.assertEqual(pct_rule.rule_config['max_percentage_per_position'], '3.5')
        self.assertEqual(abs_rule.rule_config['max_position_size'], '800')

        activity = TradingActivity.objects.filter(
            managed_account=account,
            activity_type='rule_changed',
        ).latest('created_at')
        self.assertIn('3.5%', activity.description)

