from django.test import TestCase
from accounts.models import OverBoughtSold

class OverBoughtSoldRegressionTest(TestCase):

    def setUp(self):
        # Create valid instance
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

        # Create an instance with invalid RSI (using None to simulate invalid RSI)
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

    def test_condition_integer_oversold(self):
        # Test that condition_integer correctly returns 1 when RSI >= 30
        self.assertEqual(self.stock.condition_integer, 1)  # RSI is 35, should return 1 for oversold

    def test_condition_integer_undervalued(self):
        # Test that condition_integer correctly returns 0 when RSI < 30
        self.stock.RSI = 25  # Set RSI to 25
        self.stock.save()
        self.assertEqual(self.stock.condition_integer, 0)  # RSI is 25, should return 0 for undervalued

    def test_condition_integer_invalid_rsi(self):
        # Test that condition_integer returns 1 when RSI is invalid (None or non-numeric)
        self.assertEqual(self.stock_invalid_rsi.condition_integer, 1)  # Invalid RSI should return 1 as per the method

    def test_str_method(self):
        # Test that the __str__ method returns the symbol
        self.assertEqual(str(self.stock), "AAPL")  # The symbol should be returned, "AAPL"

    def test_str_method_no_symbol(self):
        # Test that the __str__ method returns "No Symbol" when symbol is empty or None
        self.stock_invalid_rsi.symbol = ""  # Make symbol empty
        self.stock_invalid_rsi.save()
        self.assertEqual(str(self.stock_invalid_rsi), "No Symbol")  # Should return "No Symbol" if symbol is empty

    def test_condition_integer_edge_case(self):
        # Test the case where RSI is exactly 30
        self.stock.RSI = 30
        self.stock.save()
        self.assertEqual(self.stock.condition_integer, 0)  # RSI = 30 should return 0 for undervalued

    def test_condition_integer_boundary(self):
        # Test the case where RSI is slightly above 30
        self.stock.RSI = 30.1
        self.stock.save()
        self.assertEqual(self.stock.condition_integer, 1)  # RSI > 30 should return 1 for oversold

