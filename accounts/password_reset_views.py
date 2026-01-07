"""
Secure password reset views that prevent account enumeration.

These views always show the same success message regardless of whether
the email exists in the system, following OWASP security best practices.
"""

from typing import Dict, Any
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.http import HttpResponse
from django.urls import reverse_lazy
from accounts.password_reset_forms import SecurePasswordResetForm
import logging

logger = logging.getLogger(__name__)


class SecurePasswordResetView(DjangoPasswordResetView):
    """
    Custom password reset view that prevents account enumeration.

    Always shows the same success message whether or not the email exists.
    This prevents attackers from using the password reset feature to
    discover which emails are registered in the system.
    """

    form_class = SecurePasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form: SecurePasswordResetForm) -> HttpResponse:
        """
        Process the form when valid.

        Shows success message if email sent, error message if failed.
        """
        # The form's save() method will send the email if the address exists
        result = form.save(
            request=self.request,
            use_https=self.request.is_secure(),
            email_template_name=self.email_template_name,
            subject_template_name=self.subject_template_name,
        )

        # Check if email was sent successfully
        if result.get('success'):
            return self.render_to_response(self.get_context_data(form=form, email_sent=True))
        else:
            error_msg = result.get('error', 'Unable to send password reset email. Please try again later.')
            return self.render_to_response(self.get_context_data(form=form, email_error=error_msg))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)

        # Add flag to show success message if email was sent
        if kwargs.get('email_sent'):
            context['email_sent'] = True
            context['success_message'] = (
                "If an account exists with that email address, you will receive "
                "password reset instructions shortly."
            )

        return context
