"""
Unit tests for investing services

Tests business logic, calculations, and service methods in isolation.

Author: CODA Development Team
Created: November 5, 2025
Category: Unit Tests
"""

from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from investing.models import ManagedTradingAccount, OptionsPosition
from investing.services.managed_trading_service import ManagedTradingService

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
