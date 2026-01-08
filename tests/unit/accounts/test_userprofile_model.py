"""
Comprehensive unit tests for UserProfile model.
Tests user profile creation, updates, validations, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()
UserProfile = apps.get_model('accounts', 'UserProfile')
Category = apps.get_model('accounts', 'Category')


class UserProfileModelBasicTests(TestCase):
    """Basic tests for UserProfile model creation and string representation."""

    def test_profile_create_and_str(self):
        """Test profile creation and string representation."""
        user = User.objects.create_user(username='bob', password='testpass123')
        profile = UserProfile(user=user)
        self.assertTrue(hasattr(profile, 'user'))
        self.assertIsInstance(profile, UserProfile)

    def test_profile_str_with_category(self):
        """Test profile string representation with category."""
        cat = Category.objects.create(name='Investor', slug='investor')
        user = User.objects.create_user(username='investor_user', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(str(profile), 'investor_user - Investor')

    def test_profile_str_without_category(self):
        """Test profile string representation without category."""
        user = User.objects.create_user(username='plain_user', password='pass')
        profile = UserProfile(user=user)
        self.assertEqual(str(profile), "plain_user's profile")


class UserProfileDashboardUrlTests(TestCase):
    """Tests for dashboard URL property based on user category."""

    def test_dashboard_url_default(self):
        """Test default dashboard URL when no category is set."""
        user = User.objects.create_user(username='no_cat_user', password='pass')
        profile = UserProfile(user=user)
        self.assertEqual(profile.dashboard_url, 'home')

    def test_dashboard_url_investor_category(self):
        """Test dashboard URL for investor category."""
        cat = Category.objects.create(name='Investor', slug='investor')
        user = User.objects.create_user(username='investor1', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(profile.dashboard_url, 'investor_dashboard')

    def test_dashboard_url_business_category(self):
        """Test dashboard URL for business category."""
        cat = Category.objects.create(name='Business', slug='business')
        user = User.objects.create_user(username='business1', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(profile.dashboard_url, 'business_dashboard')

    def test_dashboard_url_individual_category(self):
        """Test dashboard URL for individual category."""
        cat = Category.objects.create(name='Individual', slug='individual')
        user = User.objects.create_user(username='individual1', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(profile.dashboard_url, 'individual_dashboard')

    def test_dashboard_url_unknown_category(self):
        """Test dashboard URL for unknown category slug returns home."""
        cat = Category.objects.create(name='Unknown', slug='unknown_slug')
        user = User.objects.create_user(username='unknown_user', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(profile.dashboard_url, 'home')


class UserProfileFieldValidationTests(TestCase):
    """Tests for field validations and constraints."""

    def setUp(self):
        self.user = User.objects.create_user(username='fieldtest', password='pass')
        # Profile is auto-created by signal, get it
        self.profile = self.user.profile

    def test_bio_max_length(self):
        """Test bio field max length constraint."""
        self.profile.bio = 'x' * 500
        # Should not raise - exactly at max length
        self.profile.full_clean()

    def test_bio_can_store_long_text(self):
        """Test bio field can store text (TextField doesn't enforce max_length at DB level)."""
        self.profile.bio = 'x' * 500
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(len(self.profile.bio), 500)

    def test_phone_max_length(self):
        """Test phone field max length constraint."""
        self.profile.phone = '1' * 20
        self.profile.full_clean()  # Should not raise

    def test_company_name_max_length(self):
        """Test company_name field max length constraint."""
        self.profile.company_name = 'A' * 200
        self.profile.full_clean()

    def test_alternate_email_valid(self):
        """Test alternate email field with valid email."""
        self.profile.alternate_email = 'test@example.com'
        self.profile.full_clean()

    def test_alternate_email_invalid(self):
        """Test alternate email field with invalid email."""
        self.profile.alternate_email = 'not-an-email'
        with self.assertRaises(ValidationError):
            self.profile.full_clean()

    def test_website_url_valid(self):
        """Test website field with valid URL."""
        self.profile.website = 'https://example.com'
        self.profile.full_clean()

    def test_linkedin_url_valid(self):
        """Test LinkedIn URL field with valid URL."""
        self.profile.linkedin_url = 'https://linkedin.com/in/user'
        self.profile.full_clean()

    def test_twitter_handle_max_length(self):
        """Test Twitter handle max length."""
        self.profile.twitter_handle = 'a' * 50
        self.profile.full_clean()

    def test_years_of_experience_accepts_null(self):
        """Test years of experience accepts null value."""
        self.profile.years_of_experience = None
        self.profile.full_clean()

    def test_years_of_experience_positive_integer(self):
        """Test years of experience with positive integer."""
        self.profile.years_of_experience = 10
        self.profile.full_clean()


class UserProfileGDPRConsentTests(TestCase):
    """Tests for GDPR consent fields."""

    def setUp(self):
        self.user = User.objects.create_user(username='gdprtest', password='pass')
        self.profile = self.user.profile

    def test_gdpr_consent_default_false(self):
        """Test GDPR consent defaults to False."""
        self.assertFalse(self.profile.gdpr_consent)

    def test_gdpr_consent_with_date(self):
        """Test GDPR consent with consent date."""
        now = timezone.now()
        self.profile.gdpr_consent = True
        self.profile.gdpr_consent_date = now
        self.profile.save()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.gdpr_consent)
        self.assertEqual(self.profile.gdpr_consent_date, now)

    def test_gdpr_consent_with_ip(self):
        """Test GDPR consent with IP address."""
        self.profile.gdpr_consent = True
        self.profile.gdpr_consent_ip = '192.168.1.1'
        self.profile.save()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.profile.gdpr_consent_ip, '192.168.1.1')

    def test_gdpr_consent_ipv6(self):
        """Test GDPR consent with IPv6 address."""
        self.profile.gdpr_consent = True
        self.profile.gdpr_consent_ip = '::1'
        self.profile.save()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.profile.gdpr_consent_ip, '::1')


class UserProfileEdgeCaseTests(TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_empty_optional_fields(self):
        """Test profile with all optional fields empty."""
        user = User.objects.create_user(username='empty_optional', password='pass')
        profile = user.profile  # Use auto-created profile
        profile.bio = ''
        profile.company_name = ''
        profile.job_title = ''
        profile.phone = ''
        profile.alternate_email = ''
        profile.location = ''
        profile.address = ''
        profile.website = ''
        profile.linkedin_url = ''
        profile.twitter_handle = ''
        profile.facebook_url = ''
        profile.industry = ''
        profile.skills = ''
        profile.full_clean()  # Should not raise

    def test_profile_timestamps_auto_set(self):
        """Test that timestamps are automatically set."""
        user = User.objects.create_user(username='timestamp_test', password='pass')
        profile = user.profile  # Use auto-created profile
        profile.refresh_from_db()
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_profile_updated_at_changes_on_save(self):
        """Test that updated_at changes when profile is saved."""
        user = User.objects.create_user(username='update_test', password='pass')
        profile = user.profile  # Use auto-created profile
        profile.refresh_from_db()
        original_updated_at = profile.updated_at
        
        # Update profile
        profile.bio = 'Updated bio'
        profile.save()
        profile.refresh_from_db()
        
        self.assertGreaterEqual(profile.updated_at, original_updated_at)

    def test_category_set_null_on_delete(self):
        """Test that category is set to null when category is deleted."""
        cat = Category.objects.create(name='DeleteMe', slug='deleteme')
        user = User.objects.create_user(username='cat_delete_test', password='pass')
        profile = user.profile  # Use auto-created profile
        profile.category = cat
        profile.save()
        
        # Delete category
        cat.delete()
        profile.refresh_from_db()
        
        self.assertIsNone(profile.category)


class UserProfileSignalTests(TestCase):
    """Tests for user profile signals."""

    def test_profile_created_on_user_creation(self):
        """Test that profile is automatically created when user is created."""
        user = User.objects.create_user(username='signal_test', password='pass')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)

    def test_profile_saved_when_user_saved(self):
        """Test that profile is saved when user is saved."""
        user = User.objects.create_user(username='save_signal_test', password='pass')
        user.first_name = 'Updated'
        user.save()
        # Should not raise any errors
        user.profile.refresh_from_db()
