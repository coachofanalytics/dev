import time
from django.test import TestCase
from main.models import ServiceCategory


class ServiceCategoryPerformanceTest(TestCase):
    """
    Performance tests for ServiceCategory model.
    These tests measure basic execution time for inserts and queries.

    NOTE:
    - Performance tests can vary depending on machine/database.
    - Keep thresholds reasonable to avoid false failures.
    """

    def test_bulk_create_service_categories_performance(self):
        """
        Ensure bulk creation of many ServiceCategory records runs within a reasonable time.
        """
        start_time = time.time()

        data = [
            ServiceCategory(
                service=i,
                name=f"Category {i}",
                slug=f"category-{i}",
                description=f"Sample description for category {i}",
                is_active=True,
                is_featured=(i % 5 == 0),
            )
            for i in range(1, 1001)
        ]

        ServiceCategory.objects.bulk_create(data)

        end_time = time.time()
        elapsed = end_time - start_time

        self.assertEqual(ServiceCategory.objects.count(), 1000)

        # ✅ Adjust threshold if needed depending on your environment
        self.assertLess(
            elapsed, 2.5,
            f"Bulk create took too long: {elapsed:.2f} seconds"
        )

    def test_filter_query_performance(self):
        """
        Ensure filtering active and featured categories runs fast.
        """
        # Create sample data
        ServiceCategory.objects.bulk_create([
            ServiceCategory(
                service=i,
                name=f"Perf Category {i}",
                slug=f"perf-category-{i}",
                description="Performance test record",
                is_active=True,
                is_featured=(i % 10 == 0)
            )
            for i in range(1, 2001)
        ])

        start_time = time.time()

        featured = list(
            ServiceCategory.objects.filter(is_active=True, is_featured=True)
        )

        end_time = time.time()
        elapsed = end_time - start_time

        self.assertTrue(len(featured) > 0)

        # ✅ Query should be fast
        self.assertLess(
            elapsed, 0.5,
            f"Filter query took too long: {elapsed:.2f} seconds"
        )

    def test_slug_lookup_performance(self):
        """
        Ensure lookup by slug is fast (slug is indexed/unique).
        """
        ServiceCategory.objects.bulk_create([
            ServiceCategory(
                service=i,
                name=f"Slug Category {i}",
                slug=f"slug-category-{i}",
                description="Slug lookup test",
                is_active=True,
                is_featured=False
            )
            for i in range(1, 2001)
        ])

        start_time = time.time()

        obj = ServiceCategory.objects.get(slug="slug-category-1999")

        end_time = time.time()
        elapsed = end_time - start_time

        self.assertEqual(obj.slug, "slug-category-1999")

        # ✅ Lookup should be extremely fast
        self.assertLess(
            elapsed, 0.2,
            f"Slug lookup took too long: {elapsed:.2f} seconds"
        )
