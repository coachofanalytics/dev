from django.test import TestCase
from django.db import IntegrityError
from main.models import ServiceCategory


class ServiceCategoryRegressionModelTest(TestCase):
    """
    Regression tests for ServiceCategory model.
    These tests protect core behaviors from breaking in future updates.
    """

    def test_slug_is_auto_generated_from_name(self):
        """
        Slug must auto-generate from name if slug is not given.
        """
        category = ServiceCategory.objects.create(
            service=301,
            name="Data Science & Machine Learning",
            description="ML training module"
        )
        self.assertEqual(category.slug, "data-science-machine-learning")

    def test_slug_does_not_change_when_name_changes(self):
        """
        If slug was already created, changing name should NOT overwrite slug.
        """
        category = ServiceCategory.objects.create(
            service=302,
            name="Web Development",
            description="Django services"
        )

        old_slug = category.slug
        category.name = "Web Development Updated"
        category.save()

        category.refresh_from_db()
        self.assertEqual(category.slug, old_slug)

    def test_defaults_are_correct(self):
        """
        Default values must remain consistent.
        """
        category = ServiceCategory.objects.create(name="Automation Services")
        self.assertTrue(category.is_active)
        self.assertFalse(category.is_featured)

    def test_can_set_is_featured_true(self):
        """
        is_featured can be updated and saved.
        """
        category = ServiceCategory.objects.create(name="Dashboards")
        category.is_featured = True
        category.save()

        category.refresh_from_db()
        self.assertTrue(category.is_featured)

    def test_unique_slug_constraint(self):
        """
        Slug must remain unique in the database.
        """
        ServiceCategory.objects.create(
            name="Reporting",
            slug="reporting"
        )

        with self.assertRaises(IntegrityError):
            ServiceCategory.objects.create(
                name="Reporting Duplicate",
                slug="reporting"
            )

    def test_filter_active_categories(self):
        """
        Filtering active categories must work.
        """
        ServiceCategory.objects.create(name="Active Cat", is_active=True)
        ServiceCategory.objects.create(name="Inactive Cat", is_active=False)

        active_count = ServiceCategory.objects.filter(is_active=True).count()
        inactive_count = ServiceCategory.objects.filter(is_active=False).count()

        self.assertEqual(active_count, 1)
        self.assertEqual(inactive_count, 1)

    def test_string_representation(self):
        """
        __str__ must return name.
        """
        category = ServiceCategory.objects.create(name="Career Support")
        self.assertEqual(str(category), "Career Support")
