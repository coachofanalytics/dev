from datetime import timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from django.conf import settings
from django.core.validators import MinValueValidator

from django_countries.fields import CountryField
from accounts.choices import CategoryChoices,SubCategoryChoices, GenderChoices

# Create your models here.
class CustomerUser(AbstractUser):
    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, 'Unknown')    

    # added this column here
    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.subcategory, 'Unknown')    

    # class Score(models.IntegerChoices):
    #     Male = 1
    #     Female = 2

    #id = models.AutoField(primary_key=True)
    #first_name = models.CharField(max_length=255)
    #last_name = models.CharField(max_length=255)
    #date_joined = models.DateTimeField(default=timezone.now)
    #email = models.CharField(max_length=255)

    gender = models.IntegerField(choices=GenderChoices.choices, blank=True, null=True)
    phone = models.CharField(default="90001",max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)
    category = models.IntegerField(choices=CategoryChoices.choices, default=999)
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
    

   # accounts/models.py


class Payment_History(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Or replace with your custom user model like 'accounts.CustomerUser'
        on_delete=models.CASCADE,
        related_name="payment_history"
    )
    
    payment_fees = models.IntegerField(validators=[MinValueValidator(0)])
    down_payment = models.IntegerField(default=500, validators=[MinValueValidator(0)])
    student_bonus = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    fee_balance = models.IntegerField(null=True, blank=True)
    
    plan = models.IntegerField(validators=[MinValueValidator(0)])
    subplan = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    
    payment_method = models.CharField(max_length=100)
    
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Logic to calculate fee balance
        bonus = self.student_bonus or 0
        self.fee_balance = max(0, (self.payment_fees or 0) - (self.down_payment or 0) - bonus)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment History (Customer: {self.customer_id}, Balance: {self.fee_balance})"
    
    class Meta:
        verbose_name = "Payment History"
        verbose_name_plural = "Payment Histories"
        ordering = ['-contract_submitted_date']


class LoginHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_history"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    login_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} logged in at {self.login_time}"

    class Meta:
        ordering = ["-login_time"]
        verbose_name = "Login History"
        verbose_name_plural = "Login Histories"

    


class Tracker(models.Model):
    category = models.CharField(
        max_length=25,
        null=False,
        blank=False
    )

    sub_category = models.CharField(
        max_length=25,
        null=False,
        blank=False
    )

    plan = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )

    empname = models.IntegerField(
        null=False,
        blank=False
    )

    author = models.IntegerField(
        null=False,
        blank=False
    )

    employee = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )

    login_date = models.DateTimeField(
        null=False,
        blank=False
    )

    start_time = models.TimeField(
        null=True,
        blank=True
    )

    duration = models.IntegerField(
        null=True,
        blank=True
    )

    time = models.PositiveIntegerField(
        null=False,
        blank=False
    )

    class Meta:
        db_table = "accounts_tracker"
        verbose_name = "Tracker"
        verbose_name_plural = "Trackers"

    def __str__(self):
        return f"{self.employee} | {self.category} | {self.login_date}"
