from django.test import TestCase
from main.models import DocumentRequest
from main.forms import DocumentRequestForm

class DocumentRequestModelTest(TestCase):
    def test_document_request_creation(self):
        """Test that a DocumentRequest instance can be created."""
        doc_req = DocumentRequest.objects.create(
            full_name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            document_type="birth",
            package_type="standard",
            destination_country="USA",
            description="Need birth certificate",
            consent=True
        )
        self.assertEqual(doc_req.full_name, "John Doe")
        self.assertEqual(doc_req.status, "Pending")
        self.assertEqual(str(doc_req), "John Doe - Birth Certificate")

    def test_document_request_default_status(self):
        """Test that the default status is 'Pending'."""
        doc_req = DocumentRequest.objects.create(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="+0987654321",
            document_type="marriage",
            package_type="premium",
            consent=True
        )
        self.assertEqual(doc_req.status, "Pending")

class DocumentRequestFormTest(TestCase):
    def test_form_valid_data(self):
        """Test the form with valid data."""
        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '123456789',
            'document_type': 'birth',
            'package_type': 'standard',
            'destination_country': 'Canada',
            'description': 'Test description',
            'consent': True
        }
        form = DocumentRequestForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_no_consent(self):
        """Test that the form is invalid without consent."""
        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '123456789',
            'document_type': 'birth',
            'package_type': 'standard',
            'destination_country': 'Canada',
            'description': 'Test description',
            'consent': False
        }
        form = DocumentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consent', form.errors)

    def test_form_missing_required_fields(self):
        """Test validation for missing required fields."""
        form = DocumentRequestForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('document_type', form.errors)
