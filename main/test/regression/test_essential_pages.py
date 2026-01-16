from django.test import TestCase
from django.urls import reverse

class CriticalPathRegressionTests(TestCase):
    def test_essential_pages_availability(self):
        """Smoke test for critical pages to ensure no regressions."""
        pages = [
            'home', 
            'main:crisis_page',
            'main:document_services'
        ]
        for page in pages:
            url = reverse(page)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed to load {page}")
