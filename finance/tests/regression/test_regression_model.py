from django.test import TestCase
from finance.models import OverBoughtSold


class OverBoughtSoldRegressionTest(TestCase):
    """
    Regression tests for the OverBoughtSold model to ensure that
    condition calculation, saving logic, and label mapping remain correct
    after future code changes.
    """

    def setUp(self):
        self.stock_overbought = OverBoughtSold.objects.create(symbol="AAPL", rsi="75")
        self.stock_oversold = OverBoughtSold.objects.create(symbol="TSLA", rsi="25")
        self.stock_neutral = OverBoughtSold.objects.create(symbol="GOOG", rsi="50")
        self.stock_invalid = OverBoughtSold.objects.create(symbol="MSFT", rsi="invalid")

    def test_regression_condition_integer_consistency(self):
        """
        Test that the RSI condition logic (Overbought, Oversold, Neutral)
        produces consistent integer results as originally designed.
        """
        self.assertEqual(self.stock_overbought.condition_integer, 1)
        self.assertEqual(self.stock_oversold.condition_integer, -1)
        self.assertEqual(self.stock_neutral.condition_integer, 0)
        self.assertIsNone(self.stock_invalid.condition_integer)

    def test_regression_label_consistency(self):
        """
        Verify that label mapping has not changed unintentionally.
        """
        self.assertEqual(self.stock_overbought.condition_label(), "Overbought")
        self.assertEqual(self.stock_oversold.condition_label(), "Oversold")
        self.assertEqual(self.stock_neutral.condition_label(), "Neutral")
        self.assertEqual(self.stock_invalid.condition_label(), "Unknown")

    def test_regression_save_does_not_break_condition_calculation(self):
        """
        Ensure that saving again does not break the automatic RSI condition logic.
        """
        self.stock_neutral.rsi = "80"
        self.stock_neutral.save()
        self.stock_neutral.refresh_from_db()
        self.assertEqual(self.stock_neutral.condition_label(), "Overbought")

    def test_regression_string_output_stability(self):
        """
        Confirm that __str__() output format remains stable.
        """
        self.assertEqual(str(self.stock_overbought), "AAPL - Overbought")
        self.assertEqual(str(self.stock_oversold), "TSLA - Oversold")
        self.assertEqual(str(self.stock_neutral), "GOOG - Neutral")
        self.assertEqual(str(self.stock_invalid), "MSFT - Unknown")

    def test_regression_missing_fields_handling(self):
        """
        Ensure no crash occurs when optional fields are missing.
        """
        stock = OverBoughtSold.objects.create(symbol=None, rsi="60")
        self.assertEqual(stock.condition_label(), "Neutral")
        self.assertIn("Unknown", str(stock))
