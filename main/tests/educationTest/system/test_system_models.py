from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from main.models import Scholarship, TrainingCourse


class SystemModelsTest(TestCase):
    def test_scholarship_status_transitions_and_amount_property(self):
        today = timezone.now().date()
        # past deadline -> CLOSED
        past = Scholarship.objects.create(title='Past', deadline=today - timedelta(days=1), amount_value=1000, amount_currency='USD')
        self.assertEqual(past.status, Scholarship.Status.CLOSED)

        # soon deadline -> CLOSING_SOON
        soon = Scholarship.objects.create(title='Soon', deadline=today + timedelta(days=3), amount_value=500, amount_currency='KES')
        self.assertEqual(soon.status, Scholarship.Status.CLOSING_SOON)

    def test_trainingcourse_progress_and_status_lifecycle(self):
        today = timezone.now().date()
        # upcoming
        future = TrainingCourse.objects.create(title='Future', course_code='FUT1', start_date=today + timedelta(days=5))
        self.assertEqual(future.status, TrainingCourse.Status.UPCOMING)

        # ongoing
        ongoing = TrainingCourse.objects.create(title='Ongoing', course_code='ONG1', start_date=today - timedelta(days=2), end_date=today + timedelta(days=8))
        self.assertEqual(ongoing.status, TrainingCourse.Status.ONGOING)
        pct = ongoing.progress_percentage
        self.assertIsInstance(pct, int)

        # completed
        completed = TrainingCourse.objects.create(title='Done', course_code='DONE1', start_date=today - timedelta(days=10), end_date=today - timedelta(days=1))
        self.assertEqual(completed.status, TrainingCourse.Status.COMPLETED)
