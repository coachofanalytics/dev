# accounts/tests/unit/test_unit_templates.py (No changes needed, this file is correct)

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time

from accounts.models import Tracker

User = get_user_model()

@override_settings(LOGIN_URL='/accounts/login/') 
class TrackerTemplateTest(TestCase):
    """
    Tests focused on ensuring that templates render the correct context variables and content.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up staff user and necessary Tracker objects."""
        cls.staff_user = User.objects.create_user(
            username='template_staff', 
            email='template@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # Create a Tracker object for list/update view testing
        cls.test_tracker = Tracker.objects.create(
            employee='Template Tester', 
            category='Development', 
            sub_category='Frontend',
            task='Test rendering of tracker',
            plan='Verify template output',
            login_date=timezone.now(),
            start_time=time(9, 0, 0),
            duration=90,
            time=1.5
        )
        
        # Define URLs
        cls.list_url = reverse('accounts:account-Tracker_list')
        cls.create_url = reverse('accounts:account-Tracker_create')
        cls.update_url = reverse('accounts:account-Tracker_update', args=[cls.test_tracker.pk])

    def setUp(self):
        # Log in the staff user for all tests
        self.client.login(username='template_staff', password='testpassword123')


    # ====================================================================
    # 1. Template Test: Tracker List View (tracker_list.html)
    # ====================================================================

    def test_list_template_renders_tracker_data(self):
        """
        Tests that the list template correctly receives and displays tracker data.
        """
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_list.html")
        
        # Check if the list context contains the Tracker object
        self.assertIn('Trackers', response.context)
        
        # Check if the template contains content specific to the test object
        self.assertContains(response, "Template Tester")
        self.assertContains(response, "Frontend")
        
        # Check for the link to the update view using the tracker's primary key (pk)
        expected_update_link = reverse('accounts:account-Tracker_update', args=[self.test_tracker.pk])
        self.assertContains(response, expected_update_link)


    # ====================================================================
    # 2. Template Test: Tracker Create View (tracker_create.html)
    # ====================================================================

    def test_create_template_renders_form(self):
        """
        Tests that the create template correctly renders the form fields and POST action.
        """
        response = self.client.get(self.create_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_create.html")
        
        # Check if a form object is in the context
        self.assertIn('form', response.context)
        
        # Check if the template contains the required HTML form action
        # This asserts the fix: <form method="POST" action="/accounts/add/">
        self.assertContains(response, f'action="{self.create_url}"')
        self.assertContains(response, 'name="task"')


    # ====================================================================
    # 3. Template Test: Tracker Update View (tracker_update.html)
    # ====================================================================

    def test_update_template_renders_form_with_initial_data(self):
        """
        Tests that the update template renders the form with the existing object's data.
        """
        response = self.client.get(self.update_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/tracker_update.html")

        # Check if a form object is in the context
        self.assertIn('form', response.context)
        
        # Check if the template contains the required HTML form action
        # This asserts the fix: <form method="POST" action="/accounts/tracker/update/1/">
        self.assertContains(response, f'action="{self.update_url}"')
        
        # Check for the employee name being pre-filled
        self.assertContains(response, f'value="{self.test_tracker.employee}"')