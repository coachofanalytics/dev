from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.utils.text import slugify
from django.db.models.signals import pre_save
from .utils import unique_slug_generator,slug_pre_save_receiver
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

# from tableauhyperapi import DatabaseName

User = get_user_model()
# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Service(models.Model):
    serial = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(default='training',max_length=254)
    slug = models.SlugField(default='slug',max_length=255)
    description = models.TextField(null=True, blank=True)
    sub_titles = models.TextField(null=True, blank=True)
    # executive_summary = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural = "Services"
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return "/services/{slug}/".format(slug=self.slug)

class Assets(TimeStampedModel):
    name = models.CharField(max_length=200)
    category = models.CharField(default='background',max_length=200,null=True, blank=True)
    image_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True,default='background')
    service_image =models.ImageField(null=True, blank=True, upload_to="images/",default='background')

    image_url = models.CharField(max_length=1000, null=True, blank=True,default='background')

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        image_1=self.name.split("_")[0]
        image_2=self.name.split("_")[1]
        image_name=image_1,image_2

        return image_name

    def __str__(self):
        return self.name

class Readme(TimeStampedModel):
    title = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(default='slug',max_length=255)
    description = models.TextField(blank=True, null=True)
    installation = models.TextField(blank=True, null=True)
    usage = models.TextField(blank=True, null=True)
    configuration = models.TextField(blank=True, null=True)
    deployment = models.TextField(blank=True, null=True)
    contributing = models.TextField(blank=True, null=True)
    license = models.TextField(blank=True, null=True)
    credits = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    additional_sections = models.TextField(blank=True, null=True)
    links = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Readme"
    def __str__(self):
        return self.title or "Readme Entry"

# ==============================PRESAVE SLUG GENERATORS====================================
def readme_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        if instance.title:
            instance.slug = unique_slug_generator(instance)

pre_save.connect(readme_pre_save_receiver, sender=Readme)





from django.db import models

class Volunteer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    motivation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    



class Testimonials(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=50)
    content = models.TextField()
    

from django.db import models
from django_countries.fields import CountryField  # install django-countries

class Location(models.Model):
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(blank_label='(select country)', null=True, blank=True)

    def __str__(self):
        return f"{self.city}, {self.state}, {self.country}"
models.DateTimeField()
writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

# Delete this from models.py

class MembershipRegistration(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

from django.db import models




class ServiceCategory(models.Model):
    service = models.IntegerField(null=True)
    name = models.CharField(max_length=255, null=True)
    slug = models.SlugField(max_length=255, null=True)
    description = models.TextField(null=True)
    is_active = models.BooleanField(null=True)
    is_featured = models.BooleanField(null=True)

    def __str__(self):
        return self.name or f"ServiceCategory {self.pk}"
from django.db import models

class Assets(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    image_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    service_image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    image_url = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or "Unnamed Asset"
class WCAGStandardWebsite(models.Model):
    company = models.CharField(max_length=500, null=True, blank=True)
    app_name = models.CharField(max_length=500, null=True, blank=True)
    page_name = models.TextField(null=True, blank=True)
    website_url = models.FileField(upload_to='uploads/', null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    test_field = models.CharField(max_length=10, null=True, blank=True)  # <-- TEMP

    def __str__(self):
        return self.page_name or "Unnamed Page"



class ServiceCategory(models.Model):
    service = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name or "Service Category"

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)



























