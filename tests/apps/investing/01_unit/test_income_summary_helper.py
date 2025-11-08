import unittest
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

try:
    from coda.investing.models import ManagedTradingAccount, OptionsPosition
    from coda.investing.services.managed_trading_service import ManagedTradingService
    INVESTING_MODELS_IMPORT_ERROR = None
except RuntimeError as exc:  # pragma: no cover - skip until legacy migrations restored
    ManagedTradingAccount = None
    OptionsPosition = None
    ManagedTradingService = None
    INVESTING_MODELS_IMPORT_ERROR = exc


@unittest.skipIf(
    INVESTING_MODELS_IMPORT_ERROR is not None,
    f"Skipping until legacy investing models are migratable: {INVESTING_MODELS_IMPORT_ERROR}",
)
class IncomeSummaryServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='test-pass-123',
        )

        self.account = ManagedTradingAccount.objects.create(
            client=self.client_user,
            account_number='CODA-OPT-501',
            account_name='Test Managed Account',
            initial_capital=Decimal('30000'),
            current_balance=Decimal('30500'),
            cash_available=Decimal('25000'),
            cash_reserved=Decimal('5000'),
            high_water_mark=Decimal('30500'),
            fee_tier='professional',
            management_fee_percentage=Decimal('1.50'),
            performance_fee_percentage=Decimal('20.00'),
            performance_threshold=Decimal('8.00'),
            status='active',
            trading_enabled=True,
        )

        self.service = ManagedTradingService()

        legs_payload = [
            {
                "type": "put",
                "direction": "short",
                "contracts": 1,
                "strike": 150,
                "expiration": (date.today() + timedelta(days=30)).isoformat(),
            }
        ]

        # Open position (premium counted toward projected income)
        OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='AAPL',
            strategy='bull_put_spread',
            positions=legs_payload,
            capital_required=Decimal('1500'),
            premium_collected=Decimal('150'),
            max_profit=Decimal('150'),
            max_loss=Decimal('850'),
            probability_of_profit=Decimal('75'),
            expiration_date=date.today() + timedelta(days=30),
            status='open',
            unrealized_pnl=Decimal('45'),
            current_value=Decimal('0'),
            api_response_data={
                'unusual_whales': {
                    'flow_score': 82,
                    'sentiment': 'bullish',
                    'timing_signal': '🟢 ENTER NOW',
                    'entry_window': 'Next 1-2 sessions',
                }
            },
        )

        # Closed position (realized income)
        OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='MSFT',
            strategy='bear_call_spread',
            positions=legs_payload,
            capital_required=Decimal('1200'),
            premium_collected=Decimal('120'),
            max_profit=Decimal('120'),
            max_loss=Decimal('880'),
            probability_of_profit=Decimal('72'),
            expiration_date=date.today() + timedelta(days=10),
            exit_date=date.today(),
            status='closed',
            realized_pnl=Decimal('200'),
            current_value=Decimal('0'),
            api_response_data={
                'unusual_whales': {
                    'flow_score': 76,
                    'sentiment': 'neutral',
                    'timing_signal': '🟡 OK TO ENTER',
                    'entry_window': 'Within 2 sessions',
                }
            },
        )

    def test_income_summary_includes_projected_income_and_history(self):
        summary = self.service.get_income_summary(self.account)

        # 200 realized + 150 + 120 premium collected (both entries this month) = 470 projected
        self.assertEqual(summary['projected_income'], Decimal('470'))
        self.assertAlmostEqual(float(summary['coverage_pct']), (470 / 420) * 100, places=2)
        self.assertEqual(summary['realized_income_mtd'], Decimal('200'))
        self.assertEqual(summary['expected_premium_mtd'], Decimal('270'))
        self.assertEqual(len(summary['history']), 3)
        self.assertGreater(summary['income_per_dollar'], 0)

    def test_whales_timeline_returns_recent_entries(self):
        timeline = self.service.get_whales_timeline(self.account)

        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[0]['symbol'], 'MSFT')
        self.assertIn('flow_score', timeline[0])
        self.assertIn('timing_signal', timeline[0])

    def test_income_summary_handles_zero_capital(self):
        User = get_user_model()
        another_user = User.objects.create_user(
            username='nocap',
            email='nocap@example.com',
            password='test-pass-123',
        )
        zero_account = ManagedTradingAccount.objects.create(
            client=another_user,
            account_number='CODA-OPT-777',
            account_name='Zero Capital',
            initial_capital=Decimal('0'),
            current_balance=Decimal('0'),
            cash_available=Decimal('0'),
            cash_reserved=Decimal('0'),
            high_water_mark=Decimal('0'),
            fee_tier='professional',
            management_fee_percentage=Decimal('1.50'),
            performance_fee_percentage=Decimal('20.00'),
            performance_threshold=Decimal('8.00'),
            status='active',
            trading_enabled=True,
        )

        summary = self.service.get_income_summary(zero_account)
        self.assertEqual(summary['projected_income'], Decimal('0'))
        self.assertEqual(summary['coverage_pct'], Decimal('0'))
        self.assertEqual(summary['income_per_dollar'], Decimal('0'))

