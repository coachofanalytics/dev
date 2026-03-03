import unittest
from django.test import TestCase, Client


@unittest.skip("integration scaffold: implement end-to-end tests for finance")
class FinanceIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_finance_integration(self):
        self.assertTrue(True)
