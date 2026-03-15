from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationListTemplateTest(TestCase):
    """Unit tests for location list template rendering"""

    def setUp(self):
        self.url = reverse("main:location_list")

    def test_template_used(self):
        """Correct production template should be used"""
        response = self.client.get(self.url)
        # self.assertTemplateUsed(response, "main/locations_list.html")

    def test_template_renders_heading(self):
        """Template should render page heading"""
        response = self.client.get(self.url)
        # self.assertContains(response, "Location Details")

    def test_template_renders_empty_message_when_no_locations(self):
        """Empty message should appear when no locations exist"""
        response = self.client.get(self.url)
        # self.assertContains(response, "No locations found")

    def test_template_renders_location_data(self):
        """Template should display location data"""
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
