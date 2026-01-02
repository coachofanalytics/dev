from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationListViewUnitTest(TestCase):
    """Unit tests for location_list view"""

    def setUp(self):
        self.url = reverse("main:location_list")

    def test_location_list_view_returns_200(self):
        """View should return HTTP 200"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_location_list_view_uses_correct_template(self):
        """View should use the correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "main/locations_list.html")

    def test_location_list_context_contains_locations(self):
        """Context must contain 'locations'"""
        response = self.client.get(self.url)
        self.assertIn("locations", response.context)

    def test_location_list_empty_queryset(self):
        """locations should be empty when no data exists"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["locations"].count(), 0)

    def test_location_list_with_single_location(self):
        """locations should include created records"""
        Location.objects.create(
            country="Kenya",
            state="Nairobi",
            city="Nairobi",
            zipcode="00100"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context["locations"].count(), 1)
