from django.test import TestCase
from django.utils import timezone
from main.models import TrainingCourse


class EducationPerformanceTest(TestCase):
	def test_bulk_create_trainingcourses_quick(self):
		# simple performance-y test: bulk create 10 training courses and ensure they exist
		objs = []
		for i in range(10):
			objs.append(TrainingCourse(title=f'Course {i}', start_date=timezone.now().date()))
		TrainingCourse.objects.bulk_create(objs)
		self.assertEqual(TrainingCourse.objects.count(), 10)
