from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from datetime import date
from main.models import Testimonial


class TestimonialRegressionTests(TestCase):

    def setUp(self):
        self.image = SimpleUploadedFile(
            "test.jpg",
            b"dummy_image",
            content_type="image/jpeg"
        )

        self.testimonial = Testimonial.objects.create(
            name="Alice Smith",
            position="Manager",
            organization="Global Tech",
            testimonial="Excellent service!",
            image=self.image,
        )

    def test_model_fields_integrity(self):
        self.assertEqual(self.testimonial.name, "Alice Smith")
        self.assertEqual(self.testimonial.position, "Manager")
        self.assertEqual(self.testimonial.organization, "Global Tech")
        self.assertEqual(self.testimonial.testimonial, "Excellent service!")
        self.assertTrue(self.testimonial.image.name.startswith("Testimonial/"))

    def test_auto_date_regression(self):
        self.assertEqual(self.testimonial.date, date.today())

    def test_str_method_regression(self):
        self.assertEqual(str(self.testimonial), "Testimonial from Alice Smith")

    def test_save_method_regression(self):
        old_date = self.testimonial.date
        self.testimonial.save()
        self.assertEqual(self.testimonial.date, old_date)

    def test_required_fields_regression(self):
        test = Testimonial(
            name="",
            position="CEO",
            organization="CompanyX",
            testimonial="",
            image=None
        )

        with self.assertRaises(ValidationError):
            test.full_clean()
