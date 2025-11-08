"""
Unit tests for management models

Tests individual model methods, properties, validation, and business logic.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Department
from management.models import Policy, Training
from professional_services.models import FeaturedActivity, FeaturedCategory, FeaturedSubCategory

User = get_user_model()


class TrainingModelTest(TestCase):
    """Tests for Training model validation and helper properties."""

    def setUp(self):
        self.presenter = User.objects.create_user(
            username="trainer",
            email="trainer@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
        )
        self.department = Department.objects.create(
            name=Department.IT,
            description="Technology Department",
            slug="it-department",
        )
        self.category = FeaturedCategory.objects.create(
            title=FeaturedCategory.Development,
            created_by=self.presenter,
            description="Development tracks",
        )
        self.subcategory = FeaturedSubCategory.objects.create(
            featuredcategory=self.category,
            created_by=self.presenter,
            title="Backend Engineering",
        )
        self.activity = FeaturedActivity.objects.create(
            created_by=self.presenter,
            activity_name="Django Architecture",
            description="Deep dive into Django",
        )
        self.activity.featuredsubcategory.add(self.subcategory)

        self.training = Training.objects.create(
            presenter=self.presenter,
            department=self.department,
            category=self.category,
            subcategory=self.subcategory,
            topic=self.activity,
            level=Training.Level.Level_1,
            session=1,
            description="Intro session",
            session_link="https://meet.example.com/session",
        )

    def test_str_representation(self):
        """String representation should include topic and level."""
        result = str(self.training)
        self.assertIn("Django Architecture", result)
        self.assertIn("Level 1", result)

    def test_calculated_expiry_date(self):
        """calculated_expiry_date should be one year after creation."""
        expected = self.training.created_date + timedelta(days=365)
        self.assertEqual(self.training.calculated_expiry_date.date(), expected.date())

    def test_clean_validates_positive_session(self):
        """Session must be positive; zero should raise ValidationError."""
        self.training.session = 0
        with self.assertRaises(ValidationError):
            self.training.clean()

    def test_clean_validates_expiration_after_created(self):
        """Expiration date before created date should raise ValidationError."""
        self.training.expiration_date = self.training.created_date - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.training.clean()


class PolicyModelTest(TestCase):
    """Tests for Policy model basic behavior."""

    def setUp(self):
        self.employee = User.objects.create_user(
            username="policy_admin",
            email="policy@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
        )
        self.policy = Policy.objects.create(
            employee=self.employee,
            staff="Admin",
            type="Leave",
            link="https://intranet.example.com/policies/leave",
            department=Policy.IT,
            day="Monday",
            description="Leave policy details",
            policy_doc=None,
            is_active=True,
            is_featured=True,
            is_internal=True,
        )

    def test_str_representation(self):
        """String representation should include policy ID."""
        result = str(self.policy)
        self.assertIn(str(self.policy.id), result)
        self.assertIn("policy", result.lower())

    def test_default_flags(self):
        """New policies should be active/internal by default unless specified."""
        policy = Policy.objects.create(
            employee=self.employee,
            staff="Ops",
            type="Working Hours",
            link="https://intranet.example.com/policies/hours",
            department=Policy.MANAGEMENT,
            day="Tuesday",
            description="Working hours policy",
        )
        self.assertTrue(policy.is_internal)
        self.assertFalse(policy.is_featured)

    def test_policy_fields_saved_correctly(self):
        """Validate that important fields are persisted."""
        self.assertEqual(self.policy.department, Policy.IT)
        self.assertEqual(self.policy.type, "Leave")
        self.assertEqual(self.policy.day, "Monday")
        self.assertTrue(self.policy.is_active)
