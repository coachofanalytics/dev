from django.test import TestCase, Client
from django.urls import reverse


class EducationViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_course_register_page_renders(self):
		url = reverse('main:course_register')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# expect the full page to contain the main heading
		self.assertContains(resp, 'Course Registration & Payments')

	def test_course_register_fragment_returns(self):
		url = reverse('main:course_register') + '?partial=1'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# the fragment should include the fragment container id
		self.assertContains(resp, 'id="course-register-fragment"')
