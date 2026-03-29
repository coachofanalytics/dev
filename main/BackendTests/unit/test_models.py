from django.test import TestCase
from django.utils import timezone
from main.models import Scholarship, TrainingCourse, Testimonial


class EducationModelsTest(TestCase):
	def test_create_scholarship_and_str(self):
		# create a scholarship and verify fields and __str__
		s = Scholarship.objects.create(
			title='Test Scholarship',
			provider='Test Provider',
			level='Masters',
			field='Computer Science',
			location='Global',
			deadline=timezone.now().date(),
			amount='$5000',
			status='Open'
		)
		self.assertIsNotNone(s.id)
		self.assertEqual(str(s), 'Test Scholarship')

	def test_create_trainingcourse_and_str(self):
		t = TrainingCourse.objects.create(
			title='Test Course',
			category='Digital Skills',
			duration='6 Weeks',
			format='Online',
			enrollment='Open',
			start_date=timezone.now().date()
		)
		self.assertIsNotNone(t.id)
		self.assertEqual(str(t), 'Test Course')


from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date


class TestimonialModelTest(TestCase):

    def setUp(self):
        # Create a fake image file
        self.image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )

        self.testimonial = Testimonial.objects.create(
            name="John Doe",
            position="Developer",
            organization="Tech Corp",
            testimonial="This is a great product!",
            image=self.image,
        )

    def test_testimonial_creation(self):
        """Test if the model instance is created correctly"""
        self.assertEqual(self.testimonial.name, "John Doe")
        self.assertEqual(self.testimonial.position, "Developer")
        self.assertEqual(self.testimonial.organization, "Tech Corp")
        self.assertEqual(self.testimonial.testimonial, "This is a great product!")
        self.assertTrue(self.testimonial.image.name.startswith("Testimonial/"))

    def test_auto_date_field(self):
        """Test if date is auto-set on creation"""
        self.assertEqual(self.testimonial.date, date.today())

    def test_str_method(self):
        """Test __str__ returns correct format"""
        self.assertEqual(
            str(self.testimonial),
            "Testimonial from John Doe"
        )
