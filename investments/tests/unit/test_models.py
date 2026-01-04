from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from investments.models import InvestmentStrategy

class InvestmentStrategyModelTest(TestCase):

    def setUp(self):
        """
        Create a sample InvestmentStrategy instance for testing.
        """
        self.strategy = InvestmentStrategy.objects.create(
            symbol="AAPL",
            action="IRON CONDOR",
            expiry=date.today() + timedelta(days=30),
            day_to_expiry=30,
            earnings_date=date.today() + timedelta(days=15),
            earning_flag=False,
            on_date=date.today(),
            strike_price=Decimal("150.00"),
            mid_price=Decimal("2.50"),
            ask_price=Decimal("2.60"),
            iv_rank=Decimal("35.50"),
            stock_price=Decimal("155.00"),
            raw_return=Decimal("0.0500"),
            annualized_return=Decimal("0.6000"),
            opening=Decimal("2.45"),
            comment="Testing high IV rank strategy."
        )

    def test_strategy_creation(self):
        """Tests if the model instance is created correctly."""
        self.assertTrue(isinstance(self.strategy, InvestmentStrategy))
        self.assertEqual(self.strategy.symbol, "AAPL")
        self.assertEqual(self.strategy.action, "IRON CONDOR")

    def test_string_representation(self):
        """Tests the __str__ method."""
        expected_str = f"AAPL - IRON CONDOR ({self.strategy.on_date})"
        self.assertEqual(str(self.strategy), expected_str)

    def test_default_values(self):
        """Tests if default booleans and timestamps are working."""
        self.assertTrue(self.strategy.is_active)
        self.assertFalse(self.strategy.is_featured)
        self.assertIsNotNone(self.strategy.created_at)

    def test_decimal_precision(self):
        """Tests if DecimalFields retain the correct precision."""
        self.assertEqual(self.strategy.iv_rank, Decimal("35.50"))
        self.assertEqual(self.strategy.raw_return, Decimal("0.0500"))

    def test_null_closing_fields(self):
        """Tests that closing fields can be null initially."""
        self.assertIsNone(self.strategy.closing_date)
        self.assertIsNone(self.strategy.closing)

    def test_update_closing_data(self):
        """Tests updating the closing fields later."""
        today = date.today()
        self.strategy.closing_date = today
        self.strategy.closing = Decimal("3.10")
        self.strategy.save()
        
        updated_strategy = InvestmentStrategy.objects.get(id=self.strategy.id)
        self.assertEqual(updated_strategy.closing, Decimal("3.10"))
        self.assertEqual(updated_strategy.closing_date, today)










from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from investments.models import Daily_Trades



class DailyTradesModelTest(TestCase):

    def test_create_equity_trade_success(self):
        """
        Equity trade: no strike price, no expiry
        """
        trade = Daily_Trades(
            symbol="AAPL",
            transaction="TXN-AAPL-001",
            price=Decimal("185.2500"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=10,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("1852.5000"),
            page_number="P01",
            description="Bought Apple shares"
        )

        # Should not raise
        trade.full_clean()
        trade.save()

        self.assertEqual(Daily_Trades.objects.count(), 1)

    def test_create_option_trade_requires_expiry(self):
        """
        Option trade must have expiry if strike_price > 0
        """
        trade = Daily_Trades(
            symbol="TSLA",
            transaction="TXN-TSLA-002",
            price=Decimal("6.4000"),
            strike_price=Decimal("250.0000"),
            action="STO",
            qty=1,
            date=date.today(),
            account_type="MARGIN",
            credit=Decimal("640.0000"),
            debit=Decimal("0.0000")
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()

    def test_create_option_trade_with_expiry_success(self):
        """
        Valid option trade with strike and expiry
        """
        trade = Daily_Trades(
            symbol="TSLA",
            transaction="TXN-TSLA-003",
            price=Decimal("6.4000"),
            strike_price=Decimal("250.0000"),
            action="STO",
            qty=1,
            date=date.today(),
            expiry=date(2025, 2, 21),
            account_type="MARGIN",
            credit=Decimal("640.0000"),
            debit=Decimal("0.0000")
        )

        trade.full_clean()
        trade.save()

        self.assertEqual(Daily_Trades.objects.count(), 1)

    def test_negative_price_not_allowed(self):
        """
        Price must not be negative
        """
        trade = Daily_Trades(
            symbol="AAPL",
            transaction="TXN-AAPL-NEG",
            price=Decimal("-1.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=10,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("10.0000")
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()

    def test_negative_credit_not_allowed(self):
        """
        Credit must not be negative
        """
        trade = Daily_Trades(
            symbol="MSFT",
            transaction="TXN-MSFT-NEG",
            price=Decimal("400.0000"),
            strike_price=Decimal("0.0000"),
            action="STC",
            qty=5,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("-100.0000"),
            debit=Decimal("0.0000")
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()

    def test_negative_debit_not_allowed(self):
        """
        Debit must not be negative
        """
        trade = Daily_Trades(
            symbol="AMZN",
            transaction="TXN-AMZN-NEG",
            price=Decimal("150.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=5,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("-500.0000")
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()

    def test_qty_must_be_positive(self):
        """
        Quantity must be greater than zero
        """
        trade = Daily_Trades(
            symbol="GOOG",
            transaction="TXN-GOOG-ZERO",
            price=Decimal("130.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=0,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("1300.0000")
        )

        with self.assertRaises(ValidationError):
            trade.full_clean()

    def test_string_representation(self):
        """
        __str__ output sanity check
        """
        trade = Daily_Trades(
            symbol="NFLX",
            transaction="TXN-NFLX-001",
            price=Decimal("500.0000"),
            strike_price=Decimal("0.0000"),
            action="STC",
            qty=2,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("1000.0000"),
            debit=Decimal("0.0000")
        )

        self.assertIn("NFLX", str(trade))
