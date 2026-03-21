from django.test import TestCase
from django.utils import timezone
from main.models import TrainingCourse


class PerformanceModelsTest(TestCase):
    def test_bulk_create_many_trainingcourses(self):
        # bulk create 200 courses and ensure performance path works
        today = timezone.now().date()
        objs = []
        for i in range(200):
            # provide unique slug to avoid UNIQUE constraint during bulk_create
            objs.append(TrainingCourse(title=f'Perf Course {i}', course_code=f'P{i}', start_date=today, slug=f'perf-{i}'))
        TrainingCourse.objects.bulk_create(objs)
        self.assertEqual(TrainingCourse.objects.count(), 200)
