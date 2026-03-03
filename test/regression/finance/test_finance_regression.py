import unittest
from django.test import TestCase


@unittest.skip("regression scaffold: implement concrete regression tests for finance")
class FinanceRegressionTests(TestCase):
    def test_placeholder_finance_regression(self):
        self.assertTrue(True)
