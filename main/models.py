from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


# Create your models here.
class Page(models.Model):
    page_name = models.CharField(max_length=200)

    def __str__(self):
        return self.page_name


class Description(models.Model):
    page = models.ForeignKey(
        Page, related_name="descriptions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.name} for {self.page.page_name}"


class Content(models.Model):
    SECTION_CHOICES = [
        ("Our Story", "Our Story"),
        ("Newsletter", "Newsletter"),
        ("Blog", "Blog"),
    ]

    section = models.CharField(max_length=50, choices=SECTION_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.section} - {self.title if self.title else 'Content'}"


class Assets(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(
        default="background", max_length=200, null=True, blank=True
    )
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
    service = models.ForeignKey(
        Service, related_name="subservices", on_delete=models.CASCADE
    )
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
    image = models.ImageField(upload_to="news_images/", blank=True, null=True)

    def __str__(self):
        return self.title


class Team(models.Model):
    ROLE_CHOICES = [
        ("Governor", "Governor"),
        ("Deputy Governor", "Deputy Governor"),
        ("Regional Coordinator", "Regional Coordinator"),
        ("Team Member", "Team Member"),
    ]

    LEADERSHIP_CHOICES = [
        ("Local", "Local"),
        ("Global", "Global"),
    ]

    name = models.CharField(max_length=255)
    leadership = models.CharField(
        max_length=50, choices=LEADERSHIP_CHOICES, default="Local"
    )
    facebook_link = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="people/")
    bio = models.TextField()

    def __str__(self):
        return self.name


class Gallery_image(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="gallery/")
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


# <<<<<<< 25.10_DC48_UAT_UO


# <<<<<<< 25.10_DC48_UAT_UO
# Stores email subscriptions for Safety Alerts
class SafetyAlertSubscription(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# Emergency help line configuration
class EmergencyHotline(models.Model):
    name = models.CharField(
        max_length=100, help_text="Display label, e.g., Global Hotline"
    )
    number = models.CharField(
        max_length=32, help_text="E.164 like +15551234567 or local format"
    )
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


# class EmergencyHelpActivation(models.Model):
#     EVENT_CHOICES = (
#         ("call_link_clicked", "Call Link Clicked"),
#         ("callback_requested", "Callback Requested"),
#     )
#     event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
#     name = models.CharField(max_length=100, blank=True, null=True)
#     phone = models.CharField(max_length=32, blank=True, null=True)
#     location = models.CharField(max_length=255, blank=True, null=True)
#     notes = models.TextField(blank=True, null=True)
#     ip_address = models.GenericIPAddressField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


# =======


# Medical Resource Inquiry model at top-level
# =======
# >>>>>>> 25.10_DC48_UAT_ND
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
        ("Undergraduate", "Undergraduate"),
        ("Masters", "Masters"),
        ("PhD", "PhD"),
        ("Vocational", "Vocational"),
    ]

    FIELD_CHOICES = [
        ("STEM", "STEM"),
        ("Humanities", "Humanities"),
        ("Business", "Business"),
        ("Arts", "Arts"),
    ]

    LOCATION_CHOICES = [
        ("Kenya", "Kenya"),
        ("Global", "Global"),
        ("UK", "UK"),
        ("USA", "USA"),
    ]

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Closing Soon", "Closing Soon"),
        ("Closed", "Closed"),
    ]

    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(
        max_length=100, choices=LEVEL_CHOICES, blank=True, null=True
    )
    field = models.CharField(
        max_length=100, choices=FIELD_CHOICES, blank=True, null=True
    )
    location = models.CharField(
        max_length=200, choices=LOCATION_CHOICES, blank=True, null=True
    )
    deadline = models.DateField(blank=True, null=True)
    amount = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, blank=True, null=True
    )

    class Meta:
        verbose_name = "Scholarship"
        verbose_name_plural = "Scholarships"
        ordering = ["deadline"]

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


# <<<<<<< 25.10_DC48_UAT_UO

# >>>>>>> 25.10_DC48_UAT_ND
# =======
# >>>>>>> 25.10_DC48_UAT_ND


class Testimonial(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    position = models.CharField(max_length=100, null=False, blank=True)
    organization = models.CharField(max_length=100, null=False, blank=True)
    testimonial = models.TextField(null=False, blank=False)
    image = models.ImageField(upload_to="Testimonial/", null=False, blank=True)
    date = models.DateField(auto_now_add=True, null=False)

    def __str__(self):
        return f"Testimonial from {self.name}"
    
class Governance(models.Model):
    """
    Governance Model for CRUD operations
    """
    governance_category = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    members = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=False, 
        blank=False,
        related_name='governance_memberships'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.governance_category} - {self.members.username}"
    
    class Meta:
        verbose_name = "Governance"
        verbose_name_plural = "Governance Records"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # You can add more custom logic here if needed
        super().save(*args, **kwargs)


# Add these at the bottom of your main/models.py

class InsurancePlan(models.Model):
    """Insurance plans for the comparison table"""
    provider_name = models.CharField(max_length=100)  # e.g., "Cigna"
    plan_name = models.CharField(max_length=100)      # e.g., "Global Gold"
    network = models.CharField(max_length=100)        # e.g., "Worldwide (inc. USA)"
    max_benefit = models.CharField(max_length=50)     # e.g., "$2,000,000"
    evacuation = models.CharField(max_length=50)      # e.g., "Included" or "Optional Add-on"
    score = models.DecimalField(max_digits=3, decimal_places=1)  # e.g., 9.8
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-score']
        verbose_name = "Insurance Plan"
        verbose_name_plural = "Insurance Plans"
    
    def __str__(self):
        return f"{self.provider_name} {self.plan_name}"


class AIRecommendationRule(models.Model):
    """Rules for AI recommendations based on user inputs"""
    AGE_CHOICES = [
        ('young', '18 - 30 Years'),
        ('mid', '31 - 55 Years'),
        ('senior', '56+ Years'),
    ]
    
    RESIDENCE_CHOICES = [
        ('usa', 'USA / Canada'),
        ('europe', 'Europe / UK'),
        ('other', 'Rest of World'),
    ]
    
    PRIORITY_CHOICES = [
        ('budget', 'Cost Savings'),
        ('comprehensive', 'Full Coverage'),
        ('emergency', 'Emergency Only'),
    ]
    
    age_bracket = models.CharField(max_length=20, choices=AGE_CHOICES)
    residence = models.CharField(max_length=20, choices=RESIDENCE_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    recommended_plan = models.ForeignKey(InsurancePlan, on_delete=models.CASCADE)
    recommendation_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['age_bracket', 'residence', 'priority']
        verbose_name = "AI Recommendation Rule"
        verbose_name_plural = "AI Recommendation Rules"
    
    def __str__(self):
        return f"{self.get_age_bracket_display()} - {self.get_residence_display()} - {self.get_priority_display()}"


class ExpertInquiry(models.Model):
    """Store expert consultation requests from the modal form"""
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    question = models.TextField()
    interested_plan = models.ForeignKey(InsurancePlan, on_delete=models.SET_NULL, null=True, blank=True)
    is_contacted = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Expert Inquiry"
        verbose_name_plural = "Expert Inquiries"
    
    def __str__(self):
        return f"Inquiry from {self.full_name} - {self.created_at.strftime('%Y-%m-%d')}"