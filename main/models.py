from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Count
from datetime import timedelta
from django.utils.text import slugify
import random
import string
import uuid
try:
    from .ai_services import generate_article_summary
except ImportError:
    def generate_article_summary(content):
        """Fallback when groq is not installed"""
        return content[:200] + "..."

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

    class Level(models.TextChoices):
        UNDERGRADUATE = "Undergraduate", "Undergraduate"
        MASTERS = "Masters", "Masters"
        PHD = "PhD", "PhD"
        VOCATIONAL = "Vocational", "Vocational"

    class Field(models.TextChoices):
        STEM = "STEM", "STEM"
        HUMANITIES = "Humanities", "Humanities"
        BUSINESS = "Business", "Business"
        ARTS = "Arts", "Arts"

    class Location(models.TextChoices):
        KENYA = "Kenya", "Kenya"
        GLOBAL = "Global", "Global"
        UK = "UK", "UK"
        USA = "USA", "USA"

    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSING_SOON = "Closing Soon", "Closing Soon"
        CLOSED = "Closed", "Closed"

    class Currency(models.TextChoices):
        USD = "USD", "US Dollar ($)"
        KES = "KES", "Kenyan Shilling (Ksh)"
        EUR = "EUR", "Euro (€)"
        GBP = "GBP", "British Pound (£)"

    amount_value = models.DecimalField(max_digits = 12, decimal_places=2, null=True, blank=True)
    amount_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )

    amount_description = models.CharField(max_length=100, blank=True, 
                                         help_text="E.g., 'Full tuition', 'Partial funding', etc.")

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    provider = models.CharField(max_length=255, default='')
    level = models.CharField(max_length=100, choices=Level.choices, default=Level.UNDERGRADUATE)
    field = models.CharField(max_length=100, choices=Field.choices, default=Field.STEM)
    location = models.CharField(max_length=200, choices=Location.choices, default=Location.GLOBAL)

    deadline = models.DateField(default=timezone.now)
    amount = models.CharField(max_length=100, default='0')

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline"]
    
    @property
    def amount(self):
        """Return formatted amount for display"""
        if self.amount_description:
            return self.amount_description
        
        if self.amount_value and self.amount_currency:
            # Format based on currency
            if self.amount_currency == 'USD':
                return f"${self.amount_value:,.2f}"
            elif self.amount_currency == 'KES':
                return f"KSh {self.amount_value:,.2f}"
            elif self.amount_currency == 'EUR':
                return f"€{self.amount_value:,.2f}"
            elif self.amount_currency == 'GBP':
                return f"£{self.amount_value:,.2f}"
            else:
                return f"{self.amount_currency} {self.amount_value:,.2f}"
        return "Varies"

    def generate_unique_slug(self):
        """Generates a unique slug for the scholarship"""
        base_slug = slugify(self.title)
        slug = base_slug
        while Scholarship.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{''.join(random.choices(string.digits, k=4))}"
        return slug

    def save(self, *args, **kwargs):
        # auto create unique slug
        if not self.slug:
            self.slug = self.generate_unique_slug()

        # auto update status based on deadline
        if self.deadline:
            today = timezone.now().date()
            days_left = (self.deadline - today).days

            if days_left < 0:
                self.status = self.Status.CLOSED
            elif days_left <= 7:
                self.status = self.Status.CLOSING_SOON
            else:
                self.status = self.Status.OPEN

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TrainingCourse(models.Model):
    class Category(models.TextChoices):
        TECH = "Tech", "Tech"
        BUSINESS = "Business", "Business"
        ART = "Art", "Art"
        HEALTH = "Health", "Health"

    class Format(models.TextChoices):
        ONLINE = "Online", "Online"
        OFFLINE = "Offline", "Offline"
        HYBRID = "Hybrid", "Hybrid"

    class Enrollment(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"
        CLOSING_SOON = "Closing Soon", "Closing Soon"  

    class Status(models.TextChoices):
        UPCOMING = "Upcoming", "Upcoming"
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"


    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    course_code = models.CharField(max_length=20, blank=True, help_text="e.g., CS101")
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.TECH)
    description = models.TextField(blank=True, help_text="Brief course description")
    duration = models.CharField(max_length=100, default="Self-paced", help_text="e.g., '6 weeks', '3 months', 'Self-paced'")
    format = models.CharField(max_length=50, choices=Format.choices, default=Format.ONLINE)
    enrollment = models.CharField(max_length=50, choices=Enrollment.choices, default=Enrollment.OPEN)
    max_students = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum capacity")
    enrolled_students = models.PositiveIntegerField(default=0, editable=False)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text="Optional: Course end date")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING, editable=False)
    instructor = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certificate_offered = models.BooleanField(default=False)

    syllabus = models.TextField(blank=True, help_text="Course outline/syllabus")
    prerequisites = models.TextField(blank=True, help_text="Required knowledge or courses")
    image = models.ImageField(upload_to='courses/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        verbose_name = "Training Course"
        verbose_name_plural = "Training Courses"
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['start_date']),
        ]


    def generate_unique_slug(self):
        base_slug = slugify(self.title)
        if self.course_code:
            base_slug = f"{base_slug}-{self.course_code.lower()}"
        slug = base_slug
        counter = 1
        while TrainingCourse.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()

        if self.start_date:
            today = timezone.now().date()
            end = self.end_date if self.end_date else self.start_date

            if today < self.start_date:
                self.status = self.Status.UPCOMING

            elif self.start_date <= today <= end:
                self.status = self.Status.ONGOING

            else:
                self.status = self.Status.COMPLETED


        if self.max_students and self.enrolled_students >= self.max_students:
            self.enrollment = self.Enrollment.CLOSED 
            
        elif self.enrollment == self.Enrollment.CLOSED and self.enrolled_students < self.max_students:
            pass

        super().save(*args, **kwargs)

    @property
    def spots_available(self):
        if self.max_students:
            return max(0, self.max_students - self.enrolled_students)
        return None
    
    @property
    def is_null(self):
        return self.max_students and self.enrolled_students >= self.max_students
    
    @property
    def progress_percentage(self):
        if self.status != self.Status.ONGOING or not self.end_date:
            return None
        total_duration = (self.end_date - self.start_date).days
        days_passed = (timezone.now().date() - self.start_date).days

        if total_duration > 0:
            return min(100, int((days_passed / total_duration)*100))
        return None
    def __str__(self):
        return f"{self.course_code} - {self.title}" if self.course_code else  self.title




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






class Gallery(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()

    def __str__(self):
        return self.title


class Faq(models.Model):
    CategoryChoices = [
        ('general', 'General'),
        ('technical', 'Technical'),
        ('billing', 'Billing'),
        ('account', 'Account'),
        ('other', 'Other'),
    ]
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=255, choices=CategoryChoices, default=999)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question


class GetHelp(models.Model):
    title = models.CharField(max_length=255,null=False,blank=False)
    content = models.TextField(null=False,blank=False)
    link = models.URLField(null=True,blank=False,max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=False,blank=False,auto_now_add=True)
    updated_at = models.DateTimeField(null=False,blank=False,auto_now=True)

    def __str__(self):
        return self.title


class DonationOrganization(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    linked_profile = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class History(models.Model):
    year = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="history_images/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-year', 'order']

    def __str__(self):
        return f"{self.year}: {self.title}"


class ConsularAssistancePage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consular Assistance Page"
        verbose_name_plural = "Consular Assistance Pages"

    def __str__(self):
        return self.title


class ServiceRequest(models.Model):
    """
    Reusable service request model. Currently used for Consular Consultation
    but designed with a service_type field to support Healthcare, Finance,
    Crisis, Education, Community, and News requests in the future.
    """

    SERVICE_TYPE_CHOICES = [
        ('consular', 'Consular Assistance'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('crisis', 'Crisis Support'),
        ('education', 'Education'),
        ('community', 'Community'),
        ('news', 'News'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_review', 'In Review'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]

    CONSULTATION_TYPE_CHOICES = [
        ('Legal & Immigration', 'Legal & Immigration'),
        ('Documentation', 'Documentation'),
        ('Property & Estate', 'Property & Estate'),
        ('Other', 'Other'),
    ]

    URGENCY_CHOICES = [
        ('Not Urgent', 'Not Urgent'),
        ('Moderately Urgent', 'Moderately Urgent'),
        ('Very Urgent', 'Very Urgent'),
        ('Emergency', 'Emergency'),
    ]

    # Core fields (matching the AJAX form submission)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES, default='consular')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default='')
    consultation_type = models.CharField(max_length=50, choices=CONSULTATION_TYPE_CHOICES)
    preferred_language = models.CharField(max_length=50, default='English')
    location = models.CharField(max_length=200, blank=True, default='')
    question = models.TextField(help_text="User's main consultation description")
    urgency = models.CharField(max_length=30, choices=URGENCY_CHOICES, default='Not Urgent')
    additional_notes = models.TextField(blank=True, default='')

    # Workflow / Admin fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True, default='', help_text="Internal notes (timestamped)")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_service_requests',
        help_text="Staff member assigned to handle this request"
    )
    reply_message = models.TextField(blank=True, default='', help_text="Reply sent back to the user")
    replied_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return f"[{self.get_service_type_display()}] {self.full_name} - {self.consultation_type} ({self.created_at.strftime('%Y-%m-%d')})"

    def add_note(self, note):
        """Append a timestamped note to admin_notes."""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        entry = f"[{timestamp}] {note}"
        if self.admin_notes:
            self.admin_notes += f"\n{entry}"
        else:
            self.admin_notes = entry
        self.save(update_fields=['admin_notes', 'updated_at'])

    def mark_responded(self):
        self.status = 'responded'
        if not self.replied_at:
            self.replied_at = timezone.now()
        self.save(update_fields=['status', 'replied_at', 'updated_at'])
        self.add_note("Status changed to Responded")

    def mark_closed(self):
        self.status = 'closed'
        self.save(update_fields=['status', 'updated_at'])
        self.add_note("Status changed to Closed")

    def days_since_created(self):
        delta = timezone.now() - self.created_at
        return delta.days

    def is_urgent(self):
        return self.urgency in ('Very Urgent', 'Emergency')


class Doctor(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Practice'),
        ('pediatrics', 'Pediatrics'),
        ('mental_health', 'Mental Health'),
        ('cardiology', 'Cardiology'),
        ('dentistry', 'Dentistry'),
        ('dermatology', 'Dermatology'),
        ('gynecology', 'Gynecology'),
        ('orthopedics', 'Orthopedics'),
    ]

    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('swahili', 'Swahili'),
        ('amharic', 'Amharic'),
        ('twi', 'Twi'),
        ('yoruba', 'Yoruba'),
        ('hausa', 'Hausa'),
        ('french', 'French'),
        ('arabic', 'Arabic'),
        ('somali', 'Somali'),
        ('tigrinya', 'Tigrinya'),
    ]

    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)  # e.g. "Senior Pediatrician"
    specialty = models.CharField(max_length=200)
    categories = models.JSONField(default=list)  # list of category keys
    location_city = models.CharField(max_length=200)
    location_country = models.CharField(max_length=200)
    clinic_name = models.CharField(max_length=200, blank=True)
    languages = models.JSONField(default=list)  # list of language keys
    telehealth = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    review_count = models.PositiveIntegerField(default=0)
    bio = models.TextField()
    education = models.JSONField(default=list)  # list of strings
    avatar_color = models.CharField(max_length=7, default='#4A90D9')  # CSS color for avatar bg
    avatar_initials = models.CharField(max_length=3, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_language_display_list(self):
        lang_map = dict(self.LANGUAGE_CHOICES)
        return [lang_map.get(l, l.title()) for l in self.languages]

    def get_category_display_list(self):
        cat_map = dict(self.CATEGORY_CHOICES)
        return [cat_map.get(c, c.title()) for c in self.categories]

    @property
    def full_location(self):
        parts = [self.location_city, self.location_country]
        return ', '.join(p for p in parts if p)

    def __str__(self):
        return f"{self.name} - {self.specialty}"

    class Meta:
        ordering = ['-rating', '-review_count']


class AppointmentRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
    ]

    TIME_CHOICES = [
        ('morning', 'Morning (8am–12pm)'),
        ('afternoon', 'Afternoon (12pm–5pm)'),
        ('evening', 'Evening (5pm–8pm)'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointment_requests')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=20, choices=TIME_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    honeypot = models.CharField(max_length=100, blank=True)  # spam protection
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} → {self.doctor.name} on {self.preferred_date}"

    class Meta:
        ordering = ['-created_at']


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


# In main/models.py - Update your ExpertInquiry class

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


     # ============= NEW FIELDS FOR SLA TRACKING =============
    first_response_time = models.DateTimeField(null=True, blank=True, help_text="When this inquiry was first responded to")
    resolution_time = models.DateTimeField(null=True, blank=True, help_text="When this inquiry was resolved")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inquiries',
        help_text="Agent assigned to this inquiry"
    )
    sla_deadline = models.DateTimeField(null=True, blank=True, help_text="SLA deadline based on priority")
    escalated = models.BooleanField(default=False, help_text="Whether this inquiry has been escalated")
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_inquiries'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Expert Inquiry"
        verbose_name_plural = "Expert Inquiries"
    
    def __str__(self):
        return f"Inquiry from {self.full_name} - {self.created_at.strftime('%Y-%m-%d')}"
    
    # ============= AUTOMATION METHODS =============
    
    def save(self, *args, **kwargs):
        """Override save to add automation logic"""
        is_new = self.pk is None  # Check if this is a new inquiry
        
        # Auto-add priority note based on question content
        if is_new:
            self.auto_set_priority_note()
        
        # Call the original save
        super().save(*args, **kwargs)
        
        # Trigger notifications for new inquiries
        if is_new:
            print(f"🔔 New inquiry #{self.id} from {self.full_name}")
            # We'll add email notifications in the next step
    
    def auto_set_priority_note(self):
        """Automatically add priority note based on question content"""
        urgent_keywords = [
            'emergency', 'urgent', 'asap', 'immediately', 'critical', 
            'hospital', 'accident', 'death', 'heart attack', 'stroke',
            'panic', 'desperate', 'cannot wait', 'as soon as possible'
        ]
        high_keywords = [
            'claim', 'denied', 'problem', 'issue', 'help', 'cancel', 
            'refund', 'complaint', 'confused', 'understand', 'explain',
            'coverage', 'benefit', 'expensive', 'cost'
        ]
        
        question_lower = self.question.lower() if self.question else ""
        
        # Check for urgent keywords
        for keyword in urgent_keywords:
            if keyword in question_lower:
                priority_note = "🔴 URGENT - Needs immediate attention (within 4 hours)"
                break
        else:
            # Check for high priority keywords
            for keyword in high_keywords:
                if keyword in question_lower:
                    priority_note = "🟠 HIGH PRIORITY - Address within 24 hours"
                    break
            else:
                priority_note = "🟢 NORMAL PRIORITY - Handle within 48 hours"
        
        # Add timestamp to the note
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        
        # Add to notes
        if self.notes:
            self.notes = f"[{timestamp}] {priority_note}\n{self.notes}"
        else:
            self.notes = f"[{timestamp}] {priority_note}"
    
    # ============= UTILITY METHODS =============
    
    def mark_as_contacted(self, notes=None):
        """Mark this inquiry as contacted"""
        from django.utils import timezone
        
        self.is_contacted = True
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        
        contact_note = f"[{timestamp}] ✅ Marked as contacted"
        if notes:
            contact_note += f" - Notes: {notes}"
        
        if self.notes:
            self.notes += f"\n{contact_note}"
        else:
            self.notes = contact_note
        
        self.save(update_fields=['is_contacted', 'notes', 'updated_at'])
        print(f"✅ Inquiry #{self.id} marked as contacted")
    
    def add_note(self, note):
        """Add a note to this inquiry"""
        from django.utils import timezone
        
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        note_entry = f"[{timestamp}] 📝 {note}"
        
        if self.notes:
            self.notes += f"\n{note_entry}"
        else:
            self.notes = note_entry
        
        self.save(update_fields=['notes', 'updated_at'])
        print(f"📝 Note added to inquiry #{self.id}")
    
    def get_priority(self):
        """Extract priority from notes"""
        if self.notes:
            if "🔴 URGENT" in self.notes:
                return "URGENT"
            elif "🟠 HIGH" in self.notes:
                return "HIGH"
        return "NORMAL"
    
    def days_since_created(self):
        """Get number of days since creation"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days
    
    def hours_since_created(self):
        """Get hours since creation (for urgent tracking)"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600
    
    def is_overdue(self):
        """Check if inquiry is overdue (>2 days and not contacted)"""
        return not self.is_contacted and self.days_since_created() >= 2
    
    def is_urgent_overdue(self):
        """Check if urgent inquiry is overdue (>4 hours and not contacted)"""
        return (not self.is_contacted and 
                self.get_priority() == "URGENT" and 
                self.hours_since_created() >= 4)
    
    # ============= CLASS METHODS =============
    
    @classmethod
    def get_uncontacted_inquiries(cls):
        """Get all inquiries that haven't been contacted"""
        return cls.objects.filter(is_contacted=False).order_by('-created_at')
    
    @classmethod
    def get_urgent_inquiries(cls):
        """Get all urgent inquiries"""
        urgent_list = []
        for inquiry in cls.objects.filter(is_contacted=False):
            if inquiry.get_priority() == "URGENT":
                urgent_list.append(inquiry)
        return urgent_list
    
    @classmethod
    def get_overdue_inquiries(cls):
        """Get all overdue inquiries"""
        return [i for i in cls.objects.filter(is_contacted=False) if i.is_overdue()]
    
    @classmethod
    def get_stats(cls):
        """Get statistics about inquiries"""
        total = cls.objects.count()
        uncontacted = cls.objects.filter(is_contacted=False).count()
        urgent = len(cls.get_urgent_inquiries())
        overdue = len(cls.get_overdue_inquiries())
        
        return {
            'total': total,
            'uncontacted': uncontacted,
            'contacted': total - uncontacted,
            'urgent': urgent,
            'overdue': overdue,
        }
    
    def send_notifications(self):
        """Send email notifications to admin and auto-reply to user"""
        from django.db import transaction
        transaction.on_commit(lambda: self._send_emails())
    
    def _send_emails(self):
        """Internal method to send emails"""
        try:
            # Send email to admin
            self._send_admin_notification()
            
            # Send auto-reply to user
            self._send_user_autoreply()
            
            # Add note about email notification
            self.add_note("📧 Email notifications sent to admin and user")
            print(f"📧 Emails sent for inquiry #{self.id}")
            
        except Exception as e:
            error_msg = f"❌ Failed to send emails: {str(e)}"
            print(error_msg)
            self.add_note(error_msg)
    
    def _send_admin_notification(self):
        """Send notification email to admin"""
        subject = f"New Insurance Inquiry: {self.full_name}"
        
        # HTML email
        html_content = render_to_string('main/emails/admin_notification.html', {
            'inquiry': self,
            'site_url': settings.SITE_URL
        })
        
        # Text email
        text_content = render_to_string('main/emails/admin_notification.txt', {
            'inquiry': self,
            'site_url': settings.SITE_URL
        })
        
        # Send email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    
    def _send_user_autoreply(self):
        """Send auto-reply email to the user"""
        subject = "Thank you for contacting Diaspora County 48 Insurance Support"
        
        # HTML email
        html_content = render_to_string('main/emails/user_autoreply.html', {
            'inquiry': self
        })
        
        # Text email
        text_content = render_to_string('main/emails/user_autoreply.txt', {
            'inquiry': self
        })
        
        # Send email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    
    # ============= NEW SLA METHODS =============
    
    def calculate_sla_deadline(self):
        """Calculate SLA deadline based on priority"""
        from django.utils import timezone

        created = self.created_at or timezone.now()
        
        priority = self.get_priority()
        if priority == "URGENT":
            deadline = self.created_at + timedelta(hours=4)
        elif priority == "HIGH":
            deadline = self.created_at + timedelta(hours=24)
        else:  # NORMAL
            deadline = self.created_at + timedelta(hours=48)
        
        return deadline
    
    def update_sla_deadline(self):
        """Update SLA deadline when priority changes"""
        self.sla_deadline = self.calculate_sla_deadline()
        self.save(update_fields=['sla_deadline'])
    
    def get_sla_status(self):
        """Get current SLA status with emoji"""
        if self.is_contacted:
            return "✅ Resolved"
        
        if not self.sla_deadline:
            self.sla_deadline = self.calculate_sla_deadline()
            self.save(update_fields=['sla_deadline'])
        
        from django.utils import timezone
        now = timezone.now()
        
        if now > self.sla_deadline:
            hours_overdue = (now - self.sla_deadline).total_seconds() / 3600
            return f"🔴 SLA Breached ({int(hours_overdue)}h overdue)"
        
        time_left = self.sla_deadline - now
        hours_left = time_left.total_seconds() / 3600
        
        if hours_left < 1:
            return f"🟠 Critical ({int(hours_left*60)}m left)"
        elif hours_left < 4:
            return f"🟡 At Risk ({int(hours_left)}h left)"
        else:
            return f"🟢 On Track ({int(hours_left)}h left)"
    
    def get_response_time(self):
        """Calculate response time in hours"""
        if self.first_response_time:
            delta = self.first_response_time - self.created_at
            hours = delta.total_seconds() / 3600
            if hours < 1:
                minutes = int(hours * 60)
                return f"{minutes} minutes"
            else:
                return f"{round(hours, 1)} hours"
        return "Not yet responded"
    
    def check_and_escalate(self):
        """Auto-escalate if SLA is breached"""
        from django.utils import timezone
        
        if self.is_contacted or self.escalated:
            return
        
        if not self.sla_deadline:
            self.sla_deadline = self.calculate_sla_deadline()
        
        if timezone.now() > self.sla_deadline:
            self.escalated = True
            self.escalated_at = timezone.now()
            
            # Find manager to escalate to
            manager = User.objects.filter(is_staff=True, is_superuser=True).first()
            if manager:
                self.escalated_to = manager
                
                # Send escalation email
                self.send_escalation_notification(manager)
            
            self.save(update_fields=['escalated', 'escalated_at', 'escalated_to'])
            self.add_note("🚨 AUTO-ESCALATED: SLA breached")
    
    def send_escalation_notification(self, manager):
        """Send notification when inquiry is escalated"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"🚨 ESCALATED: {self.get_priority()} Priority Inquiry"
        message = f"""
        An inquiry has been automatically escalated due to SLA breach.
        
        Customer: {self.full_name}
        Priority: {self.get_priority()}
        Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}
        SLA Deadline: {self.sla_deadline.strftime('%Y-%m-%d %H:%M')}
        
        Question: {self.question[:200]}...
        
        Please review and assign to an available agent.
        Admin Link: {settings.SITE_URL}/admin/main/expertinquiry/{self.id}/
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager.email],
            fail_silently=True,
        )
    
    # ============= ENHANCED EXISTING METHODS =============
    
    def save(self, *args, **kwargs):
        """Override save to add automation logic"""
        is_new = self.pk is None
        
        if is_new:
            self.auto_set_priority_note()
        
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.sla_deadline = self.calculate_sla_deadline()
            self.save(update_fields=['sla_deadline'])
            print(f"🔔 New inquiry #{self.id} from {self.full_name}")
            # Auto-assign to available agent
            self.auto_assign()
    
    def mark_as_contacted(self, notes=None):
        """Enhanced: Now tracks first response time"""
        from django.utils import timezone
        
        self.is_contacted = True
        if not self.first_response_time:
            self.first_response_time = timezone.now()
        
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        response_time = self.get_response_time()
        
        contact_note = f"[{timestamp}] ✅ Marked as contacted (Response time: {response_time})"
        if notes:
            contact_note += f" - Notes: {notes}"
        
        if self.notes:
            self.notes += f"\n{contact_note}"
        else:
            self.notes = contact_note
        
        self.save(update_fields=['is_contacted', 'first_response_time', 'notes', 'updated_at'])
        print(f"✅ Inquiry #{self.id} marked as contacted")
    
    def auto_assign(self):
        """Auto-assign inquiry to agent with least workload"""
        # Get all active staff members
        agents = User.objects.filter(is_staff=True, is_active=True)
        
        if not agents.exists():
            return
        
        # Count current assignments per agent
        agent_load = []
        for agent in agents:
            load = ExpertInquiry.objects.filter(
                assigned_to=agent,
                is_contacted=False
            ).count()
            agent_load.append((agent, load))
        
        # Assign to agent with least load
        agent_load.sort(key=lambda x: x[1])
        assigned_agent = agent_load[0][0]
        
        self.assigned_to = assigned_agent
        self.save(update_fields=['assigned_to'])
        
        # Notify agent
        self.send_assignment_notification(assigned_agent)
        
        self.add_note(f"🤖 Auto-assigned to {assigned_agent.get_full_name() or assigned_agent.username}")
    
    def send_assignment_notification(self, agent):
        """Send email notification to assigned agent"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"New {self.get_priority()} Priority Inquiry Assigned"
        message = f"""
        You have been assigned a new inquiry.
        
        Customer: {self.full_name}
        Email: {self.email}
        Phone: {self.phone or 'Not provided'}
        Priority: {self.get_priority()}
        SLA Deadline: {self.sla_deadline.strftime('%Y-%m-%d %H:%M')}
        
        Question: {self.question}
        
        View in admin: {settings.SITE_URL}/admin/main/expertinquiry/{self.id}/
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[agent.email],
            fail_silently=True,
        )
    
    # ============= NEW CLASS METHODS =============
    
    @classmethod
    def get_sla_compliance_stats(cls):
        """Get SLA compliance statistics"""
        total = cls.objects.count()
        if total == 0:
            return {
                'total': 0,
                'resolved': 0,
                'in_sla': 0,
                'compliance_rate': 0,
                'escalated': 0,
                'avg_response_time':None
            }
        
        responded_in_sla = 0
        total_responded = 0
        for inquiry in cls.objects.filter(is_contacted=True):
            total_responded += 1
            if inquiry.first_response_time and inquiry.sla_deadline:
                if inquiry.first_response_time <= inquiry.sla_deadline:
                    responded_in_sla += 1
        
        return {
            'total': total,
            'resolved': cls.objects.filter(is_contacted=True).count(),
            'in_sla': responded_in_sla,
            'compliance_rate': round(responded_in_sla / total * 100, 1) if total > 0 else 0,
            'escalated': cls.objects.filter(escalated=True).count(),
            'avg_response_time': cls.get_avg_response_time()
        }
    
    @classmethod
    def get_avg_response_time(cls):
        """Calculate average response time across all inquiries"""
        responded = cls.objects.filter(first_response_time__isnull=False)
        if not responded.exists():
            return None
        
        total_seconds = 0
        count = 0
        for inquiry in responded:
            if inquiry.first_response_time and inquiry.created_at:
                delta = inquiry.first_response_time - inquiry.created_at
                total_seconds += delta.total_seconds()
                count += 1

        if count == 0:
            return None
        
        avg_hours = total_seconds / count / 3600
        if avg_hours < 1:
            return f"{int(avg_hours * 60)} minutes"
        else:
            return f"{round(avg_hours, 1)} hours"
    
    @classmethod
    def check_all_sla(cls):
        """Check SLA for all open inquiries (run via cron)"""
        open_inquiries = cls.objects.filter(is_contacted=False)
        for inquiry in open_inquiries:
            inquiry.check_and_escalate()
        print(f"✅ Checked SLA for {open_inquiries.count()} inquiries")    


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    author = models.CharField(max_length=100)
    featured_image =models.ImageField(upload_to='news_images/')
    content = models.TextField()

    status = models.CharField(max_length=10,choices=STATUS_CHOICES, default='DRAFT')
    ai_summary = models.TextField(blank=True,null=False, help_text="AI_generated summary for index page")
    is_breaking = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveBigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:250]

        if self.content and not self.ai_summary:
            self.ai_summary = generate_article_summary(self.content)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    conf_token = models.CharField(max_length=100, default=uuid.uuid4, editable=False)
    confirmed = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}"

    class Meta:
        verbose_name_plural = "Subscribers"
        ordering = ['-subscribed_at']


# ============================================
# LEGAL & IMMIGRATION SERVICES MODELS
# ============================================

class LegalService(models.Model):
    """
    Model to store legal & immigration guidance services.
    Used on the Legal and Immigration Guidance dedicated page.
    """
    CATEGORY_CHOICES = [
        ('visa', 'Visa and Residency Services'),
        ('citizenship', 'Citizenship and Naturalization'),
        ('legal_referral', 'Legal Representation & Referrals'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    features = models.JSONField(default=list)  # List of bullet points
    cta_button_text = models.CharField(max_length=100, default='Learn More')
    cta_button_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)  # Display order
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Legal Service'
        verbose_name_plural = 'Legal Services'

    def __str__(self):
        return self.title


# ============================================
# COMMUNITIES APP MODELS (MERGED FROM communities app)
# ============================================

class CommunityMember(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Profile fields
    profession = models.CharField(max_length=100, default="Not Specified")
    region = models.CharField(max_length=100, default="Not Specified")
    specialization = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='member_profiles/', blank=True, null=True)
    
    # Status fields
    is_verified = models.BooleanField(default=True)
    is_public_directory = models.BooleanField(default=True)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.profession}"
    
    class Meta:
        ordering = ['-date_joined']


class DirectoryProfile(models.Model):
    MEMBERSHIP_CHOICES = [
        ('verified', 'Verified (Free)'),
        ('premium', 'Premium ($9/mo)'),
    ]
    
    CATEGORY_CHOICES = [
        ('tech', 'Tech & IT'),
        ('legal', 'Legal'),
        ('finance', 'Finance & Accounting'),
        ('health', 'Healthcare'),
        ('education', 'Education'),
        ('business', 'Business & Consulting'),
        ('creative', 'Creative & Media'),
        ('engineering', 'Engineering'),
        ('other', 'Other'),
    ]
    
    # Link to basic CommunityMember
    community_member = models.OneToOneField(
        CommunityMember,
        on_delete=models.CASCADE,
        related_name='directory_profile'
    )
    
    # Form fields
    full_name = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    region_city = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='verified')
    expertise_summary = models.TextField()
    profile_photo = models.ImageField(upload_to='directory_profiles/', blank=True, null=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.profession}"
    
    def save(self, *args, **kwargs):
        # Update the main CommunityMember if needed
        if self.community_member:
            self.community_member.name = self.full_name
            self.community_member.profession = self.profession
            self.community_member.region = self.region_city
            self.community_member.save()
        super().save(*args, **kwargs)


class ForumCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Forum Categories"


class CommunityPost(models.Model):
    """Forum post model (named CommunityPost to avoid clashes with other Post models)"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class CommentP(models.Model):
    post = models.ForeignKey(CommunityPost, related_name='comments_p', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class EventCalendar(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name
