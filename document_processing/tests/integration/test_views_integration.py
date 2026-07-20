"""Integration tests for all Document Processing portal views.

These exercise the full request/response cycle (URL resolution -> view ->
template rendering -> DB state) for every view, including the complete
3-step application workflow and the document access history flow.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from document_processing.models import (
    Application,
    Payment,
    GeneratedDocument,
    DataAccessLog,
)

User = get_user_model()


def _make_document(application, title="Passport"):
    return GeneratedDocument.objects.create(
        application=application,
        title=title,
        file=SimpleUploadedFile(f"{title}.pdf", b"%PDF-1.4 test",
                                content_type="application/pdf"),
    )


def _make_user(username):
    return User.objects.create_user(username=username, password="password123")


def _login(client, username):
    client.login(username=username, password="password123")


class PortalViewIntegrationTest(TestCase):
    """End-to-end integration tests for every portal view."""

    def setUp(self):
        self.user = _make_user("intuser")
        self.other = _make_user("intother")
        self.client = self.client_class()
        _login(self.client, "intuser")

    # --- Dashboard --------------------------------------------------------
    def test_applications_url_resolves_and_renders(self):
        resp = self.client.get(reverse("document_processing:applications"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp, "document_processing/document_application_list.html"
        )

    def test_applications_unauthenticated_redirect(self):
        anon = self.client_class()
        resp = anon.get(reverse("document_processing:applications"))
        self.assertEqual(resp.status_code, 302)

    def test_applications_db_to_template(self):
        Application.objects.create(
            user=self.user, service="passport", first_name="John",
            last_name="Doe", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="submitted",
        )
        resp = self.client.get(reverse("document_processing:applications"))
        self.assertIn(
            Application.objects.first(),
            list(resp.context["page_obj"]),
        )

    # --- Full 3-step workflow --------------------------------------------
    def test_full_application_workflow(self):
        # Step 1: create
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "national_id_replacement",
                "first_name": "Grace",
                "last_name": "Mugisha",
                "id_number": "12345678",
                "district": "gasabo",
                "sub_county": "Kimironko",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 302)
        app = Application.objects.get(first_name="Grace", user=self.user)
        self.assertEqual(app.status, "draft")

        # Step 2: summary
        resp = self.client.post(
            reverse("document_processing:application_summary", args=[app.pk]),
            {"certified": "on", "action": "next"},
        )
        self.assertRedirects(
            resp, reverse("document_processing:application_payment", args=[app.pk])
        )
        app.refresh_from_db()
        self.assertTrue(app.certified)

        # Step 3: payment
        resp = self.client.get(
            reverse("document_processing:application_payment", args=[app.pk])
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            reverse("document_processing:process_payment", args=[app.pk]),
            {"method": "mtn", "payer_phone": "250788123456"},
        )
        self.assertRedirects(
            resp, reverse("document_processing:application_payment", args=[app.pk])
        )
        app.refresh_from_db()
        self.assertEqual(app.status, "paid")
        self.assertEqual(app.payments.count(), 1)
        self.assertEqual(app.payments.first().method, "mtn")

    def test_full_workflow_draft_then_resume(self):
        # Save as draft
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "passport",
                "first_name": "Draft",
                "last_name": "User",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "save_draft",
            },
        )
        self.assertRedirects(resp, reverse("document_processing:drafts"))
        app = Application.objects.get(first_name="Draft", user=self.user)
        self.assertEqual(app.status, "draft")

        # Resume via edit
        resp = self.client.post(
            reverse("document_processing:application_edit", args=[app.pk]),
            {
                "service": "passport",
                "first_name": "Draft",
                "last_name": "User",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertRedirects(
            resp, reverse("document_processing:application_summary", args=[app.pk])
        )

    # --- Drafts ------------------------------------------------------------
    def test_drafts_url_resolves_and_renders(self):
        Application.objects.create(
            user=self.user, service="passport", first_name="Draft",
            last_name="One", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="draft",
        )
        resp = self.client.get(reverse("document_processing:drafts"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "document_processing/drafts_list.html")

    def test_delete_draft_end_to_end(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Del",
            last_name="Me", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="draft",
        )
        resp = self.client.post(
            reverse("document_processing:delete_draft", args=[app.pk])
        )
        self.assertRedirects(resp, reverse("document_processing:drafts"))
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())

    # --- Application detail ----------------------------------------------
    def test_application_detail_url_resolves(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Det",
            last_name="Ail", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="submitted",
        )
        resp = self.client.get(
            reverse("document_processing:application_detail", args=[app.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "document_processing/application_detail.html")

    def test_application_detail_cross_user_forbidden(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Det",
            last_name="Ail", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="submitted",
        )
        other_client = self.client_class()
        _login(other_client, "intother")
        resp = other_client.get(
            reverse("document_processing:application_detail", args=[app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    # --- Documents ---------------------------------------------------------
    def test_documents_url_resolves_and_renders(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Doc",
            last_name="Owner", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="completed",
        )
        _make_document(app, title="Passport")
        resp = self.client.get(reverse("document_processing:documents"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "document_processing/documents_list.html")

    def test_view_document_url_resolves(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Doc",
            last_name="Owner", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="completed",
        )
        doc = _make_document(app, title="Passport")
        resp = self.client.get(
            reverse("document_processing:view_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "document_processing/view_document.html")

    def test_download_document_url_resolves(self):
        app = Application.objects.create(
            user=self.user, service="passport", first_name="Doc",
            last_name="Owner", id_number="1234567", district="gasabo",
            sub_county="Kimironko", reason="lost", status="completed",
        )
        doc = _make_document(app, title="Passport")
        resp = self.client.get(
            reverse("document_processing:download_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 200)

    # --- Access history ----------------------------------------------------
    def test_access_history_url_resolves_and_renders(self):
        DataAccessLog.log_access(
            user=self.user, institution="Portal", data_accessed="x",
            purpose="p", access_type="view",
        )
        resp = self.client.get(reverse("document_processing:access_history"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "document_processing/access_history.html")

    def test_access_history_filter_end_to_end(self):
        DataAccessLog.log_access(
            user=self.user, institution="Health", data_accessed="x",
            purpose="p", access_type="view",
        )
        DataAccessLog.log_access(
            user=self.user, institution="Finance", data_accessed="y",
            purpose="p", access_type="view",
        )
        resp = self.client.get(
            reverse("document_processing:access_history"),
            {"institution": "Health"},
        )
        self.assertEqual(
            [l.institution for l in resp.context["page_obj"]], ["Health"]
        )

    # --- AJAX sub-counties -------------------------------------------------
    def test_subcounties_json_url_resolves(self):
        resp = self.client.get(
            reverse("document_processing:subcounties_json"),
            {"district": "kicukiro"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertIn("Gikondo", resp.json()["subcounties"])
