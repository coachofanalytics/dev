from datetime import time
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models import (
    ClientAvailability,
    Search,
    PricingSubPlan,
    Pricing
)


# =========================
# ClientAvailability Tests
# =========================
class ClientAvailabilityModelTests(TestCase):

    def test_create_client_availability_success(self):
        obj = ClientAvailability.objects.create(
            client=1,
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            time_standards="EAT",
            topic="Intro Call",
        )
        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.client, 1)
        self.assertEqual(obj.day, "Monday")

    def test_str_representation(self):
        obj = ClientAvailability.objects.create(
            client=2,
            day="Tuesday",
            start_time=time(14, 0),
            end_time=time(15, 0),
            time_standards="UTC",
            topic="Demo",
        )
        s = str(obj)
        self.assertIn("2", s)
        self.assertIn("Tuesday", s)

    def test_fields_not_null_enforced(self):
        obj = ClientAvailability(
            client=None,
            day=None,
            start_time=None,
            end_time=None,
            time_standards=None,
            topic=None,
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()


# =========================
# Search Model Tests
# =========================
class SearchModelTest(TestCase):

    def test_create_search(self):
        search = Search.objects.create(
            topic="Math",
            question="What is algebra?",
            uploaded=False
        )
        self.assertEqual(search.topic, "Math")
        self.assertFalse(search.uploaded)

    def test_string_representation(self):
        search = Search.objects.create(
            topic="Science",
            question="What is gravity?"
        )
        self.assertEqual(str(search), "Science")


# =========================
# PricingSubPlan Tests
# =========================
class PricingSubPlanModelTest(TestCase):

    import uuid

def setUp(self):
    self.pricing = Pricing.objects.create(
        name="Basic Plan",
        serial=f"PR-{uuid.uuid4().hex[:6]}",
        category=1   # ✅ FIXED
    )
        

    def test_create_subplan(self):
        subplan = PricingSubPlan.objects.create(
            my_pricing=self.pricing,
            title="Starter",
            description="Basic features",
            price=1000
        )

        self.assertEqual(subplan.title, "Starter")
        self.assertEqual(subplan.price, 1000)

    def test_relationship(self):
        subplan = PricingSubPlan.objects.create(
            my_pricing=self.pricing,
            title="Test Plan",
            description="Test Desc",
            price=500
        )

        # 🔴 match your actual field
        self.assertEqual(subplan.my_pricing.name, "Basic Plan")