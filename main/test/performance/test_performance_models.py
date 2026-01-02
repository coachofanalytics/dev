from django.test import TestCase
from main.models import Location


class LocationPerformanceModelTest(TestCase):
    """
    Performance tests for Location model.
    Focus: bulk inserts and query efficiency.
    """

    def test_bulk_create_locations(self):
        locations = [
            Location(
                zipcode=f"{10000 + i}",
                city="City",
                state="State",
                country="Kenya"
            )
            for i in range(1000)
        ]

        Location.objects.bulk_create(locations)

        self.assertEqual(Location.objects.count(), 1000)

    def test_filter_performance_by_country(self):
        Location.objects.bulk_create([
            Location(zipcode="00100", city="Nairobi", state="Nairobi County", country="Kenya"),
            Location(zipcode="20100", city="Nakuru", state="Nakuru County", country="Kenya"),
            Location(zipcode="94105", city="San Francisco", state="California", country="USA"),
        ])

        kenya_locations = Location.objects.filter(country="Kenya")
        self.assertEqual(kenya_locations.count(), 2)
