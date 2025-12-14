# accounts/tests/integration/test_integration_views.py

from django.test import TestCase, override_settings 
from django.contrib.auth import get_user_model
from django.urls import reverse
# Import any models or other necessary components if needed for setup
# from accounts.models import Tracker 

User = get_user_model()

@override_settings(LOGIN_URL='/accounts/login/') 
class TrackerListAccessTest(TestCase):
    """
    Integration tests focusing on access control for the Tracker list view.
    Checks if different user types (anonymous, normal, staff) get the correct response.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Create users and set up URLs for testing."""
        
        # 1. Staff User (Should have access)
        cls.user_staff = User.objects.create_user(
            username='user_staff', 
            email='staff@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # 2. Normal User (Should be denied access)
        cls.user_normal = User.objects.create_user(
            username='user_normal', 
            email='normal@example.com',
            password='testpassword123',
            is_staff=False
        )
        
        # 3. URL Definitions
        cls.url = reverse('accounts:account-Tracker_list')
        cls.custom_login_url = reverse('accounts:account-login') + f'?next={cls.url}'
        cls.admin_login_url = reverse('admin:login') + f'?next={cls.url}'


    # ----------------------------------------------
    # 1. Access Denied: Anonymous User
    # ----------------------------------------------

    def test_tracker_list_redirects_if_not_logged_in(self):
        """
        Test that an unauthenticated (anonymous) user is redirected to the login page.
        """
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        
        # Check if the response redirects to EITHER the custom login OR admin login
        try:
            self.assertRedirects(response, self.custom_login_url)
        except AssertionError:
            self.assertRedirects(response, self.admin_login_url) 

    # ----------------------------------------------
    # 2. Access Denied: Normal (Non-Staff) User
    # ----------------------------------------------

    def test_tracker_list_denied_for_normal_user(self):
        """
        Test that a logged-in non-staff user is denied access and redirected.
        This verifies the @staff_member_required decorator or equivalent logic.
        """
        self.client.login(username='user_normal', password='testpassword123')
        response = self.client.get(self.url)
        
        # When access is denied to an authenticated user via @staff_member_required,
        # it typically results in a 302 redirect back to the login, or occasionally 403 Forbidden.
        # We check for the redirect as defined by your original test:
        self.assertEqual(response.status_code, 302) 

        # Check the redirect target (should usually go back to a login page)
        try:
            self.assertRedirects(response, self.custom_login_url)
        except AssertionError:
            self.assertRedirects(response, self.admin_login_url)

    # ----------------------------------------------
    # 3. Access Granted: Staff User
    # ----------------------------------------------

    def test_tracker_list_accessible_by_staff_user(self):
        """
        Test that a logged-in staff user is granted access (200 OK).
        This is the most critical integration check for access control.
        """
        # Log in the staff user
        self.client.login(username='user_staff', password='testpassword123')
        
        # Access the view
        response = self.client.get(self.url)
        
        # The staff user should receive a successful status code
        self.assertEqual(response.status_code, 200) 
        
        # Optional: Check a content detail to ensure the correct template loaded
        # self.assertTemplateUsed(response, "accounts/admin/tracker_list.html")

# accounts/tests/integration/test_integration_views.py (Add the update-specific tests)

from django.test import TestCase, override_settings 
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Tracker 
from django.utils import timezone
from datetime import time

User = get_user_model()


@override_settings(LOGIN_URL='/accounts/login/') 
class TrackerListAccessTest(TestCase):
    """
    Integration tests focusing on access control for the Tracker list and update views.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Create users and set up URLs for testing."""
        
        # 1. Staff User (Should have access)
        cls.user_staff = User.objects.create_user(
            username='user_staff', 
            email='staff@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # 2. Normal User (Should be denied access)
        cls.user_normal = User.objects.create_user(
            username='user_normal', 
            email='normal@example.com',
            password='testpassword123',
            is_staff=False
        )

        # 3. Create a Tracker object to test the Update view
        cls.test_tracker = Tracker.objects.create(
            employee='Test Record', 
            category='Integration', 
            sub_category='Access',
            task='Check permissions',
            plan='Verify staff access',
            login_date=timezone.now(),
            start_time=time(10, 0, 0),
            duration=60,
            time=1
        )
        
        # 4. URL Definitions
        cls.list_url = reverse('accounts:account-Tracker_list')
        cls.update_url = reverse('accounts:account-Tracker_update', args=[cls.test_tracker.pk])
        
        # Login Redirect targets (using the list URL in the original tests)
        cls.custom_login_list_url = reverse('accounts:account-login') + f'?next={cls.list_url}'
        cls.admin_login_list_url = reverse('admin:login') + f'?next={cls.list_url}'
        
        # Login Redirect targets (for the update URL)
        cls.custom_login_update_url = reverse('accounts:account-login') + f'?next={cls.update_url}'
        cls.admin_login_update_url = reverse('admin:login') + f'?next={cls.update_url}'


    # --- Existing List View Access Tests (omitted for brevity, assume they are here) ---
    
    
    # ----------------------------------------------
    # 3. New Access Denied: Anonymous User (Update View)
    # ----------------------------------------------

    def test_tracker_update_redirects_if_not_logged_in(self):
        """
        Test that an unauthenticated (anonymous) user is redirected to the login page 
        when trying to access the update view.
        """
        response = self.client.get(self.update_url)
        
        self.assertEqual(response.status_code, 302)
        
        # Check if the response redirects to EITHER the custom login OR admin login
        try:
            self.assertRedirects(response, self.custom_login_update_url)
        except AssertionError:
            self.assertRedirects(response, self.admin_login_update_url) 


    # ----------------------------------------------
    # 4. New Access Denied: Normal (Non-Staff) User (Update View)
    # ----------------------------------------------

    def test_tracker_update_denied_for_normal_user(self):
        """
        Test that a logged-in non-staff user is denied access to the update view.
        """
        self.client.login(username='user_normal', password='testpassword123')
        response = self.client.get(self.update_url)
        
        self.assertEqual(response.status_code, 302) 

        # Check the redirect target
        try:
            self.assertRedirects(response, self.custom_login_update_url)
        except AssertionError:
            self.assertRedirects(response, self.admin_login_update_url)


    # ----------------------------------------------
    # 5. New Access Granted: Staff User (Update View)
    # ----------------------------------------------

    def test_tracker_update_accessible_by_staff_user(self):
        """
        Test that a logged-in staff user is granted access (200 OK) to the update view.
        """
        # Log in the staff user
        self.client.login(username='user_staff', password='testpassword123')
        
        # Access the view
        response = self.client.get(self.update_url)
        
        # The staff user should receive a successful status code
        self.assertEqual(response.status_code, 200)
        # Optional check to ensure it loaded the right record content
        self.assertContains(response, self.test_tracker.employee)        