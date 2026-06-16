from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import Document_Application

User = get_user_model()


class DocumentApplicationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="TestPass123"
        )

    def test_create_document_application(self):
        document = Document_Application.objects.create(
            user=self.user,
            # add your other required fields here
        )

        self.assertEqual(document.user, self.user)