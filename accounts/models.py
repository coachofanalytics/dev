from datetime import timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField

# from accounts.choices import CategoryChoices,SubCategoryChoices, GenderChoices
from django.conf import settings
# from django.db import models
# from django.utils import timezone

# from accounts.choices import CategoryChoices,SubCategoryChoices



# Create your models here.

class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField('CustomerUser', related_name='user_groups')

    class Meta:
        verbose_name_plural = "User Groups"

from django.db import models
from django.contrib.auth.models import AbstractUser


class SubCategoryChoices(models.TextChoices):
    STUDENT = "Student", "Student"
    STAFF = "Staff", "Staff"
    CLIENT = "Client", "Client"
    TRAINER = "Trainer", "Trainer"
    MANAGER = "Manager", "Manager"
    OTHER = "Other", "Other"


class CustomerUser(AbstractUser):
    # your other fields here

    sub_category = models.CharField(
        max_length=50,
        choices=SubCategoryChoices.choices,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username
    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, 'Unknown')    

    # added this column here
    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.subcategory, 'Unknown')    

    class Score(models.IntegerChoices):
        Male = 1
        Female = 2

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=255)
    gender = models.IntegerField(choices=Score.choices, blank=True, null=True)
    phone = models.CharField(default="90001",max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)
    # category = models.IntegerField(choices=CategoryChoices.choices, default=999)
    # added this column here
    sub_category = models.IntegerField(
        choices=SubCategoryChoices.choices, blank=True, null=True
    )
    is_admin = models.BooleanField("Is admin", default=False)
    is_staff = models.BooleanField("Is employee", default=False)
    is_client = models.BooleanField("Is Client", default=False)
    is_applicant = models.BooleanField("Is applicant", default=False)
    # is_employee = models.BooleanField("Is employee", default=False)
    is_employee_contract_signed = models.BooleanField(default=False)
    resume_file = models.FileField(upload_to="resumes/doc/", blank=True, null=True)

    # is_active = models.BooleanField('Is applicant', default=True)
    class Meta:
        ordering = ["-date_joined"]
        #ordering = ["username"]
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        fullname = f'{self.first_name},{self.last_name}'
        return fullname
    
    @property
    def is_recent(self):
        return self.date_joined >= timezone.now() - timedelta(days=365)
    
    @property
    def days_since_joined(self):
        return (timezone.now().date() - self.date_joined.date()).days
    

    from django.db import models

class UserGroups(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        re# app/models.py



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

    # Core links
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_history",
        null=True,
        blank=True,
        help_text="User who made/owns the payment record (optional for system/imported records).",
    )

    # What this payment was for (flexible)
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

    # Money
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    # Payment method/provider
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.OTHER)
    payment_method = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Card, Mobile Money, Bank, Wallet, etc. (optional descriptive field).",
    )

    # Gateway/processor identifiers
    provider_payment_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        db_index=True,
        help_text="External payment/intent/transaction id from provider (Stripe/PayPal/M-Pesa, etc.).",
    )
    provider_customer_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Optional external customer id from provider.",
    )

    # Status and timestamps
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    initiated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Reconciliation and evidence
    transaction_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional: amount after fees (if you want to store it).",
    )
    receipt_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    # Raw provider response (for audit/debug)
    provider_payload = models.JSONField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["provider", "provider_payment_id"]),
            models.Index(fields=["currency", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_code or 'PAY'} | {self.amount} {self.currency} | {self.provider} | {self.status}"

    def mark_succeeded(self, completed_time=None):
        self.status = self.Status.SUCCEEDED
        self.completed_at = completed_time or timezone.now()
        if self.net_amount is None:
            self.net_amount = self.amount - (self.transaction_fee or 0)
        self.save(update_fields=["status", "completed_at", "net_amount", "updated_at"])

    def mark_failed(self, note: str = ""):
        self.status = self.Status.FAILED
        if note:
            self.notes = (self.notes + "\n" + note).strip() if self.notes else note
    



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


        


class LoginHistory (models.Model):
    user = models.ForeignKey('CustomerUser', on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Login History"

    def __str__(self):
        return f"{self.user.username} - {self.login_time} to {self.logout_time}"
    


from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone



class Transaction(models.Model):
    PAY_CHOICES = [
        ("Cash", "Cash"),
        ("MPESA", "MPESA"),
        ("PayPal", "PayPal"),
        ("Stripe", "Stripe"),
        ("Bank", "Bank"),
        ("Zelle", "Zelle"),
        ("CashApp", "CashApp"),
        ("Venmo", "Venmo"),
        ("Other", "Other"),
    ]

    TYPE_CHOICES = [
        ("Income", "Income"),
        ("Expense", "Expense"),
        ("Transfer", "Transfer"),
        ("Advance", "Advance"),
        ("Refund", "Refund"),
        ("Other", "Other"),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_transactions",
    )

    department = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    receiver = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    type = models.CharField(
        max_length=100,
        choices=TYPE_CHOICES,
        default="Other",
        null=True,
        blank=True,
    )

    activity_date = models.DateTimeField(
        default=timezone.now,
    )

    receipt_link = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    transaction_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    payment_method = models.CharField(
        max_length=50,
        choices=PAY_CHOICES,
        default="Cash",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-activity_date", "-created_at"]

    def __str__(self):
        amount = self.amount or Decimal("0.00")
        return f"{self.type} - {amount} - {self.payment_method}"

    @property
    def total_amount(self):
        """Return the transaction amount plus transaction cost."""
        amount = self.amount or Decimal("0.00")
        cost = self.transaction_cost or Decimal("0.00")
        return amount + cost