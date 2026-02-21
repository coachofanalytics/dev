# from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from .utils import unique_slug_generator
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone


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

class Services(models.Model):
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

class Location(models.Model):
    zipcode =models.CharField(max_length=20)
    city =models.CharField(max_length=100)
    state =models.CharField(max_length=100)
    country =models.CharField(max_length=100)

    class Meta:
        unique_together =('zipcode','city','state','country')
        ordering =['country','state','city']

        def __str__(self):
            return f"{self.city}, {self.state},{self.country} ({self.zipcode})"
        

class Pricing(models.Model):
    serial = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Strongly recommended: use choices or FK later
    category = models.IntegerField(help_text="Category reference (e.g., Business, Individual)")
    subcategory = models.CharField(max_length=255, null=True, blank=True)

    price = models.FloatField()
    discounted_price = models.FloatField(null=True, blank=True)

    duration = models.PositiveIntegerField(
        help_text="Duration value (e.g., 30, 6, 12)"
    )
    contract_length = models.IntegerField(
        null=True,
        blank=True,
        help_text="Contract period if applicable"
    )

    is_direct = models.BooleanField(
        default=False,
        help_text="Can users purchase directly?"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Controls visibility on website"
    )

    redirect_url_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Redirect URL for purchase or details"
    )

    class Meta:
        ordering = ["serial"]

    def __str__(self):
        return self.title

        # models.py



class Testimonials(models.Model):
    title = models.CharField(null=False, max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    writer = models.IntegerField()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Testimonials.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return self.title

        # main/models.py

from django.db import models


class Plan(models.Model):
    task = models.CharField(max_length=255, null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    what = models.TextField(null=True, blank=True)
    why = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    doc = models.FileField(upload_to="plans/docs/", null=True, blank=True)

    pptlink = models.CharField(max_length=500, null=True, blank=True)
    videolink = models.CharField(max_length=500, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_answered = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.task if self.task else f"Plan {self.id}"

    class Meta:
        db_table = "main_plan"
        ordering = ["-created_at"]
