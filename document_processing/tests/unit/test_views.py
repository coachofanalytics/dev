from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from document_processing.models import Application, GeneratedDocument, DataAccessLog

User = get_user_model()


class PortalViewAccessTest(TestCase):
    """Authorization and rendering tests for the Document Processing portal."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )
        self.other = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="password123",
        )
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        self.app = Application.objects.create(
            user=self.user,
            service="national_id_replacement",
            first_name="John",
            last_name="Doe",
            id_number="12345678",
            district="gasabo",
            sub_county="Kimironko",
            reason="lost",
            status="draft",
        )

    def test_login_required_redirect(self):
        anon = Client()
        resp = anon.get(reverse("document_processing:applications"))
        self.assertEqual(resp.status_code, 302)

    def test_applications_dashboard_renders(self):
        resp = self.client.get(reverse("document_processing:applications"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "My Applications")

    def test_drafts_list_renders(self):
        resp = self.client.get(reverse("document_processing:drafts"))
        self.assertEqual(resp.status_code, 200)

    def test_documents_list_renders(self):
        resp = self.client.get(reverse("document_processing:documents"))
        self.assertEqual(resp.status_code, 200)

    def test_access_history_renders(self):
        resp = self.client.get(reverse("document_processing:access_history"))
        self.assertEqual(resp.status_code, 200)

    def test_application_create_renders(self):
        resp = self.client.get(reverse("document_processing:application_create"))
        self.assertEqual(resp.status_code, 200)

    def test_owner_can_view_application_detail(self):
        resp = self.client.get(
            reverse("document_processing:application_detail", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_other_user_cannot_view_application(self):
        other_client = Client()
        other_client.login(username="otheruser", password="password123")
        resp = other_client.get(
            reverse("document_processing:application_detail", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_application_create_valid_flow(self):
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "birth_certificate",
                "first_name": "Jane",
                "last_name": "Smith",
                "id_number": "123456",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Application.objects.filter(first_name="Jane", user=self.user).exists()
        )

    def test_application_create_invalid_id_number(self):
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "national_id_replacement",
                "first_name": "Jane",
                "last_name": "Smith",
                "id_number": "abc",  # invalid: must be 6-8 digits
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "must contain only digits")

    def test_save_draft_redirects_to_drafts(self):
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "passport",
                "first_name": "Jane",
                "last_name": "Smith",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "save_draft",
            },
        )
        self.assertRedirects(resp, reverse("document_processing:drafts"))

    def test_payment_prevents_duplicate(self):
        # Pay once.
        self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "passport",
                "first_name": "Pay",
                "last_name": "User",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        app = Application.objects.get(first_name="Pay", user=self.user)
        self.client.post(
            reverse("document_processing:application_summary", args=[app.pk]),
            {
                "certified": "on",
                "action": "next",
            },
        )
        self.client.post(
            reverse("document_processing:process_payment", args=[app.pk]),
            {"method": "mtn", "payer_phone": "250788123456"},
        )
        # Second payment attempt should be blocked (no new paid payment).
        before = app.payments.filter(status="paid").count()
        self.client.post(
            reverse("document_processing:process_payment", args=[app.pk]),
            {"method": "airtel", "payer_phone": "250788123456"},
        )
        after = Application.objects.get(pk=app.pk).payments.filter(status="paid").count()
        self.assertEqual(before, after)

