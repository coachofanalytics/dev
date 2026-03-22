from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


from main.models import Location,Search

User = get_user_model()

class LocationAdminRegressionTest(TestCase):
    """
    Regression tests for admin edge cases
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin2",
            password="admin123",
            email="admin2@test.com"
        )
        self.client.login(username="admin2", password="admin123")

    def test_admin_handles_empty_fields(self):
        """Admin does not crash with empty Location fields"""
        location = Location.objects.create()

        url = reverse(
            "admin:main_location_change",
            args=[location.id]
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_list_with_multiple_locations(self):
        """Admin list handles multiple rows safely"""
        Location.objects.create(city="Nairobi", country="Kenya")
        Location.objects.create(city="Nakuru", country="Kenya")

        url = reverse("admin:main_location_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nairobi")
        self.assertContains(response, "Nakuru")



        # tests/test_regression_models.py
from datetime import time
from django.test import TestCase

from main.models import ClientAvailability


class ClientAvailabilityRegressionTests(TestCase):
    """
    "Regression" tests lock in behavior so future changes do not break it.
    Keep these tests stable and business-rule focused.
    """

    def test_day_case_sensitive_behavior_locked(self):
        """
        This test intentionally documents current behavior: 'Monday' != 'monday'.
        If you later want case-insensitive days, change the code and update this test.
        """
        ClientAvailability.objects.create(
            client=1,
            day="Monday",
            start_time=time(8, 0),
            end_time=time(9, 0),
            time_standards="EAT",
            topic="Morning Slot",
        )

        self.assertEqual(
            ClientAvailability.objects.filter(day="Monday").count(),
            1
        )
        self.assertEqual(
            ClientAvailability.objects.filter(day="monday").count(),
            0
        )

    def test_time_standard_value_stored_as_is(self):
        """
        Locks current behavior: time_standards is stored as provided (no normalization).
        """
        obj = ClientAvailability.objects.create(
            client=3,
            day="Wednesday",
            start_time=time(13, 0),
            end_time=time(14, 0),
            time_standards="EAT",
            topic="Timezone check",
        )
        self.assertEqual(obj.time_standards, "EAT")

    def test_topic_max_length_255(self):
        """
        CharField(max_length=255) should enforce 255 at validation time.
        """
        long_topic = "x" * 256
        obj = ClientAvailability(
            client=4,
            day="Thursday",
            start_time=time(15, 0),
            end_time=time(16, 0),
            time_standards="UTC",
            topic=long_topic,
        )
        # full_clean triggers max_length validation
        with self.assertRaises(Exception):
            obj.full_clean()



class SearchRegressionTest(TestCase):

    def test_uploaded_default_false(self):
        search = Search.objects.create(
            topic="History",
            question="What is WW2?"
        )
        self.assertFalse(search.uploaded)

    def test_timestamps_auto_set(self):
        search = Search.objects.create(
            topic="Tech",
            question="What is AI?"
        )
        self.assertIsNotNone(search.created_at)
        self.assertIsNotNone(search.updated_at)

import uuid
from django.test import TestCase
from main.models import Pricing, PricingSubPlan

from django.test import TestCase
from main.models import Pricing, PricingSubPlan,Category





class PricingSubPlanIntegrationTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Standard")

        self.pricing = Pricing.objects.create(
            name="Basic Plan",
            category=self.category   # ✅ FIX
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

        self.assertEqual(str(subplan), "Advanced - 30.0")