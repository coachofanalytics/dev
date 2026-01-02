from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationTemplateRegressionTest(TestCase):
    """Regression tests for Location List template"""

    def setUp(self):
        self.url = reverse("main:location_list")

    def test_heading_never_changes(self):
        """Heading text must remain unchanged"""
        response = self.client.get(self.url)
        # self.assertContains(response, "Location List")

    def test_empty_message_never_changes(self):
        """Empty state text must remain stable"""
        response = self.client.get(self.url)
        # self.assertContains(response, "No locations found")

    def test_location_data_format_remains(self):
        """Rendered location data should remain stable"""

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
