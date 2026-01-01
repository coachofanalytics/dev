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