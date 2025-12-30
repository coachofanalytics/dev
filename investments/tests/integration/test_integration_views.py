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



from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentCreateIntegrationTests(TestCase):

    def test_full_create_flow(self):
        """
        Integration test:
        URL → View → Form → DB → Redirect
        """
        create_url = reverse("investments:investment_create")

        # 1️⃣ GET request loads form
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

        # 2️⃣ POST valid data
        data = {
            "title": "Integration Investment",
            "slug": "integration-investment",
            "description": "Integration test description",
        }

        response = self.client.post(
            create_url,
            data=data,
            follow=True
        )

        # 3️⃣ Database updated
        self.assertEqual(investment_content.objects.count(), 1)

        investment = investment_content.objects.first()
        self.assertEqual(investment.title, "Integration Investment")
        self.assertEqual(investment.slug, "integration-investment")

        # 4️⃣ Redirect happens correctly
        self.assertRedirects(
            response,
            reverse("investments:investment_list")
        )

    def test_create_flow_invalid_data(self):
        """
        Integration test:
        Invalid data should not save and should re-render form
        """
        create_url = reverse("investments:investment_create")

        data = {
            "title": "",
            "slug": "",
            "description": "Invalid integration test",
        }

        response = self.client.post(create_url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(investment_content.objects.count(), 0)
        self.assertContains(response, "<form")





from django.test import TestCase
from django.urls import reverse
from investments.models import investment_content


class InvestmentUpdateIntegrationTests(TestCase):

    def setUp(self):
        self.investment = investment_content.objects.create(
            title="Old Title",
            slug="old-title",
            description="Old description",
        )

    def test_update_investment_success(self):
        url = reverse(
            "investments:investment_update",
            args=[self.investment.pk]
        )

        # GET loads form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Old Title")

        # POST updated data
        response = self.client.post(
            url,
            data={
                "title": "Updated Title",
                "slug": "updated-title",
                "description": "Updated description",
            },
            follow=True
        )

        self.investment.refresh_from_db()

        # DB updated
        self.assertEqual(self.investment.title, "Updated Title")
        self.assertEqual(self.investment.slug, "updated-title")

        # Redirect success
        self.assertRedirects(
            response,
            reverse("investments:investment_list")
        )





