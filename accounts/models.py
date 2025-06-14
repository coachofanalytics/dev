from datetime import datetime,timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField
from accounts.choices import CategoryChoices,SubCategoryChoices, GenderChoices
from django.apps import AppConfig

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
    




from django.conf import settings
from django.db import models

class Tracker(models.Model):
    category = models.CharField(max_length=25)
    sub_category = models.CharField(max_length=25)
    task = models.CharField(max_length=25)
    plan = models.CharField(max_length=255)
    
    empname = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_name')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tracker_author')

    employee = models.CharField(max_length=255)

    login_date = models.DateTimeField()
    start_time = models.TimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)

    time = models.PositiveIntegerField(default=200)

    def __str__(self):
        return f"{self.category} - {self.task}"






  
    
class Department(models.Model):
    """Department Table will provide a list of the different departments in CODA"""

    # Department
    # BASIC = "Basic"
    HR = "HR Department"
    IT = "IT Department"
    MKT = "Marketing Department"
    FIN = "Finance Department"
    SECURITY = "Security Department"
    MANAGEMENT = "Management Department"
    # Project = "Project"
    HEALTH = "Health Department"
    Other = "Other"
    DEPARTMENT_CHOICES = [
        # (BASIC, "BASIC Department"),
        (HR, "HR Department"),
        (IT, "IT Department"),
        (MKT, "Marketing Department"),
        (FIN, "Finance Department"),
        # (Project, "Project"),
        (SECURITY, "Security Department"),
        (MANAGEMENT, "Management Department"),
        (HEALTH, "Health Department"),
        (Other, "Other"),
    ]

    name = models.CharField(
        max_length=100,
        choices=DEPARTMENT_CHOICES,
        default=Other,
    )

    description = models.TextField(max_length=500, null=True, blank=True)
    slug = models.SlugField(
        verbose_name=_("Department safe URL"), max_length=255, unique=True
    )
    # created_date = models.DateTimeField(_('entered on'),default=timezone.now, editable=True)
    is_featured = models.BooleanField("Is featured", default=True)
    is_active = models.BooleanField(default=True)







from django.db import models
from django.utils.translation import gettext_lazy as _

class Credential(models.Model):
    USER_CHOICES = [
        ("Superuser", "Superuser"),
        ("Admin", "Admin"),
        ("Employee", "Employee"),
        ("Other", "Other"),
    ]

    added_by = models.ForeignKey(CustomerUser, on_delete=models.RESTRICT)
    name = models.CharField(
        verbose_name=_("Credential Name"),
        help_text=_("Required"),
        max_length=255,
    )
    slug = models.SlugField(
        verbose_name=_("Credential safe URL"), max_length=255, unique=True
    )
    description = models.TextField(max_length=1000, default=None)
    link_name = models.CharField(max_length=255, default="General")
    link = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(
        max_length=255, blank=True, null=True, default="No Password Needed"
    )
    user_type = models.CharField(
        max_length=50, choices=USER_CHOICES, default="Other"
    )

    def __str__(self):
        return self.name





class Assets(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name



















































