from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )

    def test_document_application_creation(self):
        application = DocumentApplication.objects.create(
            user=self.user,
            service_type="passport",
            first_name="John",
            last_name="Doe",
            id_number="123456789",
            sub_county="Gasabo",
            fee=Decimal("50000.00")
        )

        self.assertEqual(application.first_name, "John")
        self.assertEqual(application.status, "draft")
        self.assertEqual(application.service_type, "passport")

    def test_default_status_is_draft(self):
        application = DocumentApplication.objects.create(
            user=self.user,
            service_type="passport",
            first_name="John",
            last_name="Doe",
            id_number="123456789",
            sub_county="Gasabo"
        )

        self.assertEqual(application.status, "draft")

    def test_fee_is_saved_correctly(self):
        application = DocumentApplication.objects.create(
            user=self.user,
            service_type="passport",
            first_name="John",
            last_name="Doe",
            id_number="123456789",
            sub_county="Gasabo",
            fee=Decimal("75000.00")
        )

        self.assertEqual(application.fee, Decimal("75000.00"))