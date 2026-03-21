from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from main.models import Scholarship, TrainingCourse


class UnitModelsTest(TestCase):
    def test_scholarship_amount_format_and_status_and_slug(self):
        future_date = timezone.now().date() + timedelta(days=30)
        s = Scholarship.objects.create(
            title="Test Scholarship",
            amount_value=1500.5,
            amount_currency='USD',
            deadline=future_date,
        )

        # amount property should format USD
        self.assertEqual(s.amount, "$1,500.50")

        # status should be OPEN for far future deadline
        self.assertEqual(s.status, Scholarship.Status.OPEN)

        # slug auto-generated and non-empty
        self.assertTrue(s.slug)

    def test_trainingcourse_slug_status_and_spots(self):
        today = timezone.now().date()
        tc = TrainingCourse.objects.create(
            title="Intro to Testing",
            course_code="TST101",
            max_students=10,
            enrolled_students=3,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=9),
            slug='intro-testing-tst101'
        )

        # slug generation (we provided slug) includes course code fragment
        self.assertIn('tst101', tc.slug)

        # status should be ONGOING for current date
        self.assertEqual(tc.status, TrainingCourse.Status.ONGOING)

        # spots available computed correctly
        self.assertEqual(tc.spots_available, 7)

        # progress percentage is an int 0-100
        pct = tc.progress_percentage
        self.assertIsInstance(pct, int)
        self.assertGreaterEqual(pct, 0)
        self.assertLessEqual(pct, 100)
