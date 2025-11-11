from django.test import TestCase
from django.utils import timezone
from main.models import Scholarship, TrainingCourse


class EducationModelsRegressionTest(TestCase):
	def test_scholarship_full_lifecycle(self):
		# create
		s = Scholarship.objects.create(title='Reg Scholarship', provider='Reg Provider', amount='1000')
		self.assertIsNotNone(s.pk)
		self.assertEqual(str(s), 'Reg Scholarship')

		# update
		s.status = 'Closed'
		s.save()
		s.refresh_from_db()
		self.assertEqual(s.status, 'Closed')

		# query/filter
		qs = Scholarship.objects.filter(provider__icontains='Reg')
		self.assertTrue(qs.exists())

		# delete
		pk = s.pk
		s.delete()
		self.assertFalse(Scholarship.objects.filter(pk=pk).exists())

	def test_trainingcourse_full_lifecycle(self):
		t = TrainingCourse.objects.create(title='Reg Course', category='Test', start_date=timezone.now().date())
		self.assertIsNotNone(t.pk)
		self.assertEqual(str(t), 'Reg Course')

		# update
		t.enrollment = 'Closed'
		t.save()
		t.refresh_from_db()
		self.assertEqual(t.enrollment, 'Closed')

		# bulk operations: create additional entries and ensure queries work
		TrainingCourse.objects.create(title='Reg Course 2')
		TrainingCourse.objects.create(title='Reg Course 3')
		self.assertGreaterEqual(TrainingCourse.objects.count(), 3)
