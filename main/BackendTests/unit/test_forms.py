from django.test import TestCase
from main.models import Scholarship

class EducationFormsTest(TestCase):
	def test_scholarship_creation_via_model(self):
		# sanity test: creating scholarship with minimal fields
		s = Scholarship.objects.create(title='Mini Scholarship')
		self.assertEqual(s.title, 'Mini Scholarship')
		self.assertIsNotNone(s.created_at)
