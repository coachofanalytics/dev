from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationRegressionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password="password123"
        )

    def test_invalid_service_type_rejected(self):
        application = DocumentApplication(
            user=self.user,
            service_type="invalid_service",
            first_name="John",
            last_name="Doe",
            id_number="123",
            sub_county="Gasabo"
        )

        with self.assertRaises(ValidationError):
            application.full_clean()