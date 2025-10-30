from django.test import TestCase
from finance.models import OverBoughtSold  # adjust app name if different

class OverBoughtSoldModelTest(TestCase):
    def setUp(self):
        # Create sample records
        self.overbought = OverBoughtSold.objects.create(symbol="AAPL", rsi="75")
        self.oversold = OverBoughtSold.objects.create(symbol="TSLA", rsi="25")
        self.neutral = OverBoughtSold.objects.create(symbol="GOOG", rsi="50")
        self.invalid = OverBoughtSold.objects.create(symbol="MSFT", rsi="invalid")

    def test_calculate_condition_integer(self):
        self.assertEqual(self.overbought.condition_integer, 1)
        self.assertEqual(self.oversold.condition_integer, -1)
        self.assertEqual(self.neutral.condition_integer, 0)
        self.assertIsNone(self.invalid.condition_integer)

    def test_condition_label(self):
        self.assertEqual(self.overbought.condition_label(), "Overbought")
        self.assertEqual(self.oversold.condition_label(), "Oversold")
        self.assertEqual(self.neutral.condition_label(), "Neutral")
        self.assertEqual(self.invalid.condition_label(), "Unknown")

    def test_str_representation(self):
        self.assertEqual(str(self.overbought), "AAPL - Overbought")
        self.assertEqual(str(self.oversold), "TSLA - Oversold")
        self.assertEqual(str(self.neutral), "GOOG - Neutral")
        self.assertEqual(str(self.invalid), "MSFT - Unknown")
