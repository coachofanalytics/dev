"""
Onboarding service for managing user registration and verification flow.
"""
import secrets
from datetime import timedelta
from typing import Tuple, Optional
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from onboarding.models import OnboardingProgress, EmailVerificationToken


class OnboardingService:
    """Service for managing user onboarding flow."""

    TOKEN_EXPIRY_HOURS = 24

    @staticmethod
    def create_onboarding_progress(user: User) -> OnboardingProgress:
        """
        Create onboarding progress record for a new user.

        Args:
            user: The User instance

        Returns:
            OnboardingProgress instance
        """
        progress, created = OnboardingProgress.objects.get_or_create(user=user)
        return progress

    @staticmethod
    def generate_verification_token(user: User) -> EmailVerificationToken:
        """
        Generate a unique email verification token for the user.

        Args:
            user: The User instance

        Returns:
            EmailVerificationToken instance
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)

        # Calculate expiry time
        expires_at = timezone.now() + timedelta(hours=OnboardingService.TOKEN_EXPIRY_HOURS)

        # Create the token record
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

        return verification_token

    @staticmethod
    def send_verification_email(user: User, token: str) -> bool:
        """
        Send verification email to user.

        Args:
            user: The User instance
            token: The verification token

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Build verification URL
            site_url = getattr(settings, 'SITE_URL', 'https://biashara.nairobiluxhomes.co.ke')
            verification_url = f"{site_url}/onboarding/verify-email/{token}/"

            # Email subject and message
            subject = 'Verify your Biashara Bridges account'
            message = f"""
Hello {user.first_name},

Thank you for registering with Biashara Bridges!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {OnboardingService.TOKEN_EXPIRY_HOURS} hours.

If you didn't create an account, please ignore this email.

Best regards,
The Biashara Bridges Team
            """

            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Welcome to Biashara Bridges!</h2>
        <p>Hello {user.first_name},</p>
        <p>Thank you for registering with Biashara Bridges!</p>
        <p>Please verify your email address by clicking the button below:</p>
        <a href="{verification_url}" class="button">Verify Email Address</a>
        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{verification_url}">{verification_url}</a></p>
        <p>This link will expire in {OnboardingService.TOKEN_EXPIRY_HOURS} hours.</p>
        <div class="footer">
            <p>If you didn't create an account, please ignore this email.</p>
            <p>Best regards,<br>The Biashara Bridges Team</p>
        </div>
    </div>
</body>
</html>
            """

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            return True

        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False

    @staticmethod
    def verify_email_token(token: str) -> Tuple[bool, Optional[User], str]:
        """
        Verify an email verification token.

        Args:
            token: The verification token string

        Returns:
            Tuple of (success: bool, user: User or None, message: str)
        """
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)

            # Check if token is valid
            if not verification_token.is_valid():
                if verification_token.is_used:
                    return False, None, "This verification link has already been used."
                else:
                    return False, None, "This verification link has expired. Please request a new one."

            # Mark token as used
            verification_token.mark_used()

            # Mark user's email as verified
            user = verification_token.user
            progress = OnboardingProgress.objects.get(user=user)
            progress.mark_email_verified()

            # Mark Django user as active
            user.is_active = True
            user.save(update_fields=['is_active'])

            return True, user, "Email verified successfully! Please complete your profile."

        except EmailVerificationToken.DoesNotExist:
            return False, None, "Invalid verification link."

    @staticmethod
    def resend_verification_email(user: User) -> Tuple[bool, str]:
        """
        Resend verification email to user.

        Args:
            user: The User instance

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if user already verified
            progress = OnboardingProgress.objects.get(user=user)
            if progress.email_verified:
                return False, "Your email is already verified."

            # Invalidate old tokens
            EmailVerificationToken.objects.filter(
                user=user,
                is_used=False
            ).update(is_used=True)

            # Generate new token
            token = OnboardingService.generate_verification_token(user)

            # Send email
            success = OnboardingService.send_verification_email(user, token.token)

            if success:
                return True, "Verification email sent successfully!"
            else:
                return False, "Failed to send verification email. Please try again later."

        except Exception as e:
            print(f"Error resending verification email: {e}")
            return False, "An error occurred. Please try again later."

    @staticmethod
    def check_onboarding_status(user: User) -> dict:
        """
        Check user's onboarding status and return detailed information.

        Args:
            user: The User instance

        Returns:
            Dict with onboarding status information
        """
        try:
            progress = OnboardingProgress.objects.get(user=user)

            return {
                'is_complete': progress.is_complete(),
                'email_verified': progress.email_verified,
                'profile_completed': progress.profile_completed,
                'next_step_url': progress.get_next_step_url(),
                'status': progress.get_status(),
                'created_at': progress.created_at,
                'completed_at': progress.completed_at,
            }

        except OnboardingProgress.DoesNotExist:
            # Create progress if it doesn't exist
            progress = OnboardingService.create_onboarding_progress(user)
            return {
                'is_complete': False,
                'email_verified': False,
                'profile_completed': False,
                'next_step_url': '/onboarding/verify-email/',
                'status': 'Email Verification Pending',
                'created_at': progress.created_at,
                'completed_at': None,
            }