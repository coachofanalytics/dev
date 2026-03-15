from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationListViewIntegrationTest(TestCase):
    """Integration tests for location_list view"""

    def setUp(self):
        self.url = reverse("main:location_list")


    def test_location_list_url_exists(self):
        """URL should return 200"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_location_list_uses_correct_template(self):
        """Correct template should be rendered"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "main/locations_list.html")

    def test_location_list_context_exists(self):
        """locations should exist in context"""
        response = self.client.get(self.url)
        self.assertIn("locations", response.context)

    def test_location_list_with_data(self):
        """Locations should appear when data exists"""
        Location.objects.create(
            country="Kenya",
            state="Nairobi",
            city="Nairobi",
            zipcode="00100"
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["locations"]), 1)
        self.assertContains(response, "Kenya")
        self.assertContains(response, "Nairobi")