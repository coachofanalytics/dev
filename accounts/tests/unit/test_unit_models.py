from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import time
from accounts.models import Tracker  # Ensure this matches your app name

class TrackerModelTest(TestCase):

    def setUp(self):
        """
        Set up data used for multiple tests to avoid repetition.
        """
        self.valid_data = {
            "category": "Development",
            "sub_category": "Backend",
            "task": "Testing",
            "plan": "Write unit tests for models",
            "employee": "John Doe",
            "login_date": timezone.now(),
            "start_time": time(9, 0, 0),
            "duration": 60,
            "time": 120
        }

    def test_create_valid_tracker(self):
        """
        Test that a Tracker object can be created with valid data.
        """
        tracker = Tracker.objects.create(**self.valid_data)
        self.assertTrue(isinstance(tracker, Tracker))
        self.assertEqual(tracker.category, "Development")
        self.assertEqual(tracker.employee, "John Doe")

    def test_string_representation(self):
        """
        Test the __str__ method returns the expected format.
        """
        tracker = Tracker.objects.create(**self.valid_data)
        expected_string = f"Tracker for {tracker.employee} on {tracker.login_date}"
        self.assertEqual(str(tracker), expected_string)

    def test_verbose_names(self):
        """
        Test that the meta verbose names are correct.
        """
        self.assertEqual(Tracker._meta.verbose_name, "Tracker")
        self.assertEqual(Tracker._meta.verbose_name_plural, "Trackers")

    # --- Validation Tests (max_length) ---

    def test_category_max_length(self):
        """
        Test that category cannot exceed 25 characters.
        """
        self.valid_data['category'] = 'x' * 26
        tracker = Tracker(**self.valid_data)
        with self.assertRaises(ValidationError):
            tracker.full_clean()

    def test_sub_category_max_length(self):
        """
        Test that sub_category cannot exceed 25 characters.
        """
        self.valid_data['sub_category'] = 'x' * 26
        tracker = Tracker(**self.valid_data)
        with self.assertRaises(ValidationError):
            tracker.full_clean()

    def test_task_max_length(self):
        """
        Test that task cannot exceed 25 characters.
        """
        self.valid_data['task'] = 'x' * 26
        tracker = Tracker(**self.valid_data)
        with self.assertRaises(ValidationError):
            tracker.full_clean()

    # --- Integrity Tests (null=False) ---

    def test_category_cannot_be_null(self):
        """
        Test that creating a tracker explicitly set to None raises IntegrityError.
        """
        # FIX: We explicitly set this to None. 
        # (Simply removing the key might default to an empty string in some configurations)
        self.valid_data['category'] = None
        
        with self.assertRaises(IntegrityError):
            Tracker.objects.create(**self.valid_data)

    def test_login_date_cannot_be_null(self):
        """
        Test that login_date is required.
        """
        self.valid_data.pop('login_date')
        with self.assertRaises(IntegrityError):
            Tracker.objects.create(**self.valid_data)

    # --- Edge Case Tests ---

    def test_employee_can_be_null(self):
        """
        Test that employee can be None (null=True).
        """
        self.valid_data['employee'] = None
        tracker = Tracker.objects.create(**self.valid_data)
        self.assertIsNone(tracker.employee)

    def test_time_must_be_positive(self):
        """
        Test that the 'time' field validates against negative numbers.
        """
        self.valid_data['time'] = -10
        tracker = Tracker(**self.valid_data)
        
        # FIX: We catch either ValidationError (Python check) OR IntegrityError (DB check).
        # We also call save() in case full_clean() lets it slide but the DB blocks it.
        with self.assertRaises((ValidationError, IntegrityError)):
            tracker.full_clean()
            tracker.save()