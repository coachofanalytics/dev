"""Unit tests for all Document Processing portal views.

Covers authorization (AC1, AC12), rendering, and the core business logic of
each view: draft save (AC4), the 3-step workflow (AC5-AC9), payment duplicate
prevention (AC9), document access logging (AC10/AC11), and the AJAX sub-county
helper (AC6).
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from document_processing.models import (
    Application,
    Payment,
    GeneratedDocument,
    DataAccessLog,
)

User = get_user_model()


def _make_document(application, title="Doc", content=b"%PDF-1.4 test"):
    return GeneratedDocument.objects.create(
        application=application,
        title=title,
        file=SimpleUploadedFile(f"{title}.pdf", content, content_type="application/pdf"),
    )


def _make_user(username, **kwargs):
    defaults = dict(password="password123")
    defaults.update(kwargs)
    return User.objects.create_user(username=username, **defaults)


def _make_application(user, **kwargs):
    defaults = dict(
        user=user,
        service="national_id_replacement",
        first_name="John",
        last_name="Doe",
        id_number="12345678",
        district="gasabo",
        sub_county="Kimironko",
        reason="lost",
        status="draft",
    )
    defaults.update(kwargs)
    return Application.objects.create(**defaults)


class PortalViewUnitTest(TestCase):
    """Unit tests for every view in document_processing.views."""

    def setUp(self):
        self.user = _make_user(
            "unituser", email="unit@example.com", first_name="John", last_name="Doe"
        )
        self.other = _make_user("otherunit", email="other@example.com")
        self.client = Client()
        self.client.login(username="unituser", password="password123")
        self.app = _make_application(self.user)

    # --- Auth gate (AC1) --------------------------------------------------
    def test_all_views_require_login(self):
        anon = Client()
        names = [
            "document_processing:applications",
            "document_processing:drafts",
            "document_processing:documents",
            "document_processing:access_history",
            "document_processing:application_create",
            "document_processing:subcounties_json",
        ]
        for name in names:
            resp = anon.get(reverse(name))
            self.assertEqual(resp.status_code, 302, name)

    # --- document_application_list (AC3) ---------------------------------
    def test_applications_dashboard_renders(self):
        resp = self.client.get(reverse("document_processing:applications"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "My Applications")

    def test_applications_dashboard_scoped_to_user(self):
        _make_application(self.other, first_name="Other")
        resp = self.client.get(reverse("document_processing:applications"))
        page_obj = resp.context["page_obj"]
        names = [a.first_name for a in page_obj]
        self.assertIn("John", names)
        self.assertNotIn("Other", names)

    def test_applications_search_by_application_no(self):
        _make_application(self.user, application_number="DC48-26-010101-AAAA")
        resp = self.client.get(
            reverse("document_processing:applications"),
            {"search": "AAAA", "field": "application_no"},
        )
        self.assertIn(
            "DC48-26-010101-AAAA",
            [a.application_number for a in resp.context["page_obj"]],
        )

    def test_applications_search_by_applicant(self):
        _make_application(self.user, first_name="Zelda")
        resp = self.client.get(
            reverse("document_processing:applications"),
            {"search": "Zelda", "field": "applicant"},
        )
        self.assertIn("Zelda", [a.first_name for a in resp.context["page_obj"]])

    def test_applications_status_filter(self):
        _make_application(self.user, status="approved")
        resp = self.client.get(
            reverse("document_processing:applications"), {"status": "approved"}
        )
        self.assertTrue(
            all(a.status == "approved" for a in resp.context["page_obj"])
        )

    def test_applications_stats_counts(self):
        _make_application(self.user, status="approved")
        resp = self.client.get(reverse("document_processing:applications"))
        stats = {s["label"]: s["value"] for s in resp.context["stats"]}
        self.assertEqual(stats["Total Applications"], 2)
        self.assertEqual(stats["Approved"], 1)

    # --- application_detail (AC12) ---------------------------------------
    def test_application_detail_owner_ok(self):
        resp = self.client.get(
            reverse("document_processing:application_detail", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_application_detail_other_user_404(self):
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.get(
            reverse("document_processing:application_detail", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_application_detail_logs_access(self):
        self.client.get(
            reverse("document_processing:application_detail", args=[self.app.pk])
        )
        self.assertTrue(
            DataAccessLog.objects.filter(
                user=self.user, access_type="view"
            ).exists()
        )

    # --- drafts_list (AC4) -----------------------------------------------
    def test_drafts_list_renders_only_drafts(self):
        _make_application(self.user, status="submitted")
        resp = self.client.get(reverse("document_processing:drafts"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            all(a.status == "draft" for a in resp.context["page_obj"])
        )

    # --- delete_draft (AC4) ----------------------------------------------
    def test_delete_draft_get_confirmation(self):
        resp = self.client.get(
            reverse("document_processing:delete_draft", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_draft_post_deletes(self):
        resp = self.client.post(
            reverse("document_processing:delete_draft", args=[self.app.pk])
        )
        self.assertRedirects(resp, reverse("document_processing:drafts"))
        self.assertFalse(Application.objects.filter(pk=self.app.pk).exists())

    def test_delete_draft_other_user_404(self):
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.post(
            reverse("document_processing:delete_draft", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    # --- application_create (AC5, AC6) -----------------------------------
    def test_application_create_get_renders(self):
        resp = self.client.get(reverse("document_processing:application_create"))
        self.assertEqual(resp.status_code, 200)

    def test_application_create_next_redirects_to_summary(self):
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
        app = Application.objects.get(first_name="Jane", user=self.user)
        self.assertRedirects(
            resp, reverse("document_processing:application_summary", args=[app.pk])
        )

    def test_application_create_save_draft(self):
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
        app = Application.objects.get(first_name="Jane", user=self.user)
        self.assertEqual(app.status, "draft")
        self.assertEqual(app.completion_percentage, 40)

    def test_application_create_invalid_id_number(self):
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "national_id_replacement",
                "first_name": "Jane",
                "last_name": "Smith",
                "id_number": "abc",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "must contain only digits")

    def test_application_create_missing_subcounty_invalid(self):
        resp = self.client.post(
            reverse("document_processing:application_create"),
            {
                "service": "passport",
                "first_name": "Jane",
                "last_name": "Smith",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please select a sub-county")

    # --- application_edit (AC5) ------------------------------------------
    def test_application_edit_get_renders(self):
        resp = self.client.get(
            reverse("document_processing:application_edit", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_application_edit_post_updates(self):
        resp = self.client.post(
            reverse("document_processing:application_edit", args=[self.app.pk]),
            {
                "service": "passport",
                "first_name": "Edited",
                "last_name": "Name",
                "id_number": "1234567",
                "district": "kicukiro",
                "sub_county": "Gikondo",
                "reason": "lost",
                "action": "next",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.app.refresh_from_db()
        self.assertEqual(self.app.first_name, "Edited")

    def test_application_edit_other_user_404(self):
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.get(
            reverse("document_processing:application_edit", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    # --- application_summary (AC7) ---------------------------------------
    def test_application_summary_get_renders(self):
        resp = self.client.get(
            reverse("document_processing:application_summary", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_application_summary_post_certified_redirects(self):
        resp = self.client.post(
            reverse("document_processing:application_summary", args=[self.app.pk]),
            {"certified": "on", "action": "next"},
        )
        self.assertRedirects(
            resp, reverse("document_processing:application_payment", args=[self.app.pk])
        )
        self.app.refresh_from_db()
        self.assertTrue(self.app.certified)
        self.assertEqual(self.app.completion_percentage, 80)

    def test_application_summary_requires_certification(self):
        resp = self.client.post(
            reverse("document_processing:application_summary", args=[self.app.pk]),
            {"action": "next"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "must certify")

    def test_application_summary_notify_phone_requires_phone(self):
        resp = self.client.post(
            reverse("document_processing:application_summary", args=[self.app.pk]),
            {"notify_by_phone": "on", "certified": "on", "action": "next"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Enter a phone number")

    def test_application_summary_cancel_redirects_to_dashboard(self):
        resp = self.client.post(
            reverse("document_processing:application_summary", args=[self.app.pk]),
            {"certified": "on", "action": "cancel"},
        )
        self.assertRedirects(resp, reverse("document_processing:applications"))

    # --- application_payment (AC8) ---------------------------------------
    def test_application_payment_get_renders(self):
        resp = self.client.get(
            reverse("document_processing:application_payment", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_application_payment_other_user_404(self):
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.get(
            reverse("document_processing:application_payment", args=[self.app.pk])
        )
        self.assertEqual(resp.status_code, 404)

    # --- process_payment (AC8, AC9) --------------------------------------
    def test_process_payment_creates_paid_payment(self):
        self._advance_to_payment()
        resp = self.client.post(
            reverse("document_processing:process_payment", args=[self.app.pk]),
            {"method": "mtn", "payer_phone": "250788123456"},
        )
        self.assertRedirects(
            resp, reverse("document_processing:application_payment", args=[self.app.pk])
        )
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "paid")
        self.assertEqual(self.app.payments.filter(status="paid").count(), 1)

    def test_process_payment_prevents_duplicate(self):
        self._advance_to_payment()
        self.client.post(
            reverse("document_processing:process_payment", args=[self.app.pk]),
            {"method": "mtn", "payer_phone": "250788123456"},
        )
        before = self.app.payments.filter(status="paid").count()
        self.client.post(
            reverse("document_processing:process_payment", args=[self.app.pk]),
            {"method": "airtel", "payer_phone": "250788123456"},
        )
        after = Application.objects.get(pk=self.app.pk).payments.filter(status="paid").count()
        self.assertEqual(before, after)

    def test_process_payment_mobile_money_requires_phone(self):
        self._advance_to_payment()
        resp = self.client.post(
            reverse("document_processing:process_payment", args=[self.app.pk]),
            {"method": "mtn", "payer_phone": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "mobile money phone number")

    def test_process_payment_logs_access(self):
        self._advance_to_payment()
        self.client.post(
            reverse("document_processing:process_payment", args=[self.app.pk]),
            {"method": "mtn", "payer_phone": "250788123456"},
        )
        self.assertTrue(
            DataAccessLog.objects.filter(
                user=self.user, institution="Payment Provider"
            ).exists()
        )

    # --- documents_list (AC10) -------------------------------------------
    def test_documents_list_renders_only_owners_docs(self):
        GeneratedDocument.objects.create(
            application=self.app, title="My Doc", file="documents/m.pdf"
        )
        other_app = _make_application(self.other)
        GeneratedDocument.objects.create(
            application=other_app, title="Other Doc", file="documents/o.pdf"
        )
        resp = self.client.get(reverse("document_processing:documents"))
        titles = [d.title for d in resp.context["page_obj"]]
        self.assertIn("My Doc", titles)
        self.assertNotIn("Other Doc", titles)

    # --- view_document (AC10, AC12) --------------------------------------
    def test_view_document_owner_ok(self):
        doc = _make_document(self.app, title="Doc")
        resp = self.client.get(
            reverse("document_processing:view_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_view_document_other_user_404(self):
        doc = _make_document(self.app, title="Doc")
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.get(
            reverse("document_processing:view_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_view_document_logs_access(self):
        doc = _make_document(self.app, title="Doc")
        self.client.get(
            reverse("document_processing:view_document", args=[doc.pk])
        )
        self.assertTrue(
            DataAccessLog.objects.filter(
                user=self.user, access_type="view"
            ).exists()
        )

    # --- download_document (AC10, AC12) ----------------------------------
    def test_download_document_owner_ok(self):
        doc = _make_document(self.app, title="Doc")
        resp = self.client.get(
            reverse("document_processing:download_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Disposition"], 'attachment; filename="Doc.pdf"'
        )

    def test_download_document_other_user_404(self):
        doc = _make_document(self.app, title="Doc")
        other_client = Client()
        other_client.login(username="otherunit", password="password123")
        resp = other_client.get(
            reverse("document_processing:download_document", args=[doc.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_download_document_logs_access(self):
        doc = _make_document(self.app, title="Doc")
        self.client.get(
            reverse("document_processing:download_document", args=[doc.pk])
        )
        self.assertTrue(
            DataAccessLog.objects.filter(
                user=self.user, access_type="download"
            ).exists()
        )

    # --- access_history (AC11) -------------------------------------------
    def test_access_history_renders_only_owners_logs(self):
        DataAccessLog.log_access(
            user=self.user, institution="A", data_accessed="x",
            purpose="p", access_type="view"
        )
        DataAccessLog.log_access(
            user=self.other, institution="B", data_accessed="y",
            purpose="p", access_type="view"
        )
        resp = self.client.get(reverse("document_processing:access_history"))
        institutions = [l.institution for l in resp.context["page_obj"]]
        self.assertIn("A", institutions)
        self.assertNotIn("B", institutions)

    def test_access_history_institution_filter(self):
        DataAccessLog.log_access(
            user=self.user, institution="Health", data_accessed="x",
            purpose="p", access_type="view"
        )
        DataAccessLog.log_access(
            user=self.user, institution="Finance", data_accessed="y",
            purpose="p", access_type="view"
        )
        resp = self.client.get(
            reverse("document_processing:access_history"),
            {"institution": "Health"},
        )
        institutions = [l.institution for l in resp.context["page_obj"]]
        self.assertEqual(institutions, ["Health"])

    # --- subcounties_json (AC6) ------------------------------------------
    def test_subcounties_json_returns_options(self):
        resp = self.client.get(
            reverse("document_processing:subcounties_json"),
            {"district": "gasabo"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Kimironko", data["subcounties"])

    def test_subcounties_json_unknown_district_empty(self):
        resp = self.client.get(
            reverse("document_processing:subcounties_json"),
            {"district": "nowhere"},
        )
        self.assertEqual(resp.json()["subcounties"], [])

    # --- Helper -----------------------------------------------------------
    def _advance_to_payment(self):
        """Drive the app through steps 1-2 so payment is reachable."""
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
            {"certified": "on", "action": "next"},
        )
        self.app = app
