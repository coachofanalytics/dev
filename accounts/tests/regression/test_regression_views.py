# accounts/tests/regression/test_regression_views.py

from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Tracker 
# If your FK models are required for setup, you must import them:
# from accounts.models import Category, SubCategory 
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time

User = get_user_model()

# --- Placeholder/Setup for required Foreign Key model IDs ---
# These are placeholder IDs and must match actual created objects if FKs are required.
CATEGORY_ID = 1
SUBCATEGORY_ID = 2

@override_settings(LOGIN_URL='/accounts/login/')
class TrackerRegressionTest(TestCase):
    """
    Tests to prevent specific, known bugs from reappearing (regression).
    Focuses on the Tracker_list view and the Tracker_create view validation.
    """

    @classmethod
    def setUpTestData(cls):
        """Setup users and URL required for the regression tests."""
        cls.staff_user = User.objects.create_user(
            username='staff_reg', 
            email='staff_reg@example.com',
            password='testpassword123',
            is_staff=True
        )
        cls.list_url = reverse('accounts:account-Tracker_list') 
        cls.create_url = reverse('accounts:account-Tracker_create')
        
        # Foreign Key IDs setup: Use placeholders or actual created object IDs
        cls.category_id = CATEGORY_ID
        cls.subcategory_id = SUBCATEGORY_ID
        

    def setUp(self):
        # Log in the staff user before each test
        self.client.login(username='staff_reg', password='testpassword123')


    # ----------------------------------------------------------------------
    # Regression Test 1: Empty Data Handling (Bug #1234)
    # ----------------------------------------------------------------------

    def test_bug_fixed_view_status_code_on_empty_data(self):
        """
        Regression test: Ensures the view returns a 200 OK (not a 500 error) 
        when the database table is completely empty.
        """
        # Delete any initial data created in setUpTestData that might interfere
        Tracker.objects.all().delete() 
        
        response = self.client.get(self.list_url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('Trackers', response.context)
        self.assertEqual(len(response.context['Trackers']), 0)


    # ----------------------------------------------------------------------
    # Regression Test 2: Correct Data Rendering (Bug #5678)
    # ----------------------------------------------------------------------

    def test_bug_fixed_incorrect_employee_name_rendering(self):
        """
        Regression test: Ensures the template renders the correct employee 
        name instead of accidentally showing the employee ID.
        """
        # Create a tracker record with all required fields
        bug_tracker = Tracker.objects.create(
            employee='John Smith', 
            category='Regression', 
            sub_category='Testing',
            task='Verify employee rendering',
            plan='Ensure data correctness',
            login_date=timezone.now(),
            start_time=time(10, 0, 0),
            duration=30,
            time=1
        )
        
        response = self.client.get(self.list_url)

        # Assertion: Verify the employee name (the fix) is rendered
        self.assertContains(response, bug_tracker.employee)
        self.assertEqual(response.status_code, 200)

    # ----------------------------------------------------------------------
    # Regression Test 3: Task Max Length Validation (The recently fixed bug)
    # ----------------------------------------------------------------------

    def get_invalid_data_bug_task_max_length(self):
        """Data that caused the max_length bug (Task field too long)."""
        return {
            # Pass Foreign Key IDs as strings
            'category': str(self.category_id), 
            'sub_category': str(self.subcategory_id), 
            
            # 🚨 Regression Test Case: Task is 26 characters (should fail validation)
            'task': 'This task is too long now!', 
            'plan': 'Regression plan',
            'employee': 'staff_reg', 
            'login_date': timezone.now().strftime('%Y-%m-%d'), 
            'start_time': '10:00:00',
            'duration': '60', 
            'time': '1',
        }

    def test_task_max_length_validation_rejects_long_data(self):
        """
        Regression test: Ensures data exceeding 25 characters for 'task'
        is correctly rejected by form validation.
        """
        invalid_data = self.get_invalid_data_bug_task_max_length()
        initial_tracker_count = Tracker.objects.count()

        # 1. POST the invalid data
        response = self.client.post(self.create_url, invalid_data)

        # 2. Check: The POST should fail, re-rendering the form (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_create.html")

        # 3. Check: Database count must NOT have increased
        self.assertEqual(Tracker.objects.count(), initial_tracker_count)

        # 4. Check: The form errors must contain the specific error message
        self.assertFormError(
            response, 
            'form', 
            'task', 
            'Ensure this value has at most 25 characters (it has 26).'
        )