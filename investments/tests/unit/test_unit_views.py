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





from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentCreateViewTests(TestCase):

    def test_create_page_loads(self):
        """
        GET request should load the investment create page
        """
        response = self.client.get(
            reverse("investments:investment_create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "investments/invest_create.html"
        )
        self.assertIn("form", response.context)

    def test_create_investment_successfully(self):
        """
        POST request should create a new investment and redirect
        """
        data = {
            "title": "Test Investment",
            "slug": "test-investment",
            "description": "Test investment description",
        }

        response = self.client.post(
            reverse("investments:investment_create"),
            data
        )

        # Object created
        self.assertEqual(
            investment_content.objects.count(),
            1
        )

        # Redirect after success
        self.assertRedirects(
            response,
            reverse("investments:investment_list")
        )

        # Data saved correctly
        investment = investment_content.objects.first()
        self.assertEqual(investment.title, "Test Investment")
        self.assertEqual(investment.slug, "test-investment")

    def test_create_invalid_form_does_not_save(self):
        """
        Invalid POST should not create record
        """
        data = {
            "title": "",  # invalid
            "slug": "",
            "description": "",
        }

        response = self.client.post(
            reverse("investments:investment_create"),
            data
        )

        # No object created
        self.assertEqual(
            investment_content.objects.count(),
            0
        )

        # Page re-renders form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "investments/invest_create.html"
        )




from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentUpdateViewUnitTests(TestCase):

    def setUp(self):
        self.investment = investment_content.objects.create(
            title="Initial",
            slug="initial",
            description="Initial description",
        )

    def test_update_view_returns_200(self):
        url = reverse(
            "investments:investment_update",
            args=[self.investment.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_view_updates_object(self):
        url = reverse(
            "investments:investment_update",
            args=[self.investment.pk]
        )

        response = self.client.post(
            url,
            {
                "title": "Changed",
                "slug": "changed",
                "description": "Changed description",
            }
        )

        self.investment.refresh_from_db()
        self.assertEqual(self.investment.title, "Changed")
     
