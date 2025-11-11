from django.test import TestCase
from finance.models import OverBoughtSold
from django.utils import timezone


class OverBoughtSoldIntegrationTest(TestCase):
    def setUp(self):
        """
        Set up initial conditions for integration tests.
        Creates a stock entry.
        """
        self.stock_data = {
            "description": "Apple Inc.",
            "last": 145.30,
            "volume": 50000,
            "RSI": 75.0,
            "EPS": 5.50,
            "PE": 28.0,
            "rank": "Top Performer",
            "profit_margins": 22.5,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        self.stock = OverBoughtSold.objects.create(symbol="AAPL", **self.stock_data)

    def test_bulk_create_integration(self):
        """
        Test the bulk creation of stock entries and verify if they are saved correctly.
        """
        # Create multiple stock entries using bulk_create, but pass `symbol` separately
        stock_entries = [
            OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}")
            for i in range(1, 1001)
        ]

        # Perform bulk create
        OverBoughtSold.objects.bulk_create(stock_entries)

        # Verify the bulk creation
        self.assertEqual(
            OverBoughtSold.objects.count(), 1001
        )  # Including the original stock
        self.assertTrue(OverBoughtSold.objects.filter(symbol="AAPL_1").exists())

    def test_bulk_update_integration(self):
        """
        Test if bulk update works correctly for stock entries.
        """
        # Create multiple stock entries for update
        stock_entries = [
            OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}")
            for i in range(1, 1001)
        ]
        OverBoughtSold.objects.bulk_create(stock_entries)

        # Perform bulk update (e.g., set RSI to 50 for all stocks)
        OverBoughtSold.objects.update(RSI=50.0)

        # Verify the bulk update
        self.assertTrue(OverBoughtSold.objects.filter(RSI=50.0).exists())
