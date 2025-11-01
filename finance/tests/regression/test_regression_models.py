from django.test import TestCase
from finance.models import OverBoughtSold

class OverBoughtSoldRegressionTest(TestCase):

    def test_rsi_status_logic_boundary(self):
        self.assertEqual(OverBoughtSold(RSI=70).status, "Neutral")
        self.assertEqual(OverBoughtSold(RSI=71).status, "Overbought")
        self.assertEqual(OverBoughtSold(RSI=30).status, "Neutral")
        self.assertEqual(OverBoughtSold(RSI=29).status, "Oversold")

    def test_handling_invalid_rsi_does_not_crash(self):
        stock = OverBoughtSold(RSI="invalid")
        self.assertEqual(stock.status, "Unknown")
