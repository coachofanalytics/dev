import unittest
import time
from django.test import TestCase, Client


@unittest.skip("performance scaffold: implement benchmarks for communities")
class CommunitiesPerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_communities_performance(self):
        start = time.time()
        end = time.time()
        self.assertLessEqual(end - start, 5.0)
