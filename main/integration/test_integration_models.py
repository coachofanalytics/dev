from django.test import TestCase
from django.db import IntegrityError
from main.models import ServiceCategory


class ServiceCategoryIntegrationModelTest(TestCase):
    """
    Integration tests for ServiceCategory model.

    Focus:
    - Database save + retrieval
    - Slug uniqueness behavior
    - Full object lifecycle operations (create, update, deactivate)
    """

    def test_create_and_retrieve_service_category(self):
        """Create category and confirm it is saved and retrievable from DB"""
        category = ServiceCategory.objects.create(
            service=201,
            name="Data Analytics Training",
            description="Practical training in Excel, SQL, Power BI and Python.",
            is_active=True,
            is_featured=True
        )

        saved = ServiceCategory.objects.get(id=category.id)

        self.assertEqual(saved.name, "Data Analytics Training")
        self.assertEqual(saved.service, 201)
        self.assertTrue(saved.is_active)
        self.assertTrue(saved.is_featured)
        self.assertEqual(saved.slug, "data-analytics-training")

    def test_update_service_category(self):
        """Update category fields and confirm DB reflects changes"""
        category = ServiceCategory.objects.create(
            service=202,
            name="Automation & AI Integration",
            description="Initial description."
        )

        category.description = "Updated description with more details."
