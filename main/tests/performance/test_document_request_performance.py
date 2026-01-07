from django.test import TestCase, Client
from django.urls import reverse
import time

class DocumentRequestPerformanceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.services_url = reverse('main:services_spa')
        self.submit_url = reverse('main:submit_request')

    def test_services_spa_response_time(self):
        """Test that the services SPA page loads within acceptable limits (e.g., < 500ms)."""
        start_time = time.time()
        response = self.client.get(self.services_url)
        end_time = time.time()
        
        duration = end_time - start_time
        self.assertEqual(response.status_code, 200)
        # Using a generous limit for test environment, but ideally this is fast
        self.assertLess(duration, 1.0, f"Services SPA took too long: {duration}s")

    def test_submit_request_response_time(self):
        """Test that submitting a request is fast (e.g., < 500ms)."""
        data = {
            'full_name': 'Performance User',
            'email': 'perf@example.com',
            'phone': '+1234567890',
            'document_type': 'birth',
            'package_type': 'standard',
            'destination_country': 'France',
            'description': 'Perf test',
            'consent': 'on'
        }
        
        start_time = time.time()
        response = self.client.post(self.submit_url, data)
        end_time = time.time()
        
        duration = end_time - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 1.0, f"Submit Request took too long: {duration}s")
