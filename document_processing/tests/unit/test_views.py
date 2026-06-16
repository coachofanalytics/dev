from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='password123'
        )

        self.url = reverse(
            'document_processing:DocumentApplication'
        )

    def create_application(self, user):
        return DocumentApplication.objects.create(
            user=user,
            service_type='passport',
            first_name='John',
            last_name='Doe',
            id_number='1234567890123456',
            sub_county='Gasabo',
            reason='Testing application',
            status='submitted',
            fee=5000
        )

    def test_login_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_access_view(self):
        self.client.login(
            username='testuser',
            password='password123'
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_processing/DocumentApplication.html'
        )

    def test_only_current_user_applications_are_displayed(self):
        user_app = self.create_application(self.user)
        other_app = self.create_application(self.other_user)

        self.client.login(
            username='testuser',
            password='password123'
        )

        response = self.client.get(self.url)

        page_obj = response.context['page_obj']

        self.assertIn(user_app, page_obj)
        self.assertNotIn(other_app, page_obj)

    def test_applications_are_ordered_by_submitted_at_desc(self):
        app1 = self.create_application(self.user)
        app2 = self.create_application(self.user)

        self.client.login(
            username='testuser',
            password='password123'
        )

        response = self.client.get(self.url)

        page_obj = response.context['page_obj']

        self.assertEqual(page_obj[0], app2)
        self.assertEqual(page_obj[1], app1)

    def test_pagination_first_page(self):
        for i in range(15):
            DocumentApplication.objects.create(
                user=self.user,
                service_type='passport',
                first_name=f'John{i}',
                last_name='Doe',
                id_number=f'ID{i}',
                sub_county='Gasabo',
                reason='Test',
                status='submitted',
                fee=5000
            )

        self.client.login(
            username='testuser',
            password='password123'
        )

        response = self.client.get(self.url)

        page_obj = response.context['page_obj']

        self.assertEqual(len(page_obj), 10)
        self.assertTrue(page_obj.has_next())

    def test_pagination_second_page(self):
        for i in range(15):
            DocumentApplication.objects.create(
                user=self.user,
                service_type='passport',
                first_name=f'John{i}',
                last_name='Doe',
                id_number=f'ID{i}',
                sub_county='Gasabo',
                reason='Test',
                status='submitted',
                fee=5000
            )

        self.client.login(
            username='testuser',
            password='password123'
        )

        response = self.client.get(
            self.url,
            {'page': 2}
        )

        page_obj = response.context['page_obj']

        self.assertEqual(len(page_obj), 5)
        self.assertFalse(page_obj.has_next())