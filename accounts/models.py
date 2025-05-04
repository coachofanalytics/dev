from datetime import datetime,timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField
from accounts.choices import CategoryChoices,SubCategoryChoices, GenderChoices
from accounts.modelmanager import DepartmentManager
from django.db.models.signals import pre_save

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

    objects=DepartmentManager()

    @classmethod
    def get_default_pk(cls):
        cat, created = cls.objects.get_or_create(
            name="Other", defaults=dict(description="this is not an cat")
        )
        return cat.pk

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def get_absolute_url(self):
            return reverse('main:department_reports', args=[self.slug])    

    def __str__(self):
        return self.name
 
 
# =========================CREDENTIALS TABLE======================================


class CredentialCategory(models.Model):
    department = models.ForeignKey(
        to=Department, on_delete=models.CASCADE, default=Department.get_default_pk
    )
    # created_by= models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(
        verbose_name=_("Category Name"),
        help_text=_("Required"),
        max_length=255,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name=_("category safe URL"), max_length=255, unique=True
    )
    description = models.TextField(max_length=1000, default=None)
    entry_date = models.DateTimeField(_("entered on"), auto_now_add=True, editable=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("management:credentialcategorylist", args=[self.slug])

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        # return f"{self.category} Categories"
        return f"{self.category}"

# ========================================SLUGS GENERATOR====================================================
def credentialcategory_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(credentialcategory_pre_save_receiver, sender=CredentialCategory)


class Credential(models.Model):
    USER_CHOICES = [
        ("Superuser", "Superuser"),
        ("Admin", "Admin"),
        ("Employee", "Employee"),
        ("Other", "Other"),
    ]
    category = models.ManyToManyField(
        CredentialCategory, blank=True, related_name="credentialcategory"
    )
    added_by = models.ForeignKey(CustomerUser, on_delete=models.RESTRICT)
    name = models.CharField(
        verbose_name=_("credential Name"),
        help_text=_("Required"),
        max_length=255,
    )
    slug = models.SlugField(
        verbose_name=_("credential safe URL"), max_length=255, unique=True
    )
    description = models.TextField(max_length=1000, default=None)
    link_name = models.CharField(max_length=255, default="General")
    link = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(
        max_length=255, blank=True, null=True, default="No Password Needed"
    )
    entry_date = models.DateTimeField(_("entered on"), auto_now_add=True, editable=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    user_types = models.CharField(
        max_length=25,
        choices=USER_CHOICES,
        default="Other",
    )

    class Meta:
        verbose_name_plural = "credentials"

    def get_absolute_url(self):
        return reverse("management:credential")

    def __str__(self):
        return self.name


class LoginHistory(models.Model):
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    # You can add more fields as needed

    def __str__(self):
        return f'{self.user.username} - {self.login_time} to {self.logout_time}'

    @property
    def login_duration(self):
        number_hours=(self.logout_time-self.login_time ).hours
        return number_hours