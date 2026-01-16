from django.test import TestCase
from main.models import Scholarship
from main.forms import DocumentationRequestForm

class EducationFormsTest(TestCase):
	def test_scholarship_creation_via_model(self):
		# sanity test: creating scholarship with minimal fields
		s = Scholarship.objects.create(title='Mini Scholarship')
		self.assertEqual(s.title, 'Mini Scholarship')

class DocumentationFormsTest(TestCase):
	def test_documentation_request_form_valid(self):
		data = {
			'full_name': 'John Doe',
			'email': 'john@example.com',
			'phone': '+254712345678',
			'document_type': 'birth',
			'package_type': 'standard',
			'destination_country': 'UK',
			'description': 'Test description',
			'consent': True
		}
		form = DocumentationRequestForm(data=data)
		self.assertTrue(form.is_valid())

	def test_documentation_request_form_invalid_no_consent(self):
		data = {
			'full_name': 'John Doe',
			'email': 'john@example.com',
			'phone': '+254712345678',
			'document_type': 'birth',
			'package_type': 'standard',
			'destination_country': 'UK',
			'description': 'Test description',
			'consent': False
		}
		form = DocumentationRequestForm(data=data)
		self.assertFalse(form.is_valid())
		self.assertIn('consent', form.errors)

	def test_documentation_request_form_invalid_email(self):
		data = {
			'full_name': 'John Doe',
			'email': 'invalid-email',
			'phone': '+254712345678',
			'document_type': 'birth',
			'package_type': 'standard',
			'destination_country': 'UK',
			'description': 'Test description',
			'consent': True
		}
		form = DocumentationRequestForm(data=data)
		self.assertFalse(form.is_valid())
		self.assertIn('email', form.errors)
