from django.test import TestCase
from main.models import Service, SubService, ExpertServiceRequest, DocumentServiceRequest

class ServiceModelTests(TestCase):
    def setUp(self):
        # Create a Service and SubServices
        self.service = Service.objects.create(
            title="Test Service",
            description="Test Description",
            slug="test-service",
            ordering=1
        )
        SubService.objects.create(service=self.service, title="Bullet 1")
        SubService.objects.create(service=self.service, title="Bullet 2")

    def test_service_model_logic(self):
        """Test Service and SubService linking and string representation."""
        self.assertEqual(str(self.service), "Test Service")
        self.assertEqual(self.service.subservices.count(), 2)
        self.assertEqual(str(self.service.subservices.first()), "Bullet 1 - Test Service")

class ExpertRequestModelTests(TestCase):
    def test_expert_request_model_creation(self):
        request_obj = ExpertServiceRequest.objects.create(
            service_type='legal_aid',
            location='Nairobi',
            urgency='urgent',
            message='Need help'
        )
        self.assertEqual(str(request_obj), "legal_aid (urgent) - Nairobi")
        self.assertEqual(request_obj.status, 'pending')

class DocumentRequestModelTests(TestCase):
    def test_create_document_request_logic(self):
        req = DocumentServiceRequest.objects.create(
            service_type='translation',
            message='Translate this'
        )
        self.assertEqual(req.status, 'pending')
        self.assertEqual(str(req), "Translation Services - None (pending)")
