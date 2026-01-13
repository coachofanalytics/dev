from django.test import TestCase
from django.utils import timezone
from main.models import Scholarship, TrainingCourse, DocumentationRequest


class EducationModelsTest(TestCase):
	def test_create_scholarship_and_str(self):
		# create a scholarship and verify fields and __str__
		s = Scholarship.objects.create(
			title='Test Scholarship',
			provider='Test Provider',
			level='Masters',
			field='Computer Science',
			location='Global',
			deadline=timezone.now().date(),
			amount='$5000',
			status='Open'
		)
		self.assertIsNotNone(s.id)
		self.assertEqual(str(s), 'Test Scholarship')

	def test_create_trainingcourse_and_str(self):
		t = TrainingCourse.objects.create(
			title='Test Course',
			category='Digital Skills',
			duration='6 Weeks',
			format='Online',
			enrollment='Open',
			start_date=timezone.now().date()
		)
		self.assertIsNotNone(t.id)
		self.assertEqual(str(t), 'Test Course')

class DocumentationModelsTest(TestCase):
	def test_create_documentation_request_and_str(self):
		dr = DocumentationRequest.objects.create(
			full_name='Test User',
			email='test@example.com',
			phone='+1234567890',
			document_type='birth',
			destination_country='USA',
			description='Need birth certificate for visa',
			consent=True
		)
		self.assertIsNotNone(dr.id)
		self.assertEqual(str(dr), 'Test User (Birth Certificate)')
		self.assertEqual(dr.status, 'Pending')

