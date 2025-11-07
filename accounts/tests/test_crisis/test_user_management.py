from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class CrisisUserManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        # Create a regular user
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        # Create a superuser
        self.admin_user = self.User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

    def test_login_during_crisis(self):
        """Test login functionality during crisis scenario"""
        response = self.client.post(reverse('accounts:account-login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Successful login should redirect

    def test_unauthorized_access_during_crisis(self):
        """Test unauthorized access attempts during crisis"""
        # Try accessing protected page without login
        response = self.client.get(reverse('main:plans'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertIn('login', response.url)

    def test_superuser_access_during_crisis(self):
        """Test superuser access during crisis"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('main:plans'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_restricted_access(self):
        """Test regular user access to restricted areas during crisis"""
        self.client.login(username='testuser', password='testpass123')
        # Try accessing a superuser-only view
        response = self.client.get(reverse('main:update_service', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 403)  # Should return forbidden

    def test_user_profile_access_during_crisis(self):
        """Test user profile access during crisis"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:account-profile'))
        self.assertEqual(response.status_code, 200)