"""
Audit logging models for compliance and security tracking.

This module provides immutable audit logging capabilities to track all
significant events in the system for compliance with ISO 27001 and other
regulatory requirements.
"""

import uuid
from typing import Optional, Dict, Any

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """
    Immutable audit log for tracking all system events.

    This model stores all significant events for compliance and security
    auditing. Records are immutable after creation to ensure data integrity.
    """

    EVENT_TYPE_CHOICES = [
        # Authentication events
        ("login_success", "Login Successful"),
        ("login_failed", "Login Failed"),
        ("logout", "Logout"),
        ("password_changed", "Password Changed"),
        ("password_reset_requested", "Password Reset Requested"),
        ("password_reset_completed", "Password Reset Completed"),
        # MFA events (for future implementation)
        ("mfa_enabled", "MFA Enabled"),
        ("mfa_disabled", "MFA Disabled"),
        ("mfa_verified", "MFA Verified"),
        ("mfa_failed", "MFA Verification Failed"),
        # User management
        ("user_created", "User Created"),
        ("user_updated", "User Updated"),
        ("user_deleted", "User Deleted"),
        ("user_activated", "User Activated"),
        ("user_deactivated", "User Deactivated"),
        # Profile management
        ("profile_updated", "Profile Updated"),
        ("profile_viewed", "Profile Viewed"),
        # Payment events
        ("payment_initiated", "Payment Initiated"),
        ("payment_completed", "Payment Completed"),
        ("payment_failed", "Payment Failed"),
        ("payment_refunded", "Payment Refunded"),
        # Subscription events
        ("subscription_created", "Subscription Created"),
        ("subscription_renewed", "Subscription Renewed"),
        ("subscription_cancelled", "Subscription Cancelled"),
        ("subscription_expired", "Subscription Expired"),
        # Data events (GDPR)
        ("data_exported", "Data Exported"),
        ("data_deleted", "Data Deleted"),
        ("consent_given", "Consent Given"),
        ("consent_withdrawn", "Consent Withdrawn"),
        # Security events
        ("suspicious_activity", "Suspicious Activity Detected"),
        ("account_locked", "Account Locked"),
        ("account_unlocked", "Account Unlocked"),
        ("permission_changed", "Permission Changed"),
        # System events
        ("admin_action", "Admin Action"),
        ("system_error", "System Error"),
        ("api_access", "API Access"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ]

    # Primary key - UUID for uniqueness and security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="info", db_index=True
    )
    description = models.TextField(help_text="Human-readable description of the event")

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who triggered the event",
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        help_text="Username at time of event (preserved even if user deleted)",
    )

    # Generic foreign key for linking to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, help_text="Browser/client user agent")
    request_method = models.CharField(max_length=10, blank=True, help_text="HTTP method")
    request_path = models.CharField(max_length=500, blank=True, help_text="Request URL path")

    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data (old/new values, error details, etc.)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_log"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["ip_address", "-created_at"]),
        ]
        # Make logs immutable - no updates or deletes
        permissions = [
            ("view_audit_log", "Can view audit logs"),
            ("export_audit_log", "Can export audit logs"),
        ]

    def __str__(self) -> str:
        """Return string representation of audit log."""
        user_str = self.username or "Anonymous"
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {user_str} - {self.get_event_type_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save audit log.

        Ensures username is captured from user if not provided.
        Prevents updates to existing records.
        """
        # Prevent updates - audit logs are immutable
        # Use _state.adding to check if this is a new instance
        if not self._state.adding:
            raise ValueError("Audit logs are immutable and cannot be updated")

        # Capture username from user if not provided
        if self.user and not self.username:
            self.username = self.user.username

        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Prevent deletion of audit logs."""
        raise ValueError("Audit logs are immutable and cannot be deleted")


class LoginHistory(models.Model):
    """
    Detailed login history for security monitoring.

    Tracks all login attempts (successful and failed) with device
    fingerprinting and geolocation data for anomaly detection.
    """

    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("blocked", "Blocked"),
    ]

    FAILURE_REASON_CHOICES = [
        ("invalid_credentials", "Invalid Credentials"),
        ("account_disabled", "Account Disabled"),
        ("account_locked", "Account Locked"),
        ("mfa_required", "MFA Required"),
        ("mfa_failed", "MFA Failed"),
        ("rate_limited", "Rate Limited"),
        ("suspicious_activity", "Suspicious Activity"),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_history",
    )
    username = models.CharField(max_length=150, db_index=True)

    # Login details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    failure_reason = models.CharField(
        max_length=50, choices=FAILURE_REASON_CHOICES, blank=True, null=True
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(db_index=True, null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    # Device fingerprinting
    device_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        help_text="Unique device identifier hash",
        db_index=True,
    )
    device_type = models.CharField(
        max_length=50, blank=True, help_text="desktop, mobile, tablet, etc."
    )
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True, verbose_name="Operating System")

    # Geolocation
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Session information
    session_key = models.CharField(max_length=40, blank=True)

    # Risk scoring (for future use with risk-based authentication)
    risk_score = models.IntegerField(
        default=0,
        help_text="Risk score 0-100, higher is riskier",
    )

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "login_history"
        verbose_name = "Login History"
        verbose_name_plural = "Login Histories"
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["-attempted_at"]),
            models.Index(fields=["user", "-attempted_at"]),
            models.Index(fields=["username", "-attempted_at"]),
            models.Index(fields=["ip_address", "-attempted_at"]),
            models.Index(fields=["status", "-attempted_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of login history."""
        return f"{self.username} - {self.get_status_display()} - {self.attempted_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def is_suspicious(self) -> bool:
        """Check if login attempt has high risk score."""
        return self.risk_score >= 70

    @property
    def location(self) -> str:
        """Get formatted location string."""
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        elif self.country:
            return self.country
        return "Unknown"
