from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser, Region, Chapter
from django.utils.text import slugify
from datetime import timedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from coda_project import settings



#from tableauhyperapi import DatabaseName

User = get_user_model()
# Create your models here.

class Page(models.Model):
    page_name = models.CharField(max_length=200)

    def __str__(self):
        return self.page_name

class Description(models.Model):
    page = models.ForeignKey(Page, related_name='descriptions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,null=False, blank=False) 
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
    category = models.CharField(default='background',max_length=200,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=1000, null=True, blank=True)

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
    

class Feedback(models.Model):
    user= models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # category = models.ForeignKey(UserCategory,null=True,blank=True,on_delete=models.CASCADE)
    topic = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
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
    CATEGORY_CHOICES = [
    ("political", "Political"),
    ("business", "Business"),
    ("education", "Education"),
    ("health", "Health"),
    ("culture", "Culture"),
    ("technology", "Technology"),
    ("events", "Events"),
    ]
    title = models.CharField(max_length=200, default="")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="news", default="")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="news", default="")
    content = models.TextField(default="")
    source = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="")
    link = models.URLField(null=True,blank=True)
    published_date = models.DateField()
    is_event = models.BooleanField(default=False)
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)  # Add this line for image field
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)


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
    leadership = models.CharField(max_length=50, choices=LEADERSHIP_CHOICES, default='Local')  # or another default value
    facebook_link = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='people/')
    bio = models.TextField()

    def __str__(self):
        return self.name


class Gallery(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()

    def __str__(self):
        return self.title



class ContactUs(models.Model):
    name = models.CharField(max_length=100, help_text="Full name of the user.")
    email = models.EmailField(help_text="Email address for correspondence.")
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, 
        help_text="Phone number of the user (optional)."
    )
    message = models.TextField(help_text="Message or inquiry from the user.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the message was submitted.")
    is_resolved = models.BooleanField(default=False, help_text="Flag to mark whether the query has been addressed.")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    



class Faq(models.Model):
    CategoryChoices = [
        ('general', 'General'),
        ('technical', 'Technical'),
        ('billing', 'Billing'),
        ('account', 'Account'),
        ('other', 'Other'),
    ]
    question = models.CharField(max_length=255) #add questions 
    answer = models.TextField() #add answers
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

    


class Governance(models.Model):
    GovernanceCategoryChoices = [
        ('Global Executive Committee', 'Global Executive Committee'),
        ('Regional Administration', 'Regional Administration'),
        ('County Assembly Administration', 'County Assembly Administration')
    ]
    governance_category = models.CharField(max_length=255, choices=GovernanceCategoryChoices)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    members = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='governance')
    # user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='governance')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regions', default="")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='chapter', default="")
    image = models.ImageField(upload_to='img/governance', default='img/governance/dc48k_logo.png')
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ui_order = models.IntegerField(unique=False, default=0) # used organize leadership/photos on ui.

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.governance_category)
            slug = base_slug
            num = 1
            while Governance.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.governance_category}, {self.title}, {self.members}"
    

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


# ============================================
# HEALTHCARE INFORMATION MODELS
# ============================================

class MedicalResourceInquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


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
    title = models.CharField(max_length=200)
    specialty = models.CharField(max_length=200)
    categories = models.JSONField(default=list)
    location_city = models.CharField(max_length=200)
    location_country = models.CharField(max_length=200)
    clinic_name = models.CharField(max_length=200, blank=True)
    languages = models.JSONField(default=list)
    telehealth = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    review_count = models.PositiveIntegerField(default=0)
    bio = models.TextField()
    education = models.JSONField(default=list)
    avatar_color = models.CharField(max_length=7, default='#4A90D9')
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
        ('morning', 'Morning (8am-12pm)'),
        ('afternoon', 'Afternoon (12pm-5pm)'),
        ('evening', 'Evening (5pm-8pm)'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointment_requests')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=20, choices=TIME_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    honeypot = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} -> {self.doctor.name} on {self.preferred_date}"

    class Meta:
        ordering = ['-created_at']


class InsurancePlan(models.Model):
    """Insurance plans for the comparison table"""
    provider_name = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    network = models.CharField(max_length=100)
    max_benefit = models.CharField(max_length=50)
    evacuation = models.CharField(max_length=50)
    score = models.DecimalField(max_digits=3, decimal_places=1)
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

    # SLA tracking fields
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

    def save(self, *args, **kwargs):
        """Override save to add automation logic"""
        is_new = self.pk is None
        if is_new:
            self.auto_set_priority_note()
        super().save(*args, **kwargs)
        if is_new:
            self.sla_deadline = self.calculate_sla_deadline()
            self.save(update_fields=['sla_deadline'])
            self.auto_assign()

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
        priority_note = ""

        for keyword in urgent_keywords:
            if keyword in question_lower:
                priority_note = "URGENT - Needs immediate attention (within 4 hours)"
                break
        else:
            for keyword in high_keywords:
                if keyword in question_lower:
                    priority_note = "HIGH PRIORITY - Address within 24 hours"
                    break
            else:
                priority_note = "NORMAL PRIORITY - Handle within 48 hours"

        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')

        if self.notes:
            self.notes = f"[{timestamp}] {priority_note}\n{self.notes}"
        else:
            self.notes = f"[{timestamp}] {priority_note}"

    def mark_as_contacted(self, notes=None):
        """Mark this inquiry as contacted"""
        from django.utils import timezone
        self.is_contacted = True
        if not self.first_response_time:
            self.first_response_time = timezone.now()
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        response_time = self.get_response_time()
        contact_note = f"[{timestamp}] Marked as contacted (Response time: {response_time})"
        if notes:
            contact_note += f" - Notes: {notes}"
        if self.notes:
            self.notes += f"\n{contact_note}"
        else:
            self.notes = contact_note
        self.save(update_fields=['is_contacted', 'first_response_time', 'notes', 'updated_at'])

    def add_note(self, note):
        """Add a note to this inquiry"""
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        note_entry = f"[{timestamp}] {note}"
        if self.notes:
            self.notes += f"\n{note_entry}"
        else:
            self.notes = note_entry
        self.save(update_fields=['notes', 'updated_at'])

    def get_priority(self):
        """Extract priority from notes"""
        if self.notes:
            if "URGENT" in self.notes:
                return "URGENT"
            elif "HIGH" in self.notes:
                return "HIGH"
        return "NORMAL"

    def days_since_created(self):
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days

    def hours_since_created(self):
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600

    def is_overdue(self):
        return not self.is_contacted and self.days_since_created() >= 2

    def is_urgent_overdue(self):
        return (not self.is_contacted and
                self.get_priority() == "URGENT" and
                self.hours_since_created() >= 4)

    @classmethod
    def get_uncontacted_inquiries(cls):
        return cls.objects.filter(is_contacted=False).order_by('-created_at')

    @classmethod
    def get_urgent_inquiries(cls):
        urgent_list = []
        for inquiry in cls.objects.filter(is_contacted=False):
            if inquiry.get_priority() == "URGENT":
                urgent_list.append(inquiry)
        return urgent_list

    @classmethod
    def get_overdue_inquiries(cls):
        return [i for i in cls.objects.filter(is_contacted=False) if i.is_overdue()]

    @classmethod
    def get_stats(cls):
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

    def calculate_sla_deadline(self):
        from django.utils import timezone
        created = self.created_at or timezone.now()
        priority = self.get_priority()
        if priority == "URGENT":
            deadline = created + timedelta(hours=4)
        elif priority == "HIGH":
            deadline = created + timedelta(hours=24)
        else:
            deadline = created + timedelta(hours=48)
        return deadline

    def update_sla_deadline(self):
        self.sla_deadline = self.calculate_sla_deadline()
        self.save(update_fields=['sla_deadline'])

    def get_sla_status(self):
        if self.is_contacted:
            return "Resolved"
        if not self.sla_deadline:
            self.sla_deadline = self.calculate_sla_deadline()
            self.save(update_fields=['sla_deadline'])
        from django.utils import timezone
        now = timezone.now()
        if now > self.sla_deadline:
            hours_overdue = (now - self.sla_deadline).total_seconds() / 3600
            return f"SLA Breached ({int(hours_overdue)}h overdue)"
        time_left = self.sla_deadline - now
        hours_left = time_left.total_seconds() / 3600
        if hours_left < 1:
            return f"Critical ({int(hours_left*60)}m left)"
        elif hours_left < 4:
            return f"At Risk ({int(hours_left)}h left)"
        else:
            return f"On Track ({int(hours_left)}h left)"

    def get_response_time(self):
        if self.first_response_time:
            delta = self.first_response_time - self.created_at
            hours = delta.total_seconds() / 3600
            if hours < 1:
                return f"{int(hours * 60)} minutes"
            else:
                return f"{round(hours, 1)} hours"
        return "Not yet responded"

    def check_and_escalate(self):
        from django.utils import timezone
        if self.is_contacted or self.escalated:
            return
        if not self.sla_deadline:
            self.sla_deadline = self.calculate_sla_deadline()
        if timezone.now() > self.sla_deadline:
            self.escalated = True
            self.escalated_at = timezone.now()
            manager = User.objects.filter(is_staff=True, is_superuser=True).first()
            if manager:
                self.escalated_to = manager
            self.save(update_fields=['escalated', 'escalated_at', 'escalated_to'])
            self.add_note("AUTO-ESCALATED: SLA breached")

    def auto_assign(self):
        agents = User.objects.filter(is_staff=True, is_active=True)
        if not agents.exists():
            return
        agent_load = []
        for agent in agents:
            load = ExpertInquiry.objects.filter(
                assigned_to=agent,
                is_contacted=False
            ).count()
            agent_load.append((agent, load))
        agent_load.sort(key=lambda x: x[1])
        assigned_agent = agent_load[0][0]
        self.assigned_to = assigned_agent
        self.save(update_fields=['assigned_to'])
        self.add_note(f"Auto-assigned to {assigned_agent.get_full_name() or assigned_agent.username}")

    @classmethod
    def get_sla_compliance_stats(cls):
        total = cls.objects.count()
        if total == 0:
            return {'total': 0, 'resolved': 0, 'in_sla': 0, 'compliance_rate': 0, 'escalated': 0, 'avg_response_time': None}
        responded_in_sla = 0
        for inquiry in cls.objects.filter(is_contacted=True):
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
        open_inquiries = cls.objects.filter(is_contacted=False)
        for inquiry in open_inquiries:
            inquiry.check_and_escalate()
