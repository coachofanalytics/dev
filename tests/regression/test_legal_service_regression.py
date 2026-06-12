from django.test import TestCase
from django.urls import reverse

from main.models import LegalService


class LegalServiceRegressionTests(TestCase):
    def test_public_guidance_page_excludes_inactive_and_orders_by_order(self):
        LegalService.objects.create(
            title="Second",
            category="visa",
            description="Visible second",
            order=2,
            is_active=True,
        )
        LegalService.objects.create(
            title="First",
            category="citizenship",
            description="Visible first",
            order=1,
            is_active=True,
        )
        LegalService.objects.create(
            title="Hidden",
            category="legal_referral",
            description="Should not show",
            order=0,
            is_active=False,
        )

        response = self.client.get(reverse("main:legal_immigration_guidance"))
        self.assertEqual(response.status_code, 200)

        services = list(response.context["services"])
        self.assertEqual([svc.title for svc in services], ["First", "Second"])
        self.assertNotIn("Hidden", response.content.decode())

    def test_test_page_lists_all_services_for_crud(self):
        LegalService.objects.create(
            title="Inactive but editable",
            category="visa",
            description="Still visible for CRUD table",
            order=5,
            is_active=False,
        )

        response = self.client.get(reverse("main:legal_service_test"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inactive but editable")
