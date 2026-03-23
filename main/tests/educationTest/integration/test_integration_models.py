from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from main.models import TrainingCourse


class IntegrationModelsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_education_training_view_renders_courses(self):
        # create a sample course with a valid date
        today = timezone.now().date()
        TrainingCourse.objects.create(
            title="Integration Course",
            course_code="INT100",
            start_date=today,
            end_date=today + timedelta(days=10),
            slug='integration-int100'
        )

        url = reverse('main:education_training')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # view should include courses in context
        self.assertIn('courses', resp.context)
        self.assertTrue(len(resp.context['courses']) >= 1)
