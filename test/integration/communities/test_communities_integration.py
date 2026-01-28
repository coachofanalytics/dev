import unittest
from django.test import TestCase, Client


@unittest.skip("integration scaffold: implement end-to-end tests for communities")
class CommunitiesIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_communities_integration(self):
        self.assertTrue(True)
