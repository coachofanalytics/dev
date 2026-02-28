from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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



class Governance(models.Model):
    governance_category = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    members = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(null=False, blank=False)
    updated_at = models.DateTimeField(null=False, blank=False)

    def __str__(self):
        return self.governance_category


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
        
        question_lower = self.question.lower()
        
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
