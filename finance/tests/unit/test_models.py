from django.test import TestCase
from finance.models import OverBoughtSold

class OverBoughtSoldModelTest(TestCase):

    def setUp(self):
        self.stock = OverBoughtSold.objects.create(
            symbol="AAPL",
            RSI=75,
            EPS=5.25,
            PE=28.5,
            profit_margins=12.5
        )

    def test_str_representation(self):
        self.assertEqual(str(self.stock), "AAPL")

    def test_status_overbought(self):
        self.assertEqual(self.stock.status, "Overbought")

    def test_status_oversold(self):
        stock = OverBoughtSold.objects.create(symbol="TSLA", RSI=25)
        self.assertEqual(stock.status, "Oversold")

    def test_status_neutral(self):
        stock = OverBoughtSold.objects.create(symbol="MSFT", RSI=50)
        self.assertEqual(stock.status, "Neutral")

    def test_status_unknown_when_no_rsi(self):
        stock = OverBoughtSold.objects.create(symbol="GOOG", RSI=None)
        self.assertEqual(stock.status, "Unknown")
