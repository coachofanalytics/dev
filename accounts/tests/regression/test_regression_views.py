# accounts/tests/regression/test_regression_views.py

from django.test import TestCase
from django.urls import reverse
from accounts.models import Tracker 
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time

User = get_user_model()

class TrackerRegressionTest(TestCase):
    """
    Tests to prevent specific, known bugs from reappearing (regression).
    """

    @classmethod
    def setUpTestData(cls):
        """Setup users required for the regression tests."""
        cls.staff_user = User.objects.create_user(
            username='staff_reg', 
            email='staff_reg@example.com',
            password='testpassword123',
            is_staff=True
        )
        cls.view_url = reverse('accounts:account-Tracker_list') 


    # ----------------------------------------------------------------------
    # Example 1: Bug related to a specific HTTP status code or data filter
    # ----------------------------------------------------------------------

    def test_bug_fixed_view_status_code_on_empty_data(self):
        """
        Regression test: Ensures the view returns a 200 OK (not a 500 error) 
        when the database table is completely empty (Bug #1234).
        """
        # Delete any initial data created in setUpTestData that might interfere
        Tracker.objects.all().delete() 
        
        self.client.login(username='staff_reg', password='testpassword123')
        response = self.client.get(self.view_url)
        
        # Assertion 1: Check for successful HTTP status code
        self.assertEqual(response.status_code, 200)

        # Assertion 2: Check for the actual context variable name ('Trackers')
        self.assertIn('Trackers', response.context)
        
        # Check that the list is empty
        self.assertEqual(len(response.context['Trackers']), 0)
        
        # NOTE: If your template definitely displays the string 'No tracking data found', 
        # you can add this back:
        # self.assertContains(response, "No tracking data found", status_code=200)


    # ----------------------------------------------------------------------
    # Example 2: Bug related to template context rendering an incorrect field
    # ----------------------------------------------------------------------

    def test_bug_fixed_incorrect_employee_name_rendering(self):
        """
        Regression test: Ensures the template renders the correct employee 
        name instead of accidentally showing the employee ID (Bug #5678).
        """
        # Supply all NOT NULL required fields to avoid IntegrityError
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
        
        self.client.login(username='staff_reg', password='testpassword123')
        response = self.client.get(self.view_url)

        # Assertion: Verify the employee name (the fix) is rendered
        self.assertContains(response, bug_tracker.employee)
        
        # Ensure the response is a success code before checking content
        self.assertEqual(response.status_code, 200)