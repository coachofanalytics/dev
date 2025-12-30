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




from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentCreateRegressionViewTests(TestCase):

    def test_create_page_loads(self):
        """
        CREATE page should continue to load successfully
        """
        response = self.client.get(
            reverse("investments:investment_create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "investments/invest_create.html"
        )

    def test_create_post_still_creates_object(self):
        """
        CREATE POST should still save investment_content
        """
        data = {
            "title": "Regression Create",
            "slug": "regression-create",
            "description": "Regression create description",
        }

        response = self.client.post(
            reverse("investments:investment_create"),
            data=data,
            follow=True
        )

        # Object created
        self.assertEqual(
            investment_content.objects.count(),
            1
        )

        self.assertEqual(
            investment_content.objects.first().title,
            "Regression Create"
        )

        # Redirect still works
        self.assertRedirects(
            response,
            reverse("investments:investment_list")
        )

    def test_create_invalid_data_does_not_save(self):
        """
        Invalid data must not create records
        """
        data = {
            "title": "",
            "slug": "",
            "description": "Invalid data",
        }

        response = self.client.post(
            reverse("investments:investment_create"),
            data=data
        )

        self.assertEqual(
            investment_content.objects.count(),
            0
        )

        self.assertEqual(response.status_code, 200)
