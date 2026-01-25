from django.test import TestCase
from main.models import ServiceCategory


class ServiceCategoryModelTest(TestCase):

    def test_create_service_category(self):
        """ServiceCategory should be created successfully"""
        category = ServiceCategory.objects.create(
            service=101,
            name="Data Analytics Training",
            description="Practical training in Excel, SQL, Power BI, Tableau and Python."
        )

        self.assertEqual(category.service, 101)
        self.assertEqual(category.name, "Data Analytics Training")
        self.assertIsNotNone(category.id)

    def test_slug_auto_generated(self):
        """Slug should be auto-generated from name if not provided"""
        category = ServiceCategory.objects.create(
            service=102,
            name="Automation & AI Integration",
            description="AI workflow automations and OpenAI integrations."
        )

        self.assertEqual(category.slug, "automation-ai-integration")

    def test_default_is_active(self):
        """is_active should default to True"""
        category = ServiceCategory.objects.create(name="Web Development (Django)")
        self.assertTrue(category.is_active)

    def test_default_is_featured(self):
        """is_featured should default to False"""
        category = ServiceCategory.objects.create(name="Research & Statistical Consulting")
        self.assertFalse(category.is_featured)

    def test_str_returns_name(self):
        """__str__ should return the category name"""
        category = ServiceCategory.objects.create(name="Dashboard & Reporting Services")
        self.assertEqual(str(category), "Dashboard & Reporting Services")
