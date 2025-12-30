from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentViewsRegressionTest(TestCase):
    """
    Regression tests ensure previously working functionality
    continues to work after changes.
    """

    def setUp(self):
        # Create baseline data that must always render correctly
        self.investment = investment_content.objects.create(
            title="Test Investment",
            slug="test-investment",
            description="Regression test investment record"
        )

    def test_investment_list_page_still_renders(self):
        """
        Ensure investment list page still loads successfully
        """
        response = self.client.get(reverse("investments:investment_list"))
        self.assertEqual(response.status_code, 200)

    def test_investment_list_uses_correct_template(self):
        """
        Ensure correct template is still used
        """
        response = self.client.get(reverse("investments:investment_list"))
        self.assertTemplateUsed(response, "investments/invest_list.html")

    def test_investment_list_displays_existing_data(self):
        """
        Ensure existing investment records still appear on page
        """
        response = self.client.get(reverse("investments:investment_list"))
        self.assertContains(response, "Test Investment")
        self.assertContains(response, "test-investment")
        self.assertContains(response, "Regression test investment record")
