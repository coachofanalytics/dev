from django.test import TestCase
from django.urls import reverse
from datetime import time
from django.utils import timezone
from accounts.models import Tracker 


class TrackerListViewTest(TestCase):
    """Tests for the Tracker_list view."""

    @classmethod
    def setUpTestData(cls):
        """Create test data, ensuring timezone-aware datetimes are used."""
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
            login_date=timezone.now(), # Use timezone.now() for awareness
        )
        
        # Tracker 2
        Tracker.objects.create(
            **base_data,
            task='Fix mobile layout', 
            employee='Jane Smith',
            login_date=timezone.now() - timezone.timedelta(days=1),
        )

    def test_view_url_exists_at_desired_location(self):
        """Test if the URL path /accounts/Tracker/ is accessible (no 404 error)."""
        # --- FIX: Use the full path including the 'accounts/' prefix ---
        response = self.client.get('/accounts/Tracker/') 
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        """Test if the URL is accessible using the namespace:name."""
        # --- FIX: Use the namespace 'accounts:account-Tracker_list' ---
        response = self.client.get(reverse('accounts:account-Tracker_list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """Test if the correct template 'accounts/admin/tracker_list.html' is used."""
        # --- FIX: Use the namespace 'accounts:account-Tracker_list' ---
        response = self.client.get(reverse('accounts:account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_list.html")

    def test_context_contains_all_trackers(self):
        """Test that the 'Trackers' context variable contains all objects."""
        # --- FIX: Use the namespace 'accounts:account-Tracker_list' ---
        response = self.client.get(reverse('accounts:account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('Trackers', response.context)
        self.assertEqual(len(response.context['Trackers']), 2)

    def test_template_displays_tracker_data(self):
        """Test if the rendered HTML contains key data from the created objects."""
        # --- FIX: Use the namespace 'accounts:account-Tracker_list' ---
        response = self.client.get(reverse('accounts:account-Tracker_list'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'Implement Nav Bar')
        self.assertContains(response, 'John Doe')