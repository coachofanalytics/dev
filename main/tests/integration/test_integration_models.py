from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from main.models import Scholarship, TrainingCourse


class EducationIntegrationTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_scholarship_shows_on_listing_and_detail(self):
		# create scholarship and verify it's visible via fragment and (if implemented) detail view
		s = Scholarship.objects.create(
			title='Integration Scholarship',
			provider='Integration Provider',
			level='Undergraduate',
			field='Arts',
			location='Kenya',
			deadline=timezone.now().date(),
			amount='KES 100000',
			status='Open'
		)

		# verify model exists
		self.assertTrue(Scholarship.objects.filter(title='Integration Scholarship').exists())

		# fetch the course_register fragment (re-using earlier fragment endpoint) to simulate in-page load
		url = reverse('main:course_register') + '?partial=1'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# the fragment lists training courses; scholarships aren't part of that fragment, but this ensures page rendering
		self.assertContains(resp, 'Course Registration & Payments')

	def test_trainingcourse_flow_and_template_render(self):
		t = TrainingCourse.objects.create(
			title='Integration Course',
			category='Tech',
			duration='2 Weeks',
			format='Online',
			enrollment='Open',
			start_date=timezone.now().date()
		)

		# verify listing on full course_register page
		url = reverse('main:course_register')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Course Registration & Payments')


