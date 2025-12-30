from django.test import SimpleTestCase
from django.urls import reverse


class InvestmentRegressionURLTests(SimpleTestCase):

    def test_investment_list_url_still_exists(self):
        url = reverse("investments:investment_list")
        self.assertEqual(url, "/investments/invest_list/")

    def test_dashboard_url_still_exists(self):
        url = reverse("investments:investments_dashboard")
        self.assertEqual(url, "/investments/investments/")
