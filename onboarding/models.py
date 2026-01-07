"""
Onboarding models for tracking user registration and profile completion.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import secrets


def default_token_expiry():
    return timezone.now() + timedelta(days=1)


def default_token_value():
    return secrets.token_urlsafe(32)


class OnboardingProgress(models.Model):
    """
    Tracks user onboarding progress through registration and profile completion.

    Flow:
    1. User registers with basic info (first_name, last_name, email, category)
    2. Email verification sent → email_verified = True
    3. User completes full profile → profile_completed = True
    4. Onboarding complete → completed_at timestamp set
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding_progress',
        primary_key=True
    )
    email_verified = models.BooleanField(
        default=False,
        help_text='True if user clicked email verification link'
    )
    profile_completed = models.BooleanField(
        default=False,
        help_text='True if user completed full profile information'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When user first registered'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When user completed all onboarding steps'
    )
    category_selected = models.BooleanField(
        default=False,
        help_text='True if user has selected their category'
    )

    class Meta:
        verbose_name = 'Onboarding Progress'
        verbose_name_plural = 'Onboarding Progress Records'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_status()}"

    def get_status(self) -> str:
        """Get human-readable onboarding status."""
        if self.is_complete():
            return "Complete"
        elif self.profile_completed:
            return "Profile Completed (waiting verification)"
        elif self.email_verified:
            return "Email Verified (profile pending)"
        else:
            return "Email Verification Pending"

    def is_complete(self) -> bool:
        """Check if onboarding is fully complete."""
        return self.email_verified and self.category_selected and self.profile_completed and self.completed_at is not None

    def mark_email_verified(self) -> None:
        """Mark email as verified."""
        self.email_verified = True
        self.save(update_fields=['email_verified'])

    def mark_profile_completed(self) -> None:
        """Mark profile as completed and set completion timestamp if all steps done."""
        self.profile_completed = True
        if self.email_verified and self.category_selected and not self.completed_at:
            self.completed_at = timezone.now()
        self.save(update_fields=['profile_completed', 'completed_at'])

    def get_next_step_url(self) -> str:
        """Get the URL for the next onboarding step."""
        if not self.email_verified:
            return '/onboarding/check-email/'
        elif not self.category_selected:
            return '/onboarding/select-category/'
        elif not self.profile_completed:
            return '/onboarding/complete-profile/'
        else:
            # Don't return /dashboard/ to avoid redirect loops
            # The calling code should handle completed onboarding
            return None


class EmailVerificationToken(models.Model):
    """
    Temporary tokens for email verification.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.CharField(
        max_length=100,
        unique=True,
        default=default_token_value,
        help_text='Unique verification token'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        default=default_token_expiry,
        help_text='When this token expires (24 hours from creation)'
    )
    is_used = models.BooleanField(
        default=False,
        help_text='True if token has been used'
    )

    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Token for {self.user.username} ({'used' if self.is_used else 'active'})"

    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_used(self) -> None:
        """Mark token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])
