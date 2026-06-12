from django.test import TestCase
from django.urls import reverse

from main.models import LegalService


class LegalServiceCrudIntegrationTests(TestCase):
    def test_full_crud_flow_through_test_routes(self):
        create_url = reverse("main:legal_service_test")

        create_response = self.client.post(
            create_url,
            {
                "title": "Visa Application Help",
                "category": "visa",
                "description": "Help with visa application documents.",
                "features": "Eligibility review\nDocument checklist",
                "cta_button_text": "Start",
                "cta_button_url": "https://example.com/start",
                "order": 1,
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(LegalService.objects.count(), 1)

        service = LegalService.objects.get()
        self.assertEqual(service.features, ["Eligibility review", "Document checklist"])

        edit_url = reverse("main:legal_service_test_edit", args=[service.pk])
        edit_response = self.client.post(
            edit_url,
            {
                "title": "Visa and Residency Help",
                "category": "visa",
                "description": "Updated legal support.",
                "features": "Case review\nEmbassy guidance",
                "cta_button_text": "Apply",
                "cta_button_url": "https://example.com/apply",
                "order": 2,
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)

        service.refresh_from_db()
        self.assertEqual(service.title, "Visa and Residency Help")
        self.assertEqual(service.order, 2)
        self.assertEqual(service.features, ["Case review", "Embassy guidance"])

        delete_url = reverse("main:legal_service_test_delete", args=[service.pk])
        delete_response = self.client.post(delete_url, follow=True)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(LegalService.objects.count(), 0)
