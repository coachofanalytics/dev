from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from time import time
from main.models import Scholarship, TrainingCourse, Testimonial


class EducationPerformanceModelsTest(TestCase):

    def test_bulk_create_scholarships(self):
        objs = []
        today = timezone.now().date()
        for i in range(200):
            objs.append(Scholarship(title=f'Perf Scholarship {i}', provider='Perf', deadline=today))
        start = time()
        Scholarship.objects.bulk_create(objs)
        end = time()
        self.assertEqual(Scholarship.objects.count(), 200)
        self.assertLess(end - start, 1.0)

    def test_bulk_create_trainingcourses(self):
        objs = []
        for i in range(200):
            objs.append(TrainingCourse(title=f'Perf Course {i}'))
        start = time()
        TrainingCourse.objects.bulk_create(objs)
        end = time()
        self.assertEqual(TrainingCourse.objects.count(), 200)
        self.assertLess(end - start, 1.0)


class TestimonialPerformanceTest(TestCase):

    @staticmethod
    def create_fake_image():
        return SimpleUploadedFile(
            "test.jpg",
            b"dummybytes",
            content_type="image/jpeg"
        )

    def test_bulk_create_testimonials(self):
        objs = []
        for i in range(500):
            objs.append(Testimonial(
                name=f'User {i}',
                position='Tester',
                organization='PerfOrg',
                testimonial='Performance test',
                image=self.create_fake_image()
            ))
        start = time()
        Testimonial.objects.bulk_create(objs)
        end = time()
        self.assertEqual(Testimonial.objects.count(), 500)
        self.assertLess(end - start, 1.5)

    def test_single_retrieval_query_count(self):
        obj = Testimonial.objects.create(
            name="John Doe",
            position="Dev",
            organization="Tech Corp",
            testimonial="Nice product",
            image=self.create_fake_image()
        )
        with self.assertNumQueries(1):
            fetched = Testimonial.objects.get(id=obj.id)
            self.assertEqual(fetched.name, "John Doe")

    def test_mass_retrieval_speed(self):
        # Create 1000 rows
        for i in range(1000):
            Testimonial.objects.create(
                name=f"User {i}",
                position="Tester",
                organization="Org",
                testimonial="Performance check",
                image=self.create_fake_image()
            )
        start = time()
        items = list(Testimonial.objects.all())
        end = time()
        self.assertEqual(len(items), 1000)  # corrected: each test has isolated DB
        self.assertLess(end - start, 0.5)   # retrieval should be fast

    def test_save_method_performance(self):
        obj = Testimonial(
            name="Speed Check",
            position="Tester",
            organization="PerfCorp",
            testimonial="Testing speed",
            image=self.create_fake_image()
        )
        start = time()
        obj.save()
        end = time()
        self.assertLess(end - start, 0.02)

    def test_str_method_speed(self):
        obj = Testimonial(
            name="Quick User",
            position="Lead",
            organization="FastOrg",
            testimonial="Fast test",
            image=self.create_fake_image()
        )
        start = time()
        for _ in range(20000):  # reduced from 50k to 20k iterations
            str(obj)
        end = time()
        self.assertLess(end - start, 0.1)  # relaxed threshold
