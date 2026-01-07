"""
Views for MFA functionality.
"""

import base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView

from accounts.mfa.forms import (
    BackupCodeForm,
    MFADisableForm,
    MFASetupForm,
    MFAVerifyForm,
)
from accounts.mfa.services import BackupCodesService, TOTPService
from audit.services import AuditService


@method_decorator([login_required, never_cache], name="dispatch")
class MFASetupView(LoginRequiredMixin, FormView):
    """View for setting up MFA."""

    template_name = "mfa/setup.html"
    form_class = MFASetupForm

    def get_context_data(self, **kwargs):
        """Add QR code to context."""
        context = super().get_context_data(**kwargs)

        # Get or create MFA device
        device, created = TOTPService.get_or_create_device(self.request.user)

        # Generate QR code
        qr_code_bytes = TOTPService.generate_qr_code(device)
        qr_code_base64 = base64.b64encode(qr_code_bytes).decode()

        context["qr_code"] = qr_code_base64
        context["secret_key"] = device.secret_key
        context["device"] = device

        return context

    def form_valid(self, form):
        """Verify token and activate MFA."""
        token = form.cleaned_data["token"]
        device = TOTPService.get_device(self.request.user)

        if not device:
            messages.error(self.request, "MFA device not found. Please try again.")
            return redirect("mfa:setup")

        if TOTPService.verify_and_activate(device, token):
            # Generate backup codes
            backup_codes = BackupCodesService.generate_codes(self.request.user)

            # Log MFA enrollment
            AuditService.log_event(
                event_type="mfa_enabled",
                description=f"User {self.request.user.username} enabled MFA",
                user=self.request.user,
                request=self.request,
                severity="info",
            )

            messages.success(
                self.request,
                "Two-factor authentication enabled successfully! "
                "Please save your backup codes in a safe place.",
            )
            return redirect("mfa:backup_codes")
        else:
            messages.error(
                self.request,
                "Invalid verification code. Please try again.",
            )
            return self.form_invalid(form)


@method_decorator([login_required, never_cache], name="dispatch")
class MFABackupCodesView(LoginRequiredMixin, TemplateView):
    """View for displaying backup codes."""

    template_name = "mfa/backup_codes.html"

    def get_context_data(self, **kwargs):
        """Add backup codes to context."""
        context = super().get_context_data(**kwargs)

        backup_codes = BackupCodesService.get_unused_codes(self.request.user)
        context["backup_codes"] = backup_codes
        context["remaining_count"] = len(backup_codes)

        return context


@method_decorator([login_required, never_cache], name="dispatch")
class MFARegenerateCodesView(LoginRequiredMixin, View):
    """View for regenerating backup codes."""

    def post(self, request):
        """Regenerate backup codes."""
        # Verify user has MFA enabled
        if not TOTPService.is_mfa_enabled(request.user):
            messages.error(request, "MFA is not enabled for your account.")
            return redirect("accounts:profile")

        # Regenerate codes
        BackupCodesService.regenerate_codes(request.user)

        # Log event
        AuditService.log_event(
            event_type="mfa_backup_codes_regenerated",
            description=f"User {request.user.username} regenerated backup codes",
            user=request.user,
            request=request,
            severity="info",
        )

        messages.success(
            request,
            "New backup codes generated! Your old backup codes are no longer valid.",
        )
        return redirect("mfa:backup_codes")


@method_decorator([login_required, never_cache], name="dispatch")
class MFADisableView(LoginRequiredMixin, FormView):
    """View for disabling MFA."""

    template_name = "mfa/disable.html"
    form_class = MFADisableForm

    def form_valid(self, form):
        """Verify password and disable MFA."""
        password = form.cleaned_data["password"]

        # Verify password
        if not self.request.user.check_password(password):
            messages.error(self.request, "Incorrect password.")
            return self.form_invalid(form)

        # Disable MFA
        if TOTPService.disable_mfa(self.request.user):
            # Log event
            AuditService.log_event(
                event_type="mfa_disabled",
                description=f"User {self.request.user.username} disabled MFA",
                user=self.request.user,
                request=self.request,
                severity="warning",
            )

            messages.success(
                self.request,
                "Two-factor authentication has been disabled.",
            )
        else:
            messages.error(self.request, "MFA is not enabled for your account.")

        return redirect("accounts:profile")


@method_decorator([never_cache], name="dispatch")
class MFAVerifyView(FormView):
    """View for verifying MFA during login."""

    template_name = "mfa/verify.html"
    form_class = MFAVerifyForm

    def dispatch(self, request, *args, **kwargs):
        """Check if user is in MFA verification state."""
        if not request.session.get("mfa_user_id"):
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add context for template."""
        context = super().get_context_data(**kwargs)
        context["use_backup_code"] = self.request.GET.get("backup") == "1"
        return context

    def form_valid(self, form):
        """Verify TOTP token."""
        from django.contrib.auth import get_user_model, login

        User = get_user_model()

        user_id = self.request.session.get("mfa_user_id")
        token = form.cleaned_data["token"]

        try:
            user = User.objects.get(id=user_id)
            device = TOTPService.get_device(user)

            if not device or not device.is_active:
                messages.error(self.request, "MFA is not configured for this account.")
                return redirect("accounts:login")

            if device.verify_token(token):
                # Clear MFA session data
                del self.request.session["mfa_user_id"]
                self.request.session.pop("mfa_backend", None)

                # Log user in
                backend = self.request.session.get(
                    "mfa_backend", "django.contrib.auth.backends.ModelBackend"
                )
                login(self.request, user, backend=backend)

                # Log successful MFA verification
                AuditService.log_event(
                    event_type="mfa_verified",
                    description=f"User {user.username} completed MFA verification",
                    user=user,
                    request=self.request,
                    severity="info",
                )

                messages.success(self.request, "Login successful!")
                return redirect(self.get_success_url())
            else:
                messages.error(
                    self.request,
                    "Invalid verification code. Please try again or use a backup code.",
                )
                return self.form_invalid(form)

        except User.DoesNotExist:
            messages.error(self.request, "Invalid session. Please log in again.")
            return redirect("accounts:login")

    def get_success_url(self):
        """Get redirect URL after successful verification."""
        return self.request.session.pop("mfa_redirect_url", "/")


@method_decorator([never_cache], name="dispatch")
class MFABackupCodeVerifyView(FormView):
    """View for verifying backup code during login."""

    template_name = "mfa/verify_backup.html"
    form_class = BackupCodeForm

    def dispatch(self, request, *args, **kwargs):
        """Check if user is in MFA verification state."""
        if not request.session.get("mfa_user_id"):
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Verify backup code."""
        from django.contrib.auth import get_user_model, login

        User = get_user_model()

        user_id = self.request.session.get("mfa_user_id")
        code = form.cleaned_data["code"]

        try:
            user = User.objects.get(id=user_id)

            backup_code = BackupCodesService.verify_code(user, code)

            if backup_code:
                # Clear MFA session data
                del self.request.session["mfa_user_id"]
                self.request.session.pop("mfa_backend", None)

                # Log user in
                backend = self.request.session.get(
                    "mfa_backend", "django.contrib.auth.backends.ModelBackend"
                )
                login(self.request, user, backend=backend)

                # Log backup code usage
                AuditService.log_event(
                    event_type="mfa_backup_code_used",
                    description=f"User {user.username} used backup code for login",
                    user=user,
                    request=self.request,
                    severity="warning",
                )

                # Get remaining codes count
                remaining = BackupCodesService.get_remaining_count(user)

                if remaining <= 2:
                    messages.warning(
                        self.request,
                        f"Login successful! You have only {remaining} backup code(s) remaining. "
                        "Please regenerate your backup codes soon.",
                    )
                else:
                    messages.success(
                        self.request,
                        f"Login successful! You have {remaining} backup codes remaining.",
                    )

                return redirect(self.get_success_url())
            else:
                messages.error(
                    self.request,
                    "Invalid backup code. Please try again.",
                )
                return self.form_invalid(form)

        except User.DoesNotExist:
            messages.error(self.request, "Invalid session. Please log in again.")
            return redirect("accounts:login")

    def get_success_url(self):
        """Get redirect URL after successful verification."""
        return self.request.session.pop("mfa_redirect_url", "/")
