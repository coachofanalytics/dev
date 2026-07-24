from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db.models.signals import pre_save
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
try:
    from professional_services.models import ActivityLinks, FeaturedActivity, FeaturedCategory, FeaturedSubCategory
except ImportError:
    # Stub classes for lightweight branches where professional_services is removed
    ActivityLinks = None
    FeaturedActivity = None
    FeaturedCategory = None
    FeaturedSubCategory = None
from .utils import unique_slug_generator,slug_pre_save_receiver
from django.urls import reverse
from django.utils import timezone
from django_countries.fields import CountryField
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


# =============================================================================
# SHARED BASE MODELS FOR CODE OPTIMIZATION
# =============================================================================

class UserReferenceMixin(models.Model):
    """
    Mixin for consistent user references across all models
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s",
        help_text="User associated with this record"
    )
    
    class Meta:
        abstract = True


class ContractBase(TimeStampedModel):
    """
    Base model for contract-related fields shared across apps
    Eliminates duplication between investing and finance apps
    """
    client_signature = models.ImageField(
        upload_to="signatures/", 
        blank=True, 
        null=True,
        help_text="Client signature image"
    )
    company_rep = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Company representative name"
    )
    contract_submitted_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date contract was submitted"
    )
    client_date = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Client signature date"
    )
    rep_date = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Representative signature date"
    )
    contract_signed = models.BooleanField(
        default=False,
        help_text="Whether contract has been signed"
    )
    contract_signed_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date contract was signed"
    )
    
    class Meta:
        abstract = True


class DocumentMixin(models.Model):
    """
    Mixin for document storage and management
    """
    documents = models.JSONField(
        default=list, 
        blank=True,
        help_text="Stored documents and verification files"
    )
    
    class Meta:
        abstract = True


class StatusMixin(models.Model):
    """
    Mixin for status tracking with audit trail
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of the record"
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="modified_%(app_label)s_%(class)s",
        help_text="User who last modified this record"
    )
    modification_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Reason for the last modification"
    )
    
    class Meta:
        abstract = True

class Location(models.Model):
    zipcode = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = CountryField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Location")

    def __str__(self):
        return str(self.state)

class Company(TimeStampedModel):
    """Company Table will provide a list of the different company affiliated with CODA"""
    class Coda_Relation(models.IntegerChoices):
        client = 1
        investor = 2
        background = 3
        other = 4
    name = models.CharField(max_length=100,null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    sector = models.CharField(max_length=100,null=True, blank=True)
    mission = models.CharField(max_length=100,null=True, blank=True)
    website = models.CharField(max_length=100,null=True, blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        # default=1,
        null=True, 
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        # default=1,
        null=True, 
        blank=True
    )
    description = models.TextField(max_length=500, null=True, blank=True)
    relation=models.IntegerField(choices=Coda_Relation.choices, default=4)
    
    # Receipt branding fields
    logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True,
        help_text="Company logo for receipts and emails (kept for future use)"
    )
    receipt_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Email address for sending receipts (e.g., info@domain.com)"
    )
    display_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Display name for receipts (e.g., 'CODA ANALYTICS' or 'DC48K')"
    )
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Company address for receipts"
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['relation']),
        ]

    def __str__(self):
        return self.name
    

class Service(models.Model):
    serial = models.PositiveIntegerField(null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,default=1)
    title = models.CharField(default='training',max_length=254)
    slug = models.SlugField(default='slug',max_length=255)
    description = models.TextField(null=True, blank=True)
    sub_titles = models.TextField(null=True, blank=True)
    # executive_summary = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural = "Services"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['company']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return "/services/{slug}/".format(slug=self.slug)

class ServiceCategory(models.Model):
    def get_default_service():
        try:
            return Service.objects.get_or_create(serial=1)[0].id
        except:
            return 1
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, default=get_default_service)
    name = models.CharField(max_length=254)
    slug = models.SlugField(null=True, blank=True,unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class Pricing(models.Model):
    class Contract(models.IntegerChoices):
        One_month = 1
        Two_months = 2
        Three_months = 3
        open = 12
    serial = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE,default=1)
    # subcategory = models.CharField(default='Full Course', max_length=200, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(999999.99)]
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01), MaxValueValidator(999999.99)]
    )
    duration =  models.PositiveIntegerField(null=True, blank=True)
    contract_length = models.IntegerField(choices=Contract.choices, default=3)
    is_direct = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    redirect_url_path = models.CharField(max_length=1024, null=True)

    class Meta:
        verbose_name_plural = "Pricing"

    def clean(self):
        """Validate Pricing model data"""
        from django.core.exceptions import ValidationError
        
        # Validate discounted price vs regular price
        if self.discounted_price and self.price:
            if self.discounted_price >= self.price:
                raise ValidationError("Discounted price must be less than regular price")
        
        # Validate duration if provided
        if self.duration and self.duration <= 0:
            raise ValidationError("Duration must be positive")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PricingSubPlan(TimeStampedModel):
    my_pricing = models.ForeignKey(Pricing, on_delete=models.CASCADE)
    title = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(999999.99)]
    )
    
    class Meta:
        verbose_name_plural = "PricingSubPlan"

    def __str__(self):
        return self.title + '-' + self.my_pricing.title

class Testimonials(models.Model):
    # asset_id = models.ForeignKey(Assets, on_delete=models.CASCADE,default=1)
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    writer = models.ForeignKey(
        User,
        verbose_name=("writer name"),
        on_delete=models.CASCADE,
        # UPDATED: Use category-based filtering instead of deleted is_client field
        limit_choices_to=(Q(is_staff=True) | Q(category__in=[1, 3, 4, 5, 6, 7])),  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        )
    class Meta:
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('main:post-detail', kwargs={'pk': self.pk})
    

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
    
class Plan(models.Model):
    CAT_CHOICES = [
        ("Financial", "Financial"),
        ("Health", "Health"),
        ("Family", "Family"),
        ("Work", "Work"),
        ("Meetings", "Meetings"),
        ("Other", "Other"),
    ]
    GOAL_CHOICES = [
        ("Business", "Business"),
        ("Employment", "Employment"),
        ("Savings", "Savings"),
        ("Insurance", "Insurance"),
        ("Relationship", "Relationship"),
        ("Trips", "Trips"),
        ("Other", "Other"),
    ]
    DAY_CHOICES = [
        ("Sunday", "Sunday"),
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
    ]
    STATUS_CHOICES = [
        ("Critical", "Critical"),
        ("High", "High"),
        ("Medium", "Medium"),
        ("Low", "Low"),
    ]
    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="Other",
    )
    goal = models.CharField(
        max_length=25,
        choices=GOAL_CHOICES,
        default="Other",
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default="Low",
    )
    day = models.CharField(
        max_length=25,
        choices=DAY_CHOICES,
        default="Sunday",
    )
    planner = models.ForeignKey(
        User,
        related_name="planner",
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
        and (Q(is_admin=True) | Q(is_superuser=True)),
    )
    responsible_party = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=1,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True)),
    )
    task = models.CharField(max_length=255, default="CODA")
    duration = models.IntegerField(null=False, default=4)  # how long will it take
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    what = models.TextField()  # What is needed?
    why = models.TextField()  # Why do they need it ?
    how = (
        models.TextField()
    )  # how should it be delivered/Which platform or mode of delivery?
    comments = models.TextField(default='No Comment',null=True, blank=True)  # What is needed?
    doc = models.FileField(upload_to="Uploads/Support_Docs/", null=True, blank=True)
    pptlink = models.CharField(max_length=300, default="link",null=True, blank=True)
    videolink = models.CharField(max_length=300, default="Video",null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_answered = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Plan"
        # ordering = ["-created_at","-updated_at"]
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['category']),
            models.Index(fields=['goal']),
            models.Index(fields=['status']),
            models.Index(fields=['planner']),
            models.Index(fields=['responsible_party']),
            # Composite indexes for common query patterns
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['planner', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]

    def clean(self):
        """Validate Plan model data"""
        from django.core.exceptions import ValidationError
        
        # Validate duration
        if self.duration and self.duration <= 0:
            raise ValidationError("Duration must be positive")
        
        # Validate end time vs start time
        if hasattr(self, 'end_time') and hasattr(self, 'start_time'):
            if self.end_time and self.start_time and self.end_time <= self.start_time:
                raise ValidationError("End time must be after start time")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def doc_url(self):
        if self.doc and hasattr(self.doc, 'url'):
            return self.doc.url
    @property
    def delivery(self):
        delivery=self.duration + self.created_at
        return delivery

    def get_absolute_url(self):
        return reverse("main:plans")

    def __str__(self):
        return self.goal


class ClientAvailability(models.Model):
    DAY_CHOICES = [
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    ]

    TIME_ZONE_CHOICES = [
        ("PST", "PST"),
        ("CST", "CST"),
        ("EST", "EST"),
        ("EAT", "EAT"),
    ]

    client = models.ForeignKey(User, related_name="trainer", on_delete=models.CASCADE)
    day = models.CharField(max_length=1, choices=DAY_CHOICES)
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    date = models.DateField(null=True,blank=True)
    time_zone = models.CharField(max_length=4,null=True, choices=TIME_ZONE_CHOICES,default='CST')
    
    # Foreign Keys to link availability with category, subcategory, task, and links
    # Using string references for compatibility with lightweight branches where professional_services may be removed
    category = models.ForeignKey(
        'professional_services.FeaturedCategory', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="Categories"
    )
    subcategory = models.ForeignKey(
        'professional_services.FeaturedSubCategory', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="subcategory"
    )
    task = models.ForeignKey(
        'professional_services.FeaturedActivity', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="task"
    )
    activity_links = models.ForeignKey(
        'professional_services.ActivityLinks', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="activity_links"
    )

    def __str__(self):
        return "{} - {} {} to {}".format(self.client.username, self.get_day_display(), self.start_time, self.end_time)

    def clean(self):
        """Validate ClientAvailability model data"""
        from django.core.exceptions import ValidationError
        
        # Validate end time vs start time
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                raise ValidationError("End time must be after start time")
        
        # Validate date if provided
        if self.date and self.date < timezone.now().date():
            raise ValidationError("Date cannot be in the past")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

class Search(models.Model):
    CAT_CHOICES = [
        ("accounts", "Registration"),
        ("application", "Application"),
        ("finance", "Financial Information"),
        ("management", "Employees Activities"),
        ("data", "Data Analysis"),
        ("getdata", "Automation"),
        ("investing", "Investments"),
        ("main", "General Information"),
        ("projectmanagement", "Field Projects"),
    ]

    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="Other",
    )

    # subcategories = models.ForeignKey(
    #     ServiceCategory,
    #     on_delete=models.CASCADE,
	# 	default=1
    # )
    searched_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=Q(is_staff=True)
        | Q(category__in=[1, 3, 4, 5, 6, 7])  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        | Q(is_admin=True)
        | Q(is_superuser=True),
    )
    # subcategory = models.CharField(max_length=255, default="training")
    topic = models.CharField(max_length=255, default="Task")
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Search"

    def get_absolute_url(self):
        return reverse("main:layout")

    def __str__(self):
        return self.question

class SearchHistory(models.Model):
    searched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="search_history"
    )
    question=models.TextField()
    topic=models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    search_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["-search_at"]
        verbose_name_plural="Search Histories"

    def __str__(self):
        return f"{self.searched_by.username} - {self.question[:50]}"



class WCAGStandardWebsite(models.Model):
    CAT_CHOICES = [
            ("accounts", "accounts"),
            ("application", "application"),
            ("finance", "finance"),
            ("management", "management"),
            ("data", "data"),
            ("getdata", "getdata"),
            ("investing", "investing"),
            ("main", "main"),
            ("projectmanagement", "projectmanagement"),
    ]
    company  = models.CharField(max_length=500,blank=True,null=True)#coda,safaricom,Google,
    app_name = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="main",
    )
    page_name    = models.CharField(max_length=500,blank=True,null=True)
    website_url  = models.CharField(max_length=500,blank=True,null=True)
    improvements = models.TextField(blank=True,null=True) 
    # page_file   = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.app_name

class WCAGStandard(TimeStampedModel):
    # my_wcag_website = models.ForeignKey(WCAGStandardWebsite, on_delete=models.CASCADE, null=True)
    criteria = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    what_to_test = models.CharField(max_length=255)
    how_to_test = models.TextField()
    user_affected = models.TextField()

    def __str__(self):
        return self.criteria
    
# ==============================PRESAVE SLUG GENERATORS====================================
def testimonials_pre_save_receiver(sender,instance,*args,**kwargs):
    if not instance.slug:
        instance.slug=unique_slug_generator


def servicecategory_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        if instance.name:
            instance.slug = unique_slug_generator(instance)

pre_save.connect(servicecategory_pre_save_receiver, sender=ServiceCategory)

pre_save.connect(testimonials_pre_save_receiver,sender=Testimonials)

pre_save.connect(slug_pre_save_receiver,sender=Service)

pre_save.connect(slug_pre_save_receiver,sender=Company)

