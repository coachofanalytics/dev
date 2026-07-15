from django.test import TestCase
from django.contrib.auth import get_user_model

from document_portal.models import DocumentApplication, DocumentDraft


class DocumentDraftModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="draftuser",
            email="draftuser@example.com",
            password="Testpass123"
        )

        self.application = DocumentApplication.objects.create(
            user=self.user,
            service_type="nid_replacement",
            first_name="John",
            last_name="Doe",
            id_number="12345678",
            district="Nairobi",
            sub_county="Westlands",
            reason="Lost ID",
            status="draft",
            fee=1500
        )

        self.draft = DocumentDraft.objects.create(
            application=self.application,
            completion_percentage=50,
            draft_data={
                "step": 1,
                "notes": "Personal information completed"
            }
        )

    def test_document_draft_created_successfully(self):
        self.assertEqual(DocumentDraft.objects.count(), 1)
        self.assertEqual(self.draft.application, self.application)
        self.assertEqual(self.draft.completion_percentage, 50)

    def test_document_draft_string_method(self):
        self.assertIn("Draft for", str(self.draft))

    def test_document_draft_json_data(self):
        self.assertEqual(self.draft.draft_data["step"], 1)
        self.assertEqual(
            self.draft.draft_data["notes"],
            "Personal information completed"
        )

        from django.test import TestCase
from django.contrib.auth import get_user_model

from document_portal.models import (
    DocumentProfile,
    DocumentApplication,
    DocumentDraft,
)


class DocumentPortalModelTest(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Testpass123"
        )

        self.profile = DocumentProfile.objects.create(
            user=self.user,
            role="citizen",
            language_preference="en",
            phone_number="0712345678",
            email_notifications=True,
            phone_notifications=True,
        )

        self.application = DocumentApplication.objects.create(
            user=self.user,
            service_type="nid_replacement",
            first_name="John",
            last_name="Doe",
            id_number="12345678",
            district="Nairobi",
            sub_county="Westlands",
            reason="Lost ID",
            status="draft",
            fee=1500,
        )

        self.draft = DocumentDraft.objects.create(
            application=self.application,
            completion_percentage=40,
            draft_data={
                "step": 1,
                "notes": "Personal information saved"
            }
        )

    def test_document_profile_created(self):
        self.assertEqual(DocumentProfile.objects.count(), 1)
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.role, "citizen")
        self.assertEqual(self.profile.language_preference, "en")
        self.assertTrue(self.profile.email_notifications)
        self.assertTrue(self.profile.phone_notifications)

    def test_document_profile_str(self):
        self.assertIn("citizen", str(self.profile))

    def test_document_application_created(self):
        self.assertEqual(DocumentApplication.objects.count(), 1)
        self.assertEqual(self.application.user, self.user)
        self.assertEqual(self.application.service_type, "nid_replacement")
        self.assertEqual(self.application.first_name, "John")
        self.assertEqual(self.application.last_name, "Doe")
        self.assertEqual(self.application.status, "draft")
        self.assertEqual(float(self.application.fee), 1500.00)

    def test_document_application_str(self):
        self.assertEqual(str(self.application), "John Doe")

    def test_document_draft_created(self):
        self.assertEqual(DocumentDraft.objects.count(), 1)
        self.assertEqual(self.draft.application, self.application)
        self.assertEqual(self.draft.completion_percentage, 40)
        self.assertEqual(self.draft.draft_data["step"], 1)

    def test_document_draft_str(self):
        self.assertIn("Draft for", str(self.draft))