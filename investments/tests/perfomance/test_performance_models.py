from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from investments.models import investment_content


class InvestmentContentPerformanceTests(TestCase):
    """
    Performance tests ensure the model behaves efficiently
    and avoids unnecessary database queries.
    """

    @classmethod
    def setUpTestData(cls):
        """Create bulk test data once for all tests"""
        records = [
            investment_content(
                title=f"Investment {i}",
                slug=f"investment-{i}",
                description="Performance testing record"
            )
            for i in range(50)
        ]
        investment_content.objects.bulk_create(records)

    def test_single_query_fetch_all(self):
        """
        Ensure fetching all investment contents executes
        only one database query.
        """
        with CaptureQueriesContext(connection) as queries:
            list(investment_content.objects.all())
        self.assertEqual(len(queries), 1)

    def test_filter_by_slug_performance(self):
        """
        Ensure filtering by slug is efficient and does not
        trigger extra queries.
        """
        with CaptureQueriesContext(connection) as queries:
            investment_content.objects.get(slug="investment-10")
        self.assertEqual(len(queries), 1)

    def test_bulk_creation_efficiency(self):
        """
        Ensure bulk creation works correctly and data count matches.
        """
        self.assertEqual(investment_content.objects.count(), 50)

    def test_model_iteration_cost(self):
        """
        Ensure iterating over queryset does not cause N+1 queries.
        """
        with CaptureQueriesContext(connection) as queries:
            for obj in investment_content.objects.all():
                _ = obj.title
        self.assertEqual(len(queries), 1)

    def test_delete_operation_performance(self):
        """
        Ensure delete operation executes minimal queries.
        """
        obj = investment_content.objects.first()
        with CaptureQueriesContext(connection) as queries:
            obj.delete()
        self.assertLessEqual(len(queries), 2)
