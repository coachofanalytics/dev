"""
Unit tests for marketing models

Tests individual model methods, properties, validation, and business logic.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models import Assets
from marketing.models import Ads, Whatsapp_Groups

User = get_user_model()


class AdsModelTest(TestCase):
    """Tests for Ads model validation and defaults."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="marketing_user",
            email="marketing@test.com",
            password="password123",
        )
        self.asset = Assets.objects.create(
            name="hero_image",
            category="marketing",
            description="Hero image",
        )

    def test_ads_creation_and_str(self):
        """Ads should be created with required fields and string representation should be title."""
        ad = Ads.objects.create(
            my_user=self.user,
            company="CODA Analytics",
            ad_title="Data Analytics Services",
            bulletin="Unlock data insights",
            image_name=self.asset,
            link="https://codanalytics.net",
            is_active=True,
            is_featured=True,
        )
        self.assertEqual(str(ad), "Data Analytics Services")
        self.assertTrue(ad.is_active)
        self.assertTrue(ad.is_featured)

    def test_ads_clean_rejects_invalid_urls(self):
        """Validation should fail when URLs do not start with http/https."""
        ad = Ads(
            my_user=self.user,
            company="CODA",
            ad_title="Invalid URL Ad",
            image_name=self.asset,
            company_site="codanalytics.net",  # Missing scheme
        )
        with self.assertRaises(ValidationError):
            ad.full_clean()

    def test_ads_requires_title_when_active(self):
        """Active ads must include title and company."""
        ad = Ads(
            my_user=self.user,
            company="",
            ad_title="",
            image_name=self.asset,
            is_active=True,
        )
        with self.assertRaises(ValidationError) as exc:
            ad.full_clean()
        self.assertIn("Ad title is required", str(exc.exception))


class WhatsappGroupsModelTest(TestCase):
    """Tests for Whatsapp_Groups validation and slug behaviour."""

    def setUp(self):
        self.group = Whatsapp_Groups.objects.create(
            group_name="Investors Hub",
            group_id="INV123",
            slug="investors-hub",
            country="KE",
            participants="250",
            category="Business",
            type="investments",
            is_active=True,
            is_featured=True,
        )

    def test_str_representation(self):
        """String representation should return group name."""
        self.assertEqual(str(self.group), "Investors Hub")

    def test_clean_rejects_missing_group_name_when_active(self):
        """Active groups require a group name and group id."""
        group = Whatsapp_Groups(
            group_id="MISSING",
            is_active=True,
        )
        with self.assertRaises(ValidationError) as exc:
            group.full_clean()
        self.assertIn("Group name is required", str(exc.exception))

    def test_clean_validates_participant_number(self):
        """Participants must be a valid positive integer."""
        self.group.participants = "-5"
        with self.assertRaises(ValidationError):
            self.group.full_clean()

    def test_unique_slug_enforced(self):
        """Duplicate slugs should raise validation error."""
        duplicate = Whatsapp_Groups(
            group_name="Another Group",
            group_id="INV456",
            slug="investors-hub",
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
