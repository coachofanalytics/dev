from django.test import TestCase
from main.models import Location,Search  # adjust if model name differs


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


        # tests/test_integration_models.py
from datetime import time
from django.test import TestCase

from main.models import ClientAvailability


class ClientAvailabilityIntegrationTests(TestCase):
    """
    "Integration" here = model + ORM + database integration,
    including basic query patterns that the app will rely on.
    """

    def setUp(self):
        ClientAvailability.objects.bulk_create([
            ClientAvailability(
                client=10, day="Monday",
                start_time=time(9, 0), end_time=time(10, 0),
                time_standards="EAT", topic="Consultation"
            ),
            ClientAvailability(
                client=10, day="Monday",
                start_time=time(11, 0), end_time=time(12, 0),
                time_standards="EAT", topic="Follow-up"
            ),
            ClientAvailability(
                client=11, day="Tuesday",
                start_time=time(9, 30), end_time=time(10, 0),
                time_standards="UTC", topic="Intro"
            ),
        ])

    def test_filter_by_client_and_day(self):
        qs = ClientAvailability.objects.filter(client=10, day="Monday").order_by("start_time")
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs.first().topic, "Consultation")
        self.assertEqual(qs.last().topic, "Follow-up")

    def test_time_range_query(self):
        """
        Example: find slots that start at/after 10:00 for client 10 on Monday.
        """
        qs = ClientAvailability.objects.filter(
            client=10, day="Monday", start_time__gte=time(10, 0)
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().topic, "Follow-up")

    def test_update_and_persist(self):
        obj = ClientAvailability.objects.get(client=11, day="Tuesday")
        obj.topic = "Kickoff"
        obj.save()

        obj2 = ClientAvailability.objects.get(pk=obj.pk)
        self.assertEqual(obj2.topic, "Kickoff")


class SearchIntegrationTest(TestCase):

    def test_create_and_retrieve(self):
        Search.objects.create(
            topic="Biology",
            question="What is DNA?",
            uploaded=True
        )

        search = Search.objects.get(topic="Biology")
        self.assertEqual(search.question, "What is DNA?")
        self.assertTrue(search.uploaded)

import uuid
from django.test import TestCase
from main.models import Pricing, PricingSubPlan
import uuid


class PricingSubPlanIntegrationTest(TestCase):



  def setUp(self):
    self.pricing = Pricing.objects.create(
        name="Basic Plan",
        serial=f"PR-{uuid.uuid4().hex[:6]}",
        category=1,
        price=1000,
        duration=30   # ✅ ADD THIS (e.g., days)
    )

    def test_create_subplan(self):
        subplan = PricingSubPlan.objects.create(
            my_pricing=self.pricing,
            title="Starter",
            description="Starter package",
            price=10.0
        )

        self.assertEqual(subplan.title, "Starter")
        self.assertEqual(subplan.price, 10.0)
        self.assertEqual(subplan.my_pricing, self.pricing)

    def test_relationship(self):
        PricingSubPlan.objects.create(
            my_pricing=self.pricing,
            title="Pro",
            description="Pro package",
            price=20.0
        )

        self.assertEqual(self.pricing.subplans.count(), 1)

    def test_string_method(self):
        subplan = PricingSubPlan.objects.create(
            my_pricing=self.pricing,
            title="Advanced",
            description="Advanced package",
            price=30.0
        )

        # ✅ COMPLETE THIS TEST
        self.assertEqual(str(subplan), "Advanced - 30.0")