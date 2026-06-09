from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationIntegrationTest(TestCase):

    def test_application_belongs_to_user(self):
        user = User.objects.create_user(
            username="noah",
            password="password123"
        )

        application = DocumentApplication.objects.create(
            user=user,
            service_type="nid_replacement",
            first_name="Noah",
            last_name="Yannick",
            id_number="987654321",
            sub_county="Kicukiro"
        )

        self.assertEqual(application.user.username, "noah")

    def test_delete_user_cascades_application(self):
        user = User.objects.create_user(
            username="test",
            password="password123"
        )

        application = DocumentApplication.objects.create(
            user=user,
            service_type="passport",
            first_name="John",
            last_name="Doe",
            id_number="123",
            sub_county="Gasabo"
        )

        user.delete()

        self.assertFalse(
            DocumentApplication.objects.filter(
                id=application.id
            ).exists()
        )