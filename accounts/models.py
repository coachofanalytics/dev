from datetime import datetime,timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField
from accounts.choices import CategoryChoices,SubCategoryChoices, GenderChoices

class CustomerUser(AbstractUser):
 
    Gender_Choices = [
        ('male','male'),
        ('female','female'),
        ('other','other')
    ]
    Category_Choices = [
        ('client','client'),
        ('employee','employee'),
        ('applicant','applicant'),
        ('other','other')
    ]
    user_id =  models.AutoField(primary_key=True) 
    first_name = models.CharField(max_length=100, null=False)
    last_name =models.CharField(max_length=100, null=False)
    date_joined =models.DateTimeField(auto_now_add=True)
    email = models.EmailField( unique=True, null=False)
    gender = models.CharField(choices=Gender_Choices, max_length=20, null=False)
    phone =models.CharField(max_length=20, unique=True, null=False)
    address =models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    country = CountryField(null=False)
    category =models.CharField(choices=Category_Choices, max_length=100, null=True)
    is_admin =models.BooleanField(default=False)
    is_employee =models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_applicant = models.BooleanField(default=False)
    resume_file =models.FileField(upload_to='resume/',null=True)
    state = models.CharField(blank=True,null=True, max_length=255)
    zipcode = models.CharField(blank=True,null=True, max_length=255)
    sub_category = models.IntegerField(choices=SubCategoryChoices.choices,blank=True, null=True)
























