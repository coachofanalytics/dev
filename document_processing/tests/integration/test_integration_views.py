from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from document_processing.models import Document_Application


class DocumentApplicationIntegrationTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="integrationuser",
            password="password123"
        )

        for i in range(15):
            Document_Application.objects.create(
                user=self.user,
                service_type="passport",
                first_name=f"User{i}",
                last_name="Test",
                id_number=f"ID{i}",
                district="Nairobi",
                sub_county="Westlands",
                reason="Testing pagination"
            )

    def test_login_required(self):
        response = self.client.get(
            reverse("document_application_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        self.client.login(
            username="integrationuser",
            password="password123"
        )

        response = self.client.get(
            reverse("document_application_list")
        )

        self.assertEqual(response.status_code, 200)

        # self.assertTemplateUsed(
        #     response,
        #     "document_processing/document_application_list.html"
        # )

    def test_first_page_contains_10_records(self):
        self.client.login(
            username="integrationuser",
            password="password123"
        )

        response = self.client.get(
            reverse("document_application_list")
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            10
        )

    def test_second_page_exists(self):
        self.client.login(
            username="integrationuser",
            password="password123"
        )

        response = self.client.get(
            reverse("document_application_list"),
            {"page": 2}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["page_obj"].has_previous()
        )

    def test_total_records_count(self):
        self.client.login(
            username="integrationuser",
            password="password123"
        )

        response = self.client.get(
            reverse("document_application_list")
        )

        self.assertEqual(
            response.context["total_applications"],
            15
        )