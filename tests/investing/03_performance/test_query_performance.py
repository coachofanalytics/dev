"""
Performance tests for investing database queries

Tests for N+1 queries, query counts, and database performance.

Author: CODA Development Team
Created: November 5, 2025
Category: Performance Tests
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.choices import UserCategory
from investing.models import ManagedTradingAccount, OptionsPosition

User = get_user_model()


class ClientPortalQueryPerformanceTest(TestCase):
    """
    Ensure the client portal avoids N+1 queries and keeps query counts stable.

    Scenario:
        - Investor with 3 managed accounts
        - Each account has 4 open positions
        - We assert the portal renders with <= 12 queries
          (baseline + deterministic relation fetches)
    """

    @classmethod
    def setUpTestData(cls):
        cls.investor = User.objects.create_user(
            username="investor_perf",
            email="investor_perf@test.com",
            password="password123",
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name="Perf",
            last_name="Investor",
        )
        cls.manager = User.objects.create_user(
            username="manager_perf",
            email="manager_perf@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
            first_name="Perf",
            last_name="Manager",
        )

        for index in range(3):
            account = ManagedTradingAccount.objects.create(
                client=cls.investor,
                account_number=f"ACC-PERF-{index}",
                account_name=f"Performance Account {index}",
                account_manager=cls.manager,
                initial_capital=Decimal("25000.00"),
                current_balance=Decimal("27500.00"),
                cash_available=Decimal("12000.00"),
                cash_reserved=Decimal("2500.00"),
                high_water_mark=Decimal("28000.00"),
                total_profit_loss=Decimal("1500.00"),
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
            )

            for position_index in range(4):
                OptionsPosition.objects.create(
                    managed_account=account,
                    symbol=f"AAPL{position_index}",
                    strategy="short_put",
                    positions=[{"contract": "AAPL", "type": "put"}],
                    capital_required=Decimal("5000.00"),
                    premium_collected=Decimal("350.00"),
                    max_profit=Decimal("700.00"),
                    max_loss=Decimal("4500.00"),
                    expiration_date=date.today() + timedelta(days=30),
                    status="open",
                )

    def test_client_portal_query_count_is_stable(self):
        """Client portal should render with a small, stable query budget."""
        self.client.login(username="investor_perf", password="password123")

        url = reverse("investing:client_portal")
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(context.captured_queries),
            12,
            msg=(
                "Client portal triggered too many database queries. "
                "Investigate select_related/prefetch usage or aggregation logic."
            ),
        )
