import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from document_processing.models import DocumentApplication

User = get_user_model()


class DocumentApplicationPerformanceTest(TestCase):

    def test_bulk_create_performance(self):
        user = User.objects.create_user(
            username="perfuser",
            password="password123"
        )

        applications = []

        for i in range(1000):
            applications.append(
                DocumentApplication(
                    user=user,
                    service_type="passport",
                    first_name=f"User{i}",
                    last_name="Test",
                    id_number=f"ID{i}",
                    sub_county="Gasabo"
                )
            )

        start = time.time()

        DocumentApplication.objects.bulk_create(applications)

        duration = time.time() - start

        self.assertEqual(
            DocumentApplication.objects.count(),
            1000
        )

        self.assertLess(duration, 5)