from django.test import TestCase
from django.utils import timezone

from main.models import Volunteer


class VolunteerModelIntegrationTests(TestCase):
    """Integration tests for the Volunteer model and database."""

    def setUp(self):
        """Create one volunteer before each test."""

        self.volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to support the DC48K community.",
        )

    def test_create_and_retrieve_volunteer(self):
        """A volunteer should be saved and retrieved."""

        saved_volunteer = Volunteer.objects.get(
            pk=self.volunteer.pk
        )

        self.assertEqual(saved_volunteer.name, "Jane Doe")
        self.assertEqual(
            saved_volunteer.email,
            "jane@example.com",
        )
        self.assertEqual(
            saved_volunteer.motivation,
            "I want to support the DC48K community.",
        )
        self.assertIsNotNone(saved_volunteer.created_at)

    def test_update_volunteer(self):
        """A volunteer application should be updated."""

        self.volunteer.name = "Jane Wanjiku Doe"
        self.volunteer.email = "jane.wanjiku@example.com"
        self.volunteer.motivation = (
            "I want to contribute my data analysis experience."
        )
        self.volunteer.save()

        updated_volunteer = Volunteer.objects.get(
            pk=self.volunteer.pk
        )

        self.assertEqual(
            updated_volunteer.name,
            "Jane Wanjiku Doe",
        )
        self.assertEqual(
            updated_volunteer.email,
            "jane.wanjiku@example.com",
        )
        self.assertEqual(
            updated_volunteer.motivation,
            "I want to contribute my data analysis experience.",
        )

    def test_delete_volunteer(self):
        """A volunteer application should be deleted."""

        volunteer_id = self.volunteer.pk

        self.volunteer.delete()

        self.assertFalse(
            Volunteer.objects.filter(
                pk=volunteer_id
            ).exists()
        )

    def test_filter_volunteer_by_email(self):
        """A volunteer should be found by email address."""

        Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to support community projects.",
        )

        result = Volunteer.objects.get(
            email="john@example.com"
        )

        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.email, "john@example.com")

    def test_created_at_is_generated_automatically(self):
        """The creation timestamp should be generated automatically."""

        before_creation = timezone.now()

        volunteer = Volunteer.objects.create(
            name="Mary Smith",
            email="mary@example.com",
            motivation="I want to assist with training.",
        )

        after_creation = timezone.now()

        self.assertIsNotNone(volunteer.created_at)
        self.assertGreaterEqual(
            volunteer.created_at,
            before_creation,
        )
        self.assertLessEqual(
            volunteer.created_at,
            after_creation,
        )

    def test_multiple_volunteers_are_stored_independently(self):
        """Separate applications should have separate primary keys."""

        second_volunteer = Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to assist with community outreach.",
        )

        self.assertEqual(Volunteer.objects.count(), 2)
        self.assertNotEqual(
            self.volunteer.pk,
            second_volunteer.pk,
        )

    def test_changes_persist_after_refresh(self):
        """Changes should persist after refreshing from the database."""

        self.volunteer.name = "Jane Updated"
        self.volunteer.save()

        self.volunteer.refresh_from_db()

        self.assertEqual(
            self.volunteer.name,
            "Jane Updated",
        )

    def test_queryset_returns_all_volunteers(self):
        """The queryset should return all stored applications."""

        Volunteer.objects.create(
            name="Peter Mwangi",
            email="peter@example.com",
            motivation="I want to contribute my technical skills.",
        )

        volunteers = Volunteer.objects.all()

        self.assertEqual(volunteers.count(), 2)
        self.assertTrue(
            volunteers.filter(
                email="jane@example.com"
            ).exists()
        )
        self.assertTrue(
            volunteers.filter(
                email="peter@example.com"
            ).exists()
        )

    def test_volunteer_string_representation(self):
        """The model should provide a readable string representation."""

        expected_value = "Jane Doe — jane@example.com"

        self.assertEqual(
            str(self.volunteer),
            expected_value,
        )