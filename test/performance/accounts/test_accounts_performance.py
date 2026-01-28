import unittest
import time
from django.test import TestCase, Client


@unittest.skip("performance scaffold: implement benchmarks for accounts")
class AccountsPerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_accounts_performance(self):
        start = time.time()
        # placeholder for a request benchmark
        end = time.time()
        self.assertLessEqual(end - start, 5.0)
