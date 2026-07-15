from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import Application

User = get_user_model()


class ApplicationIntegrationTest(TestCase):

    def test_application_belongs_to_user(self):
        user = User.objects.create_user(
            username="noah",
            password="password123"
        )

        application = Application.objects.create(
            user=user,
            
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

        application = Application.objects.create(
            user=user,
            
            first_name="John",
            last_name="Doe",
            id_number="123",
            sub_county="Gasabo"
        )

        user.delete()

        self.assertFalse(
            Application.objects.filter(
                id=application.id
            ).exists()
        )