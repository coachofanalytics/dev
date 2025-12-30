from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentIntegrationViewTests(TestCase):

    def setUp(self):
        investment_content.objects.create(
            title="Investment One",
            slug="investment-one",
            description="First investment"
        )
        investment_content.objects.create(
            title="Investment Two",
            slug="investment-two",
            description="Second investment"
        )

    def test_investment_list_page_renders_with_data(self):
        response = self.client.get(
            reverse("investments:investment_list")
        )

        # Page loads successfully
        self.assertEqual(response.status_code, 200)

        # Correct template used
        self.assertTemplateUsed(
            response,
            "investments/invest_list.html"
        )

        # Context variable exists
        self.assertIn("invest", response.context)

        # Correct number of records
        self.assertEqual(
            response.context["invest"].count(),
            2
        )

        # Data rendered in HTML
        self.assertContains(response, "Investment One")
        self.assertContains(response, "Investment Two")

    def test_dashboard_page_loads(self):
        response = self.client.get(
            reverse("investments:investments_dashboard")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "investments/home.html"
        )
