from django.test import TestCase
from django.utils import timezone

from main.models import Volunteer


class VolunteerModelIntegrationTests(TestCase):

    def test_create_and_retrieve_volunteer(self):
        volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to support the DC48K community.",
        )

        saved_volunteer = Volunteer.objects.get(pk=volunteer.pk)

        self.assertEqual(saved_volunteer.name, "Jane Doe")
        self.assertEqual(saved_volunteer.email, "jane@example.com")
        self.assertEqual(
            saved_volunteer.motivation,
            "I want to support the DC48K community.",
        )
        self.assertIsNotNone(saved_volunteer.created_at)

    def test_update_volunteer_application(self):
        volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to volunteer.",
        )

        volunteer.name = "Jane Wanjiku Doe"
        volunteer.motivation = (
            "I want to contribute my data-analysis experience."
        )
        volunteer.save()

        updated_volunteer = Volunteer.objects.get(pk=volunteer.pk)

        self.assertEqual(updated_volunteer.name, "Jane Wanjiku Doe")
        self.assertEqual(
            updated_volunteer.motivation,
            "I want to contribute my data-analysis experience.",
        )

    def test_delete_volunteer_application(self):
        volunteer = Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to support community projects.",
        )

        volunteer_id = volunteer.pk
        volunteer.delete()

        self.assertFalse(
            Volunteer.objects.filter(pk=volunteer_id).exists()
        )

    def test_filter_volunteer_by_email(self):
        Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to support the community.",
        )
        Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to share my professional skills.",
        )

        result = Volunteer.objects.get(email="john@example.com")

        self.assertEqual(result.name, "John Doe")

    def test_created_at_is_generated_by_database_workflow(self):
        before_creation = timezone.now()

        volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to volunteer.",
        )

        after_creation = timezone.now()
        saved_volunteer = Volunteer.objects.get(pk=volunteer.pk)

        self.assertGreaterEqual(
            saved_volunteer.created_at,
            before_creation,
        )
        self.assertLessEqual(
            saved_volunteer.created_at,
            after_creation,
        )

    def test_multiple_volunteers_are_stored_independently(self):
        first_volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to assist with training.",
        )
        second_volunteer = Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to assist with community outreach.",
        )

        self.assertEqual(Volunteer.objects.count(), 2)
        self.assertNotEqual(
            first_volunteer.pk,
            second_volunteer.pk,
        )
