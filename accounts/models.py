from datetime import datetime,timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    


class Score(models.Model):
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # auto-sets when record is created
    email = models.EmailField(max_length=255, unique=True)  # unique to avoid duplicates
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ], null=True, blank=True)
    phone = models.CharField(max_length=20, null=False)
    address = models.CharField(max_length=255, null=False)
    city = models.CharField(max_length=100, null=False)
    state = models.CharField(max_length=100, null=False)
    zipcode = models.CharField(max_length=20, null=False)
    country = models.CharField(max_length=100, null=False)

    CATEGORY_CHOICES = [
        ('A', 'Category A'),
        ('B', 'Category B'),
        ('C', 'Category C'),
    ]
    category = models.CharField(max_length=25, choices=CATEGORY_CHOICES, null=False)
    sub_category = models.IntegerField(null=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
