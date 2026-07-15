from django.db import models
from django.conf import settings

# Create your models here.

class Application(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("payment_pending", "Payment Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_applications"
    )

    application_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
    )

    service = models.CharField(max_length=100)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=50)

    district = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    reason = models.CharField(max_length=255)

    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    notify_by_phone = models.BooleanField(default=False)
    notify_by_email = models.BooleanField(default=False)

    certified = models.BooleanField(default=False)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="draft"
    )

    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    current_step = models.PositiveSmallIntegerField(default=1)
    completion_percentage = models.PositiveSmallIntegerField(default=0)

    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payment(models.Model):
    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("airtel", "Airtel Money"),
        ("card", "Debit/Credit Card"),
        ("cash", "Cash/Agent"),
        ("bank", "Bank Account"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    bill_id = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    payer_phone = models.CharField(max_length=30, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

class GeneratedDocument(models.Model):
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("valid", "Valid"),
        ("expired", "Expired"),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="valid"
    )

    issued_at = models.DateTimeField(auto_now_add=True)

class DataAccessLog(models.Model):
    ACCESS_TYPES = [
        ("view", "Read Only"),
        ("download", "Download"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="data_access_logs"
    )

    institution = models.CharField(max_length=255)
    data_accessed = models.CharField(max_length=255)
    purpose = models.TextField()

    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES
    )

    created_at = models.DateTimeField(auto_now_add=True)

