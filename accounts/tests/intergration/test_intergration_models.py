from django.test import TestCase
from accounts.models import OverBoughtSold

class OverBoughtSoldIntegrationTest(TestCase):

    def setUp(self):
        """
        Set up initial data for the integration tests.
        """
        # Create an instance of the OverBoughtSold model with valid data
        self.stock = OverBoughtSold.objects.create(
            symbol="AAPL",
            RSI=35,  # Valid RSI value (above 30)
            description="Apple Inc.",
            last=150,
            volume=10000,
            EPS="5.2",
            PE=30,
            rank="1",
            profit_margins=20.00  # Using decimal for percentage
        )

        # Create an instance with invalid RSI (None)
        self.stock_invalid_rsi = OverBoughtSold.objects.create(
            symbol="GOOG",
            RSI=None,  # Invalid RSI value (None)
            description="Google Inc.",
            last=2800,
            volume=5000,
            EPS="30.5",
            PE=25,
            rank="2",
            profit_margins=25.00  # Using decimal for percentage
        )

    def test_overboughtsold_data_integrity(self):
        """
        Test that data is correctly saved and retrieved from the database.
        """
        # Fetch the instance from the database
        stock_from_db = OverBoughtSold.objects.get(symbol="AAPL")

        # Assert that the retrieved data is correct
        self.assertEqual(stock_from_db.symbol, "AAPL")
        self.assertEqual(stock_from_db.RSI, 35)
        self.assertEqual(stock_from_db.description, "Apple Inc.")
        self.assertEqual(stock_from_db.last, 150)
        self.assertEqual(stock_from_db.volume, 10000)
        self.assertEqual(stock_from_db.EPS, 5.2)
        self.assertEqual(stock_from_db.PE, 30)
        self.assertEqual(stock_from_db.rank, "1")
        self.assertEqual(stock_from_db.profit_margins, 20.00)

    def test_condition_integer_property(self):
        """
        Test the condition_integer property when saving and retrieving an instance.
        """
        # Fetch the instance from the database
        stock_from_db = OverBoughtSold.objects.get(symbol="AAPL")

        # Test the condition_integer property
        self.assertEqual(stock_from_db.condition_integer, 1)  # Should return 1 because RSI is 35

        # Test with RSI set to 25
        stock_from_db.RSI = 25
        stock_from_db.save()
        self.assertEqual(stock_from_db.condition_integer, 0)  # Should return 0 because RSI is 25

    def test_str_method(self):
        """
        Test the __str__ method when fetching the model from the database.
        """
        # Fetch the instance from the database
        stock_from_db = OverBoughtSold.objects.get(symbol="AAPL")

        # Test the __str__ method
        self.assertEqual(str(stock_from_db), "AAPL")  # Should return the symbol "AAPL"

    def test_str_method_no_symbol(self):
        """
        Test the __str__ method when symbol is empty.
        """
        stock_from_db = OverBoughtSold.objects.create(
            symbol="",  # Empty symbol
            RSI=35,
            description="Apple Inc.",
            last=150,
            volume=10000,
            EPS="5.2",
            PE=30,
            rank="1",
            profit_margins=20.00
        )

        # Test that the __str__ method returns "No Symbol"
        self.assertEqual(str(stock_from_db), "No Symbol")

    def test_invalid_rsi_handling(self):
        """
        Test how the model handles invalid RSI values (non-numeric or None).
        """
        # Create a stock with an invalid RSI value (None)
        stock_invalid_rsi = OverBoughtSold.objects.create(
            symbol="GOOG",
            RSI=None,  # Invalid RSI value (None)
            description="Google Inc.",
            last=2800,
            volume=5000,
            EPS="30.5",
            PE=25,
            rank="2",
            profit_margins=25.00
        )

        # Test that condition_integer returns 1 for invalid RSI (None)
        self.assertEqual(stock_invalid_rsi.condition_integer, 1)

        # Create a stock with an invalid RSI value (string)
        stock_invalid_rsi = OverBoughtSold.objects.create(
            symbol="TSLA",
            RSI="Invalid",  # Invalid RSI value (string)
            description="Tesla Inc.",
            last=750,
            volume=3000,
            EPS="10.5",
            PE="40",
            rank="3",
            profit_margins=15.00
        )

        # Test that condition_integer returns 1 for invalid RSI (string)
        self.assertEqual(stock_invalid_rsi.condition_integer, 1)
