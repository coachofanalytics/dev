from django.test import SimpleTestCase
from django.urls import reverse, resolve
from investments.views import investment_list


class InvestmentURLsUnitTest(SimpleTestCase):

    def test_investment_list_url_resolves(self):
        """investment_list URL resolves to correct view"""
        url = reverse("investments:investment_list")
        self.assertEqual(resolve(url).func, investment_list)
