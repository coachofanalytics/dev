"""
Admin interface for onboarding models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import OnboardingProgress, EmailVerificationToken


@admin.register(OnboardingProgress)
class OnboardingProgressAdmin(admin.ModelAdmin):
    """Admin interface for OnboardingProgress."""

    list_display = [
        'user_link',
        'status_badge',
        'email_verified_check',
        'profile_completed_check',
        'created_at',
        'completed_at'
    ]
    list_filter = [
        'email_verified',
        'profile_completed',
        'created_at',
        'completed_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    readonly_fields = [
        'user',
        'created_at',
        'completed_at',
        'get_status'
    ]

    def user_link(self, obj):
        """Link to user admin page."""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'

    def status_badge(self, obj):
        """Display status as colored badge."""
        status = obj.get_status()
        if status == "Complete":
            color = 'green'
        elif 'verified' in status.lower():
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    status_badge.short_description = 'Status'

    def email_verified_check(self, obj):
        """Display email verification status."""
        if obj.email_verified:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    email_verified_check.short_description = 'Email'

    def profile_completed_check(self, obj):
        """Display profile completion status."""
        if obj.profile_completed:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    profile_completed_check.short_description = 'Profile'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin interface for EmailVerificationToken."""

    list_display = [
        'user',
        'token_preview',
        'status_badge',
        'created_at',
        'expires_at'
    ]
    list_filter = [
        'is_used',
        'created_at',
        'expires_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'token'
    ]
    readonly_fields = [
        'user',
        'token',
        'created_at',
        'expires_at',
        'is_used'
    ]

    def token_preview(self, obj):
        """Show first 10 and last 10 characters of token."""
        if len(obj.token) > 20:
            return f"{obj.token[:10]}...{obj.token[-10:]}"
        return obj.token
    token_preview.short_description = 'Token'

    def status_badge(self, obj):
        """Display token status as colored badge."""
        if obj.is_used:
            status = 'Used'
            color = 'gray'
        elif obj.is_valid():
            status = 'Active'
            color = 'green'
        else:
            status = 'Expired'
            color = 'red'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    status_badge.short_description = 'Status'
