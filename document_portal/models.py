from django.db import models
from django.conf import settings
from django.utils import timezone

# ====================
# Choices
# ====================
ACCESS_TYPE_CHOICES = [
    ("read_only", "Read-only"),
    ("download", "Download"),
    ("view", "View"),
    ("update", "Update"),
]

PAYMENT_METHODS = [
    ("mtn", "MTN Mobile Money"),
    ("airtel", "Airtel Money"),
    ("card", "Debit/Credit Card"),
    ("cash_agent", "Cash/Agents"),
    ("bank", "Bank Account"),
]

PAYMENT_STATUS = [
    ("pending", "Pending"),
    ("verified", "Verified"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
]

DOCUMENT_STATUS_CHOICES = [
    ("valid", "Valid"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
]

APPLICATION_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("pending_payment", "Pending Payment"),
    ("paid", "Paid"),
    ("processing", "Processing"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("completed", "Completed"),
]

# ====================
# Models
# ====================

class DocumentService(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DocumentApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application_number = models.CharField(max_length=50, unique=True)
    service = models.ForeignKey(DocumentService, on_delete=models.PROTECT)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    reason_for_request = models.CharField(max_length=150)

    status = models.CharField(max_length=30, choices=APPLICATION_STATUS_CHOICES, default="draft")
    fee = models.DecimalField(max_digits=10, decimal_places=2)

    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ApplicationDraft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application = models.OneToOneField(
        DocumentApplication,
        on_delete=models.CASCADE,
        related_name="draft"
    )
    data_snapshot = models.JSONField(default=dict)
    completion_percentage = models.PositiveIntegerField(default=0)
    last_completed_step = models.PositiveIntegerField(default=1)
    last_modified = models.DateTimeField(auto_now=True)


class DocumentDraft(models.Model):
    application = models.OneToOneField(DocumentApplication, on_delete=models.CASCADE)
    completion_percentage = models.IntegerField(default=0)
    draft_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Draft for {self.application}"


class GeneratedDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application = models.ForeignKey(DocumentApplication, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    document_type = models.CharField(max_length=100)
    issue_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default="valid")
    file = models.FileField(upload_to="generated_documents/")
    created_at = models.DateTimeField(auto_now_add=True)


class DataAccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution = models.CharField(max_length=150)
    data_accessed = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    access_type = models.CharField(max_length=30, choices=ACCESS_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_portal_payments"
    )
    application = models.OneToOneField(
        DocumentApplication,
        on_delete=models.CASCADE,
        related_name="payment"
    )
    method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_reference = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default="pending")
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)