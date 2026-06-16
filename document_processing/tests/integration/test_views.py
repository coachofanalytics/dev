from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationIntegrationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='john',
            password='password123'
        )

        self.url = reverse(
            'document_processing:DocumentApplication'
        )

    def create_application(self):
        return DocumentApplication.objects.create(
            user=self.user,
            service_type='passport',
            first_name='John',
            last_name='Doe',
            id_number='123456789',
            sub_county='Gasabo',
            reason='Testing',
            status='submitted',
            fee=5000
        )

    def test_url_resolves_and_returns_page(self):
        self.client.login(
            username='john',
            password='password123'
        )

        self.create_application()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_processing/DocumentApplication.html'
        )

    def test_database_to_template_integration(self):
        app = self.create_application()

        self.client.login(
            username='john',
            password='password123'
        )

        response = self.client.get(self.url)

        page_obj = response.context['page_obj']

        self.assertIn(app, page_obj)

    def test_unauthenticated_users_redirected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)