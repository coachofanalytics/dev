"""
Unit tests for investing services

Tests business logic, calculations, and service methods in isolation.

Author: CODA Development Team
Created: November 5, 2025
Category: Unit Tests
"""

from datetime import timedelta
from unittest.mock import patch
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from investing.models import ManagedTradingAccount, OptionsPosition, BrokerConnection, OptionsPositionHistory
from investing.services.managed_trading_service import ManagedTradingService
from investing.services.broker_api_service import BrokerAPIService
from investing.services.predictive_analytics_service import PredictiveAnalyticsService

User = get_user_model()


class ManagedTradingServiceIncomeSummaryTests(TestCase):
    """Validate managed client income and dashboard helpers."""

    def setUp(self):
        self.service = ManagedTradingService()
        self.client_user = User.objects.create_user(
            username="managed_client",
            email="managed_client@test.com",
            password="securepass123",
            is_active=True,
        )
        self.account: ManagedTradingAccount = self.service.create_managed_account(
            client_user=self.client_user,
            account_data={
                "account_name": "Phase 3 Account",
                "initial_capital": Decimal("20000.00"),
                "fee_tier": "professional",
            },
        )
        self.now = timezone.now()
        self._seed_income_history()

    def _create_position(self, **overrides):
        """Helper to create options positions with sensible defaults."""
        default_data = {
            "managed_account": self.account,
            "symbol": overrides.get("symbol", "AAPL"),
            "strategy": overrides.get("strategy", "short_put"),
            "positions": overrides.get(
                "positions",
                [
                    {
                        "type": "put",
                        "strike": 175,
                        "contracts": 1,
                        "premium": 2.5,
                    }
                ],
            ),
            "capital_required": overrides.get("capital_required", Decimal("2000.00")),
            "premium_collected": overrides.get("premium_collected", Decimal("150.00")),
            "max_profit": overrides.get("max_profit", Decimal("150.00")),
            "max_loss": overrides.get("max_loss", Decimal("2000.00")),
            "expiration_date": overrides.get(
                "expiration_date",
                self.now.date() + timedelta(days=30),
            ),
            "status": overrides.get("status", "open"),
            "api_response_data": overrides.get(
                "api_response_data",
                {},
            ),
        }
        position = OptionsPosition.objects.create(**default_data)

        # Update auto-managed dates/pnl values if provided
        update_fields = {}
        if "entry_date" in overrides:
            update_fields["entry_date"] = overrides["entry_date"]
        if "exit_date" in overrides:
            update_fields["exit_date"] = overrides["exit_date"]
        if "realized_pnl" in overrides:
            update_fields["realized_pnl"] = overrides["realized_pnl"]
        if "unrealized_pnl" in overrides:
            update_fields["unrealized_pnl"] = overrides["unrealized_pnl"]
        if update_fields:
            OptionsPosition.objects.filter(pk=position.pk).update(**update_fields)
            position.refresh_from_db()
        return position

    def _seed_income_history(self):
        """Create trailing income data for 3-month history."""
        # Two months ago
        two_months_ago = (self.now - relativedelta(months=2)).date()
        self._create_position(
            status="closed",
            entry_date=two_months_ago + timedelta(days=2),
            exit_date=two_months_ago + timedelta(days=20),
            premium_collected=Decimal("120.00"),
            realized_pnl=Decimal("80.00"),
            symbol="MSFT",
        )

        # Previous month
        last_month = (self.now - relativedelta(months=1)).date()
        self._create_position(
            status="closed",
            entry_date=last_month + timedelta(days=4),
            exit_date=last_month + timedelta(days=18),
            premium_collected=Decimal("150.00"),
            realized_pnl=Decimal("95.00"),
            symbol="SPY",
        )

        # Current month (closed position contributing realized income)
        month_start = self.now.date().replace(day=1)
        self._create_position(
            status="closed",
            entry_date=(month_start - timedelta(days=10)),
            exit_date=self.now.date() - timedelta(days=2),
            premium_collected=Decimal("0.00"),
            realized_pnl=Decimal("180.00"),
            symbol="QQQ",
        )

        # Current month (open position with premium + UW data)
        self._create_position(
            status="open",
            entry_date=self.now.date() - timedelta(days=3),
            premium_collected=Decimal("210.00"),
            api_response_data={
                "unusual_whales": {
                    "flow_score": 88,
                    "sentiment": "bullish",
                    "timing_signal": "Sweep > $1M",
                    "entry_window": "0-2 days",
                }
            },
            symbol="NVDA",
            unrealized_pnl=Decimal("65.00"),
        )

    def test_income_summary_includes_target_gap_and_clamped_coverage(self):
        summary = self.service.get_income_summary(self.account, months=3)

        self.assertEqual(summary["target"], self.service.MANAGED_INCOME_TARGET)
        self.assertEqual(summary["realized_income_mtd"], Decimal("180.00"))
        self.assertEqual(summary["expected_premium_mtd"], Decimal("210.00"))
        self.assertEqual(summary["projected_income"], Decimal("390.00"))
        self.assertEqual(summary["target_gap"], Decimal("30.00"))
        self.assertEqual(summary["baseline_income"], Decimal("390.00"))
        self.assertGreater(summary["coverage_pct"], Decimal("0"))
        self.assertLessEqual(summary["coverage_pct_clamped"], Decimal("100"))
        self.assertEqual(len(summary["history"]), 3)
        self.assertEqual(summary["history"][-1]["net_income"], Decimal("390.00"))

        income_per_dollar = summary["income_per_dollar"]
        self.assertAlmostEqual(float(income_per_dollar), 0.0195, places=4)

    def test_whales_timeline_surfaces_recent_flow_metadata(self):
        timeline = self.service.get_whales_timeline(self.account, limit=5)
        self.assertGreaterEqual(len(timeline), 1)
        latest = timeline[0]

        self.assertEqual(latest["symbol"], "NVDA")
        self.assertEqual(latest["flow_score"], 88)
        self.assertEqual(latest["timing_signal"], "Sweep > $1M")
        self.assertEqual(latest["entry_window"], "0-2 days")


class BrokerAPIServiceTests(TestCase):
    """Validate broker sync logic and credential handling."""

    def setUp(self):
        self.service = ManagedTradingService()
        self.sync_service = BrokerAPIService()
        self.user = User.objects.create_user(
            username="broker_client",
            email="broker_client@test.com",
            password="securepass123",
            is_active=True,
        )
        self.account = self.service.create_managed_account(
            client_user=self.user,
            account_data={
                "account_name": "Broker Synced Account",
                "initial_capital": Decimal("15000.00"),
                "fee_tier": "professional",
            },
        )
        self.connection = BrokerConnection.objects.create(
            managed_account=self.account,
            broker="tasty",
        )
        self.connection.set_credentials(
            api_key="TASTY-KEY-1234",
            api_secret="SECRET-5678",
        )
        self.connection.save()

    def test_credentials_are_encrypted_and_masked(self):
        """Ensure secrets are stored encrypted with masked helpers."""
        self.assertTrue(self.connection.api_key_encrypted)
        self.assertNotEqual(self.connection.api_key_encrypted, "TASTY-KEY-1234")
        self.assertEqual(self.connection.api_key_last4, "1234")
        self.assertEqual(self.connection.masked_api_key, "••••1234")
        self.assertEqual(self.connection.get_api_key(), "TASTY-KEY-1234")

    def test_sync_positions_creates_and_updates_records(self):
        """Broker sync should upsert positions without duplication."""
        expiration = timezone.now().date() + timedelta(days=30)
        payload = [
            {
                "symbol": "AAPL",
                "strategy": "short_put",
                "expiration_date": expiration,
                "premium_collected": "250.00",
                "capital_required": "2500.00",
                "unrealized_pnl": "75.00",
                "status": "open",
                "legs": [{"type": "short_put", "strike": 175, "contracts": 1}],
            }
        ]

        with patch.object(BrokerAPIService, "_fetch_from_broker", return_value=payload):
            result = self.sync_service.sync_positions(self.account, performed_by=self.user)

        self.assertEqual(result, {"created": 1, "updated": 0, "skipped": 0})
        position = OptionsPosition.objects.get(managed_account=self.account, symbol="AAPL")
        self.assertEqual(position.premium_collected, Decimal("250.00"))
        self.assertEqual(position.unrealized_pnl, Decimal("75.00"))
        self.connection.refresh_from_db()
        self.assertIsNotNone(self.connection.last_sync)

        # Sync again with modified values to ensure update path works
        payload[0]["unrealized_pnl"] = "55.00"
        with patch.object(BrokerAPIService, "_fetch_from_broker", return_value=payload):
            result = self.sync_service.sync_positions(self.account, performed_by=self.user)
        self.assertEqual(result, {"created": 0, "updated": 1, "skipped": 0})
        position.refresh_from_db()
        self.assertEqual(position.unrealized_pnl, Decimal("55.00"))

    def test_sync_raises_without_connection(self):
        """Accounts without broker connections should error."""
        new_account = self.service.create_managed_account(
            client_user=self.user,
            account_data={
                "account_name": "No Broker Account",
                "initial_capital": Decimal("10000.00"),
                "fee_tier": "professional",
            },
        )
        with self.assertRaises(ValidationError):
            self.sync_service.sync_positions(new_account)


class PredictiveAnalyticsServiceTests(TestCase):
    """Validate predictive analytics fallback projections."""

    def setUp(self):
        self.trading_service = ManagedTradingService()
        self.analytics_service = PredictiveAnalyticsService()
        self.user = User.objects.create_user(
            username="analytics_client",
            email="analytics_client@test.com",
            password="securepass123",
            is_active=True,
        )
        self.account = self.trading_service.create_managed_account(
            client_user=self.user,
            account_data={
                "account_name": "Analytics Account",
                "initial_capital": Decimal("18000.00"),
                "fee_tier": "professional",
            },
        )
        self._seed_history()

    def _seed_history(self):
        base_date = timezone.now().date() - timedelta(days=90)
        for offset, profit in enumerate([Decimal("180.00"), Decimal("220.00"), Decimal("150.00"), Decimal("195.00")]):
            position = OptionsPosition.objects.create(
                managed_account=self.account,
                symbol=f"SYM{offset}",
                strategy="short_put",
                positions=[{"type": "short_put", "strike": 100 + offset, "contracts": 1}],
                capital_required=Decimal("2500.00"),
                premium_collected=profit,
                max_profit=profit,
                max_loss=Decimal("2500.00"),
                entry_date=base_date + timedelta(days=offset * 7),
                expiration_date=base_date + timedelta(days=offset * 7 + 30),
                exit_date=base_date + timedelta(days=offset * 7 + 15),
                status="closed",
            )
            OptionsPositionHistory.objects.create(
                position=position,
                was_profitable=True,
                actual_return_amount=profit,
                actual_return_percentage=Decimal("12.0"),
                days_held=15,
                annualized_return=Decimal("25.0"),
                exit_reason="profit_target",
            )

    def test_forecast_returns_history_and_projection(self):
        result = self.analytics_service.forecast_account_balance(self.account, periods=5)
        self.assertIn('history', result)
        self.assertIn('forecast', result)
        self.assertGreaterEqual(len(result['history']), 4)
        self.assertEqual(len(result['forecast']), 5)

    def test_forecast_requires_minimum_history(self):
        OptionsPositionHistory.objects.all().delete()
        with self.assertRaises(ValueError):
            self.analytics_service.forecast_account_balance(self.account)
