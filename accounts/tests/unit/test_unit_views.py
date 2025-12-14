# accounts/tests/unit/test_unit_views.py (The Final Definitive Solution)

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import time
from django.db.models.query import QuerySet

from accounts.models import Tracker
from accounts.forms import Trackerform 

# 🚨 ASSUMPTION: You have separate models for Category/SubCategory.
# If not, replace these with the actual model names (e.g., if you only have a Category model)
# You MUST uncomment and import the actual model(s) here for the test to run.
# from accounts.models import Category, SubCategory 

User = get_user_model()

# ----------------------------------------------------------------------
# Helper class to simulate Foreign Key models if they exist in your app
# If your actual models are imported above, you can delete this.
class DummyCategory:
    def __init__(self, id):
        self.pk = id
class DummySubCategory:
    def __init__(self, id):
        self.pk = id
# ----------------------------------------------------------------------


class TrackerListViewTest(TestCase):
    # ... (Keep this class as is, as it's not the failing part) ...
    # Note: Ensure the models used in setUpTestData here match the models created below.
    # ...
    @classmethod
    def setUpTestData(cls):
        """Create test data and a staff user."""
        cls.staff_user = User.objects.create_user(
            username='staff_list', 
            email='list@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # 🚨 You need to create Category/SubCategory objects here for the setup data
        # Example using Dummy models for placeholder purposes:
        cls.category_obj = DummyCategory(id=1)
        cls.subcategory_obj = DummySubCategory(id=1) 
        
        base_data = {
            'category': 'Default Cat', 
            'sub_category': 'Default Sub', 
            'plan': 'Refactor all CSS', 
            'duration': 60,
            'time': 120,
            'start_time': time(9, 0, 0), 
        }

        # Tracker 1
        cls.tracker1 = Tracker.objects.create(
            **base_data,
            task='Implement Nav Bar', 
            employee='John Doe',              
            login_date=timezone.now(),
        )
        # ... rest of setUpTestData ...

# accounts/tests/unit/test_unit_views.py (Focus on TrackerCreateViewTest)

# ... (Keep all imports and the non-failing TrackerListViewTest class above) ...

# ---------------------------------------------------------------------------------
# TrackerCreateViewTest 
# ---------------------------------------------------------------------------------

@override_settings(LOGIN_URL='/accounts/login/') 
class TrackerCreateViewTest(TestCase):
    """
    Unit tests for the Tracker_create view function.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Create the staff user
        cls.staff_user = User.objects.create_user(
            username='staff_create', 
            email='staff_create@example.com',
            password='testpassword123',
            is_staff=True
        )
        cls.create_url = reverse('accounts:account-Tracker_create')
        cls.list_url = reverse('accounts:account-Tracker_list')
        cls.admin_login_url = reverse('admin:login') + f'?next={cls.create_url}' 
        
        # 🚨 CRITICAL FIX: Create FK objects and store their IDs
        # 
        # !!! YOU MUST UNCOMMENT AND USE YOUR ACTUAL MODEL NAMES HERE !!!
        # Example: 
        # from accounts.models import Category, SubCategory 
        # cls.category_obj = Category.objects.create(name='Development')
        # cls.subcategory_obj = SubCategory.objects.create(name='Backend', category=cls.category_obj)
        #
        # For this final attempt, we must assume you can create these:
        
        # **ASSUMING you have a simple model named Category and SubCategory**
        # If your models are complex or named differently, this will still fail.
        try:
             from accounts.models import Category, SubCategory 
             cls.category_obj = Category.objects.create(name='Test Category')
             cls.subcategory_obj = SubCategory.objects.create(name='Test SubCategory')
             cls.category_id = cls.category_obj.pk
             cls.subcategory_id = cls.subcategory_obj.pk
        except ImportError:
             # Fallback if Category models are not present or named differently.
             print("\n\n!! WARNING: FK MODELS NOT FOUND. USING PLACEHOLDER IDS !!\n")
             cls.category_id = 1
             cls.subcategory_id = 2


    def setUp(self):
        self.client.login(username='staff_create', password='testpassword123')

    # accounts/tests/unit/test_unit_views.py (Inside TrackerCreateViewTest)

    # --- Sample Valid Data (Corrected length for 'task') ---
    def get_valid_data(self):
        return {
            # Safest guess for required Category/SubCategory fields: simple strings
            'category': str(self.category_id) if hasattr(self, 'category_id') else '1', 
            'sub_category': str(self.subcategory_id) if hasattr(self, 'subcategory_id') else '2', 
            
            # FIX: Shortened to 25 characters
            'task': 'Write unit tests for view', 
            'plan': 'Complete testing suite',
            
            # Setting employee to a non-blank string to pass form validation
            'employee': 'staff_create', 
            
            # Date/Time fields MUST be passed as strings
            'login_date': timezone.now().strftime('%Y-%m-%d'), 
            'start_time': '14:00:00',
            
            # Numerical fields passed as strings
            'duration': '120', 
            'time': '2',
        }

    # ====================================================================
    # 2. POST Request Test 
    # ====================================================================

    def test_post_valid_data_creates_record_and_redirects(self):
        """Test POST request with valid data saves the object and redirects to list view."""
        data = self.get_valid_data()
        initial_tracker_count = Tracker.objects.count()

        # This will contain the form if validation fails (status 200)
        response = self.client.post(self.create_url, data, follow=True) 
        
        # 🚨 Diagnostic check for form errors if the count check fails 🚨
        if 'form' in response.context and response.context['form'].errors:
            print("\n\n" + "="*70)
            print("FINAL DIAGNOSTIC: FORM VALIDATION ERRORS FOUND")
            print(response.context['form'].errors)
            print("="*70 + "\n")

        # Check database count (This MUST be initial_tracker_count + 1)
        self.assertEqual(Tracker.objects.count(), initial_tracker_count + 1) # Line 140
        
        self.assertTemplateUsed(response, "accounts/admin/tracker_list.html")
        self.assertEqual(response.status_code, 200)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Record created successfully!')

    # ... (Keep the rest of the tests as is) ...



# accounts/tests/unit/test_unit_views.py (Add this class)

# ... (Keep the TrackerListViewTest and TrackerCreateViewTest classes above) ...

# ---------------------------------------------------------------------------------
# TrackerUpdateViewTest 
# ---------------------------------------------------------------------------------

@override_settings(LOGIN_URL='/accounts/login/') 
class TrackerUpdateViewTest(TestCase):
    """
    Unit tests for the Tracker_update view function.
    """

    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.staff_user = User.objects.create_user(
            username='staff_update', 
            email='staff_update@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # Create an existing Tracker object to update
        # Assuming required fields are simple strings/integers for creation simplicity
        cls.tracker_to_update = Tracker.objects.create(
            employee='Old Employee', 
            category='Old Cat', 
            sub_category='Old Sub',
            task='Old Task',
            plan='Old Plan',
            login_date=timezone.now(),
            start_time=time(8, 0, 0),
            duration=60,
            time=1
        )
        
        # Define URLs
        cls.update_url = reverse('accounts:account-Tracker_update', args=[cls.tracker_to_update.pk])
        cls.list_url = reverse('accounts:account-Tracker_list')
        cls.admin_login_url = reverse('admin:login') + f'?next={cls.update_url}'

    def setUp(self):
        # Log in the staff user for all tests
        self.client.login(username='staff_update', password='testpassword123')

    # --- Sample Valid Data ---
    def get_valid_update_data(self):
        # Data that is guaranteed to be valid and different from the initial data
        return {
            'employee': 'New Employee',  # Changed
            'category': 'New Category',
            'sub_category': 'New SubCategory',
            'task': 'New Task',
            'plan': 'New Plan',
            
            # Using current date/time in the expected string format
            'login_date': timezone.now().strftime('%Y-%m-%d'), 
            'start_time': '10:00:00',
            'duration': '120',
            'time': '2',
        }

    # ====================================================================
    # 1. GET Request Test (Initial Data Loading)
    # ====================================================================

    def test_get_tracker_update_renders_correct_template_and_initial_data(self):
        response = self.client.get(self.update_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_update.html")
        
        # Check if the initial data is loaded into the form
        self.assertContains(response, self.tracker_to_update.task)
        self.assertContains(response, self.tracker_to_update.employee)

    def test_get_non_existent_tracker_returns_404(self):
        # Try to access an update view for a primary key that doesn't exist (e.g., 999)
        non_existent_url = reverse('accounts:account-Tracker_update', args=[999])
        response = self.client.get(non_existent_url)
        
        # Verify get_object_or_404 correctly raises a 404
        self.assertEqual(response.status_code, 404)

    # ====================================================================
    # 2. POST Request Test (Valid Data)
    # ====================================================================

    def test_post_valid_data_updates_record_and_redirects(self):
        """Test POST request with valid data updates the object and redirects."""
        data = self.get_valid_update_data()
        
        # Get the initial count and PK (should not change)
        initial_tracker_count = Tracker.objects.count()
        pk_before_update = self.tracker_to_update.pk

        response = self.client.post(self.update_url, data, follow=True)
        
        # Check 1: Database count must remain the same (no new record created)
        self.assertEqual(Tracker.objects.count(), initial_tracker_count)
        
        # Check 2: Redirect to the list view
        self.assertRedirects(response, self.list_url)

        # Check 3: Data in the database is actually updated
        updated_tracker = Tracker.objects.get(pk=pk_before_update)
        self.assertEqual(updated_tracker.employee, 'New Employee')
        self.assertEqual(updated_tracker.task, 'New Task')
        
        # Check 4: Success message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Record update successfully!')

    # ====================================================================
    # 3. POST Request Test (Invalid Data)
    # ====================================================================
    
    def test_post_invalid_data_does_not_save_and_re_renders_form(self):
        """Test that invalid data does not update the record."""
        # Invalid data: setting a required field (task) to be too long (26 chars)
        invalid_data = self.get_valid_update_data()
        invalid_data['task'] = 'This task is intentionally too long now!' 

        # Get the initial employee name before the failed POST attempt
        old_employee_name = self.tracker_to_update.employee
        initial_tracker_count = Tracker.objects.count()

        response = self.client.post(self.update_url, invalid_data)
        
        # Check 1: Still 200 OK (re-rendering the form with errors)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_update.html")

        # Check 2: Database count remains the same
        self.assertEqual(Tracker.objects.count(), initial_tracker_count)

        # Check 3: The data in the database is NOT updated
        tracker_after_failure = Tracker.objects.get(pk=self.tracker_to_update.pk)
        self.assertEqual(tracker_after_failure.employee, old_employee_name)
        
        # Check 4: Form displays the validation error
        self.assertFormError(
            response, 
            'form', 
            'task', 
            # This error message assumes max_length=25 from previous debugging
            'Ensure this value has at most 25 characters (it has 40).' 
        )    