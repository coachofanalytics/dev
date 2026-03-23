from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from main.models import Scholarship, TrainingCourse


class RegressionModelsTest(TestCase):
    def test_scholarship_slug_uniqueness_on_duplicate_titles(self):
        today = timezone.now().date()
        s1 = Scholarship.objects.create(title='Duplicate Title', deadline=today + timedelta(days=10))
        s2 = Scholarship.objects.create(title='Duplicate Title', deadline=today + timedelta(days=15))
        self.assertNotEqual(s1.slug, s2.slug)

    def test_trainingcourse_enrollment_closes_when_full(self):
        today = timezone.now().date()
        tc = TrainingCourse.objects.create(title='Reg Course', course_code='RG1', max_students=2, enrolled_students=2, start_date=today)
        # after save enrollment should be CLOSED
        tc.refresh_from_db()
        self.assertEqual(tc.enrollment, TrainingCourse.Enrollment.CLOSED)
