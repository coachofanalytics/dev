from django.test import TestCase
import finance.utils as futils


class FinanceUtilsTests(TestCase):
    def test_get_budget_periods_structure(self):
        months, years = futils.get_budget_periods()
        self.assertIsInstance(months, list)
        self.assertIsInstance(years, list)
        self.assertEqual(len(months), 3)
        self.assertEqual(len(years), 3)
