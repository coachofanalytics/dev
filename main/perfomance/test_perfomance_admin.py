import time
from datetime import time as dt_time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from main.models import ClientAvailability


User = get_user_model()


class ClientAvailabilityAdminPerformanceTest(TestCase):

    def setUp(self):

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123"
        )

        self.client = Client()
        self.client.login(username="admin", password="admin123")

        # Create many records
        records = [
            ClientAvailability(
                client=i,
                day="Monday",
                start_time=dt_time(9, 0),
                end_time=dt_time(10, 0),
                time_standards="EAT",
                topic="Consultation"
            )
            for i in range(1000)
        ]

        ClientAvailability.objects.bulk_create(records)

    def test_admin_list_page_performance(self):
        """Test admin list page loading speed"""

        start = time.time()

        response = self.client.get("/admin/main/clientavailability/")

        end = time.time()

        duration = end - start

        self.assertEqual(response.status_code, 200)

        print(f"\nAdmin list page loaded in {duration:.4f} seconds")

    def test_admin_query_performance(self):
        """Test admin query speed"""

        start = time.time()

        count = ClientAvailability.objects.filter(day="Monday").count()

        end = time.time()

        duration = end - start

        self.assertEqual(count, 1000)

        print(f"\nAdmin query took {duration:.4f} seconds")