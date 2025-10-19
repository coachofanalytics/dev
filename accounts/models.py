from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from accounts.choices import CategoryChoices, SubCategoryChoices


# from accounts.models import Department, Credential, CredentialCategory, TaskGroups, Tracker, All_transaction



# ✅ Transaction type choices defined globally
TRANSACTION_TYPE_CHOICES = [
    ('INCOME', 'Income'),
    ('EXPENSE', 'Expense'),
]


# =========================
# USER GROUPS MODEL
# =========================
class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField('CustomerUser', related_name='user_groups')

    class Meta:
        verbose_name_plural = "User Groups"


# =========================
# CUSTOM USER MODEL
# =========================
class CustomerUser(AbstractUser):
    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, 'Unknown')

    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.sub_category, 'Unknown')

    class Score(models.IntegerChoices):
        Male = 1
        Female = 2

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=255)
    gender = models.IntegerField(choices=Score.choices, blank=True, null=True)
    phone = models.CharField(default="90001", max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)
    category = models.IntegerField(choices=CategoryChoices.choices, default=999)
    sub_category = models.IntegerField(choices=SubCategoryChoices.choices, blank=True, null=True)
    is_admin = models.BooleanField("Is admin", default=False)
    is_staff = models.BooleanField("Is employee", default=False)
    is_client = models.BooleanField("Is Client", default=False)
    is_applicant = models.BooleanField("Is applicant", default=False)
    is_employee_contract_signed = models.BooleanField(default=False)
    resume_file = models.FileField(upload_to="resumes/doc/", blank=True, null=True)

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

# =====================================================
# LOGIN HISTORY MODEL
# =====================================================
class LoginHistory(models.Model):
    user = models.ForeignKey('CustomerUser', on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Login History"

    def __str__(self):
        return f"{self.user.username} - {self.login_time} to {self.logout_time}"


# =====================================================
# ALL TRANSACTION MODEL
# =====================================================

TRANSACTION_TYPE_CHOICES = [
    ('INCOME', 'Income'),
    ('EXPENSE', 'Expense'),
]

class All_transaction(models.Model):
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "All Transactions"

    def __str__(self):
        return f"{self.type} - {self.amount}"


class Transaction(models.Model):
    # ----------------------------
    # CHOICES
    # ----------------------------
    CAT_CHOICES = [
        ('Salary', 'Salary'),
        ('Health', 'Health'),
        ('Transport', 'Transport'),
        ('Food_Accomodation', 'Food & Accommodation'),
        ('Internet_Airtime', 'Internet & Airtime'),
        ('Recruitment', 'Recruitment'),
        ('Labour', 'Labour'),
        ('Electricity', 'Electricity'),
        ('Construction', 'Construction'),
        ('Training', 'Training'),
        ('Grocery', 'Grocery'),
        ('Gas', 'Gas'),
        ('Poshmil', 'Poshmil'),
        ('Other', 'Other'),
    ]

    PAY_CHOICES = [
        ('Cash', 'Cash'),
        ('Mpesa', 'Mpesa'),
        ('Bank_Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Other', 'Other'),
    ]

    # ----------------------------
    # FIELDS
    # ----------------------------
    sender = models.ForeignKey(
        'accounts.CustomerUser',  # string reference avoids circular import
        verbose_name=_('Sender'),
        related_name='transactions_sent',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'is_staff': True, 'is_active': True},
    )

    department = models.ForeignKey(
    'departments.Department',  # ✅ Correct reference
    verbose_name=_('Department'),
    on_delete=models.CASCADE,
    null=True,
    blank=True,


    )

    receiver = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    activity_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=255, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, choices=PAY_CHOICES, default='Other')
    category = models.CharField(max_length=100, choices=CAT_CHOICES, default='Other')

    # Computed field
    @property
    def total_transactions_amt(self):
        if self.amount and self.qty:
            return self.amount * self.qty
        return self.amount or 0

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Transactions"
        ordering = ['-activity_date']

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.payment_method})"
