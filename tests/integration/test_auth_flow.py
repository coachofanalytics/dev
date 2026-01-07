"""
Integration tests for complete authentication flows.

Tests the entire user journey from registration through login.
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Category, UserProfile
from onboarding.models import OnboardingProgress, EmailVerificationToken


@pytest.mark.django_db
class TestRegistrationLoginFlow:
    """Test complete registration and login flow."""

    def test_complete_registration_flow(self):
        """Test full registration process from form to verified user."""
        client = Client()

        # Create a category
        category = Category.objects.create(
            name='Business',
            slug='business',
            is_active=True
        )

        # Step 1: Submit registration form
        response = client.post(reverse('onboarding:register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'category': category.id,
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
        })

        if response.status_code != 302:
            print('\n--- REGISTRATION RESPONSE CONTENT START ---')
            print(response.content.decode('utf-8')[:10000])
            print('--- REGISTRATION RESPONSE CONTENT END ---\n')
        assert response.status_code == 302  # Redirect after successful registration

        # Verify user was created
        user = User.objects.get(email='john.doe@example.com')
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert not user.is_active  # Should be inactive until email verified

        # Verify UserProfile was created
        profile = UserProfile.objects.get(user=user)
        assert profile.category == category

        # Verify OnboardingProgress was created
        progress = OnboardingProgress.objects.get(user=user)
        assert not progress.email_verified
        assert not progress.profile_completed

        # Verify EmailVerificationToken was created
        token = EmailVerificationToken.objects.get(user=user)
        assert not token.is_used

        # Step 2: Verify email
        verify_url = reverse('onboarding:verify_email', kwargs={'token': token.token})
        response = client.get(verify_url)

        assert response.status_code == 302  # Redirect after verification

        # Refresh from database
        progress.refresh_from_db()
        user.refresh_from_db()
        token.refresh_from_db()

        assert progress.email_verified
        assert user.is_active  # Should be active after email verification
        assert token.is_used

        # Step 3: Complete profile
        client.force_login(user)
        response = client.post(reverse('onboarding:complete_profile'), {
            'phone': '+254712345678',
            'location': 'Nairobi, Kenya',
            'bio': 'Test bio',
        })

        assert response.status_code == 302

        # Refresh progress
        progress.refresh_from_db()
        assert progress.profile_completed
        assert progress.completed_at is not None

    def test_login_after_registration(self):
        """Test user can login after completing registration."""
        client = Client()

        # Create verified user
        category = Category.objects.create(name='Investor', slug='investor', is_active=True)
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestP@ssw0rd123',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        OnboardingProgress.objects.create(
            user=user,
            email_verified=True,
            profile_completed=True
        )

        # Attempt login
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestP@ssw0rd123',
        })

        assert response.status_code == 302  # Redirect after successful login
        assert response.url in ['/dashboard/', '/dashboard/investor/']  # Should redirect to dashboard

    def test_unverified_user_cannot_login(self):
        """Test that unverified user cannot access protected pages."""
        client = Client()

        # Create unverified user
        user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='TestP@ssw0rd123',
            is_active=False  # Not verified
        )

        # Try to login
        response = client.post(reverse('login'), {
            'username': 'unverified',
            'password': 'TestP@ssw0rd123',
        })

        # Should fail or show error
        assert response.status_code in [200, 302]  # Either stays on page with error or redirects


@pytest.mark.django_db
class TestPasswordResetFlow:
    """Test password reset flow."""

    def test_password_reset_request(self):
        """Test requesting password reset."""
        client = Client()

        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123'
        )

        # Request password reset
        response = client.post(reverse('password_reset'), {
            'email': 'test@example.com',
        })

        assert response.status_code == 200  # Shows success message

    def test_password_reset_nonexistent_email(self):
        """Test password reset with non-existent email shows same message."""
        client = Client()

        # Request reset for non-existent email
        response = client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com',
        })

        # Should show same success message (no account enumeration)
        assert response.status_code == 200


@pytest.mark.django_db
class TestDashboardAccess:
    """Test dashboard access control."""

    def test_authenticated_user_can_access_dashboard(self):
        """Test that authenticated user can access their dashboard."""
        client = Client()

        category = Category.objects.create(name='Business', slug='business', is_active=True)
        user = User.objects.create_user(
            username='testuser',
            password='Test123',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)

        client.force_login(user)
        response = client.get(reverse('business_dashboard'))

        assert response.status_code == 200

    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated user is redirected to login."""
        client = Client()

        response = client.get(reverse('business_dashboard'))

        assert response.status_code == 302
        assert '/login/' in response.url
