from django.test import TestCase
from main.models import Location   # adjust if model name differs


class LocationIntegrationTest(TestCase):
    """
    Integration test to ensure Location model
    is saved, retrieved, and queried correctly
    through the ORM.
    """

    def test_location_create_and_fetch(self):
        location = Location.objects.create(
            zipcode="00100",
            city="Nairobi",
            state="Nairobi County",
            country="Kenya"
        )

        fetched = Location.objects.get(id=location.id)

        self.assertEqual(fetched.city, "Nairobi")
        self.assertEqual(fetched.country, "Kenya")

    def test_location_filtering(self):
        Location.objects.create(
            zipcode="00100",
            city="Nairobi",
            state="Nairobi County",
            country="Kenya"
        )
        Location.objects.create(
            zipcode="20100",
            city="Nakuru",
            state="Nakuru County",
            country="Kenya"
        )

        kenya_locations = Location.objects.filter(country="Kenya")

        self.assertEqual(kenya_locations.count(), 2)
