from datetime import timedelta
from django.contrib.auth.models import AbstractUser, Group
from django.db import models 
from django.utils import timezone
from django_countries.fields import CountryField
from accounts.choices import CategoryChoices, SubCategoryChoices


class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField("CustomerUser", related_name="user_groups")

    class Meta:
        verbose_name_plural = "User Groups"


class CustomerUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Ensures unique email + preserves username for admin login.
    """

    # Override username: keep as unique (Django default)
    # Username exists in AbstractUser → no need to redefine it.

    # Make email unique to avoid admin login errors
    email = models.EmailField(unique=True)

    class Score(models.IntegerChoices):
        Male = 1
        Female = 2

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)

    gender = models.IntegerField(choices=Score.choices, blank=True, null=True)
    phone = models.CharField(default="90001", max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)

    category = models.IntegerField(choices=CategoryChoices.choices, default=999)
    sub_category = models.IntegerField(
        choices=SubCategoryChoices.choices, blank=True, null=True
    )

    is_admin = models.BooleanField("Is admin", default=False)
    is_staff = models.BooleanField("Is employee", default=False)
    is_client = models.BooleanField("Is Client", default=False)
    is_applicant = models.BooleanField("Is applicant", default=False)
    is_employee_contract_signed = models.BooleanField(default=False)

    resume_file = models.FileField(upload_to="resumes/doc/", blank=True, null=True)

    # Authentication settings (KEEP username login)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name_plural = "Users"

    # Helper properties
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_recent(self):
        return self.date_joined >= timezone.now() - timedelta(days=365)

    @property
    def days_since_joined(self):
        return (timezone.now().date() - self.date_joined.date()).days

    # Display helpers
    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, "Unknown")

    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.sub_category, "Unknown")


class LoginHistory(models.Model):
    user = models.ForeignKey("CustomerUser", on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Login History"

    def __str__(self):
        return f"{self.user.username} - {self.login_time} to {self.logout_time}"

class Tracker(models.Model):
    category = models.CharField(max_length=25, null=False)
    sub_category = models.CharField(max_length=25, null=False)
    task = models.CharField(max_length=25, null=False)
    plan = models.CharField(max_length=255, null=False)
    
    # Removed empname and updated to employee
    employee = models.CharField(max_length=255, null=True) 
    login_date = models.DateTimeField(null=False)
    start_time = models.TimeField(null=False)
    duration = models.IntegerField(null=False)
    time = models.PositiveIntegerField(null=False)

    def __str__(self):
        return f"Tracker for {self.employee} on {self.login_date}"

    class Meta:
        verbose_name = "Tracker"
        verbose_name_plural = "Trackers"
