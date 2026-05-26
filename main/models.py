from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser, Region, Chapter
from django.utils.text import slugify
from django.utils import timezone
import random
import string



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

    amount_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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
        if not self.slug:
            self.slug = self.generate_unique_slug()

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
        elif self.enrollment == self.Enrollment.CLOSED and self.max_students and self.enrolled_students < self.max_students:
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
            return min(100, int((days_passed / total_duration) * 100))
        return None

    def __str__(self):
        return f"{self.course_code} - {self.title}" if self.course_code else self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    position = models.CharField(max_length=100, null=False, blank=True)
    organization = models.CharField(max_length=100, null=False, blank=True)
    testimonial = models.TextField(null=False, blank=False)
    image = models.ImageField(upload_to="Testimonial/", null=False, blank=True)
    date = models.DateField(auto_now_add=True, null=False)

    def __str__(self):
        return f"Testimonial from {self.name}"
