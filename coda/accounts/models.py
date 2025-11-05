from datetime import timedelta
from decimal import *
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import pre_save
from django.utils.translation import gettext_lazy as _
from accounts.modelmanager import DepartmentManager
from management.utils import unique_slug_generator
from django_countries.fields import CountryField

# from accounts.choices import UserCategory as CategoryChoices, ApplicantSubCategoryChoices as SubCategoryChoices
from accounts.choices import UserCategory as CategoryChoices
from .user_utils import (
    get_user_employment_status,
    get_user_client_status,
    get_user_applicant_status,
    get_user_lifecycle_stage,
    get_user_engagement_score,
    get_user_permissions,
    get_user_display_info,
    validate_user_category_combination,
)


# Create your models here.
class UserGroups(Group):
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    users = models.ManyToManyField("CustomerUser", related_name="user_groups")

    class Meta:
        verbose_name_plural = "User Groups"


class CustomerUser(AbstractUser):
    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, "Unknown")

    # added this column here
    def get_subcategory_display_name(self):
        from .choices import get_subcategory_display_name

        return get_subcategory_display_name(self.category, self.sub_category)

    class Score(models.IntegerChoices):
        Male = 1
        Female = 2

    # user_permissions field is inherited from AbstractUser
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=255)
    gender = models.IntegerField(choices=Score.choices, blank=True, null=True)
    phone = models.CharField(default="90001", max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    zipcode = models.CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)
    category = models.IntegerField(choices=CategoryChoices.choices, default=999)
    # added this column here
    sub_category = models.IntegerField(blank=True, null=True)
    is_admin = models.BooleanField("Is admin", default=False)
    # REMOVED: is_staff = models.BooleanField("Is employee", default=False)  # Django already provides this
    # REMOVED: is_client = models.BooleanField("Is Client", default=False)  # Can compute from category
    # REMOVED: is_applicant = models.BooleanField("Is applicant", default=False)  # Can compute from category
    # REMOVED: is_employee_contract_signed = models.BooleanField(default=False)  # Can compute from category + subcategory
    resume_file = models.FileField(upload_to="resumes/doc/", blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(unique=True, null=True, blank=True)

    # is_active = models.BooleanField('Is applicant', default=True)
    class Meta:
        # ordering = ["-date_joined"]
        ordering = ["username"]
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["date_joined"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["category", "sub_category"]),
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            # Composite indexes for common query patterns
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["is_active", "is_staff"]),
            models.Index(fields=["date_joined", "is_active"]),
            models.Index(fields=["email", "is_active"]),
        ]

    @property
    def full_name(self):
        fullname = "{} {}".format(self.first_name, self.last_name)
        return fullname
    
    @property
    def user_details(self):
        user_details = (
            "Username: {}\n"
            "Phone Number: {}\n"
            "Email: {}\n"
            "City: {}\n"
            # "Country: {}".format(self.country.name if self.country else 'N/A')
        ).format(self.username, self.phone, self.email, self.city)
        return user_details
    
    @property
    def is_recent(self):
        return self.date_joined >= timezone.now() - timedelta(days=365)
    
    @property
    def tenure(self):
        number_days = (timezone.now().date() - self.date_joined.date()).days
        months = number_days / 30
        return months
    
    # NEW COMPUTED PROPERTIES (replacing redundant boolean fields)
    @property
    def employment_status(self):
        """Computed employment status - replaces is_employee_contract_signed"""
        return get_user_employment_status(self)

    @property
    def client_status(self):
        """Computed client status - replaces is_client"""
        return get_user_client_status(self)

    @property
    def applicant_status(self):
        """Computed applicant status - replaces is_applicant"""
        return get_user_applicant_status(self)

    @property
    def lifecycle_stage(self):
        """Computed lifecycle stage - no stored field needed"""
        return get_user_lifecycle_stage(self)

    @property
    def engagement_score(self):
        """Computed engagement score - no stored field needed"""
        return get_user_engagement_score(self)

    @property
    def computed_permissions(self):
        """Computed permissions - no stored fields needed"""
        return get_user_permissions(self)

    @property
    def display_info(self):
        """Comprehensive user display information - no stored fields needed"""
        return get_user_display_info(self)

    def get_login_days(self):
        login_history = LoginHistory.objects.filter(user=self).order_by("login_time")
        return [entry.login_time for entry in login_history]

    def get_login_count(self):
        return LoginHistory.objects.filter(user=self).count()

    def has_logged_in_last_days(self, days):
        recent_date = timezone.now().date() - timedelta(days=days)
        return LoginHistory.objects.filter(
            user=self, login_time__gte=recent_date
        ).exists()

    def clean(self):
        """Validate category and subcategory combinations"""
        from django.core.exceptions import ValidationError

        if self.category and self.sub_category:
            is_valid, error_message = validate_user_category_combination(
                self.category, self.sub_category
            )
            if not is_valid:
                raise ValidationError(error_message)

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Clean, focused user profile model - NO business logic"""
    
    # Education choices
    class Education(models.IntegerChoices):
        High_School = 1, "High School"
        Some_College = 2, "Some College"
        Bachelor = 3, "Bachelor's Degree"
        Masters = 4, "Master's Degree"
        Doctorate = 5, "Doctorate"
    
    # Performance tier choices (for ALL users, not just KCC)
    class PerformanceTier(models.TextChoices):
        NEW = 'new', 'New'
        BRONZE = 'bronze', 'Bronze'
        SILVER = 'silver', 'Silver'
        GOLD = 'gold', 'Gold'
        PLATINUM = 'platinum', 'Platinum'
    
    # Staff level choices
    class StaffLevel(models.TextChoices):
        JUNIOR = 'junior', 'Junior'
        SENIOR = 'senior', 'Senior'
        MANAGER = 'manager', 'Manager'
        EXECUTIVE = 'executive', 'Executive'
    
    # ==================== CORE PROFILE FIELDS ====================
    user = models.OneToOneField(
        "accounts.CustomerUser", 
        related_name="profile", 
        on_delete=models.CASCADE
    )
    
    # Professional information
    position = models.CharField(max_length=255, blank=True, null=True, help_text="Job title or position")
    company = models.CharField(max_length=254, null=True, blank=True, help_text="Current employer or company")
    description = models.TextField(blank=True, null=True, help_text="Professional summary or bio")
    linkedin = models.URLField(max_length=500, null=True, blank=True, help_text="LinkedIn profile URL")
    
    # Education and skills
    education = models.IntegerField(choices=Education.choices, default=3, help_text="Highest education level")
    skills = models.JSONField(default=list, blank=True, help_text="List of skills and competencies")
    
    # Profile images
    image = models.ImageField(
        default="default.jpg", 
        upload_to="Application_Profile_pics", 
        blank=True,
        help_text="Profile picture"
    )
    image2 = models.ForeignKey(
        "main.Assets", 
        related_name="profile_image", 
        on_delete=models.CASCADE,
        default=1,
        help_text="Secondary profile image"
    )
    
    # Document uploads
    upload_a = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True, help_text="Document A")
    upload_b = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True, help_text="Document B")
    upload_c = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True, help_text="Document C")
    
    # ==================== IDENTIFICATION FIELDS ====================
    national_id_no = models.CharField(max_length=254, null=True, blank=True, help_text="National ID number")
    id_file = models.ImageField(upload_to='id_files/', null=True, blank=True, help_text="ID document")
    
    # ==================== EMERGENCY CONTACT FIELDS ====================
    emergency_name = models.CharField(max_length=254, null=True, blank=True, help_text="Emergency contact name")
    emergency_address = models.CharField(max_length=254, null=True, blank=True, help_text="Emergency contact address")
    emergency_citizenship = models.CharField(max_length=254, null=True, blank=True, help_text="Emergency contact citizenship")
    emergency_national_id_no = models.CharField(max_length=254, null=True, blank=True, help_text="Emergency contact ID")
    emergency_phone = models.CharField(max_length=254, null=True, blank=True, help_text="Emergency contact phone")
    emergency_email = models.EmailField(max_length=254, null=True, blank=True, help_text="Emergency contact email")

    account_number = models.CharField(max_length=254, null=True, blank=True, help_text="Account number")
    country = models.CharField(max_length=2, null=True, blank=True, help_text="User's country code")
    # ==================== KCC MEMBERSHIP FIELDS ====================
    is_karen_country_club_member = models.BooleanField(
        default=False, 
        help_text="Whether user is a Karen Country Club member"
    )
    kcc_membership_number = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Karen Country Club membership number"
    )
    kcc_membership_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when user became a KCC member"
    )
    kcc_membership_expiry = models.DateField(
        null=True, 
        blank=True,
        help_text="Karen Country Club membership expiry date"
    )
    
    # ==================== UNIFIED PERFORMANCE TRACKING ====================
    # Performance tier (for ALL users, not just KCC)
    performance_tier = models.CharField(
        max_length=20,
        choices=PerformanceTier.choices,
        default=PerformanceTier.NEW,
        help_text="Performance tier (affects loan terms for all users)"
    )
    
    # Staff-specific fields
    staff_level = models.CharField(
        max_length=20,
        choices=StaffLevel.choices, 
        null=True,
        blank=True,
        help_text="Staff level (affects loan terms)"
    )
    
    # ==================== LOAN ELIGIBILITY FIELDS ====================
    monthly_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly income for loan eligibility"
    )
    
    employment_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Employment start date for loan eligibility"
    )
    
    credit_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Credit score (300-850)"
    )
    
    # ==================== USER PREFERENCES ====================
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp')
        ],
        default='email',
        help_text="Preferred method of contact"
    )
    
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Notification preferences (email, SMS, etc.)"
    )
    
    # ==================== SYSTEM FIELDS ====================
    section = models.CharField(max_length=2, default="A", blank=True, help_text="User section")
    laptop_status = models.BooleanField("Has laptop", default=True, help_text="Whether user has a laptop")
    is_active = models.BooleanField("Is active", default=True, help_text="Whether profile is active")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ==================== META CONFIGURATION ====================
    class Meta:
        db_table = 'accounts_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['performance_tier']),
            models.Index(fields=['is_karen_country_club_member']),
            models.Index(fields=['staff_level']),
            models.Index(fields=['monthly_income']),
            models.Index(fields=['created_at']),
            # Composite indexes
            models.Index(fields=['performance_tier', 'is_karen_country_club_member']),
            models.Index(fields=['staff_level', 'performance_tier']),
        ]
    
    def __str__(self):
        return "{} Profile".format(self.user.username)
    
    # ==================== SIMPLE COMPUTED PROPERTIES ====================
    # Only simple calculations that don't hit the database
    @property
    def full_name(self):
        """Simple computed property - no database queries"""
        return "{} {}".format(self.user.first_name, self.user.last_name)
    
    @property
    def employment_months(self):
        """Simple calculation that doesn't hit database"""
        if not self.employment_start_date:
            return 0
        delta = timezone.now().date() - self.employment_start_date
        return delta.days // 30
    
    @property
    def img_url(self):
        """Get profile image URL"""
        if self.image2:
            return self.image2.image_url
        return "default_image_url.jpg"
    
    @property
    def img_category(self):
        """Get profile image category"""
        if self.image2:
            return self.image2.category
        return None
    
    # ==================== VALIDATION METHODS ====================
    def clean(self):
        """Validate UserProfile model data"""
        from django.core.exceptions import ValidationError
        
        # Validate emergency contact information
        if self.emergency_name and not self.emergency_phone and not self.emergency_email:
            raise ValidationError("Emergency contact must have either phone or email")
        
        # Validate KCC membership
        if self.is_karen_country_club_member:
            if not self.kcc_membership_number:
                raise ValidationError("KCC membership number is required for members")
            if not self.kcc_membership_expiry:
                raise ValidationError("KCC membership expiry date is required for members")
        
        # Validate KCC expiry date
        if self.kcc_membership_expiry and self.kcc_membership_expiry < timezone.now().date():
            raise ValidationError("KCC membership expiry date cannot be in the past")
        
        # Validate credit score range
        if self.credit_score is not None:
            if not (300 <= self.credit_score <= 850):
                raise ValidationError("Credit score must be between 300 and 850")
        
        # Validate monthly income
        if self.monthly_income is not None and self.monthly_income < 0:
            raise ValidationError("Monthly income cannot be negative")
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation and auto-updates"""
        # Auto-set KCC membership date if becoming a member
        if self.is_karen_country_club_member and not self.kcc_membership_date:
            self.kcc_membership_date = timezone.now().date()
        
        self.clean()
        super().save(*args, **kwargs)
 

class LoginHistory(models.Model):
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    # You can add more fields as needed

    def __str__(self):
        return "{} - {} to {}".format(self.user.username, self.login_time, self.logout_time)

    @property
    def login_duration(self):
        number_hours = (self.logout_time - self.login_time).hours
        return number_hours
    
    
class Department(models.Model):
    """Department Table will provide a list of the different departments in CODA"""

    # Department
    # BASIC = "Basic"
    HR = "HR Department"
    IT = "IT Department"
    MKT = "Marketing Department"
    FIN = "Finance Department"
    SECURITY = "Security Department"
    MANAGEMENT = "Management Department"
    # Project = "Project"
    HEALTH = "Health Department"
    Other = "Other"
    DEPARTMENT_CHOICES = [
        # (BASIC, "BASIC Department"),
        (HR, "HR Department"),
        (IT, "IT Department"),
        (MKT, "Marketing Department"),
        (FIN, "Finance Department"),
        # (Project, "Project"),
        (SECURITY, "Security Department"),
        (MANAGEMENT, "Management Department"),
        (HEALTH, "Health Department"),
        (Other, "Other"),
    ]

    name = models.CharField(
        max_length=100,
        choices=DEPARTMENT_CHOICES,
        default=Other,
    )

    description = models.TextField(max_length=500, null=True, blank=True)
    slug = models.SlugField(
        verbose_name=_("Department safe URL"), max_length=255, unique=True
    )
    # created_date = models.DateTimeField(_('entered on'),default=timezone.now, editable=True)
    is_featured = models.BooleanField("Is featured", default=True)
    is_active = models.BooleanField(default=True)

    objects = DepartmentManager()

    @classmethod
    def get_default_pk(cls):
        cat, created = cls.objects.get_or_create(
            name="Other", defaults=dict(description="this is not an cat")
        )
        return cat.pk

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def get_absolute_url(self):
        if self.slug:
            return reverse("main:department_reports", args=[self.slug])
        return "#"

    def __str__(self):
        return self.name
 
 
# =========================CREDENTIALS TABLE======================================
class CredentialCategory(models.Model):
    department = models.ForeignKey(
        to=Department, on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    # created_by= models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(
        verbose_name=_("Category Name"),
        help_text=_("Required"),
        max_length=255,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name=_("category safe URL"), max_length=255, unique=True
    )
    description = models.TextField(max_length=1000, default=None)
    entry_date = models.DateTimeField(_("entered on"), auto_now_add=True, editable=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Set default department if none provided"""
        if not self.department:
            try:
                self.department = Department.objects.get(name="Other")
            except Department.DoesNotExist:
                # Create default department if it doesn't exist
                self.department = Department.objects.create(
                    name="Other", description="this is not an cat"
                )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("management:credentialcategorylist", args=[self.slug])

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        # return f"{self.category} Categories"
        return "{}".format(self.category)


class Credential(models.Model):
    USER_CHOICES = [
        ("Superuser", "Superuser"),
        ("Admin", "Admin"),
        ("Employee", "Employee"),
        ("Other", "Other"),
    ]
    category = models.ManyToManyField(
        CredentialCategory, blank=True, related_name="credentialcategory"
    )
    added_by = models.ForeignKey(CustomerUser, on_delete=models.RESTRICT)
    name = models.CharField(
        verbose_name=_("credential Name"),
        help_text=_("Required"),
        max_length=255,
    )
    slug = models.SlugField(
        verbose_name=_("credential safe URL"), max_length=255, unique=True
    )
    description = models.TextField(max_length=1000, default=None)
    link_name = models.CharField(max_length=255, default="General")
    link = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(
        max_length=255, blank=True, null=True, default="No Password Needed"
    )
    entry_date = models.DateTimeField(_("entered on"), auto_now_add=True, editable=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    user_types = models.CharField(
        max_length=25,
        choices=USER_CHOICES,
        default="Other",
    )

    class Meta:
        verbose_name_plural = "credentials"

    def clean(self):
        """Validate Credential model data"""
        from django.core.exceptions import ValidationError

        # Validate password length if provided
        if self.password and self.password != "No Password Needed":
            if len(self.password) < 8:
                raise ValidationError("Password must be at least 8 characters long")

        # Validate link format if provided
        if self.link and not self.link.startswith(("http://", "https://")):
            raise ValidationError("Link must start with http:// or https://")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("management:credential")

    def __str__(self):
        return self.name

# ========================================SLUGS GENERATOR====================================================
def credentialcategory_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(credentialcategory_pre_save_receiver, sender=CredentialCategory)


class TaskGroups(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=55, unique=True, default="Group A")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # @classmethod
    # def get_default_pk(cls):
    #     cat, created = cls.objects.get_or_create(
    #         title="Group A"
    #     )
    #     return cat.pk

    def __str__(self):
        return self.title


# ========================================TIME TRACKER====================================================
# Time Tracking Model
class Tracker(models.Model):
    class Duration(models.IntegerChoices):
        One_Hour = 1
        Two_Hours = 2
        Three_Hours = 3
        Four_Hours = 4
        Five_Hours = 5
        Eight_Hours = 8
        Ten_Hours = 10


    # Job Category.
    CAT_CHOICES = [
        ("Job_Support", "Job_Support"),
        ("Interview", "Interview"),
        ("Training", "Training"),
        ("Mentorship", "Mentorship"),
        ("Other", "Other"),
    ]
    # Sub Category.
    SUBCAT_CHOICES = [
        ("Requirements", "Requirements"),
        ("Troubleshooting", "Troubleshooting"),
        ("Development", "Development"),
        ("Testing", "Testing"),
        ("Other", "Other"),
    ]
    # Task/Activities
    TASK_CHOICES = [
        ("reporting", "reporting"),
        ("database", "database"),
        ("Business Analysis", "Business Analysis"),
        ("Data Cleaning", "Data Cleaning"),
        ("Other", "Other"), 
    ]
    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
    )
    sub_category = models.CharField(
        max_length=25, choices=SUBCAT_CHOICES, default="Other"
    )
    task = models.CharField(
        max_length=25,
        choices=TASK_CHOICES,
    )
    plan = models.CharField(
        verbose_name=_("group"), help_text=_("Required"), max_length=255, default="B"
    )
    empname = models.ForeignKey(
        "accounts.CustomerUser",
        verbose_name=_("Employee"),
        related_name="Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        #  limit_choices_to=Q(is_staff=True)|Q(is_admin=True) | Q(is_superuser=True) and Q(is_active=True),
        limit_choices_to={"is_staff": True, "is_active": True},
    )

    author = models.ForeignKey(
        "accounts.CustomerUser",
        verbose_name=_("Client"),
        related_name="Client",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={
            "category__in": [1, 3, 4, 5, 6, 7],
            "is_active": True,
        },  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
    )
    employee = models.CharField(
        verbose_name="Company/End Client",
        help_text=_("Required"),
        max_length=255,
        default="CODA",
    )
    # clientname = models.ForeignKey('accounts.CustomerUser', on_delete=models.CASCADE, related_name="clientname",limit_choices_to={'is_client': True})
    # login_date = models.DateTimeField(auto_now_add=True)
    login_date = models.DateTimeField(default=timezone.now, editable=True)
    start_time = models.TimeField(auto_now_add=True)
    duration = models.IntegerField(choices=Duration.choices, default=2)
    time = models.PositiveIntegerField(
        # max_digits=3,
        help_text=_("Maximum 200"),
        error_messages={
            "name": {" max_length": ("The maximum hours must be between 0 and 199")}
        },
        default=120,
    )

    class Meta:
        ordering = ["login_date"]
        indexes = [
            models.Index(fields=["login_date"]),
            models.Index(fields=["category", "sub_category"]),
            models.Index(fields=["empname"]),
            models.Index(fields=["author"]),
            # Composite indexes for common query patterns
            models.Index(fields=["login_date", "category"]),
            models.Index(fields=["empname", "login_date"]),
            models.Index(fields=["author", "login_date"]),
            models.Index(fields=["category", "empname"]),
        ]

    def get_absolute_url(self):
        return reverse("usertime", args=[self.username])

    def clean(self):
        """Validate Tracker model data"""
        from django.core.exceptions import ValidationError

        # Validate time field (maximum 200 hours = 12000 minutes)
        if self.time and self.time > 12000:
            raise ValidationError("Time cannot exceed 200 hours (12000 minutes)")

        # Validate duration vs time consistency
        if self.duration and self.time:
            duration_minutes = self.duration * 60
            if self.time < duration_minutes:
                raise ValidationError("Time cannot be less than duration")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def end(self):
        # Calculate end time based on login date and duration
        end_time = self.login_date + timedelta(hours=self.duration)
        return end_time.strftime("%H:%M")

    @property
    def total_payment(self):
        # Calculate total payment based on duration and time
        # Assuming time is in minutes and duration is in hours
        total_minutes = self.time
        total_hours = total_minutes / 60.0
        return total_hours


class Team_Members(models.Model):
    CAT_CHOICES = [
        ("board", "Board Members"),
        ("analytics_team", "Analytics Team"),
        ("future_talent", "Future Talent"),
        ("support_team", "Support Team"),
        ("clients", "Clients"),
        ("other", "other"),
    ]

    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="Other",
    )

    title = models.CharField(max_length=255, default="Project Manager")
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Team Classification"
        indexes = [
            models.Index(fields=["category"]),
        ]

    def get_absolute_url(self):
        return reverse("main:layout")

    def __str__(self):
        return self.title


class TeamProfile(models.Model):
    """
    Team-specific metadata using Django Groups for categorization.
    
    Design: SMALL model (5 data fields). Category stored in Django Groups.
    UserProfile NOT modified - keeps it at 38 fields.
    
    Usage:
        - Manual roles (BOG, Elite, Lead, etc.) assigned via admin
        - Trainees auto-categorized by points
        - Promotion tracking built-in
    """
    
    # Core relationship
    user = models.OneToOneField(
        'accounts.CustomerUser',  # Use string reference to avoid circular import
        on_delete=models.CASCADE,
        related_name='team_profile',
        help_text='User this team profile belongs to'
    )
    
    # Display priority (for ordering within category)
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Display priority (higher number = shown first within category)'
    )
    
    # Cached points (calculated daily for performance)
    total_points = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Cached total points (recalculated daily by management command)'
    )
    
    # Assignment method tracking
    is_manually_assigned = models.BooleanField(
        default=False,
        db_index=True,
        help_text='True = manual assignment (admin), False = points-based (auto)'
    )
    
    # Promotion tracking
    last_promoted = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When last promoted to manual category'
    )
    
    promotion_notes = models.TextField(
        blank=True,
        help_text='Promotion notes (who promoted, why, approval notes)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_teamprofile'
        verbose_name = 'Team Profile'
        verbose_name_plural = 'Team Profiles'
        indexes = [
            models.Index(fields=['priority', '-total_points']),
            models.Index(fields=['is_manually_assigned']),
        ]
    
    def __str__(self):
        category = self.category or 'Uncategorized'
        return f"{self.user.username} - {category}"
    
    @property
    def category(self):
        """
        Get team category from user's groups.
        
        Returns:
            String category name or None if not assigned
        """
        TEAM_GROUPS = [
            'BOG/Leadership',
            'Elite Team',
            'Lead Team',
            'Support Team',
            'Senior Analysts',
            'Junior Analysts',
            'Senior Trainee',
            'Junior Trainee',
            'Elementary',
        ]
        
        for group_name in TEAM_GROUPS:
            if self.user.groups.filter(name=group_name).exists():
                return group_name
        
        return None
    
    @property
    def category_slug(self):
        """Get category slug for URL/template use"""
        if not self.category:
            return 'uncategorized'
        
        return self.category.lower().replace('/', '_').replace(' ', '_')
    
    @property
    def is_promotion_ready(self):
        """Check if trainee is ready for manual promotion (6,000+ points)"""
        return (
            not self.is_manually_assigned and
            self.total_points >= 6000
        )