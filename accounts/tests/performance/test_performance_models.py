import time
import random
from datetime import timedelta
from django.test import TestCase
from django.db import connection, transaction
from django.utils import timezone
from datetime import time as dt_time
from accounts.models import Tracker # Ensure this matches your app name
from django.db.models import Sum

# Define constants for testing scale
RECORD_COUNT = 5000  # Number of records to create for the test
EMPLOYEES = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
CATEGORIES = ["Development", "Testing", "Meetings", "Training"]

class TrackerPerformanceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Set up a large dataset (5000 records) once for all performance tests.
        """
        cls.start_time = timezone.now()
        print(f"\n--- Setting up {RECORD_COUNT} test records... ---")
        
        # 1. Prepare data list
        trackers_to_create = []
        for i in range(RECORD_COUNT):
            # Calculate naive date
            naive_date = cls.start_time.date() - timedelta(days=random.randint(1, 30))
            
            # FIX for RuntimeWarning: Convert to timezone-aware datetime at midnight
            login_date = timezone.make_aware(timezone.datetime.combine(naive_date, dt_time.min))
            
            trackers_to_create.append(
                Tracker(
                    category=random.choice(CATEGORIES),
                    sub_category=random.choice(["A", "B", "C"]),
                    task=f"Task {i % 10}",
                    plan="Standard plan detail",
                    employee=random.choice(EMPLOYEES),
                    login_date=login_date, # Use the timezone-aware datetime
                    start_time=dt_time(9, 0, 0),
                    duration=random.randint(30, 180),
                    time=random.randint(60, 240)
                )
            )

        # 2. Bulk Create (efficient insertion)
        with transaction.atomic():
            Tracker.objects.bulk_create(trackers_to_create, batch_size=1000)

        cls.creation_end_time = timezone.now()
        duration = (cls.creation_end_time - cls.start_time).total_seconds()
        print(f"Creation Time: {duration:.4f} seconds.")
        
        # FIX for TypeError: Use Python's built-in assert instead of TestCase.assertEqual()
        assert Tracker.objects.count() == RECORD_COUNT, f"Expected {RECORD_COUNT} records, but found {Tracker.objects.count()}"
        
    def get_query_info(self, query_set):
        """Helper to print query and execution time (optional, for manual analysis)"""
        # This function requires DEBUG=True in settings to log queries
        pass

    ## --- Performance Test Cases ---

    def test_01_bulk_creation_speed(self):
        """
        Tests the time taken to create the large dataset (measured in setUpTestData).
        This test serves as a simple sanity check/benchmark for the setup phase.
        """
        duration = (self.creation_end_time - self.start_time).total_seconds()
        print(f"\n[PERF] Bulk Creation of {RECORD_COUNT} records took {duration:.4f}s")
        # Assertions here are tricky. We can only assert it was fast enough.
        # Arbitrary threshold: should be under 2 seconds for 5k records locally.
        self.assertLess(duration, 2.0, "Bulk creation is too slow.")


    def test_02_simple_filter_query_speed(self):
        """
        Tests the speed of a simple filter query on an indexed field (PK/ID).
        """
        start = time.time()
        # Querying an internal ID (indexed by default)
        result = Tracker.objects.filter(id=random.randint(1, RECORD_COUNT)).first()
        end = time.time()
        
        elapsed = end - start
        print(f"\n[PERF] Simple Indexed Filter took: {elapsed:.6f}s")
        self.assertIsNotNone(result)
        # Should be almost instantaneous
        self.assertLess(elapsed, 0.005) 


    def test_03_filter_on_unindexed_field_speed(self):
        """
        Tests the speed of filtering on the 'employee' field (CharField).
        This is the benchmark to show improvement if you add an index.
        """
        start = time.time()
        # Querying a common field
        result_count = Tracker.objects.filter(employee="Bob").count()
        end = time.time()
        
        elapsed = end - start
        print(f"\n[PERF] Filter on 'employee' took: {elapsed:.6f}s (Count: {result_count})")
        self.assertGreater(result_count, 0)
        # Arbitrary threshold: should be under 0.05 seconds for 5k records
        self.assertLess(elapsed, 0.05)
        
        
    def test_04_complex_aggregation_speed(self):
        """
        Tests the speed of a complex query involving filtering and aggregation (Sum).
        """
        start = time.time()
        
        # Calculate the total duration for Development tasks done by Alice
        aggregation = Tracker.objects.filter(
            employee="Alice",
            category="Development"
        ).aggregate(total_duration=Sum('duration'))
        
        end = time.time()
        
        elapsed = end - start
        print(f"\n[PERF] Complex Aggregation (Filter + Sum) took: {elapsed:.6f}s")
        self.assertIn('total_duration', aggregation)
        # Arbitrary threshold: should be under 0.1 seconds for 5k records
        self.assertLess(elapsed, 0.1)