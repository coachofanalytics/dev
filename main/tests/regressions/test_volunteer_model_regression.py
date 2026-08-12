from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from main.models import Volunteer


class VolunteerModelRegressionTests(TestCase):
    """Regression tests for previously identified Volunteer model risks."""

    def setUp(self):
        self.volunteer = Volunteer.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            motivation="I want to support the DC48K community.",
        )

    def test_volunteer_table_supports_record_creation(self):
        """
        Regression: main_volunteer must exist after migrations.
        """

        self.assertIsNotNone(self.volunteer.pk)
        self.assertEqual(Volunteer.objects.count(), 1)

    def test_created_at_is_populated_automatically(self):
        """
        Regression: created_at must not require manual input.
        """

        self.assertIsNotNone(self.volunteer.created_at)

    def test_valid_email_passes_model_validation(self):
        """
        Regression: a valid email address must pass validation.
        """

        volunteer = Volunteer(
            name="John Doe",
            email="john@example.com",
            motivation="I want to support community activities.",
        )

        volunteer.full_clean()

    def test_invalid_email_fails_model_validation(self):
        """
        Regression: malformed email addresses must be rejected.
        """

        volunteer = Volunteer(
            name="John Doe",
            email="not-a-valid-email",
            motivation="I want to support community activities.",
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean()

    def test_blank_name_fails_model_validation(self):
        """
        Regression: a volunteer application must include a name.
        """

        volunteer = Volunteer(
            name="",
            email="john@example.com",
            motivation="I want to support community activities.",
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean()

    def test_blank_email_fails_model_validation(self):
        """
        Regression: a volunteer application must include an email.
        """

        volunteer = Volunteer(
            name="John Doe",
            email="",
            motivation="I want to support community activities.",
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean()

    def test_blank_motivation_fails_model_validation(self):
        """
        Regression: a volunteer must provide a motivation statement.
        """

        volunteer = Volunteer(
            name="John Doe",
            email="john@example.com",
            motivation="",
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean()

    def test_name_longer_than_100_characters_fails_validation(self):
        """
        Regression: name must respect the 100-character model limit.
        """

        volunteer = Volunteer(
            name="A" * 101,
            email="john@example.com",
            motivation="I want to support community activities.",
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean()

    def test_data_persists_after_refresh_from_database(self):
        """
        Regression: saved application information must persist.
        """

        self.volunteer.refresh_from_db()

        self.assertEqual(self.volunteer.name, "Jane Doe")
        self.assertEqual(self.volunteer.email, "jane@example.com")
        self.assertEqual(
            self.volunteer.motivation,
            "I want to support the DC48K community.",
        )

    def test_updating_record_does_not_replace_created_at(self):
        """
        Regression: editing an application must preserve its creation time.
        """

        original_created_at = self.volunteer.created_at

        self.volunteer.name = "Jane Wanjiku Doe"
        self.volunteer.save()
        self.volunteer.refresh_from_db()

        self.assertEqual(
            self.volunteer.created_at,
            original_created_at,
        )

    def test_deleting_one_volunteer_does_not_delete_others(self):
        """
        Regression: deleting one application must not affect another.
        """

        second_volunteer = Volunteer.objects.create(
            name="John Doe",
            email="john@example.com",
            motivation="I want to support community outreach.",
        )

        self.volunteer.delete()

        self.assertFalse(
            Volunteer.objects.filter(
                email="jane@example.com"
            ).exists()
        )
        self.assertTrue(
            Volunteer.objects.filter(
                pk=second_volunteer.pk
            ).exists()
        )