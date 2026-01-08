"""
Comprehensive unit tests for Onboarding models.
Tests onboarding progress, email verification tokens, and step tracking.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
OnboardingProgress = apps.get_model('onboarding', 'OnboardingProgress')
EmailVerificationToken = apps.get_model('onboarding', 'EmailVerificationToken')


class OnboardingProgressBasicTests(TestCase):
    """Basic tests for OnboardingProgress model."""

    def setUp(self):
        self.user = User.objects.create_user(username='onboarduser', password='pass')

    def test_onboarding_progress_creation(self):
        """Test creating onboarding progress."""
        progress = OnboardingProgress.objects.create(user=self.user)
        self.assertEqual(progress.user, self.user)
        self.assertFalse(progress.email_verified)
        self.assertFalse(progress.profile_completed)

    def test_onboarding_progress_str_representation(self):
        """Test onboarding progress string representation."""
        progress = OnboardingProgress.objects.create(user=self.user)
        expected_status = progress.get_status()
        self.assertIn(self.user.username, str(progress))

    def test_default_values(self):
        """Test onboarding progress default values."""
        progress = OnboardingProgress.objects.create(user=self.user)
        self.assertFalse(progress.email_verified)
        self.assertFalse(progress.profile_completed)
        self.assertFalse(progress.category_selected)
        self.assertIsNone(progress.completed_at)


class OnboardingProgressStatusTests(TestCase):
    """Tests for onboarding status methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')
        self.progress = OnboardingProgress.objects.create(user=self.user)

    def test_get_status_email_pending(self):
        """Test status when email verification pending."""
        status = self.progress.get_status()
        self.assertEqual(status, 'Email Verification Pending')

    def test_get_status_email_verified(self):
        """Test status when email verified but profile pending."""
        self.progress.email_verified = True
        self.progress.save()
        status = self.progress.get_status()
        self.assertEqual(status, 'Email Verified (profile pending)')

    def test_get_status_profile_completed_waiting_verification(self):
        """Test status when profile completed but email not verified."""
        self.progress.profile_completed = True
        self.progress.save()
        status = self.progress.get_status()
        self.assertEqual(status, 'Profile Completed (waiting verification)')

    def test_get_status_complete(self):
        """Test status when all steps complete."""
        self.progress.email_verified = True
        self.progress.profile_completed = True
        self.progress.category_selected = True
        self.progress.completed_at = timezone.now()
        self.progress.save()
        status = self.progress.get_status()
        self.assertEqual(status, 'Complete')


class OnboardingProgressIsCompleteTests(TestCase):
    """Tests for is_complete method."""

    def setUp(self):
        self.user = User.objects.create_user(username='completeuser', password='pass')
        self.progress = OnboardingProgress.objects.create(user=self.user)

    def test_is_complete_false_initially(self):
        """Test is_complete returns False initially."""
        self.assertFalse(self.progress.is_complete())

    def test_is_complete_false_partial_completion(self):
        """Test is_complete returns False with partial completion."""
        self.progress.email_verified = True
        self.progress.save()
        self.assertFalse(self.progress.is_complete())

    def test_is_complete_true_all_steps(self):
        """Test is_complete returns True when all steps complete."""
        self.progress.email_verified = True
        self.progress.profile_completed = True
        self.progress.category_selected = True
        self.progress.completed_at = timezone.now()
        self.progress.save()
        self.assertTrue(self.progress.is_complete())


class OnboardingProgressMarkMethodTests(TestCase):
    """Tests for mark methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='markuser', password='pass')
        self.progress = OnboardingProgress.objects.create(user=self.user)

    def test_mark_email_verified(self):
        """Test marking email as verified."""
        self.assertFalse(self.progress.email_verified)
        self.progress.mark_email_verified()
        self.progress.refresh_from_db()
        self.assertTrue(self.progress.email_verified)

    def test_mark_profile_completed(self):
        """Test marking profile as completed."""
        self.assertFalse(self.progress.profile_completed)
        self.progress.mark_profile_completed()
        self.progress.refresh_from_db()
        self.assertTrue(self.progress.profile_completed)

    def test_mark_profile_completed_sets_completed_at(self):
        """Test marking profile completed sets completed_at if all steps done."""
        self.progress.email_verified = True
        self.progress.category_selected = True
        self.progress.save()
        
        self.progress.mark_profile_completed()
        self.progress.refresh_from_db()
        
        self.assertIsNotNone(self.progress.completed_at)


class OnboardingProgressNextStepTests(TestCase):
    """Tests for get_next_step_url method."""

    def setUp(self):
        self.user = User.objects.create_user(username='stepuser', password='pass')
        self.progress = OnboardingProgress.objects.create(user=self.user)

    def test_next_step_email_not_verified(self):
        """Test next step when email not verified."""
        url = self.progress.get_next_step_url()
        self.assertEqual(url, '/onboarding/check-email/')

    def test_next_step_category_not_selected(self):
        """Test next step when category not selected."""
        self.progress.email_verified = True
        self.progress.save()
        url = self.progress.get_next_step_url()
        self.assertEqual(url, '/onboarding/select-category/')

    def test_next_step_profile_not_completed(self):
        """Test next step when profile not completed."""
        self.progress.email_verified = True
        self.progress.category_selected = True
        self.progress.save()
        url = self.progress.get_next_step_url()
        self.assertEqual(url, '/onboarding/complete-profile/')

    def test_next_step_all_complete(self):
        """Test next step when all steps complete."""
        self.progress.email_verified = True
        self.progress.category_selected = True
        self.progress.profile_completed = True
        self.progress.save()
        url = self.progress.get_next_step_url()
        self.assertIsNone(url)


class EmailVerificationTokenBasicTests(TestCase):
    """Basic tests for EmailVerificationToken model."""

    def setUp(self):
        self.user = User.objects.create_user(username='tokenuser', password='pass')

    def test_token_creation(self):
        """Test creating a verification token."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertEqual(token.user, self.user)
        self.assertIsNotNone(token.token)
        self.assertFalse(token.is_used)

    def test_token_auto_generated(self):
        """Test token is auto-generated."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertTrue(len(token.token) > 0)

    def test_token_str_representation(self):
        """Test token string representation."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertIn(self.user.username, str(token))


class EmailVerificationTokenValidityTests(TestCase):
    """Tests for token validity checking."""

    def setUp(self):
        self.user = User.objects.create_user(username='validityuser', password='pass')

    def test_is_valid_new_token(self):
        """Test is_valid returns True for new token."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid())

    def test_is_valid_used_token(self):
        """Test is_valid returns False for used token."""
        token = EmailVerificationToken.objects.create(user=self.user)
        token.is_used = True
        token.save()
        self.assertFalse(token.is_valid())

    def test_is_valid_expired_token(self):
        """Test is_valid returns False for expired token."""
        token = EmailVerificationToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()
        self.assertFalse(token.is_valid())


class EmailVerificationTokenMarkUsedTests(TestCase):
    """Tests for mark_used method."""

    def setUp(self):
        self.user = User.objects.create_user(username='markuser', password='pass')

    def test_mark_used(self):
        """Test marking token as used."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertFalse(token.is_used)
        token.mark_used()
        token.refresh_from_db()
        self.assertTrue(token.is_used)


class EmailVerificationTokenExpiryTests(TestCase):
    """Tests for token expiry."""

    def setUp(self):
        self.user = User.objects.create_user(username='expiryuser', password='pass')

    def test_default_expiry_24_hours(self):
        """Test default expiry is 24 hours from creation."""
        token = EmailVerificationToken.objects.create(user=self.user)
        expected_expiry = token.created_at + timedelta(days=1)
        self.assertAlmostEqual(
            token.expires_at.timestamp(),
            expected_expiry.timestamp(),
            delta=60  # Allow 60 seconds variance
        )

    def test_token_unique(self):
        """Test token value is unique."""
        from django.db import IntegrityError
        token1 = EmailVerificationToken.objects.create(user=self.user)
        
        # Try to create with same token - this should fail
        with self.assertRaises(IntegrityError):
            EmailVerificationToken.objects.create(
                user=self.user,
                token=token1.token
            )


class EmailVerificationTokenMultipleTokensTests(TestCase):
    """Tests for multiple tokens per user."""

    def setUp(self):
        self.user = User.objects.create_user(username='multiuser', password='pass')

    def test_multiple_tokens_per_user(self):
        """Test user can have multiple tokens."""
        token1 = EmailVerificationToken.objects.create(user=self.user)
        token2 = EmailVerificationToken.objects.create(user=self.user)
        
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 2)
        self.assertNotEqual(token1.token, token2.token)

