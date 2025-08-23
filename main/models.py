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
    


class  ClientAvailability(models.Model):
    client  =models.CharField(max_length=255,null=False)
    day  = models.CharField(max_length=255,null=False)
    start_time =models.TimeField(null=False)
    end_time =models.TimeField(null=False)
    time_standards =models.CharField(max_length=22,null= False)
    topic=models.CharField(max_length=100,null=False)
  
class service_coda(models.Model):
    serial =models.PositiveIntegerField(null=True)
    # company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True)
    title =models.CharField(max_length=255)
    slug =models.SlugField(null=True)
    description =models.TextField(null=True)
    sub_titles =models.TextField(null=True)
    executive_summary =models.TextField(null=True)
    is_active =models.BooleanField(null=True)
    is_featured =models.BooleanField(null=True)

from django.conf import settings

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













































