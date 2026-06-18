from django.test import TestCase, Client
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.views import *
import unittest
from typing import Any

Tracker = Any
User = Any

class TestCrisisManagement(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_error_pages(self):
        """Test that error pages are displayed correctly"""
        error_pages = [
            ('main:400error', 'main/errors/400.html'),
            ('main:403error', 'main/errors/403.html'),
            ('main:404error', 'main/errors/404.html'),
            ('main:500error', 'main/errors/500.html'),
        ]
        for url_name, template in error_pages:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, template)

    def test_subscribe_alerts(self):
        response = self.client.post(reverse('main:subscribe_alerts'), {"email": "user@example.com"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

    def test_activate_helpline_minimal(self):
        response = self.client.post(reverse('main:activate_helpline'), {"phone": "123456789"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

# class TestHomeView(TestCase):

#     def setUp(self):
#         self.client = Client()
#         self.home_url = redirect('')

#     def test_home_view(self):
#         response = self.client.get(self.home_url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'main/home_templates/layout.html')


class TestTrackView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_track_create_view(self):
        self.tracker = Tracker.objects.create(
            category="Job_Support",
            task="database",
        )

        self.assertEqual(Tracker.objects.count(), 1)

    def test_track_update_view(self):
        self.tracker = Tracker.objects.create(
            category="Job_Support",
            task="database",
        )
        self.tracker_update = self.tracker
        self.tracker_update.category = "Interview"
        self.tracker_update.save()

        self.assertEqual(self.tracker_update.category, "Interview")

    def test_track_delete_view(self):
        self.category = "Interview"
        self.task = "database"
        self.duration = 10
        self.tracker = Tracker.objects.create(
            category=self.category,
            task=self.task,
        )
        self.tracker.delete()
        self.assertEqual(Tracker.objects.count(), 0)


class TestUserTrackerView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_tracker_url = redirect("/accounts/tracker")

    def test_user_tracker_view(self):
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail.com",
            gender="1",
            is_staff=True,
            is_active=True,
            username="johndoee",
        )

        response = self.client.post(self.user_tracker_url)
        self.assertEqual(User.objects.count(), 1)

        # self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, 'accounts/usertracker.html')

        trackers = Tracker.objects.all().filter(author=self.user).count()
        self.assertEqual(int(trackers), 0)

class TestUserDeleteView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_delete_view(self):
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail.com",
            gender="1",
            is_staff=True,
            is_active=True,
            username="johndoee",
        )
        self.assertEqual(User.objects.all().count(), 1)
        self.user.delete()
        self.assertEqual(User.objects.all().count(), 0)


@unittest.skip("Disabled: non-crisis client tests")
class TestClientView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_client_create_view(self):
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail.com",
            category=1,
            sub_category=4,
            is_client=True,
            username="johndoee",
        )
        self.assertEqual(User.objects.all().count(), 1)

    def test_client_update_view(self):
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail.com",
            category=1,
            sub_category=4,
            is_client=True,
            username="johndoee",
        )
        self.assertEqual(User.objects.all().count(), 1)
        self.user_update = self.user
        self.user_update.first_name = "Jane"
        self.user_update.save()
        self.assertEqual(self.user_update.first_name, "Jane")

    def test_client_delete_view(self):
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail.com",
            category=1,
            sub_category=4,
            is_client=True,
            username="johndoee",
        )
        self.assertEqual(User.objects.all().count(), 1)
        self.user.delete()
        self.assertEqual(User.objects.all().count(), 0)
