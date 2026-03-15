from django.test import TestCase
from django.urls import reverse
from main.models import Location


class LocationListViewRegressionTest(TestCase):
    """Regression tests to ensure future changes don't break behavior"""

    def setUp(self):
        self.url = reverse("main:location_list")


    def test_location_list_with_no_data(self):
        """View should not crash when no locations exist"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["locations"],
            []
        )

    def test_location_ordering_is_respected(self):
        """Ordering defined in Meta should be respected"""
        Location.objects.create(
            country="USA",
            state="California",
            city="Los Angeles",
            zipcode="90001"
        )
        Location.objects.create(
            country="Kenya",
            state="Nairobi",
            city="Nairobi",
            zipcode="00100"
        )

        response = self.client.get(self.url)
        locations = response.context["locations"]

        self.assertEqual(locations[0].country, "Kenya")
        self.assertEqual(locations[1].country, "USA")