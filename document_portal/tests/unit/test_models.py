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