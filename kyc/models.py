"""
KYC (Know Your Customer) Models
Document verification and identity management
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone

User = get_user_model()


class KYCDocument(models.Model):
    """
    KYC Document for user identity verification.
    Supports multiple document types with file scanning and encryption.
    """

    DOCUMENT_TYPE_CHOICES = [
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('business_registration', 'Business Registration Certificate'),
        ('tax_certificate', 'Tax Registration Certificate'),
        ('proof_of_address', 'Proof of Address (Utility Bill)'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other Document'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)

    # File storage
    document_file = models.FileField(
        upload_to='kyc_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        help_text='Allowed formats: PDF, JPG, PNG, DOC, DOCX. Max size: 10MB'
    )

    # Verification status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Document details
    document_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Document ID or reference number (if applicable)'
    )
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)

    # Verification tracking
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_kyc_documents',
        limit_choices_to={'is_staff': True}
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(
        blank=True,
        help_text='Staff notes about verification decision'
    )

    # Security
    is_scanned = models.BooleanField(
        default=False,
        help_text='Whether document was scanned for viruses/malware'
    )
    scan_result = models.CharField(max_length=200, blank=True)
    is_encrypted = models.BooleanField(default=False)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'uploaded_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_document_type_display()} ({self.status})"

    @property
    def is_expired(self) -> bool:
        """Check if document has expired."""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def is_verified(self) -> bool:
        """Check if document is approved."""
        return self.status == 'approved'

    @property
    def requires_review(self) -> bool:
        """Check if document needs review."""
        return self.status in ['pending', 'under_review']

    def approve(self, staff_user: User, notes: str = '') -> None:
        """
        Approve the KYC document and update user verification level.

        Args:
            staff_user: Staff member approving the document
            notes: Optional verification notes
        """
        self.status = 'approved'
        self.verified_by = staff_user
        self.verified_at = timezone.now()
        self.verification_notes = notes
        self.save()
        
        # Update user's verification level
        from .models import KYCVerificationLevel
        level, created = KYCVerificationLevel.objects.get_or_create(user=self.user)
        
        # Mark appropriate verification based on document type
        if self.document_type in ['national_id', 'passport', 'drivers_license']:
            level.identity_verified = True
        elif self.document_type == 'proof_of_address':
            level.address_verified = True
        elif self.document_type == 'business_registration':
            level.business_verified = True
        
        # Recalculate verification level and permissions
        level.update_level()

    def reject(self, staff_user: User, notes: str) -> None:
        """
        Reject the KYC document.

        Args:
            staff_user: Staff member rejecting the document
            notes: Required rejection reason
        """
        self.status = 'rejected'
        self.verified_by = staff_user
        self.verified_at = timezone.now()
        self.verification_notes = notes
        self.save()

    def mark_under_review(self, staff_user: User) -> None:
        """Mark document as under review."""
        self.status = 'under_review'
        self.verified_by = staff_user
        self.save()


class KYCVerificationLevel(models.Model):
    """
    User KYC verification level tracking.
    Defines what level of verification a user has completed.
    """

    LEVEL_CHOICES = [
        ('basic', 'Basic - Email Verified'),
        ('standard', 'Standard - ID Document Verified'),
        ('enhanced', 'Enhanced - ID + Address Verified'),
        ('premium', 'Premium - Full KYC Completed'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='kyc_level',
        primary_key=True
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='basic')

    # Verification flags
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    identity_verified = models.BooleanField(default=False)
    address_verified = models.BooleanField(default=False)
    business_verified = models.BooleanField(default=False)

    # Limits and permissions based on KYC level
    transaction_limit_daily = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Daily transaction limit in USD'
    )
    can_invest = models.BooleanField(default=False)
    can_receive_investment = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'KYC Verification Level'
        verbose_name_plural = 'KYC Verification Levels'

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_level_display()}"

    def update_level(self) -> None:
        """Auto-update verification level based on completed verifications."""
        if (self.email_verified and self.phone_verified and
            self.identity_verified and self.address_verified and self.business_verified):
            self.level = 'premium'
            self.transaction_limit_daily = 100000
            self.can_invest = True
            self.can_receive_investment = True
        elif self.email_verified and self.phone_verified and self.identity_verified and self.address_verified:
            self.level = 'enhanced'
            self.transaction_limit_daily = 10000
            self.can_invest = True
            self.can_receive_investment = True
        elif self.email_verified and self.identity_verified:
            self.level = 'standard'
            self.transaction_limit_daily = 1000
            self.can_invest = False
            self.can_receive_investment = False
        else:
            self.level = 'basic'
            self.transaction_limit_daily = 100
            self.can_invest = False
            self.can_receive_investment = False

        self.save()
