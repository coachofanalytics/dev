from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import  Group
from django.db import models
from django.utils import timezone
# from django_countries.fields import CountryField
from django.core.exceptions import ValidationError
# from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from accounts.choices import CategoryChoices, SubCategoryChoices
from django_countries.fields import CountryField

def validate_resume_size(file):
    maximum_size = 5 * 1024 * 1024  # 5 MB
    if file.size > maximum_size:
        raise ValidationError("The resume file must not exceed 5 MB.")


class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField(
        'CustomerUser',
        related_name='user_groups',
        blank=True
    )

    class Meta:
        verbose_name_plural = "User Groups"


class CustomerUser(AbstractUser):
    class GenderChoices(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, 'Unknown')

    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.sub_category, 'Unknown')

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=255)
    
    gender = models.CharField(
        max_length=30,
        choices=GenderChoices.choices,
        blank=True,
        null=True,
    )
    
    phone = models.CharField(default="90001", max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=999
    )

    sub_category = models.IntegerField(
        choices=SubCategoryChoices.choices,
        blank=True,
        null=True
    )

    is_admin = models.BooleanField("Is admin", default=False)
    is_staff = models.BooleanField("Is employee", default=False)
    is_client = models.BooleanField("Is Client", default=False)
    is_applicant = models.BooleanField("Is applicant", default=False)
    is_employee_contract_signed = models.BooleanField(default=False)
    resume_file = models.FileField(upload_to="resumes/doc/", blank=True, null=True, validators=[validate_resume_size])

    class Meta:
        ordering = ["-date_joined"]
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_recent(self):
        return self.date_joined >= timezone.now() - timedelta(days=365)

    @property
    def days_since_joined(self):
        return (timezone.now().date() - self.date_joined.date()).days


class PaymentHistory(models.Model):
    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        MPESA = "mpesa", "M-Pesa"
        CASHAPP = "cashapp", "Cash App"
        ZELLE = "zelle", "Zelle"
        VENMO = "venmo", "Venmo"
        BANK = "bank", "Bank Transfer"
        CASH = "cash", "Cash"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        CANCELED = "canceled", "Canceled"

    class Currency(models.TextChoices):
        USD = "USD", "USD"
        KES = "KES", "KES"
        RWF = "RWF", "RWF"
        UGX = "UGX", "UGX"
        EUR = "EUR", "EUR"
        GBP = "GBP", "GBP"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_history",
        null=True,
        blank=True,
        help_text="User who made/owns the payment record.",
    )

    purpose = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Short label, e.g. Contribution, Membership, Invoice, Donation, Order.",
    )

    reference_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Internal reference, e.g. INV-00021, CONTRIB-2026-003, ORDER-1133.",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.OTHER
    )

    payment_method = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Card, Mobile Money, Bank, Wallet, etc.",
    )

    provider_payment_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        db_index=True,
        help_text="External transaction/payment ID from provider.",
    )

    provider_customer_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Optional external customer ID from provider.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED
    )

    initiated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    transaction_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount after fees.",
    )

    receipt_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    provider_payload = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["provider", "provider_payment_id"]),
            models.Index(fields=["currency", "created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.reference_code or 'PAY'} | "
            f"{self.amount} {self.currency} | "
            f"{self.provider} | {self.status}"
        )

    def mark_succeeded(self, completed_time=None):
        self.status = self.Status.SUCCEEDED
        self.completed_at = completed_time or timezone.now()

        if self.net_amount is None:
            self.net_amount = self.amount - (self.transaction_fee or 0)

        self.save(
            update_fields=[
                "status",
                "completed_at",
                "net_amount",
                "updated_at",
            ]
        )

    def mark_failed(self, note=""):
        self.status = self.Status.FAILED

        if note:
            self.notes = (self.notes + "\n" + note).strip() if self.notes else note

        self.save(update_fields=["status", "notes", "updated_at"])


class Tracker(models.Model):
    category = models.CharField(max_length=25)
    sub_category = models.CharField(max_length=25)
    plan = models.CharField(max_length=255)

    empname = models.IntegerField()
    author = models.IntegerField()

    employee = models.CharField(max_length=255)
    login_date = models.DateTimeField()

    start_time = models.TimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} - {self.category} - {self.login_date}"


class LoginHistory(models.Model):
    user = models.ForeignKey(
        'CustomerUser',
        on_delete=models.CASCADE,
        related_name="login_history"
    )
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Login History"
        ordering = ["-login_time"]

    def __str__(self):
        return f"{self.user.username} - {self.login_time} to {self.logout_time}"
    