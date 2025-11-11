from django.test import TestCase
from finance.models import OverBoughtSold  # Update if model is in a different app

class OverBoughtSoldIntegrationTest(TestCase):

    def setUp(self):
        self.stock1 = OverBoughtSold.objects.create(symbol="AAPL", RSI=75, EPS=5.25, PE=28.5, profit_margins=12.5)
        self.stock2 = OverBoughtSold.objects.create(symbol="TSLA", RSI=25, EPS=3.10, PE=90.2, profit_margins=5.80)
        self.stock3 = OverBoughtSold.objects.create(symbol="MSFT", RSI=50)

    def test_model_saved_and_retrieved(self):
        """Test that objects are saved and can be retrieved"""
        stocks = OverBoughtSold.objects.all()
        self.assertEqual(stocks.count(), 3)
        # Because of ordering = ["-created_at"], MSFT is first, then TSLA, then AAPL
        self.assertEqual(stocks[0].symbol, "MSFT")
        self.assertEqual(stocks[1].symbol, "TSLA")
        self.assertEqual(stocks[2].symbol, "AAPL")

    def test_status_logic_saved_correctly(self):
        """Test that status property returns correct classification"""
        self.assertEqual(self.stock1.status, "Overbought")   # RSI 75
        self.assertEqual(self.stock2.status, "Oversold")     # RSI 25
        self.assertEqual(self.stock3.status, "Neutral")      # RSI 50

    def test_update_model(self):
        """Test updating a record and verifying changes"""
        self.stock1.RSI = 20
        self.stock1.save()
        updated_stock = OverBoughtSold.objects.get(symbol="AAPL")
        self.assertEqual(updated_stock.status, "Oversold")

    def test_delete_model(self):
        """Test delete functionality in ORM"""
        self.stock3.delete()
        self.assertEqual(OverBoughtSold.objects.count(), 2)
