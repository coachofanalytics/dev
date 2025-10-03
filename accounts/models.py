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
from django.utils.text import slugify

class Department(models.Model):
    description = models.CharField(max_length=500, null=True, blank=True)
    slug = models.SlugField(unique=True, null=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.description[:50])  # auto-generate slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description
    


from django.db import models

class Credential(models.Model):
    department = models.CharField(max_length=255, null=False)
    # category = models.ManyToManyField('Category')  # Replace with actual related model
    added_by = models.IntegerField(null=False)
    name = models.CharField(max_length=255, null=False)
    slug = models.SlugField(null=False)
    description = models.TextField(max_length=1000, null=False)
    link_name = models.CharField(max_length=255, null=False)
    link = models.CharField(max_length=100, null=False)
    password = models.CharField(max_length=255, null=True)
    entry_date = models.DateField(null=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    user_types = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name   

  
    
class TaskGroup(models.Model):
    title = models.CharField(max_length=55)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class TeamMember(models.Model):  # 🔄 Renamed to singular (best practice)
    category = models.CharField(max_length=25)
    title = models.CharField(max_length=255, blank=True)  
    description = models.TextField()
    
    def __str__(self):
        return f"{self.title} ({self.category})"

class CredentialCategoryy(models.Model):
    verbose_name = models.CharField(max_length=255, null=True)
    description = models.TextField(max_length=100)  # <-- this must exist
    entry_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(null=False)
    is_featured = models.BooleanField(null=True)

    def __str__(self):
        return self.verbose_name if self.verbose_name else f"category {self.id}"

    
    


        




