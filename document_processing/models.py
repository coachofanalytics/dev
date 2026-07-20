import secrets

from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

SERVICE_CHOICES = [
    ("national_id_replacement", "National ID Replacement"),
    ("birth_certificate", "Birth Certificate"),
    ("passport", "Passport Application"),
    ("good_conduct", "Certificate of Good Conduct"),
    ("marriage_certificate", "Marriage Certificate"),
    ("business_permit", "Business Permit"),
]

# Default service fee (KES) per service type.
SERVICE_FEES = {
    "national_id_replacement": 1500,
    "birth_certificate": 1000,
    "passport": 4500,
    "good_conduct": 1050,
    "marriage_certificate": 500,
    "business_permit": 2000,
}

# Expected ID number length/format per service (used for inline validation).
SERVICE_ID_RULES = {
    "national_id_replacement": {"label": "National ID", "min": 6, "max": 8, "digits": True},
    "birth_certificate": {"label": "Birth Certificate No.", "min": 6, "max": 12, "digits": True},
    "passport": {"label": "Passport No.", "min": 7, "max": 9, "digits": False},
    "good_conduct": {"label": "National ID", "min": 6, "max": 8, "digits": True},
    "marriage_certificate": {"label": "National ID", "min": 6, "max": 8, "digits": True},
    "business_permit": {"label": "Registration No.", "min": 4, "max": 12, "digits": False},
}

REASON_CHOICES = [
    ("lost", "Lost / Misplaced"),
    ("damaged", "Damaged"),
    ("name_change", "Name Change"),
    ("expired", "Expired"),
    ("first_time", "First Time Application"),
    ("correction", "Correction of Details"),
    ("other", "Other"),
]

DISTRICT_CHOICES = [
    ("gasabo", "Gasabo"),
    ("kicukiro", "Kicukiro"),
    ("nyarugenge", "Nyarugenge"),
    ("rubavu", "Rubavu"),
    ("musanze", "Musanze"),
    ("huye", "Huye"),
    ("rusizi", "Rusizi"),
    ("nyagatare", "Nyagatare"),
]

# Sub-counties keyed by district (for dependent dropdowns).
SUBCOUNTY_MAP = {
    "gasabo": ["Kimironko", "Remera", "Kacyiru", "Gisozi", "Ndera"],
    "kicukiro": ["Kagarama", "Gikondo", "Kanombe", "Niboye", "Masaka"],
    "nyarugenge": ["Nyakabanda", "Muhima", "Gitega", "Kimisagara", "Rwampara"],
    "rubavu": ["Gisenyi", "Rubavu", "Nyamyumba", "Nyakiliba"],
    "musanze": ["Muhoza", "Gacuriro", "Kimonyi", "Shingiro"],
    "huye": ["Tumba", "Ngoma", "Ruhuha", "Kinazi"],
    "rusizi": ["Kamembe", "Cyangugu", "Nkanka", "Bugarama"],
    "nyagatare": ["Nyagatare", "Rukomo", "Katabagemu", "Karama"],
}


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

    service = models.CharField(
        max_length=100,
        choices=SERVICE_CHOICES,
        default="national_id_replacement"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=50)

    district = models.CharField(
        max_length=100,
        choices=DISTRICT_CHOICES,
        blank=True
    )
    sub_county = models.CharField(max_length=100, blank=True)
    reason = models.CharField(
        max_length=255,
        choices=REASON_CHOICES,
        blank=True
    )

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

    def save(self, *args, **kwargs):
        # Auto-assign a human-friendly application number on first save.
        if not self.application_number:
            prefix = "DC48"
            now = timezone.now()
            year = now.strftime("%y")
            stamp = now.strftime("%m%d%H%M%S")
            suffix = secrets.token_hex(3).upper()
            self.application_number = f"{prefix}-{year}-{stamp}-{suffix}"
        super().save(*args, **kwargs)

    @property
    def is_draft(self):
        return self.status == "draft"

    @property
    def applicant_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def service_fee(self):
        return SERVICE_FEES.get(self.service, self.fee or 0)

    @property
    def payment(self):
        """Return the most recent payment for this application, if any."""
        return self.payments.order_by("-created_at").first()

    @property
    def payment_status(self):
        pay = self.payment
        if pay:
            return pay.status
        return "none"

    def __str__(self):
        return f"{self.application_number or self.id} - {self.get_service_display()}"

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

    # Time-limited secure token used for download/view links.
    secure_token = models.CharField(max_length=64, blank=True, db_index=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="valid"
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.secure_token:
            import secrets
            self.secure_token = secrets.token_urlsafe(32)
            self.token_expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_token_valid(self):
        return self.token_expires_at and self.token_expires_at > timezone.now()

    def __str__(self):
        return self.title

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

    @classmethod
    def log_access(cls, user, institution, data_accessed, purpose, access_type="view"):
        """Convenience helper to record a data-access event."""
        return cls.objects.create(
            user=user,
            institution=institution,
            data_accessed=data_accessed,
            purpose=purpose,
            access_type=access_type,
        )

    def __str__(self):
        return f"{self.institution} - {self.data_accessed}"

