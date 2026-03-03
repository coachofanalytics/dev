import unittest
from django.test import TestCase


@unittest.skip("regression scaffold: implement concrete regression tests for memberjoin")
class MemberJoinRegressionTests(TestCase):
    def test_placeholder_memberjoin_regression(self):
        self.assertTrue(True)
