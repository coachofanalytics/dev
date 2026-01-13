from django.test import TestCase, Client
from django.urls import reverse

class DocumentationRegressionTemplatesTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_index_template_has_document_form_fields(self):
		url = reverse('main:services_spa')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		
		# Check for specific form fields and IDs as expected by the JS in index.html
		self.assertContains(resp, 'id="document_type"')
		self.assertContains(resp, 'id="full_name"')
		self.assertContains(resp, 'id="email"')
		self.assertContains(resp, 'id="id_phone"')
		self.assertContains(resp, 'id="destination_country"')
		self.assertContains(resp, 'id="consent"')
		
		# Check for the submit button
		self.assertContains(resp, 'type="submit"')
		
		# Check for the feedback message container
		self.assertContains(resp, 'id="form-message"')
