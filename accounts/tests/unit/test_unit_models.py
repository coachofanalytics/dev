from django.test import TestCase
from django.urls import reverse
from datetime import datetime, time
from django.utils import timezone
# Ensure correct imports based on where your code lives
from accounts.models import Tracker 
# Assuming your view is in accounts/views.py
# from accounts.views import Tracker_list 


class TrackerListViewTest(TestCase):
    """Tests for the Tracker_list view."""

    @classmethod
    def setUpTestData(cls):
        """
        Create test data: a few Tracker objects, providing all required fields
        based on the Tracker model definition.
        """
        # Define base data to avoid repetition
        base_data = {
            'category': 'Development', 
            'sub_category': 'Frontend', 
            'plan': 'Refactor all CSS', 
            'start_time': time(9, 0, 0),
            'duration': 60,
            'time': 120
        }

        # Tracker 1
        Tracker.objects.create(
            **base_data,
            task='Implement Nav Bar', 
            employee='John Doe',              
            login_date=timezone.now(),
        )
        
        # Tracker 2
        # Use a slightly different task and time for distinction
        Tracker.objects.create(
            **base_data,
            task='Fix mobile layout', 
            employee='Jane Smith',
            login_date=timezone.now() - timezone.timedelta(days=1), # Different date
        )

    def test_view_url_accessible_by_name(self):
        """Test if the URL is accessible using the name 'account-Tracker_list'."""
        # The name is 'account-Tracker_list' from your path: path('Tracker/', views.Tracker_list, name='account-Tracker_list')
        response = self.client.get(reverse('account-Tracker_list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """Test if the correct template 'accounts/admin/tracker_list.html' is used."""
        response = self.client.get(reverse('account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_list.html")

    def test_context_contains_all_trackers(self):
        """Test that the 'Trackers' context variable contains all objects."""
        response = self.client.get(reverse('account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        
        # 1. Check that the variable name in context matches the view: {"Trackers":Trackers}
        self.assertIn('Trackers', response.context)
        
        # 2. Check that the context contains the correct number of objects
        all_trackers_count = Tracker.objects.count()
        self.assertEqual(all_trackers_count, 2) # Should be 2 from setUpTestData
        self.assertEqual(len(response.context['Trackers']), all_trackers_count)
        
        # 3. Check the content type is a QuerySet
        self.assertTrue(hasattr(response.context['Trackers'], 'query'))

    def test_template_displays_tracker_data(self):
        """Test if the rendered HTML contains key data from the created objects."""
        response = self.client.get(reverse('account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check for unique field values from the test data (e.g., tasks and employees)
        self.assertContains(response, 'Implement Nav Bar')
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Fix mobile layout')
        self.assertContains(response, 'Jane Smith')