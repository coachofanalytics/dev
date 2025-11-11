# finance/tests/regression/test_regression_urls.py
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from finance.views import OverBoughtSold_list


class OverBoughtSoldURLRegressionTests(SimpleTestCase):
    def test_reverse_namespaced_url(self):
        url = reverse("finance:overboughtsold_list")
        self.assertEqual(url, "/finance/overboughtsold/")  # includes prefix

    def test_url_resolves_to_correct_view(self):
        url = reverse("finance:overboughtsold_list")  # don't hard-code
        match = resolve(url)
        self.assertIs(match.func, OverBoughtSold_list)
