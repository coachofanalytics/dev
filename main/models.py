from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser

User = get_user_model()

# new models i create myself
# models.py


class Opportunity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    motivation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class NetworkItem(models.Model):
    CATEGORY_CHOICES = [
        ('donation', 'Donation'),
        ('volunteer', 'Volunteer'),
        ('help', 'Help Request'),
    ]

    URGENCY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES)
    location = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


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
    description = models.TextField()

    def __str__(self):
        return self.title


class SubService(models.Model):
    service = models.ForeignKey(Service, related_name='subservices', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()

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


# Consular Services and Legal Immigration Resources (moved from communities)
class ConsularService(models.Model):
    SERVICE_TYPES = [
        ('government', 'Government Agency'),
        ('legal_aid', 'Legal Aid Organization'),
        ('nonprofit', 'Non-Profit Organization'),
        ('consultation', 'Consultation Service'),
    ]
    
    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country_coverage = models.CharField(max_length=255, help_text="e.g., USA, Mexico, Global")
    services_offered = models.TextField(help_text="Comma-separated list of services")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Consular Services"
        ordering = ['-is_featured', '-updated_at']

    def __str__(self):
        return f"{self.name} ({self.service_type})"


class LegalImmigrationResource(models.Model):
    RESOURCE_CATEGORIES = [
        ('visa', 'Visa Information'),
        ('green_card', 'Green Card & Permanent Residency'),
        ('citizenship', 'Citizenship & Naturalization'),
        ('employment', 'Employment Authorization'),
        ('asylum', 'Asylum & Refugee'),
        ('deportation', 'Deportation Defense'),
        ('family', 'Family Sponsorship'),
        ('rights', 'Legal Rights'),
    ]
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=RESOURCE_CATEGORIES)
    content = models.TextField()
    external_url = models.URLField(blank=True, null=True)
    related_service = models.ForeignKey(ConsularService, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for search")
    is_critical = models.BooleanField(default=False, help_text="Mark as critical information")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Legal Immigration Resources"
        ordering = ['-is_critical', '-updated_at']

    def __str__(self):
        return f"{self.title} ({self.category})"
#added myself


class Consultation(models.Model):

    CONSULTATION_TYPES = [
        ('immigration', 'Immigration Visa'),
        ('asylum', 'Asylum'),
        ('family', 'Family Immigration'),
        ('work', 'Work Permit'),
        ('student', 'Student Visa'),
        ('legal', 'General Legal Advice'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=200)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    country = models.CharField(max_length=100)

    consultation_type = models.CharField(
        max_length=100,
        choices=CONSULTATION_TYPES
    )

    description = models.TextField()

    document = models.FileField(
        upload_to='consultation_documents/',
        blank=True,
        null=True
    )

    preferred_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

        # new models for make donation

        from django.db import models

class Donation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    name = models.CharField(max_length=255)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True)
    anonymous = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.amount}"
    
    from django.db import models

# choices
GENDER_CHOICES = [
    ('Male','Male'),
    ('Female','Female'),
    ('Other','Other'),
]

AVAILABILITY_CHOICES = [
    ('Full-time','Full-time'),
    ('Part-time','Part-time'),
    ('Occasional','Occasional'),
]

ROLE_CHOICES = [
    ('Field volunteer','Field volunteer'),
    ('Online volunteer','Online volunteer'),
    ('Event volunteer','Event volunteer'),
    ('Team leader','Team leader'),
    ('Trainer / Mentor','Trainer / Mentor'),
    ('Fundraising ambassador','Fundraising ambassador'),
]

STATUS_CHOICES = [
    ('Pending','Pending'),
    ('Approved','Approved'),
    ('Rejected','Rejected'),
]


class Volunteer(models.Model):

    # 1️⃣ BASIC INFO
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    profile_photo = models.ImageField(upload_to='volunteers/photos/', blank=True, null=True)

    # 2️⃣ AVAILABILITY
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    available_days = models.CharField(max_length=200)
    hours_per_week = models.IntegerField()

    # 3️⃣ SKILLS
    skills = models.TextField()
    interests = models.TextField()

    # 4️⃣ TERRITORY
    territory = models.CharField(max_length=150)
    is_remote = models.BooleanField(default=False)

    # 5️⃣ MOTIVATION
    motivation = models.TextField()
    experience = models.TextField(blank=True)
    impact_goal = models.TextField()

    # 6️⃣ DOCUMENTS
    cv = models.FileField(upload_to='volunteers/cv/', blank=True, null=True)
    id_document = models.FileField(upload_to='volunteers/id/', blank=True, null=True)
    certificates = models.FileField(upload_to='volunteers/certificates/', blank=True, null=True)

    # 7️⃣ ROLE
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)

    # 8️⃣ EMERGENCY CONTACT
    emergency_name = models.CharField(max_length=200)
    emergency_relationship = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)

    # 9️⃣ AGREEMENTS
    accepted_terms = models.BooleanField(default=False)
    receive_updates = models.BooleanField(default=True)

    # ADMIN SIDE
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name