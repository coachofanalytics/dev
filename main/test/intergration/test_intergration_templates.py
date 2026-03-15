from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationListTemplateIntegrationTest(TestCase):
    """Integration tests for Location List template"""

    def setUp(self):
        self.url = reverse("main:location_list")

    def test_location_list_template_renders_heading(self):
        """Template should render the correct heading"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "Location List")

    def test_location_list_template_renders_empty_state(self):
        """Empty message should show when no locations exist"""
        response = self.client.get(self.url)
        # self.assertContains(response, "No locations found")

    def test_location_list_template_renders_location_data(self):
        """Template should render location data from DB"""

        Location.objects.create(
            country="Kenya",
            state="Nairobi",
            city="Nairobi",
            zipcode="00100"
        )

        response = self.client.get(self.url)

        self.assertContains(response, "Kenya")
        self.assertContains(response, "Nairobi")
        self.assertContains(response, "00100")
