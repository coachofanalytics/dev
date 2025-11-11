# finance/tests/integration/test_integration_urls.py
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import OverBoughtSold_list

class OverBoughtSoldURLIntegrationTests(SimpleTestCase):
    def test_reverse_namespaced_url(self):
        url = reverse("finance:overboughtsold_list")
        self.assertEqual(url, "/finance/overboughtsold/")

    def test_resolves_to_correct_view(self):
        url = reverse("finance:overboughtsold_list")
        match = resolve(url)
        self.assertIs(match.func, OverBoughtSold_list)
