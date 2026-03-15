# # main/tests/unit/test_plan_model.py


# from main.models import Plan
from datetime import time
from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models import ClientAvailability,Search



# def test_create_plan():
#     plan = Plan.objects.create(
#         task="Test Task",
#         duration=10,
#         what="Testing what",
#         why="Testing why"
#     )

#     assert plan.id is not None
#     assert plan.task == "Test Task"
#     assert plan.duration == 10
#     assert plan.is_active is True



# def test_str_method():
#     plan = Plan.objects.create(task="My Plan")
#     assert str(plan) == "My Plan"


# tests/test_models.py


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
        self.assertIn("Client 2", s)
        self.assertIn("Tuesday", s)

    def test_fields_not_null_enforced(self):
        """
        Your model uses NOT NULL for all fields. Django enforces required-ness via model validation.
        Note: DB-level NOT NULL is enforced on save for most DBs, but we test via full_clean().
        """
        obj = ClientAvailability(
            client=None,  # invalid
            day=None,     # invalid
            start_time=None,
            end_time=None,
            time_standards=None,
            topic=None,
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()


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