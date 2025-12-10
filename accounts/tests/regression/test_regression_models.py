from django.test import TestCase
from django.db.models import Sum, F
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import time, timedelta
from accounts.models import Tracker  # Ensure this matches your app name

class TrackerRegressionTest(TestCase):

    def setUp(self):
        """
        Setup data for regression and edge-case testing.
        Using a single base date for consistency.
        """
        self.test_date = timezone.make_aware(timezone.datetime(2025, 12, 10, 0, 0, 0))
        self.duration_data = 120  # Duration in minutes
        self.time_data = 7200    # Time in seconds (120 minutes * 60 seconds)

        # Base record 1: Standard entry
        self.tracker_standard = Tracker.objects.create(
            category="Development",
            sub_category="Backend",
            task="Feature X",
            plan="Implement API",
            employee="Alice",
            login_date=self.test_date,
            start_time=time(9, 0, 0),
            duration=self.duration_data,
            time=self.time_data
        )

    # --- 1. Regression Tests for Common Fixes (e.g., Naive Datetime) ---

    def test_regression_timezone_aware_login_date(self):
        """
        Regression check to ensure login_date is saved as timezone-aware, 
        preventing past RuntimeWarnings or database errors.
        """
        retrieved_tracker = Tracker.objects.get(pk=self.tracker_standard.pk)
        self.assertTrue(timezone.is_aware(retrieved_tracker.login_date))
        self.assertEqual(retrieved_tracker.login_date, self.test_date)

    # --- 2. Boundary and Edge Cases ---

    def test_regression_employee_null_allowed(self):
        """
        Test the employee field can explicitly be saved as NULL (null=True).
        (Regression check for a potential past failure if null=True was not honored)
        """
        tracker_null = Tracker.objects.create(
            category="Admin",
            sub_category="Setup",
            task="Onboarding",
            plan="Initial setup for new employee",
            employee=None, # Explicitly setting to None
            login_date=self.test_date,
            start_time=time(8, 0, 0),
            duration=30,
            time=1800
        )
        retrieved_tracker = Tracker.objects.get(pk=tracker_null.pk)
        self.assertIsNone(retrieved_tracker.employee)

    def test_regression_max_length_boundary(self):
        """
        Test saving fields exactly at their maximum length (25 characters).
        (Regression check for off-by-one errors)
        """
        max_str = 'X' * 25
        
        Tracker.objects.create(
            category=max_str,
            sub_category=max_str,
            task=max_str,
            plan="Short plan",
            employee="Test Max",
            login_date=self.test_date,
            start_time=time(10, 0, 0),
            duration=1,
            time=60
        )
        # Test passes if no ValidationError or database error is raised.
        retrieved_tracker = Tracker.objects.latest('id')
        self.assertEqual(retrieved_tracker.category, max_str)


    def test_regression_zero_duration_and_time(self):
        """
        Test saving an entry where duration and time are zero (e.g., task logged but no work done).
        (Since duration is an IntegerField and time is a PositiveIntegerField, time must be >= 0)
        """
        Tracker.objects.create(
            category="Admin",
            sub_category="Planning",
            task="No work",
            plan="Planned future tasks",
            employee="Zero Test",
            login_date=self.test_date,
            start_time=time(12, 0, 0),
            duration=0,
            time=0 
        )
        # Test passes if no ValidationError or database error is raised.
        retrieved_tracker = Tracker.objects.latest('id')
        self.assertEqual(retrieved_tracker.duration, 0)
        self.assertEqual(retrieved_tracker.time, 0)

    # --- 3. Functional Regression (Testing saved business logic) ---

    def test_regression_arithmetic_aggregation(self):
        """
        Regression check to ensure the ORM's F() expressions and Sum() aggregation 
        still work correctly across the model's integer fields.
        """
        # Create a second record
        Tracker.objects.create(
            category="Development",
            sub_category="Frontend",
            task="CSS fixes",
            plan="Fix styling",
            employee="Alice",
            login_date=self.test_date,
            start_time=time(11, 0, 0),
            duration=30,
            time=1800
        )

        # Aggregation: Sum of duration
        total_duration = Tracker.objects.filter(employee="Alice").aggregate(total=Sum('duration'))
        self.assertEqual(total_duration['total'], 120 + 30) # 150 minutes

        # F-Expression Check (Update 'time' field by adding 600 seconds)
        Tracker.objects.filter(employee="Alice").update(time=F('time') + 600)
        
        # Check the updated value for the standard tracker
        updated_tracker = Tracker.objects.get(pk=self.tracker_standard.pk)
        expected_time = self.time_data + 600 # 7200 + 600 = 7800
        self.assertEqual(updated_tracker.time, expected_time)