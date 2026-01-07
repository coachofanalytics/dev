"""
GDPR Compliance models.

Implements GDPR requirements:
- Article 15: Right to access (data export)
- Article 17: Right to erasure (right to be forgotten)
- Consent management
- Data processing records
"""

import uuid
from typing import Optional

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class ConsentRecord(models.Model):
    """
    Track user consent for data processing.

    GDPR Article 7: Conditions for consent
    GDPR Article 13: Information to be provided
    """

    CONSENT_TYPE_CHOICES = [
        ("terms_of_service", "Terms of Service"),
        ("privacy_policy", "Privacy Policy"),
        ("marketing", "Marketing Communications"),
        ("analytics", "Analytics & Tracking"),
        ("third_party_sharing", "Third-Party Data Sharing"),
        ("cookies", "Cookie Usage"),
        ("data_processing", "Data Processing"),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="consent_records",
        help_text="User who gave consent",
    )

    # Consent details
    consent_type = models.CharField(
        max_length=50,
        choices=CONSENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of consent given",
    )

    is_given = models.BooleanField(
        default=False,
        help_text="Whether consent is currently given",
    )

    version = models.CharField(
        max_length=20,
        help_text="Version of policy/terms user consented to",
    )

    # Metadata
    consent_text = models.TextField(
        blank=True,
        help_text="Full text of what user consented to",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when consent was given",
    )

    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="Browser user agent when consent was given",
    )

    # Timestamps
    given_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consent was given",
    )

    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consent was withdrawn",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gdpr_consent_record"
        verbose_name = "Consent Record"
        verbose_name_plural = "Consent Records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "consent_type"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        status = "Given" if self.is_given else "Withdrawn"
        return f"{self.user.username} - {self.get_consent_type_display()} ({status})"

    def give_consent(
        self,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Record that user gave consent.

        Args:
            ip_address: IP address of user
            user_agent: Browser user agent
        """
        self.is_given = True
        self.given_at = timezone.now()
        self.withdrawn_at = None
        if ip_address is not None:
            self.ip_address = ip_address
        if user_agent is not None:
            self.user_agent = user_agent
        self.save()

    def withdraw_consent(self) -> None:
        """Record that user withdrew consent."""
        self.is_given = False
        self.withdrawn_at = timezone.now()
        self.save()


class DataExportRequest(models.Model):
    """
    Track requests for user data export.

    GDPR Article 15: Right of access by the data subject
    GDPR Article 20: Right to data portability
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("expired", "Expired"),
    ]

    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("csv", "CSV"),
        ("pdf", "PDF"),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="data_export_requests",
        help_text="User requesting data export",
    )

    # Request details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    export_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default="json",
        help_text="Format for exported data",
    )

    # File information
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to exported file",
    )

    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Size of exported file in bytes",
    )

    download_count = models.IntegerField(
        default=0,
        help_text="Number of times file was downloaded",
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When export file expires (30 days)",
    )
    last_downloaded_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if export failed",
    )

    class Meta:
        db_table = "gdpr_data_export_request"
        verbose_name = "Data Export Request"
        verbose_name_plural = "Data Export Requests"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["user", "-requested_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user.username} - {self.get_status_display()} - {self.requested_at.strftime('%Y-%m-%d')}"

    def mark_processing(self) -> None:
        """Mark request as processing."""
        self.status = "processing"
        self.save()

    def mark_completed(self, file_path: str, file_size: int) -> None:
        """
        Mark request as completed.

        Args:
            file_path: Path to exported file
            file_size: Size of file in bytes
        """
        self.status = "completed"
        self.file_path = file_path
        self.file_size = file_size
        self.processed_at = timezone.now()
        # Set expiry to 30 days from now
        self.expires_at = timezone.now() + timezone.timedelta(days=30)
        self.save()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark request as failed.

        Args:
            error_message: Error description
        """
        self.status = "failed"
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save()

    def record_download(self) -> None:
        """Record that file was downloaded."""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()

    @property
    def is_expired(self) -> bool:
        """Check if export has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class DataDeletionRequest(models.Model):
    """
    Track requests for account and data deletion.

    GDPR Article 17: Right to erasure ('right to be forgotten')
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("grace_period", "Grace Period"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="data_deletion_requests",
        help_text="User requesting deletion",
    )

    # Backup user info (in case user is deleted)
    username = models.CharField(max_length=150)
    email = models.EmailField()

    # Request details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    reason = models.TextField(
        blank=True,
        help_text="User's reason for deletion (optional)",
    )

    # Grace period (30 days to change mind)
    grace_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End of 30-day grace period",
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_deletion_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When deletion is scheduled to occur",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When deletion was completed",
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When request was cancelled",
    )

    # Deletion metadata
    data_removed = models.JSONField(
        default=dict,
        blank=True,
        help_text="Record of what data was removed",
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if deletion failed",
    )

    class Meta:
        db_table = "gdpr_data_deletion_request"
        verbose_name = "Data Deletion Request"
        verbose_name_plural = "Data Deletion Requests"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["user", "-requested_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_deletion_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.username} - {self.get_status_display()} - {self.requested_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        """Capture username and email before save."""
        if self.user and not self.username:
            self.username = self.user.username
            self.email = self.user.email
        super().save(*args, **kwargs)

    def start_grace_period(self) -> None:
        """Start 30-day grace period."""
        self.status = "grace_period"
        self.grace_period_end = timezone.now() + timezone.timedelta(days=30)
        self.scheduled_deletion_at = self.grace_period_end
        self.save()

    def cancel_request(self) -> None:
        """Cancel deletion request."""
        if self.status in ["completed", "cancelled"]:
            raise ValidationError("Cannot cancel completed or already cancelled request")

        self.status = "cancelled"
        self.cancelled_at = timezone.now()
        self.save()

    def mark_processing(self) -> None:
        """Mark request as processing."""
        self.status = "processing"
        self.save()

    def mark_completed(self, data_removed: dict) -> None:
        """
        Mark request as completed.

        Args:
            data_removed: Dictionary of removed data
        """
        self.status = "completed"
        self.deleted_at = timezone.now()
        self.data_removed = data_removed
        self.save()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark request as failed.

        Args:
            error_message: Error description
        """
        self.status = "failed"
        self.error_message = error_message
        self.save()

    @property
    def is_in_grace_period(self) -> bool:
        """Check if still in grace period."""
        if not self.grace_period_end:
            return False
        return timezone.now() < self.grace_period_end

    @property
    def days_until_deletion(self) -> int:
        """Get days until scheduled deletion."""
        if not self.scheduled_deletion_at:
            return 0
        delta = self.scheduled_deletion_at - timezone.now()
        return max(0, delta.days)


class PrivacyPolicyVersion(models.Model):
    """
    Track versions of privacy policy for consent tracking.

    GDPR Article 13: Information to be provided
    """

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Version info
    version = models.CharField(
        max_length=20,
        unique=True,
        help_text="Version number (e.g., '1.0', '1.1')",
    )

    title = models.CharField(
        max_length=200,
        help_text="Title of privacy policy",
    )

    content = models.TextField(
        help_text="Full text of privacy policy",
    )

    summary = models.TextField(
        blank=True,
        help_text="Summary of key changes",
    )

    # Status
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this is the current active version",
    )

    # Timestamps
    effective_date = models.DateTimeField(
        help_text="When this version becomes effective",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="privacy_policies_created",
    )

    class Meta:
        db_table = "gdpr_privacy_policy_version"
        verbose_name = "Privacy Policy Version"
        verbose_name_plural = "Privacy Policy Versions"
        ordering = ["-effective_date"]
        indexes = [
            models.Index(fields=["-effective_date"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        status = "Active" if self.is_active else "Inactive"
        return f"Privacy Policy v{self.version} ({status})"

    def save(self, *args, **kwargs):
        """Ensure only one active version."""
        if self.is_active:
            # Deactivate all other versions
            PrivacyPolicyVersion.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
