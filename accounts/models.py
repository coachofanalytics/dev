from datetime import datetime,timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField
from accounts.choices import CategoryChoices,SubCategoryChoices


# Create your models here.

class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField('CustomerUser', related_name='user_groups')

    class Meta:
        verbose_name_plural = "User Groups"

class CustomerUser(AbstractUser):
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

    
from django.db import models
from django_countries.fields import CountryField


class Score(models.Model):
    first_name = models.CharField(max_length=100)   # Required field
    last_name = models.CharField(max_length=100)    # Required field
    date_joined = models.DateTimeField(auto_now_add=True)  # Automatically set on create
    email = models.EmailField(unique=True)          # Email with uniqueness
    gender = models.CharField(max_length=10, null=True, blank=True)  # Optional
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    country = CountryField()                        # Dropdown country field
    category = models.CharField(max_length=100)     # Changed to CharField for flexibility
    sub_category = models.IntegerField()            # Still integer

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
from django.db import models

class Trackers(models.Model):
    category = models.CharField(max_length=25, null=False)
    sub_category = models.CharField(max_length=25, null=False)
    task = models.CharField(max_length=25, null=False)
    plan = models.CharField(max_length=255, null=False)
    empname = models.IntegerField(null=False)   # could be ForeignKey
    author = models.IntegerField(null=False)    # could be ForeignKey
    employees = models.CharField(max_length=255, null=False)
    login_date = models.DateTimeField(null=False)
    start_time = models.TimeField(null=False)
    duration = models.IntegerField(null=False)
    time = models.PositiveIntegerField(null=False)  # removed max_length

    def __str__(self):
        return f"{self.category} - {self.task}"
# class Trackerr(models.Model):
#     # fields...
#     class Meta:
#         db_table = "accounts_trackers"




