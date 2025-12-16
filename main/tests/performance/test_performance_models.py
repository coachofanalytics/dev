from django.test import TestCase
from django.utils import timezone
from main.models import Scholarship, TrainingCourse


class EducationPerformanceModelsTest(TestCase):
	def test_bulk_create_scholarships(self):
		# bulk create 200 scholarships to exercise DB insert performance (kept moderate to avoid CI slowness)
		objs = []
		today = timezone.now().date()
		for i in range(200):
			objs.append(Scholarship(title=f'Perf Scholarship {i}', provider='Perf', deadline=today))
		Scholarship.objects.bulk_create(objs)
		self.assertEqual(Scholarship.objects.count(), 200)

	def test_bulk_create_trainingcourses(self):
		objs = []
		for i in range(200):
			objs.append(TrainingCourse(title=f'Perf Course {i}'))
		TrainingCourse.objects.bulk_create(objs)
		self.assertEqual(TrainingCourse.objects.count(), 200)

