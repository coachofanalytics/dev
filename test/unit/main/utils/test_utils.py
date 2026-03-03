from django.test import TestCase
import main.utils as utils


class MainUtilsTests(TestCase):
    def test_countdown_in_month_returns_tuple(self):
        result = utils.countdown_in_month()
        self.assertIsInstance(result, tuple)
        # expects five elements per implementation
        self.assertEqual(len(result), 5)
