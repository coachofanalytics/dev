from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.client import RequestFactory

class ErrorHandlingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_400_error_page(self):
        """Test that 400 error page is displayed correctly"""
        response = self.client.get(reverse('main:400error'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/400.html')

    def test_403_error_page(self):
        """Test that 403 error page is displayed correctly"""
        response = self.client.get(reverse('main:403error'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/403.html')

    def test_404_error_page(self):
        """Test that 404 error page is displayed correctly"""
        response = self.client.get(reverse('main:404error'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/404.html')

    def test_500_error_page(self):
        """Test that 500 error page is displayed correctly"""
        response = self.client.get(reverse('main:500error'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/500.html')

    def test_general_error_page(self):
        """Test that general error page is displayed with message"""
        response = self.client.get(reverse('main:general-errors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/generalerrors.html')
        self.assertIn('message', response.context)