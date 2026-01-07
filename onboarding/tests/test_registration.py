"""
Tests for onboarding app - registration and email verification.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Category
from onboarding.models import OnboardingProgress, EmailVerificationToken
from onboarding.services.onboarding_service import OnboardingService


class RegistrationTestCase(TestCase):
    """Tests for user registration functionality."""

    def setUp(self):
        """Set up test client and categories."""
        self.client = Client()
        self.individual = Category.objects.create(
            name='Individual', slug='individual', is_active=True
        )
        self.business = Category.objects.create(
            name='Business', slug='business', is_active=True
        )
        self.investor = Category.objects.create(
            name='Investor', slug='investor', is_active=True
        )

    def test_registration_page_loads(self):
        """Test that registration page loads successfully."""
        response = self.client.get(reverse('onboarding:register'))
        self.assertEqual(response.status_code, 200)

    def test_registration_page_shows_active_categories(self):
        """Test that registration form shows only active categories."""
        response = self.client.get(reverse('onboarding:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Individual')
        self.assertContains(response, 'Business')
        self.assertContains(response, 'Investor')

    def test_registration_with_valid_data(self):
        """Test registration with valid data creates user."""
        response = self.client.post(reverse('onboarding:register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'category': self.individual.id,
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        })
        user_exists = User.objects.filter(email='john.doe@example.com').exists()
        self.assertTrue(user_exists)

    def test_registration_with_existing_email(self):
        """Test registration with existing email shows error."""
        User.objects.create_user(
            username='existing', email='existing@example.com', password='testpass123'
        )
        response = self.client.post(reverse('onboarding:register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'existing@example.com',
            'category': self.individual.id,
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_registration_with_mismatched_passwords(self):
        """Test registration with mismatched passwords shows error."""
        response = self.client.post(reverse('onboarding:register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'category': self.individual.id,
            'password': 'securepass123',
            'password_confirm': 'differentpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')

    def test_registration_creates_inactive_user(self):
        """Test that registered user is inactive until email verified."""
        self.client.post(reverse('onboarding:register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'category': self.individual.id,
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        })
        user = User.objects.get(email='john.doe@example.com')
        self.assertFalse(user.is_active)


class EmailVerificationTestCase(TestCase):
    """Tests for email verification functionality."""

    def setUp(self):
        """Set up test client, user and verification token."""
        self.client = Client()
        self.category = Category.objects.create(
            name='Individual', slug='individual', is_active=True
        )
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='testpass123', is_active=False
        )
        self.user.profile.category = self.category
        self.user.profile.save()
        self.progress = OnboardingProgress.objects.create(
            user=self.user, email_verified=False, profile_completed=False
        )
        self.token = EmailVerificationToken.objects.create(user=self.user)

    def test_check_email_page_loads(self):
        """Test that check email page loads successfully."""
        response = self.client.get(reverse('onboarding:check_email'))
        self.assertEqual(response.status_code, 200)

    def test_verify_email_with_valid_token(self):
        """Test email verification with valid token activates user."""
        self.client.get(reverse('onboarding:verify_email', args=[self.token.token]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_verify_email_with_invalid_token(self):
        """Test email verification with invalid token redirects."""
        response = self.client.get(
            reverse('onboarding:verify_email', args=['invalid-token-12345'])
        )
        self.assertIn(response.status_code, [200, 302])

    def test_verification_token_marked_as_used(self):
        """Test that verification token is marked as used after verification."""
        self.client.get(reverse('onboarding:verify_email', args=[self.token.token]))
        self.token.refresh_from_db()
        self.assertTrue(self.token.is_used)


class OnboardingServiceTestCase(TestCase):
    """Tests for OnboardingService functionality."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name='Individual', slug='individual', is_active=True
        )
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='testpass123', is_active=False
        )

    def test_create_onboarding_progress(self):
        """Test creating onboarding progress."""
        progress = OnboardingService.create_onboarding_progress(self.user)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.user, self.user)

    def test_generate_verification_token(self):
        """Test generating verification token."""
        token = OnboardingService.generate_verification_token(self.user)
        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.is_used)

    def test_verify_email_token_success(self):
        """Test successful email token verification."""
        OnboardingProgress.objects.create(user=self.user)
        token = EmailVerificationToken.objects.create(user=self.user)
        success, user, message = OnboardingService.verify_email_token(token.token)
        self.assertTrue(success)
        self.assertEqual(user, self.user)

    def test_verify_email_token_invalid(self):
        """Test invalid email token verification."""
        success, user, message = OnboardingService.verify_email_token('invalid-token')
        self.assertFalse(success)
        self.assertIsNone(user)
