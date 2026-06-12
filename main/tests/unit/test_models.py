from django.test import TestCase
from main.models import LegalService


class LegalServiceModelTest(TestCase):

    def setUp(self):
        self.legal_service = LegalService.objects.create(
            title="Visa Assistance",
            category="visa",
            description="Help with visa applications and residency permits.",
            image_url="https://example.com/image.jpg",
            features=[
                "Visa application support",
                "Residency permit guidance",
                "Document verification"
            ],
            cta_button_text="Apply Now",
            cta_button_url="https://example.com/apply",
            order=1,
            is_active=True
        )

    def test_legal_service_creation(self):
        """Test if LegalService object is created correctly"""
        service = self.legal_service

        self.assertEqual(service.title, "Visa Assistance")
        self.assertEqual(service.category, "visa")
        self.assertEqual(
            service.description,
            "Help with visa applications and residency permits."
        )
        self.assertEqual(
            service.image_url,
            "https://example.com/image.jpg"
        )
        self.assertEqual(
            service.features,
            [
                "Visa application support",
                "Residency permit guidance",
                "Document verification"
            ]
        )
        self.assertEqual(service.cta_button_text, "Apply Now")
        self.assertEqual(
            service.cta_button_url,
            "https://example.com/apply"
        )
        self.assertEqual(service.order, 1)
        self.assertTrue(service.is_active)

    def test_string_representation(self):
        """Test __str__ method"""
        self.assertEqual(str(self.legal_service), "Visa Assistance")

    def test_default_values(self):
        """Test model default values"""
        service = LegalService.objects.create(
            title="Citizenship Support",
            category="citizenship",
            description="Support for citizenship applications."
        )

        self.assertEqual(service.cta_button_text, "Learn More")
        self.assertEqual(service.order, 0)
        self.assertTrue(service.is_active)
        self.assertEqual(service.features, [])

    def test_meta_ordering(self):
        """Test model ordering"""
        self.assertEqual(LegalService._meta.ordering, ['order'])

    def test_verbose_names(self):
        """Test verbose names in Meta"""
        self.assertEqual(
            LegalService._meta.verbose_name,
            "Legal Service"
        )
        self.assertEqual(
            LegalService._meta.verbose_name_plural,
            "Legal Services"
        )