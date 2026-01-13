from django.test import TestCase, Client
from django.urls import reverse
from main.models import DocumentationRequest


class EducationViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_course_register_page_renders(self):
		url = reverse('main:course_register')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# expect the full page to contain the main heading
		self.assertContains(resp, 'Course Registration & Payments')

	def test_course_register_fragment_returns(self):
		url = reverse('main:course_register') + '?partial=1'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# the fragment should include the fragment container id
		self.assertContains(resp, 'id="course-register-fragment"')

class DocumentationViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_services_spa_renders(self):
		url = reverse('main:services_spa')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# Check if the form is present in the context or template
		self.assertContains(resp, '<form')
		self.assertContains(resp, 'id="document-request-form"')

	def test_submit_request_success(self):
		url = reverse('main:submit_request')
		data = {
			'full_name': 'Test User',
			'email': 'test@example.com',
			'phone': '+1234567890',
			'document_type': 'birth',
			'package_type': 'standard',
			'destination_country': 'USA',
			'description': 'Description here',
			'consent': True
		}
		resp = self.client.post(url, data)
		self.assertEqual(resp.status_code, 200)
		json_data = resp.json()
		self.assertTrue(json_data['success'])
		self.assertIn('submitted successfully', json_data['message'])
		self.assertTrue(DocumentationRequest.objects.filter(email='test@example.com').exists())

	def test_submit_request_invalid(self):
		url = reverse('main:submit_request')
		data = {
			'full_name': '', # Required
			'email': 'invalid-email',
			'consent': False
		}
		resp = self.client.post(url, data)
		self.assertEqual(resp.status_code, 400)
		json_data = resp.json()
		self.assertFalse(json_data['success'])
		self.assertIn('error', json_data)
