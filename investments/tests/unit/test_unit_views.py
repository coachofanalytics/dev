from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentListViewUnitTest(TestCase):

    def setUp(self):
        self.investment = investment_content.objects.create(
            title="Test Investment",
            slug="test-investment",
            description="Test description"
        )

    def test_investment_list_status_code(self):
        """Investment list page returns HTTP 200"""
        url = reverse("investments:investment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_investment_list_template_used(self):
        """Correct template is rendered"""
        url = reverse("investments:investment_list")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "investments/invest_list.html")

    def test_investment_list_context_exists(self):
        """Context variable 'invest' exists"""
        url = reverse("investments:investment_list")
        response = self.client.get(url)
        self.assertIn("invest", response.context)

    def test_investment_list_context_data(self):
        """Investment data is correctly passed"""
        url = reverse("investments:investment_list")
        response = self.client.get(url)

        self.assertEqual(len(response.context["invest"]), 1)
        self.assertEqual(
            response.context["invest"][0].title,
            "Test Investment"
        )
