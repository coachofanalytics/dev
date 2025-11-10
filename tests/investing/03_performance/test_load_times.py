"""
Performance tests for investing page load times

Tests response times and performance benchmarks.

Author: CODA Development Team
Created: November 5, 2025
Category: Performance Tests
"""

import time
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.choices import UserCategory
from investing.models import ManagedTradingAccount, OptionsPosition

User = get_user_model()


def _seed_managed_accounts(owner, manager, account_count=3, positions_per_account=4):
    """
    Helper to generate managed accounts with open positions for performance tests.
    """
    accounts = []
    for index in range(account_count):
        account = ManagedTradingAccount.objects.create(
            client=owner,
            account_number=f"ACC-LOAD-{index}",
            account_name=f"Load Account {index}",
            account_manager=manager,
            initial_capital=Decimal("20000.00"),
            current_balance=Decimal("21500.00"),
            cash_available=Decimal("9000.00"),
            cash_reserved=Decimal("1800.00"),
            high_water_mark=Decimal("22000.00"),
            total_profit_loss=Decimal("1300.00"),
            total_trades=12,
            winning_trades=7,
            losing_trades=5,
        )
        accounts.append(account)

        for position_index in range(positions_per_account):
            OptionsPosition.objects.create(
                managed_account=account,
                symbol=f"MSFT{position_index}",
                strategy="covered_call",
                positions=[{"contract": "MSFT", "type": "call"}],
                capital_required=Decimal("4500.00"),
                premium_collected=Decimal("275.00"),
                max_profit=Decimal("600.00"),
                max_loss=Decimal("4200.00"),
                expiration_date=date.today() + timedelta(days=21),
                status="open",
            )
    return accounts


class ClientPortalLoadTimeTest(TestCase):
    """Ensure the client portal responds within targeted SLAs."""

    @classmethod
    def setUpTestData(cls):
        cls.investor = User.objects.create_user(
            username="investor_load",
            email="investor_load@test.com",
            password="password123",
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name="Load",
            last_name="Investor",
        )
        cls.manager = User.objects.create_user(
            username="manager_load",
            email="manager_load@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
            first_name="Load",
            last_name="Manager",
        )
        _seed_managed_accounts(cls.investor, cls.manager, account_count=4, positions_per_account=5)

    def test_client_portal_renders_under_half_second(self):
        """Client portal page should render quicker than 500ms."""
        self.client.login(username="investor_load", password="password123")

        url = reverse("investing:client_portal")
        start = time.perf_counter()
        response = self.client.get(url)
        duration = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            duration,
            0.50,
            msg="Client portal render time exceeded 500ms budget in test environment.",
        )
