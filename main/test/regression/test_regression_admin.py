from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from main.models import Location

User = get_user_model()

class LocationAdminRegressionTest(TestCase):
    """
    Regression tests for admin edge cases
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin2",
            password="admin123",
            email="admin2@test.com"
        )
        self.client.login(username="admin2", password="admin123")

    def test_admin_handles_empty_fields(self):
        """Admin does not crash with empty Location fields"""
        location = Location.objects.create()

        url = reverse(
            "admin:main_location_change",
            args=[location.id]
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_list_with_multiple_locations(self):
        """Admin list handles multiple rows safely"""
        Location.objects.create(city="Nairobi", country="Kenya")
        Location.objects.create(city="Nakuru", country="Kenya")

        url = reverse("admin:main_location_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nairobi")
        self.assertContains(response, "Nakuru")
