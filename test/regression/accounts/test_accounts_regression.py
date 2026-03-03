import unittest
from django.test import TestCase


@unittest.skip("regression scaffold: implement concrete regression tests for accounts")
class AccountsRegressionTests(TestCase):
    def test_placeholder_accounts_regression(self):
        self.assertTrue(True)
