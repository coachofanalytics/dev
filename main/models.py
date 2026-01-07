from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser

User = get_user_model()


# Create your models here.
class Page(models.Model):
    page_name = models.CharField(max_length=200)

    def __str__(self):
        return self.page_name


class Description(models.Model):
    page = models.ForeignKey(Page, related_name='descriptions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.name} for {self.page.page_name}"


class Content(models.Model):
    SECTION_CHOICES = [
        ('Our Story', 'Our Story'),
        ('Newsletter', 'Newsletter'),
        ('Blog', 'Blog'),
    ]

    section = models.CharField(max_length=50, choices=SECTION_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.section} - {self.title if self.title else 'Content'}"


class Assets(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(default='background', max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        parts = self.name.split("_")
        return parts if len(parts) >= 2 else self.name

    def __str__(self):
        return self.name


class Feedback(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    topic = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.topic


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    ordering = models.PositiveIntegerField(default=0)
    slug = models.SlugField(blank=True, null=True, help_text="Unique ID for anchors (e.g. 'consular', 'financial')")
    cta_text = models.CharField(max_length=100, default="Learn More", blank=True, null=True, help_text="Text for the call-to-action button")
    cta_link = models.CharField(max_length=255, default="#", blank=True, null=True, help_text="URL name or path for the button")

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return self.title


class SubService(models.Model):
    service = models.ForeignKey(Service, related_name='subservices', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.service}"


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    link = models.URLField(null=True, blank=True)
    published_date = models.DateField()
    is_event = models.BooleanField(default=False)
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)

    def __str__(self):
        return self.title


class Team(models.Model):
    ROLE_CHOICES = [
        ('Governor', 'Governor'),
        ('Deputy Governor', 'Deputy Governor'),
        ('Regional Coordinator', 'Regional Coordinator'),
        ('Team Member', 'Team Member'),
    ]

    LEADERSHIP_CHOICES = [
        ('Local', 'Local'),
        ('Global', 'Global'),
    ]

    name = models.CharField(max_length=255)
    leadership = models.CharField(max_length=50, choices=LEADERSHIP_CHOICES, default='Local')
    facebook_link = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='people/')
    bio = models.TextField()

    def __str__(self):
        return self.name


class Gallery_image(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()

    def __str__(self):
        return self.title


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class Donation_organisation(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    donor_name = models.CharField(max_length=100)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation of {self.amount} by {self.donor_name} ({self.email})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} => ({self.message})"


class Donation_organization(models.Model):
    donor_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor_name} - {self.amount}"


#<<<<<<< 25.10_DC48_UAT_UO

#<<<<<<< 25.10_DC48_UAT_UO
# Stores email subscriptions for Safety Alerts
class SafetyAlertSubscription(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# Emergency help line configuration
class EmergencyHotlines(models.Model):
    name = models.CharField(max_length=100, help_text="Display label, e.g., Global Hotline")
    number = models.CharField(max_length=32, help_text="E.164 like +15551234567 or local format")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.name} ({self.number})"


class StaffContact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    notify_via_email = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class EmergencyHelpActivations(models.Model):
    EVENT_CHOICES = (
        ("call_link_clicked", "Call Link Clicked"),
        ("callback_requested", "Callback Requested"),
    )
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
#=======

# Medical Resource Inquiry model at top-level
#=======
#>>>>>>> 25.10_DC48_UAT_ND
class MedicalResourceInquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


# Scholarship model with filters
class Scholarship(models.Model):
    LEVEL_CHOICES = [
        ('Undergraduate', 'Undergraduate'),
        ('Masters', 'Masters'),
        ('PhD', 'PhD'),
        ('Vocational', 'Vocational'),
    ]

    FIELD_CHOICES = [
        ('STEM', 'STEM'),
        ('Humanities', 'Humanities'),
        ('Business', 'Business'),
        ('Arts', 'Arts'),
    ]

    LOCATION_CHOICES = [
        ('Kenya', 'Kenya'),
        ('Global', 'Global'),
        ('UK', 'UK'),
        ('USA', 'USA'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closing Soon', 'Closing Soon'),
        ('Closed', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(max_length=100, choices=LEVEL_CHOICES, blank=True, null=True)
    field = models.CharField(max_length=100, choices=FIELD_CHOICES, blank=True, null=True)
    location = models.CharField(max_length=200, choices=LOCATION_CHOICES, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    amount = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=True, null=True)
    

    class Meta:
        verbose_name = "Scholarship"
        verbose_name_plural = "Scholarships"
        ordering = ['deadline']

    def __str__(self):
        return self.title


class TrainingCourse(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=150, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    format = models.CharField(max_length=100, blank=True, null=True)
    enrollment = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Training Course"
        verbose_name_plural = "Training Courses"

    def __str__(self):
        return self.title
#<<<<<<< 25.10_DC48_UAT_UO
    
#>>>>>>> 25.10_DC48_UAT_ND
#=======
#>>>>>>> 25.10_DC48_UAT_ND

class DocumentServiceRequest(models.Model):
    SERVICE_CHOICES = [
        ('application_assistance', 'Application Assistance and Review'),
        ('translation', 'Translation Services'),
        ('document_review', 'Document Review and Authentication'),
        ('registration_support', 'Birth/Death Certificate Registration Support'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    document_file = models.FileField(upload_to='document_services/', blank=True, null=True)
    message = models.TextField(help_text="Describe your specific needs or issues.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.user} ({self.status})"


class ExpertServiceRequest(models.Model):
    SERVICE_CHOICES = [
        ('consular_assistance', 'Consular Assistance'),
        ('crisis_management', 'Crisis Management'),
        ('legal_aid', 'Legal Aid'),
        ('other', 'Other'),
    ]

    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    location = models.CharField(max_length=255)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal')
    message = models.TextField()
    status = models.CharField(max_length=20, default='pending') # pending, working, resolved
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type} ({self.urgency}) - {self.location}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    story = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    # Optional: link to a specific service if you want to categorize them
    service_category = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Consular, Document")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class GlobalSetting(models.Model):
    """
    Store key-value pairs for dynamic site settings (e.g., Expert Email, Hotline Number).
    """
    key = models.CharField(max_length=100, unique=True, help_text="Unique identifier, e.g., 'expert_email'")
    value = models.TextField(help_text="The content/value for this setting")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="What is this setting for?")

    def __str__(self):
        return f"{self.key}: {self.value}"
