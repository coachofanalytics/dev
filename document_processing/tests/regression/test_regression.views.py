from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

# from document_processing.models import Document_Application


class DocumentApplicationRegressionTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="regressionuser",
            email="regressionuser@example.com",
            password="password123"
        )

        self.client.login(
            username="regressionuser",
            password="password123"
        )

        self.document = Document_Application.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            service_type="passport",
        )

    def test_empty_search_does_not_crash(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"search": ""}
        )

        self.assertEqual(response.status_code, 200)

    def test_non_matching_search_returns_empty_queryset(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"search": "NOT_FOUND_123"}
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            0
        )

    def test_invalid_page_number_does_not_crash(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"page": 999}
        )

        self.assertEqual(response.status_code, 200)

    def test_search_context_is_preserved(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"search": "Jane"}
        )

        self.assertEqual(
            response.context["search"],
            "Jane"
        )

    def test_search_by_last_name(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"search": "Smith"}
        )

        self.assertEqual(response.status_code, 200)

    def test_search_by_service_type(self):
        response = self.client.get(
            reverse("document_application_list"),
            {"search": "passport"}
        )

        self.assertEqual(response.status_code, 200)