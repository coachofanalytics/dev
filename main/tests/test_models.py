from django.test import TestCase
from accounts.models import Location


class LocationModelTest(TestCase):

    def setUp(self):
        self.location = Location.objects.create(
            zipcode="00100",
            city="Nairobi",
            state="Nairobi County",
            country="Kenya"
        )

    def test_location_creation(self):
        self.assertEqual(Location.objects.count(), 1)

    def test_location_fields(self):
        self.assertEqual(self.location.zipcode, "00100")
        self.assertEqual(self.location.city, "Nairobi")
        self.assertEqual(self.location.state, "Nairobi County")
        self.assertEqual(self.location.country, "Kenya")

    def test_nullable_fields_allowed(self):
        location = Location.objects.create()
        self.assertIsNone(location.zipcode)
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.country)

    def test_string_representation(self):
        self.assertEqual(str(self.location), "Nairobi, Kenya")
