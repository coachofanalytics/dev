from django.test import TestCase
from django.urls import reverse
from main.models import Service, SubService, ExpertServiceRequest

class ServiceViewTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(
            title="Test Service",
            description="Test Description",
            slug="test-service",
            ordering=1
        )
        SubService.objects.create(service=self.service, title="Bullet 1")

    def test_our_service_page_rendering(self):
        """Test the 'our_service' view loads correctly and includes context."""
        response = self.client.get(reverse('main:our_service'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/our_service.html")
        self.assertIn('services', response.context)
        self.assertContains(response, "Test Service")
        self.assertContains(response, "Bullet 1")

class ExpertContactViewTests(TestCase):
    def test_contact_expert_ajax_submission(self):
        """Test the AJAX submission endpoint saves data to DB."""
        data = {
            'service_type': 'crisis_management',
            'location': 'London',
            'urgency': 'normal',
            'message': 'Testing AJAX'
        }
        response = self.client.post(reverse('main:contact_expert'), data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Request submitted successfully!'})
        
        # Verify generated DB record
        self.assertTrue(ExpertServiceRequest.objects.filter(message='Testing AJAX').exists())
