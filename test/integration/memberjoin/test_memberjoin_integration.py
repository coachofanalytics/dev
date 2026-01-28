import unittest
from django.test import TestCase, Client


@unittest.skip("integration scaffold: implement end-to-end tests for memberjoin")
class MemberJoinIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_memberjoin_integration(self):
        self.assertTrue(True)
