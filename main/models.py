from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django_countries.fields import CountryField
from .utils import unique_slug_generator
from django.db import models
from django.utils import timezone



User = get_user_model()

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Services(models.Model):
    serial = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(default='training', max_length=254)
    slug = models.SlugField(default='slug', max_length=255)
    description = models.TextField(null=True, blank=True)
    sub_titles = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Services"
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return f"/services/{self.slug}/"

class Assets(TimeStampedModel):
    name = models.CharField(max_length=200)
    category = models.CharField(default='background', max_length=200, null=True, blank=True)
    image_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, default='background')
    service_image = models.ImageField(null=True, blank=True, upload_to="images/", default='background')
    image_url = models.CharField(max_length=1000, null=True, blank=True, default='background')

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        if self.name and "_" in self.name:
            return self.name.split("_")[:2]
        return self.name, ""

    def __str__(self):
        return self.name

class Readme(TimeStampedModel):
    title = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(default='slug', max_length=255)
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

def readme_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug and instance.title:
        instance.slug = unique_slug_generator(instance)

pre_save.connect(readme_pre_save_receiver, sender=Readme)


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
    date_posted = models.DateTimeField(auto_now_add=True)
    writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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

class Location(models.Model):
    zipcode = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(blank_label='(select country)', null=True, blank=True)

    class Meta:
        unique_together = ('zipcode', 'city', 'state', 'country')
        ordering = ['country', 'state', 'city']

    def __str__(self):
        return f"{self.city}, {self.state}, {self.country} ({self.zipcode})"


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


class Pricing(models.Model):
    serial = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.IntegerField(help_text="Category reference (e.g., Business, Individual)")
    subcategory = models.CharField(max_length=255, null=True, blank=True)
    price = models.FloatField()
    discounted_price = models.FloatField(null=True, blank=True)
    duration = models.PositiveIntegerField(help_text="Duration value (e.g., 30, 6, 12)")
    contract_length = models.IntegerField(null=True, blank=True, help_text="Contract period if applicable")
    is_direct = models.BooleanField(default=False, help_text="Can users purchase directly?")
    is_active = models.BooleanField(default=True, help_text="Controls visibility on website")
    redirect_url_path = models.CharField(max_length=255, null=True, blank=True, help_text="Redirect URL for purchase or details")

    class Meta:
        ordering = ["serial"]

    def __str__(self):
        return self.title


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


class ClientAvailability(models.Model):
    client = models.IntegerField(null=False, blank=False)
    day = models.CharField(max_length=20, null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    time_standards = models.CharField(max_length=20, null=False, blank=False)
    topic = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return f"Client {self.client} - {self.day} ({self.start_time} to {self.end_time})"
    

class Search(models.Model):
    topic = models.CharField(max_length=255, null=False)
    question = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded = models.BooleanField(default=False)

    def __str__(self):
        return self.topic
    
class Company(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    mission = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name or "Company"
    





class Event(models.Model):
    """
    Model representing a community event on the calendar.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    event_date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, help_text="Physical location or virtual link")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date']
        verbose_name = 'Community Event'
        verbose_name_plural = 'Community Events'

    def __str__(self):
        return self.title






















































