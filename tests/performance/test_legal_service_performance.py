from django.test import TestCase
from django.urls import reverse

from main.models import LegalService


class LegalServicePerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(60):
            LegalService.objects.create(
                title=f"Service {i}",
                category="visa" if i % 2 == 0 else "citizenship",
                description="Perf test service",
                order=i,
                is_active=True,
            )

    def test_guidance_page_query_count_is_reasonable(self):
        with self.assertNumQueries(1):
            response = self.client.get(reverse("main:legal_immigration_guidance"))
            self.assertEqual(response.status_code, 200)

    def test_test_page_query_count_is_reasonable(self):
        with self.assertNumQueries(1):
            response = self.client.get(reverse("main:legal_service_test"))
            self.assertEqual(response.status_code, 200)
