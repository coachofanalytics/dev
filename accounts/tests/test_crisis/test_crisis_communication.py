from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.forms import ContactForm
from django.core import mail

class CrisisCommunicationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_contact_form_display(self):
        """Test that contact form is displayed correctly"""
        response = self.client.get(reverse('main:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/contact/contact_message.html')
        self.assertIsInstance(response.context['form'], ContactForm)

    def test_contact_form_submission(self):
        """Test that contact form submission works correctly"""
        form_data = {
            'task': 'NA',
            'plan': 'NA',
            'message': 'Test crisis message'
        }
        response = self.client.post(reverse('main:contact'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/errors/generalerrors.html')
        self.assertIn('message', response.context)
        self.assertIn('48 hours', response.context['message'])

    def test_get_respos_with_empty_message(self):
        """Test response system with empty message"""
        response = self.client.get(reverse('main:get_respos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid user message', response.json()['response'])

    def test_get_respos_with_valid_message(self):
        """Test response system with valid message"""
        response = self.client.get(
            reverse('main:get_respos'),
            {'userMessage': 'Test crisis message'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('response', response.json())