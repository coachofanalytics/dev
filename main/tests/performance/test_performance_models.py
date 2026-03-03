# from django.test import TestCase
# from main.models import Location


# class LocationPerformanceModelTest(TestCase):
#     """
#     Performance tests for Location model.
#     Focus: bulk inserts and query efficiency.
#     """

#     def test_bulk_create_locations(self):
#         locations = [
#             Location(
#                 zipcode=f"{10000 + i}",
#                 city="City",
#                 state="State",
#                 country="Kenya"
#             )
#             for i in range(1000)
#         ]

#         Location.objects.bulk_create(locations)

#         self.assertEqual(Location.objects.count(), 1000)

#     def test_filter_performance_by_country(self):
#         Location.objects.bulk_create([
#             Location(zipcode="00100", city="Nairobi", state="Nairobi County", country="Kenya"),
#             Location(zipcode="20100", city="Nakuru", state="Nakuru County", country="Kenya"),
#             Location(zipcode="94105", city="San Francisco", state="California", country="USA"),
#         ])

#         kenya_locations = Location.objects.filter(country="Kenya")
#         self.assertEqual(kenya_locations.count(), 2)

#         # tests/test_performance_models.py
import time as pytime
from datetime import time
from django.test import TestCase
import time

from main.models import ClientAvailability,Search


class ClientAvailabilityPerformanceTests(TestCase):
    """
    Performance tests should be conservative and avoid flakiness.
    We measure relative performance and enforce reasonable upper bounds.
    """

    def test_bulk_create_is_fast_enough(self):
        n = 2000  # adjust based on your CI environment if needed
        rows = [
            ClientAvailability(
                client=99,
                day="Friday",
                start_time=time(9, 0),
                end_time=time(10, 0),
                time_standards="EAT",
                topic=f"Slot {i}",
            )
            for i in range(n)
        ]

        t0 = pytime.perf_counter()
        ClientAvailability.objects.bulk_create(rows, batch_size=500)
        elapsed = pytime.perf_counter() - t0

        # Sanity checks
        self.assertEqual(ClientAvailability.objects.count(), n)

        # Guardrail: keep generous to reduce CI flakiness.
        # If this fails, your DB/test runner is unusually slow or batch_size is too small.
        self.assertLess(elapsed, 3.5)

    def test_query_by_client_and_day_is_reasonable(self):
        # Prepare a moderate dataset
        n = 3000
        ClientAvailability.objects.bulk_create([
            ClientAvailability(
                client=1 if i % 2 == 0 else 2,
                day="Monday" if i % 3 == 0 else "Tuesday",
                start_time=time(9, 0),
                end_time=time(10, 0),
                time_standards="EAT",
                topic=f"T{i}",
            )
            for i in range(n)
        ], batch_size=500)

        t0 = pytime.perf_counter()
        qs = ClientAvailability.objects.filter(client=1, day="Monday")
        count = qs.count()
        elapsed = pytime.perf_counter() - t0

        self.assertGreater(count, 0)
        self.assertLess(elapsed, 0.75)



class SearchPerformanceTest(TestCase):

    def test_bulk_insert_performance(self):
        start_time = time.time()

        for i in range(1000):
            Search.objects.create(
                topic=f"Topic {i}",
                question="Sample question"
            )

        duration = time.time() - start_time
        self.assertLess(duration, 5)