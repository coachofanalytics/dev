import unittest
from django.test import TestCase, Client


@unittest.skip("integration scaffold: implement end-to-end tests for accounts")
class AccountsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_accounts_integration(self):
        self.assertTrue(True)
