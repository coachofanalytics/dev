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




# accounts/tests/regression/test_regression_views.py (Add this class)

# ... (Keep the existing imports and TrackerRegressionTest class) ...

# ----------------------------------------------------------------------
# New Regression Test Class for Update View
# ----------------------------------------------------------------------

@override_settings(LOGIN_URL='/accounts/login/')
class TrackerUpdateRegressionTest(TestCase):
    """
    Tests to prevent specific, known bugs from reappearing in the Tracker_update view.
    Focuses on form validation when updating an existing record.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Setup users, URLs, and a record to be updated."""
        cls.staff_user = User.objects.create_user(
            username='staff_update_reg', 
            email='staff_upreg@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # Create the Tracker object that will be targeted for update
        cls.tracker_to_update = Tracker.objects.create(
            employee='John Doe', 
            category='Initial', 
            sub_category='Setup',
            task='Short initial task', # < 25 chars
            plan='Initial plan',
            login_date=timezone.now(),
            start_time=time(10, 0, 0),
            duration=60,
            time=1
        )
        
        # Define URLs
        cls.update_url = reverse('accounts:account-Tracker_update', args=[cls.tracker_to_update.pk])
        cls.list_url = reverse('accounts:account-Tracker_list')

    def setUp(self):
        # Log in the staff user before each test
        self.client.login(username='staff_update_reg', password='testpassword123')


    # ----------------------------------------------------------------------
    # Regression Test 1: Task Max Length Validation (Bug fixed in Create/Update)
    # ----------------------------------------------------------------------

    def get_invalid_update_data(self):
        """Data that violates the max_length constraint on the 'task' field."""
        # Start with the existing, valid data from the object being updated
        # and only change the 'task' field to be invalid.
        return {
            'employee': self.tracker_to_update.employee, 
            'category': self.tracker_to_update.category,
            'sub_category': self.tracker_to_update.sub_category,
            
            # 🚨 Regression Test Case: Task is 26 characters (should fail validation)
            'task': 'This task is too long now!', 
            
            'plan': self.tracker_to_update.plan,
            'login_date': self.tracker_to_update.login_date.strftime('%Y-%m-%d'), 
            'start_time': self.tracker_to_update.start_time.strftime('%H:%M:%S'),
            'duration': str(self.tracker_to_update.duration),
            'time': str(self.tracker_to_update.time),
        }

    def test_update_task_max_length_validation_rejects_long_data(self):
        """
        Regression test: Ensures POSTing data exceeding 25 characters for 'task'
        to the update view is correctly rejected by form validation.
        """
        initial_task = self.tracker_to_update.task
        invalid_data = self.get_invalid_update_data()
        
        # 1. POST the invalid data to the update URL
        response = self.client.post(self.update_url, invalid_data)

        # 2. Check: The POST should fail, re-rendering the form (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_update.html")

        # 3. Check: The object in the database must NOT have been updated
        self.tracker_to_update.refresh_from_db()
        self.assertEqual(self.tracker_to_update.task, initial_task) # Task must still be 'Short initial task'

        # 4. Check: The form errors must contain the specific error message
        self.assertFormError(
            response, 
            'form', 
            'task', 
            'Ensure this value has at most 25 characters (it has 26).'
        )        




# accounts/tests/integration/test_integration_views.py (Add the following methods to your existing integration class)

# ... (Assume you have the setUpTestData that defines user_staff, user_normal, and test_tracker) ...

# ----------------------------------------------
# New Access Denied: Anonymous User (Delete View)
# ----------------------------------------------

def test_tracker_delete_get_redirects_if_not_logged_in(self):
    """
    Test that an unauthenticated user is redirected to the login page 
    when trying to access the delete confirmation page (GET request).
    """
    response = self.client.get(self.delete_url)
    
    self.assertEqual(response.status_code, 302)
    # Check if the response redirects to EITHER the custom login OR admin login
    expected_redirect = reverse('accounts:account-login') + f'?next={self.delete_url}'
    self.assertRedirects(response, expected_redirect, target_status_code=200)

def test_tracker_delete_post_redirects_if_not_logged_in(self):
    """
    Test that an unauthenticated user is redirected to the login page 
    when trying to POST (execute deletion). The record must not be deleted.
    """
    initial_count = Tracker.objects.count()
    response = self.client.post(self.delete_url)
    
    self.assertEqual(response.status_code, 302)
    
    # Crucial check: Deletion must not happen
    self.assertEqual(Tracker.objects.count(), initial_count) 


# ----------------------------------------------
# New Access Denied: Normal (Non-Staff) User (Delete View)
# ----------------------------------------------

def test_tracker_delete_denied_for_normal_user_get(self):
    """
    Test that a logged-in non-staff user is denied access to the delete confirmation page (GET).
    """
    self.client.login(username='user_normal', password='testpassword123')
    response = self.client.get(self.delete_url)
    
    # If using @staff_member_required, non-staff users are treated like anonymous and redirected.
    self.assertEqual(response.status_code, 302) 
    
    # Check the redirect target (usually to login or an error page)
    expected_redirect = reverse('accounts:account-login') + f'?next={self.delete_url}'
    self.assertRedirects(response, expected_redirect, target_status_code=200)

def test_tracker_delete_denied_for_normal_user_post(self):
    """
    Test that a logged-in non-staff user is denied access to POST the deletion. 
    The record must not be deleted.
    """
    self.client.login(username='user_normal', password='testpassword123')
    initial_count = Tracker.objects.count()

    response = self.client.post(self.delete_url)
    
    self.assertEqual(response.status_code, 302)
    
    # Crucial check: Deletion must not happen
    self.assertEqual(Tracker.objects.count(), initial_count) 


# ----------------------------------------------
# New Access Granted: Staff User (Delete View)
# ----------------------------------------------

def test_tracker_delete_accessible_by_staff_user(self):
    """
    Test that a logged-in staff user is granted access to the delete view (GET request).
    """
    # Log in the staff user
    self.client.login(username='user_staff', password='testpassword123')
    
    # Access the view (GET)
    response = self.client.get(self.delete_url)
    
    # The staff user should receive a successful status code
    self.assertEqual(response.status_code, 200)
    # Check for the key confirmation text
    self.assertContains(response, self.test_tracker.employee)

def test_tracker_delete_post_succeeds_for_staff_user(self):
    """
    Test that a logged-in staff user can successfully POST to delete a record.
    """
    # Log in the staff user
    self.client.login(username='user_staff', password='testpassword123')
    
    # Create a fresh record to ensure this test doesn't interfere with others
    tracker_to_delete_test = Tracker.objects.create(
        employee='Staff Delete Test', 
        category='Test', 
        sub_category='Delete',
        task='Temp record',
        plan='Temp plan',
        login_date=timezone.now(),
        start_time=time(12, 0, 0),
        duration=30,
        time=0.5
    )
    delete_url_test = reverse('accounts:account-Tracker_delete', args=[tracker_to_delete_test.pk])
    initial_count = Tracker.objects.count()

    # Access the view (POST)
    response = self.client.post(delete_url_test, follow=True)
    
    # Check 1: Successful deletion leads to a redirect
    self.assertRedirects(response, self.list_url)
    
    # Check 2: Database count decreased
    self.assertEqual(Tracker.objects.count(), initial_count - 1) 
    
    # Check 3: Record is truly gone 
    self.assertFalse(Tracker.objects.filter(pk=tracker_to_delete_test.pk).exists())



# accounts/tests/integration/test_integration_views.py (Add the following methods)

# ... (Assuming your setUpTestData now includes self.test_tracker and self.detail_url is defined) ...

# ----------------------------------------------
# New Access Denied: Anonymous User (Detail View)
# ----------------------------------------------

def test_tracker_detail_get_redirects_if_not_logged_in(self):
    """
    Test that an unauthenticated user is redirected to the login page 
    when trying to access the detail view.
    """
    # URL for detail view is self.detail_url
    response = self.client.get(self.detail_url)
    
    self.assertEqual(response.status_code, 302)
    
    # Check if the response redirects to the login page
    expected_redirect = reverse('accounts:account-login') + f'?next={self.detail_url}'
    self.assertRedirects(response, expected_redirect, target_status_code=200)


# ----------------------------------------------
# New Access Denied: Normal (Non-Staff) User (Detail View)
# ----------------------------------------------

def test_tracker_detail_denied_for_normal_user(self):
    """
    Test that a logged-in non-staff user is denied access to the detail view.
    """
    self.client.login(username='user_normal', password='testpassword123')
    response = self.client.get(self.detail_url)
    
    # Non-staff users should be redirected by @staff_member_required.
    self.assertEqual(response.status_code, 302) 
    
    # Check the redirect target
    expected_redirect = reverse('accounts:account-login') + f'?next={self.detail_url}'
    self.assertRedirects(response, expected_redirect, target_status_code=200)


# ----------------------------------------------
# New Access Granted: Staff User (Detail View)
# ----------------------------------------------

def test_tracker_detail_accessible_by_staff_user(self):
    """
    Test that a logged-in staff user is granted access (200 OK) to the detail view.
    """
    # Log in the staff user
    self.client.login(username='user_staff', password='testpassword123')
    
    # Access the view
    response = self.client.get(self.detail_url)
    
    # The staff user should receive a successful status code and see the content
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.test_tracker.employee)




# accounts/tests/regression/test_regression_views.py (Add this class)

# ... (Keep the existing imports and other RegressionTest classes) ...

# ----------------------------------------------------------------------
# New Regression Test Class for Detail View
# ----------------------------------------------------------------------

@override_settings(LOGIN_URL='/accounts/login/')
class TrackerDetailRegressionTest(TestCase):
    """
    Tests to ensure the Tracker_detail view remains functional and renders
    key data correctly over time.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Setup user, URLs, and a specific record to be viewed."""
        cls.staff_user = User.objects.create_user(
            username='staff_detail_reg', 
            email='staff_dreg@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # Create a Tracker object with specific, identifiable data
        cls.test_task_content = "This is a unique task for detail regression"
        cls.tracker_to_detail = Tracker.objects.create(
            employee='Regression Detail Check', 
            category='Check', 
            sub_category='Detail',
            task=cls.test_task_content, 
            plan='Regression view test',
            login_date=timezone.now(),
            start_time=time(14, 30, 0),
            duration=30,
            time=0.5
        )
        
        # Define URL
        cls.detail_url = reverse('accounts:account-Tracker_detail', args=[cls.tracker_to_detail.pk])

    def setUp(self):
        # Log in the staff user before each test
        self.client.login(username='staff_detail_reg', password='testpassword123')


    # ----------------------------------------------------------------------
    # Regression Test 1: Ensure Key Content Renders and View is Accessible
    # ----------------------------------------------------------------------

    def test_detail_view_renders_key_content(self):
        """
        Ensures the detail view returns 200 OK and correctly displays a
        specific, critical field (the task content).
        """
        response = self.client.get(self.detail_url)

        # 1. Check: View must be accessible (200 OK)
        self.assertEqual(response.status_code, 200)

        # 2. Check: The template must contain the unique task content
        self.assertContains(response, self.test_task_content)

        # 3. Check: The template must contain the employee name
        self.assertContains(response, self.tracker_to_detail.employee)