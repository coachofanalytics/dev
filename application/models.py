# from coda_project.application.views import first_interview
from datetime import datetime
from django.db import models
from django.utils import timezone
from main.models import Assets
from django.db.models import Q
from django.contrib.auth import get_user_model

# from finance.utils import get_exchange_rate
User = get_user_model()
# from coda_project.storage import GoogleDriveStorage

# Create your models here.
class UserProfile(models.Model):

    user = models.OneToOneField(
        "accounts.CustomerUser", related_name="profile", on_delete=models.CASCADE
    )
    position = models.CharField(max_length=255,blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    company = models.CharField(max_length=254, null=True, blank=True)
    linkedin = models.CharField(max_length=500, null=True, blank=True)
    section = models.CharField(max_length=2, default="A", blank=True)

    image = models.ImageField(
        default="default.jpg", upload_to="Application_Profile_pics", blank=True
    )
    image2 = models.ForeignKey(
        Assets, related_name="profile_image", on_delete=models.CASCADE,default=1
    )

    upload_a = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)
    upload_b = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)
    upload_c = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)

    is_active = models.BooleanField("Is featured", default=True)
    laptop_status= models.BooleanField("Is lap_status", default=True)

    national_id_no = models.CharField(max_length=254, null=True, blank=True)
    id_file = models.ImageField(upload_to='id_files/', null=True, blank=True)

    emergency_name = models.CharField(max_length=254, null=True, blank=True)
    emergency_address = models.CharField(max_length=254, null=True, blank=True)
    emergency_citizenship = models.CharField(max_length=254, null=True, blank=True)
    emergency_national_id_no = models.CharField(max_length=254, null=True, blank=True)
    emergency_phone = models.CharField(max_length=254, null=True, blank=True)
    emergency_email = models.CharField(max_length=254, null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} Applicant Profile"

    @property
    def img_url(self):
        if self.image2:
            return self.image2.image_url
        else:
            return "default_image_url.jpg"

    @property
    def img_category(self):
        img_cat=self.image2.category
        return img_cat




from django.db import models

class Reporting(models.Model):
    internal = models.AutoField(primary_key=True)
    first_interview = models.CharField(max_length=255)
    second_interview = models.CharField(max_length=255)
    third_interview = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    interview_type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.interview_type}"



class JobDetails(models.Model):
    job_description = models.TextField(null=False)
    skills_expertise = models.TextField(null=False)
    number_of_connects =models.IntegerField(null=False)
    min_payment =models.DecimalField(max_digits=10,decimal_places=2, null=False)
    max_payment = models.DecimalField(max_digits=10,decimal_places=2,null=False)
    min_duration = models.IntegerField(null=False)
    max_duration = models.IntegerField(null=False)
    project_type = models.TextField(null=False)
    deliverables = models.TextField(null=False)
    links = models.URLField(null=True)