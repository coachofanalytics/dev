from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from main.models import Location

User = get_user_model()


class LocationAdminIntegrationTest(TestCase):
    """
    Integration tests for Location model in Django Admin
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"
        )

        self.client.login(username="admin", password="admin123")

        self.location = Location.objects.create(
            zipcode="00100",
            city="Nairobi",
            state="Nairobi County",
            country="Kenya"
        )

    def test_admin_changelist_loads(self):
        """Admin list page loads successfully"""
        url = reverse("admin:main_location_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Location.objects.filter(city="Nairobi").exists()
        )

    def test_admin_change_view_loads(self):
        """Admin change page loads successfully"""
        url = reverse(
            "admin:main_location_change",
            args=[self.location.id]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_admin_add_view_loads(self):
        """Admin add page loads successfully"""
        url = reverse("admin:main_location_add")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
