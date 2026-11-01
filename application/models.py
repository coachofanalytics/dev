from django.conf import settings
from django.db import models

from main.models import Assets


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE,
    )

    position = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    company = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    linkedin = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )
    section = models.CharField(
        max_length=2,
        default="A",
        blank=True,
        null=True,
    )

    image = models.ImageField(
        default="default.jpg",
        upload_to="Application_Profile_pics/",
        blank=True,
    )

    image2 = models.ForeignKey(
        Assets,
        related_name="application_profiles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    upload_a = models.FileField(
        upload_to="Application_Profile/uploads/",
        null=True,
        blank=True,
    )
    upload_b = models.FileField(
        upload_to="Application_Profile/uploads/",
        null=True,
        blank=True,
    )
    upload_c = models.FileField(
        upload_to="Application_Profile/uploads/",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        "Is active",
        default=True,
    )
    laptop_status = models.BooleanField(
        "Is laptop status",
        default=True,
    )

    national_id_no = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    id_file = models.ImageField(
        upload_to="id_files/",
        null=True,
        blank=True,
    )

    emergency_name = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    emergency_address = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    emergency_citizenship = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    emergency_national_id_no = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    emergency_phone = models.CharField(
        max_length=254,
        blank=True,
        null=True,
    )
    emergency_email = models.EmailField(
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        username = getattr(self.user, "username", str(self.user))
        return f"{username} Applicant Profile"

    @property
    def img_url(self):
        if self.image2 and self.image2.image_url:
            return self.image2.image_url

        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass

        return ""

    @property
    def img_category(self):
        if self.image2 and self.image2.category:
            return self.image2.category

        return ""


class Reporting(models.Model):
    internal = models.AutoField(primary_key=True)

    first_interview = models.CharField(max_length=255)
    second_interview = models.CharField(max_length=255)
    third_interview = models.CharField(max_length=255)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    interview_type = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Reporting Record"
        verbose_name_plural = "Reporting Records"

    def __str__(self):
        return (
            f"{self.first_name} "
            f"{self.last_name} - "
            f"{self.interview_type}"
        )


class JobDetails(models.Model):
    job_description = models.TextField()
    skills_expertise = models.TextField()
    number_of_connects = models.PositiveIntegerField()

    min_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    max_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    min_duration = models.PositiveIntegerField()
    max_duration = models.PositiveIntegerField()

    project_type = models.TextField()

    class Meta:
        verbose_name = "Job Detail"
        verbose_name_plural = "Job Details"

    def __str__(self):
        return (
            f"{self.project_type} "
            f"({self.min_payment} - {self.max_payment})"
        )


class MyModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application_mymodels",
    )

    class Meta:
        verbose_name = "Application User Model"
        verbose_name_plural = "Application User Models"

    def __str__(self):
        return str(self.user)




class JobOpening(models.Model):
    EMPLOYMENT_TYPES = [
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
    ]

    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    department = models.CharField(max_length=255)

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default="full_time",
    )

    description = models.TextField()
    requirements = models.TextField(blank=True)

    posted_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-posted_on"]

    def __str__(self):
        return self.title




class JobApplication(models.Model):

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("reviewing", "Under Review"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("accepted", "Accepted"),
    ]

    job = models.ForeignKey(
        JobOpening,
        on_delete=models.PROTECT,
        related_name="applications",
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    cv = models.FileField(
        upload_to="job_applications/cvs/"
    )

    cover_letter = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="submitted",
    )

    applied_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_on"]

    def __str__(self):
        return f"{self.full_name} - {self.job.title}"

