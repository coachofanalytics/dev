from django.test import TestCase
from django.utils import timezone
from datetime import time, timedelta
import time as timer

from main.models import Bookings


class BookingPerformanceTests(TestCase):

    def setUp(self):
        self.sample_data = [
            Bookings(
                name=f"User {i}",
                email=f"user{i}@example.com",
                phone="1234567890",
                service_type="Consultation",
                preferred_date=timezone.now().date(),
                preferred_time=time(10, 0),
            )
            for i in range(1000)
        ]
    def test_bulk_create_performance(self):
        start = timer.time()

        Bookings.objects.bulk_create(self.sample_data)

        duration = timer.time() - start
        print(f"Bulk insert of 1000 records took {duration:.4f} seconds")

        self.assertEqual(Bookings.objects.count(), 1000)