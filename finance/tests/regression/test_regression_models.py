from django.test import TestCase
from finance.models import OverBoughtSold
from django.utils import timezone


class OverBoughtSoldRegressionTest(TestCase):
    def setUp(self):
        """
        This method sets up initial conditions for the regression tests.
        Creates an instance of the OverBoughtSold model.
        """
        self.stock = OverBoughtSold.objects.create(
            symbol="AAPL",
            description="Apple Inc.",
            last=145.30,
            volume=50000,
            RSI=75.0,
            EPS=5.50,
            PE=28.0,
            rank="Top Performer",
            profit_margins=22.5,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

    def test_symbol_not_empty(self):
        """
        Test if the symbol is not empty when the stock is created.
        """
        self.assertIsNotNone(self.stock.symbol)
        self.assertEqual(self.stock.symbol, "AAPL")

    def test_update_stock_rsi(self):
        """
        Test if updating the RSI value correctly updates the stock entry.
        """
        self.stock.RSI = 60.0
        self.stock.save()
        updated_stock = OverBoughtSold.objects.get(id=self.stock.id)
        self.assertEqual(updated_stock.RSI, 60.0)

    def test_overbought_status(self):
        """
        Test if the status is 'Overbought' when RSI > 70.
        """
        self.stock.RSI = 75.0
        self.stock.save()
        updated_stock = OverBoughtSold.objects.get(id=self.stock.id)
        self.assertEqual(updated_stock.status, "Overbought")

    def test_oversold_status(self):
        """
        Test if the status is 'Oversold' when RSI < 30.
        """
        self.stock.RSI = 25.0
        self.stock.save()
        updated_stock = OverBoughtSold.objects.get(id=self.stock.id)
        self.assertEqual(updated_stock.status, "Oversold")

    def test_neutral_status(self):
        """
        Test if the status is 'Neutral' when RSI is between 30 and 70.
        """
        self.stock.RSI = 50.0
        self.stock.save()
        updated_stock = OverBoughtSold.objects.get(id=self.stock.id)
        self.assertEqual(updated_stock.status, "Neutral")
