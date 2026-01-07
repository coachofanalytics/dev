from django.test import TestCase, Client
from django.urls import reverse
from main.models import DocumentRequest
import json

class DocumentRequestViewRegressionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.services_url = reverse('main:services_spa')
        self.submit_url = reverse('main:submit_request')

    def test_services_spa_view_status_code(self):
        """Test that the services SPA page returns 200."""
        response = self.client.get(self.services_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/index.html')
        self.assertIn('form', response.context)

    def test_submit_request_valid_post(self):
        """Test submitting a valid document request."""
        data = {
            'full_name': 'Regression User',
            'email': 'regression@example.com',
            'phone': '+1234567890',
            'document_type': 'birth',
            'package_type': 'standard',
            'destination_country': 'UK',
            'description': 'Regression test description',
            'consent': 'on'  # Checkbox value
        }
        response = self.client.post(self.submit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        
        # Verify it was saved to DB
        doc_req = DocumentRequest.objects.get(full_name='Regression User')
        self.assertEqual(doc_req.email, 'regression@example.com')
        self.assertEqual(doc_req.status, 'Pending')

    def test_submit_request_invalid_post(self):
        """Test submitting an invalid document request (missing consent)."""
        data = {
            'full_name': 'Regression User Invalid',
            'email': 'regression_invalid@example.com',
            'phone': '+1234567890',
            'document_type': 'birth',
            'package_type': 'standard',
            'destination_country': 'UK',
            'description': 'Regression test description',
            # 'consent': 'on'  <-- Missing consent
        }
        response = self.client.post(self.submit_url, data)
        
        # The view returns 400 for invalid forms (lines 699 in views.py)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        json_response = json.loads(response.content)
        self.assertFalse(json_response['success'])
        self.assertIn('error', json_response)
        
        # Verify NOT saved to DB
        self.assertFalse(DocumentRequest.objects.filter(full_name='Regression User Invalid').exists())
