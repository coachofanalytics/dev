import time
from django.test import TestCase, Client
from django.urls import reverse

class DocumentationPerformanceViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_services_spa_performance(self):
		url = reverse('main:services_spa')
		start_time = time.time()
		resp = self.client.get(url)
		duration = time.time() - start_time
		self.assertEqual(resp.status_code, 200)
		# Assert that the response time is less than 500ms (typical for a simple SPA landing page)
		self.assertLess(duration, 0.5, f"services_spa took too long: {duration}s")

	def test_submit_request_performance(self):
		url = reverse('main:submit_request')
		data = {
			'full_name': 'Perf User',
			'email': 'perf@example.com',
			'phone': '+1234567890',
			'document_type': 'birth',
			'package_type': 'standard',
			'destination_country': 'USA',
			'description': 'Description here',
			'consent': True
		}
		start_time = time.time()
		resp = self.client.post(url, data)
		duration = time.time() - start_time
		self.assertEqual(resp.status_code, 200)
		# Assert that the submission takes less than 500ms
		self.assertLess(duration, 0.5, f"submit_request took too long: {duration}s")
