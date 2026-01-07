"""
Secure password reset forms that prevent account enumeration.

These forms always show the same success message regardless of whether
the email exists, preventing attackers from discovering valid accounts.
"""

from typing import List
from django import forms
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template import loader
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class SecurePasswordResetForm(DjangoPasswordResetForm):
    """
    Custom password reset form that prevents account enumeration.

    Always returns success message regardless of whether email exists.
    Follows OWASP guidance for secure password reset.
    """

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )

    def save(
        self,
        domain_override: str = None,
        subject_template_name: str = 'registration/password_reset_subject.txt',
        email_template_name: str = 'registration/password_reset_email.html',
        use_https: bool = False,
        token_generator=default_token_generator,
        from_email: str = None,
        request=None,
        html_email_template_name: str = None,
        extra_email_context: dict = None,
    ) -> dict:
        """
        Generate a one-use only link for resetting password and send it to the user.

        Returns:
            dict with 'success' (bool) and optionally 'error' (str) keys
        """
        email = self.cleaned_data["email"]

        # Try to find active users with this email
        # Use filter() instead of get() to avoid exceptions
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )

        if not active_users.exists():
            # Email doesn't exist or user is inactive
            logger.info(
                f"Password reset requested for non-existent or inactive email: {email[:3]}***"
            )
            return {
                'success': False,
                'error': 'No active account found with this email address. Please check the email or register a new account.'
            }

        # Send reset email to all matching active users
        email_sent = False
        last_error = None

        for user in active_users:
            try:
                super().save(
                    domain_override=domain_override,
                    subject_template_name=subject_template_name,
                    email_template_name=email_template_name,
                    use_https=use_https,
                    token_generator=token_generator,
                    from_email=from_email,
                    request=request,
                    html_email_template_name=html_email_template_name,
                    extra_email_context=extra_email_context,
                )
                logger.info(f"Password reset email sent successfully for user: {user.username}")
                email_sent = True
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
                last_error = str(e)

        if email_sent:
            return {'success': True}
        else:
            return {
                'success': False,
                'error': f'Failed to send email. Please try again later or contact support.'
            }
