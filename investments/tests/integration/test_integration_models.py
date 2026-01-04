from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from investments.models import InvestmentStrategy

class ModelIntegrationTests(TestCase):

    def test_model_persistence_and_retrieval(self):
        """
        Integration: Test the full cycle of creating, saving, 
        and retrieving a record from the PostgreSQL database.
        """
        # 1. Create the record
        new_strat = InvestmentStrategy.objects.create(
            symbol="MSFT",
            action="CALL",
            expiry=date.today() + timedelta(days=10),
            day_to_expiry=10,
            earnings_date=date.today() + timedelta(days=5),
            earning_flag=True,
            on_date=date.today(),
            strike_price=Decimal("400.00"),
            mid_price=Decimal("10.00"),
            ask_price=Decimal("10.50"),
            iv_rank=Decimal("25.00"),
            stock_price=Decimal("405.00"),
            raw_return=Decimal("0.0250"),
            annualized_return=Decimal("0.9000"),
            opening=Decimal("9.80"),
            comment="Integration test for persistence."
        )

        # 2. Retrieve it using a different query parameter
        retrieved = InvestmentStrategy.objects.get(symbol="MSFT")

        # 3. Assertions to ensure data integrity across the DB bridge
        self.assertEqual(retrieved.id, new_strat.id)
        self.assertEqual(retrieved.action, "CALL")
        # Ensure Decimals aren't converted to floats/strings incorrectly
        self.assertIsInstance(retrieved.strike_price, Decimal)

    def test_active_strategy_filtering(self):
        """
        Integration: Test how the model works with querysets 
        to ensure 'is_active' logic integrates with filters.
        """
        # Create one active and one inactive strategy
        InvestmentStrategy.objects.create(
            symbol="AAPL", action="BUY", expiry=date.today(), day_to_expiry=1,
            earnings_date=date.today(), on_date=date.today(), strike_price=100,
            mid_price=1, ask_price=1.1, iv_rank=20, stock_price=101,
            raw_return=0.1, annualized_return=1.2, opening=0.9, is_active=True
        )
        InvestmentStrategy.objects.create(
            symbol="GOOG", action="SELL", expiry=date.today(), day_to_expiry=1,
            earnings_date=date.today(), on_date=date.today(), strike_price=200,
            mid_price=2, ask_price=2.1, iv_rank=22, stock_price=202,
            raw_return=0.1, annualized_return=1.2, opening=1.8, is_active=False
        )

        active_count = InvestmentStrategy.objects.filter(is_active=True).count()
        self.assertEqual(active_count, 1)








from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from investments.models import Daily_Trades


class DailyTradesIntegrationTest(TestCase):

    def test_full_lifecycle_create_read_update_delete(self):
        trade = Daily_Trades(
            symbol="NVDA",
            transaction="INT-NVDA-001",
            price=Decimal("600.0000"),
            strike_price=Decimal("600.0000"),
            action="STO",
            qty=1,
            date=date.today(),
            expiry=date(2025, 3, 15),
            account_type="MARGIN",
            credit=Decimal("300.0000"),
            debit=Decimal("0.0000"),
        )

        # CREATE
        trade.full_clean()
        trade.save()
        self.assertEqual(Daily_Trades.objects.count(), 1)

        # READ
        db_trade = Daily_Trades.objects.get(transaction="INT-NVDA-001")
        self.assertEqual(db_trade.symbol, "NVDA")

        # UPDATE
        db_trade.credit = Decimal("350.0000")
        db_trade.full_clean()
        db_trade.save()

        self.assertEqual(
            Daily_Trades.objects.get(transaction="INT-NVDA-001").credit,
            Decimal("350.0000")
        )

        # DELETE
        db_trade.delete()
        self.assertEqual(Daily_Trades.objects.count(), 0)

    def test_option_without_expiry_fails(self):
        trade = Daily_Trades(
            symbol="AMD",
            transaction="INT-AMD-FAIL",
            price=Decimal("1.2000"),
            strike_price=Decimal("150.0000"),
            action="STO",
            qty=1,
            date=date.today(),
            account_type="MARGIN",
            credit=Decimal("120.0000"),
            debit=Decimal("0.0000"),
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()
