import calendar,string
import itertools
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from decimal import *
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from coda_project import settings
from management.utils import unique_slug_generator,split_num_str
from django.contrib.auth import get_user_model
from shared_core.users import CustomerUser, Department
from accounts.models import TaskGroups
from professional_services.models import  FeaturedCategory,FeaturedSubCategory,FeaturedActivity
from shared_core.models import TimeStampedModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# User=settings.AUTH_USER_MODEL
User = get_user_model()

# --------------------------------------
class Training(models.Model):
    class Level(models.IntegerChoices):
        Level_1 = 1
        Level_2 = 2
        Level_3 = 3
        Level_4 = 4
        Level_5 = 5

    presenter = models.ForeignKey(
        User,
        verbose_name=("presenter name"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(is_staff=True)|Q(category__in=[1, 3, 4, 5, 6, 7])|Q(is_admin=True) | Q(is_superuser=True) and Q(is_active=True),  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        related_name="employee_name")
    
    department = models.ForeignKey(
        Department,
        verbose_name=("departments"),
        on_delete=models.CASCADE,
        related_name="department_name")
    

    category = models.ForeignKey(
        FeaturedCategory,
        verbose_name=("categories"),
        on_delete=models.CASCADE,
        
        limit_choices_to=Q(title='Development')|Q(title='Testing')|Q(title='Course Overview')|Q(title='Other'),
        related_name="category_name")
    
    subcategory = models.ForeignKey(
        FeaturedSubCategory,
        verbose_name=("Subcategory"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(title='Database Management')|Q(title='Reporting')|Q(title='website')|Q(title='Data Preparation')|Q(title='Business Analysis'),
        related_name="subcategory_name")
    
    
    topic = models.ForeignKey(
        FeaturedActivity,
        verbose_name=("topic"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(activity_name='Data(Database)')|Q(activity_name='Introduction to snowflakes')|Q(activity_name='Data Preparation(ETL)')|Q(activity_name='Requirements')|Q(activity_name='Tableau')|Q(activity_name='Python')|Q(activity_name='BA Interview'),
        related_name="title")
    
    level = models.IntegerField(choices=Level.choices)
    session=models.PositiveIntegerField()
    session_link = models.CharField(max_length=500, blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    expiration_date = models.DateTimeField(blank=True,null=True)
    description = models.TextField(default='No Comment',null=True, blank=True)
    is_active = models.BooleanField(default=True)
    featured= models.BooleanField(default=True)
    is_mock= models.BooleanField(default=False)

    def __str__(self):
        return f"Training {self.id} - {self.topic.activity_name if self.topic else 'No Topic'} - Level {self.level}"
    
    @property
    def calculated_expiry_date(self):
        """Calculate expiry date based on created date + 365 days"""
        if self.created_date:
            return self.created_date + timedelta(days=365)
        return timezone.now() + timedelta(days=365)

    def clean(self):
        """Validate Training model data"""
        from django.core.exceptions import ValidationError
        
        # Validate session number
        if self.session and self.session <= 0:
            raise ValidationError("Session number must be positive")
        
        # Validate expiration date if provided
        if self.expiration_date and self.created_date:
            if self.expiration_date <= self.created_date:
                raise ValidationError("Expiration date must be after created date")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)
    
# -------------------------------------COMPANY POLICIES---------------------------------------
class Policy(models.Model):
    # Department
    HR = "HR"
    IT = "IT"
    MKT = "Marketing"
    FIN = "Finance"
    SECURITY = "Security"
    MANAGEMENT = "Management"
    HEALTH = "Health"
    Other = "Other"
    DEPARTMENT_CHOICES = [
        (HR, "HR"),
        (IT, "IT"),
        (MKT, "Marketing"),
        (FIN, "Finance"),
        (SECURITY, "Security"),
        (MANAGEMENT, "Management"),
        (HEALTH, "Health"),
        (Other, "Other"),
    ]

    Leave = "Leave"
    Working_Hours = "Working Hours"
    Working_Days = "Working Days"
    Unpaid_Training = "Unpaid Training"
    Location = "Location"
    Other = "Other"
    CHOICES = [
        (Leave, "Leave"),
        (Working_Hours, "Working Hours"),
        (Working_Days, "Working Days"),
        (Unpaid_Training, "Unpaid_Training"),
        (Location, "Location"),
        (Other, "Other"),
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
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="staff_entry",
        limit_choices_to=Q(is_staff=True) & Q(is_active=True),
        # limit_choices_to=Q(is_staff=True)|Q(is_admin=True) | Q(is_superuser=True),
        default=1,
    )
    staff = models.CharField(max_length=100, null=True, blank=True, default="admin")
    upload_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    link = models.CharField(max_length=1000, blank=True, null=True)
    department = models.CharField(
        max_length=100,
        choices=DEPARTMENT_CHOICES,
        default=Other,
    )
    day = models.CharField(max_length=25, choices=DAY_CHOICES, default="Sunday")
    description = models.TextField()
    policy_doc = models.FileField(
        upload_to="policy/doc/", default=None, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Policies"

    def __str__(self):
        return f"{self.id} policy"

class BaseContract(models.Model):
    CONTRACT_TYPES = [
        ('Student', 'Student Contract'),
        ('JobSupport', 'Job Support Contract'),
        ('Loan', 'Loan Contract'),
        ('Investment', 'Investment Contract'),
        ('General', 'General Contract'),
    ]
    # id = models.AutoField(primary_key=True)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)
    client = models.ForeignKey(
        User,
        verbose_name=("client"),
        on_delete=models.CASCADE,
        default=1,
        limit_choices_to=Q(is_staff=True)|Q(category__in=[1, 3, 4, 5, 6, 7])|Q(is_admin=True) | Q(is_superuser=True) and Q(is_active=True),  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        related_name="client_name")
    contract_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    terms_and_conditions = models.TextField(blank=True)
    additional_info = models.JSONField(default=dict, blank=True)  # For flexibility
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    related_object = GenericForeignKey('related_content_type', 'related_object_id')

    class Meta:
        verbose_name_plural = "Contracts"
        ordering = ['-contract_date']

    def __str__(self):
        return f"{self.contract_type} - {self.client.username}"


# class InvestmentContract(models.Model):
#     base_contract = models.OneToOneField(BaseContract, on_delete=models.CASCADE)
#     amount_invested = models.DecimalField(max_digits=10, decimal_places=2)
#     duration = models.PositiveIntegerField()
#     monthly_payments = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     revenue_share_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)



    
# ==================================ACTIVITIES====================================
class TaskCategory(models.Model):
    # Tasks Category.
    Meetings = "Pbr session"
    Data_Analyis = "Data Analysis"
    Stocks_Options = "Stocks & Options"
    Website = "Website Development"
    Department = "Department"
    Other = "Other"

    CAT_CHOICES = [
        ("PBR", "PBR"),
        (Data_Analyis, "Data Analysis"),
        (Stocks_Options, "Stocks & Options"),
        (Website, "Website Development"),
        (Department, "Department"),
        (Other, "Other"),
    ]
    title = models.CharField(
        max_length=55,
        choices=CAT_CHOICES,
        unique=True,
        default=Other,
    )

    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # active=models.IntegerField(default=1)

    class Meta:
        verbose_name_plural = "Task Categories"

    @classmethod
    def get_default_pk(cls):
        cat, created = cls.objects.get_or_create(
            title="Other", defaults=dict(description="this is not an cat")
        )
        return cat.pk


    def get_absolute_url(self):
        return reverse("category_list")

    def __str__(self):
        return self.title


class TaskQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.filter(featured=True, is_active=True)

    def search(self, query):
        lookups = (
            Q(group__icontains=query)
            | Q(description__icontains=query)
            | Q(description__icontains=query)
            | Q(activity_name__icontains=query)
            | Q(mxearning__icontains=query)
            | Q(submission__icontains=query)
            | Q(employee__email__icontains=query)
        )
        return self.filter(lookups).distinct()


class TaskManager(models.Manager):
    def get_queryset(self):
        # return super(TaskManager, self).get_queryset().filter(is_active=True)
        return TaskQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    """ def featured(self):
        return self.get_queryset().featured() """

    def get_by_pk(self, pk):
        qs = self.get_queryset().filter(pk=pk)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_employee(self, employee):
        qs = self.get_queryset().filter(employee=employee)
        if qs.count() == 1:
            return qs.first()
        return None

    """
    def get_by_slug(self,slug):
        qs=self.get_queryset().filter(slug=slug)
        if qs.count()==1:
            return qs.first()
        return None 
    """

    def search(self, query):
        return self.get_queryset().active().search(query)


class Task(models.Model):
    group = models.CharField(
        verbose_name=_("group"),
        help_text=_("Required"),
        max_length=255,
        default="Group A",
    )
    groupname = models.ForeignKey(
        to=TaskGroups, on_delete=models.CASCADE, default=1
    )
    category = models.ForeignKey(
        to=TaskCategory, on_delete=models.CASCADE, default=TaskCategory.get_default_pk
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="assigned_user",
        limit_choices_to=Q(is_staff=True) & Q(is_active=True),
        # limit_choices_to=Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True)
        # and Q(is_active=True),
        default=999,
    )
    activity_name = models.CharField(
        verbose_name=_("Activity Name"),
        help_text=_("Required"),
        max_length=255,
    )

    description = models.TextField(
        verbose_name=_("description"),
        help_text=_("Not Required"),
        default="Add description on this activity",
    )
    # task_date=models.DateField(auto_now_add=Tru, default=)
    slug = models.SlugField(max_length=255, blank=True, default="slug")
    duration = models.PositiveIntegerField(
        # max_digits=3,
        help_text=_("Should be less than Maximum Points assigned"),
        error_messages={
            "name": {" max_length": ("Points must be less than Maximum Points")}
        },
        default=1,
    )
    point = models.DecimalField(
        max_digits=10,
        help_text=_("Should be less than Maximum Points assigned"),
        error_messages={
            "name": {" max_length": ("Points must be less than Maximum Points")}
        },
        decimal_places=2,
    )
    mxpoint = models.DecimalField(
        max_digits=10,
        help_text=_("Maximum 200"),
        error_messages={
            "name": {" max_length": ("The maximum points must be between 0 and 199")}
        },
        decimal_places=2,
    )

    mxearning = models.DecimalField(
        max_digits=10,
        help_text=_("Maximum 4999.99"),
        error_messages={
            "name": {" max_length": ("The earning must be between 0 and 4999.99")}
        },
        decimal_places=2,
    )
    submission = models.DateTimeField(
        help_text=_("Date formart :mm/dd/yyyy"), auto_now=True, editable=True, null=True
    )
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)

    objects = TaskManager()

    @classmethod
    def get_default_pk(cls):
        tak, created = cls.objects.get_or_create(
            title="Other", defaults=dict(description="this is not an task")
        )
        return tak.pk

    @property
    def submitted(self):
        submitted = datetime.date(self.submission)
        return submitted

    @property
    def deadline(self):
        today = datetime.today()
        deadline_date = datetime(
            today.year, today.month, calendar.monthrange(today.year, today.month)[-1]
        )
        deadline = datetime.date(deadline_date)
        return deadline

    @property
    def time_remaining(self):
        today = date.today()
        deadline_date = date(
            today.year, today.month, calendar.monthrange(today.year, today.month)[-1]
        )
        delta = deadline_date - today
        time_remaining = delta.days
        return time_remaining

    @property
    def late_penalty(self):
        if self.submitted > self.deadline:
            return 0.98
        else:
            return 1

    @property
    def task_url(self):
        one_list = ["one on one sessions","one on one","one on one session",]
        job_list =  ["job support","job_support"]
        onelist= [task.lower().translate({ord(c): None for c in string.whitespace}) for task in one_list] 
        joblist= [task.lower().translate({ord(c): None for c in string.whitespace}) for task in job_list] 
        activity=self.activity_name.lower().translate({ord(c): None for c in string.whitespace})
        for i,j in itertools.zip_longest(onelist,joblist):
            if(i==activity):
                return reverse("application:rate")
            elif(j==activity):
                return reverse("accounts:tracker-list")
            else:
                return reverse("management:new_evidence", args=[self.id])

    @property
    def get_pay(self):
        if self.point > self.mxpoint:
            return 0
        else:
            try:
                Earning = round(Decimal(self.point / self.mxpoint) * self.mxearning, 2)
            except Exception as ZeroDivisionError:
                Earning = 0
            compute_pay = Earning * Decimal(self.late_penalty)
            pay = round(compute_pay, 2)
            return pay

    def clean(self):
        """
        Validate Task model data.
        
        Validations:
        - point ≤ mxpoint
        - mxpoint > 0
        - mxearning ≥ 0
        - point ≥ 0
        """
        from django.core.exceptions import ValidationError
        
        # Validation 1: point ≤ mxpoint
        if self.point > self.mxpoint:
            raise ValidationError({
                'point': f'Point ({self.point}) cannot exceed maximum points ({self.mxpoint})'
            })
        
        # Validation 2: mxpoint > 0
        if self.mxpoint <= 0:
            raise ValidationError({
                'mxpoint': 'Maximum points must be greater than 0'
            })
        
        # Validation 3: point ≥ 0
        if self.point < 0:
            raise ValidationError({
                'point': 'Point cannot be negative'
            })
        
        # Validation 4: mxearning ≥ 0
        if self.mxearning < 0:
            raise ValidationError({
                'mxearning': 'Maximum earning cannot be negative'
            })
    
    def save(self, *args, **kwargs):
        """Override save to call clean() validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Tasks"
        ordering = ("-submission",)
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['is_active']),
            models.Index(fields=['featured']),
            models.Index(fields=['employee']),
            models.Index(fields=['category']),
            models.Index(fields=['groupname']),
            # Composite indexes for common query patterns
            models.Index(fields=['is_active', 'featured']),
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['submission', 'is_active']),
        ]

    def clean(self):
        """Validate Task model data"""
        from django.core.exceptions import ValidationError
        
        # Validate point vs mxpoint
        if self.point and self.mxpoint:
            if self.point > self.mxpoint:
                raise ValidationError("Point cannot exceed maximum point")
        
        # Validate duration
        if self.duration and self.duration <= 0:
            raise ValidationError("Duration must be positive")
        
        # Validate mxearning
        if self.mxearning and self.mxearning > 4999.99:
            raise ValidationError("Maximum earning cannot exceed 4999.99")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("management:activity-detail", args=[self.slug])

    def __str__(self):
        return self.activity_name

# Adding the evidence table/model
class TaskLinks(models.Model):
    # task = models.ManyToManyField(Task, blank=True,related_name='task_featured')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True),
    )
    link_name = models.CharField(max_length=255, default="General")
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    doc = models.FileField(default="None", upload_to="evidence/docs/")
    link = models.CharField(max_length=1000, blank=True, null=True)
    linkpassword = models.CharField(max_length=255, default="No Password Needed")
    drive_link = models.URLField(max_length=2000, blank=True, null=True)
    is_active = models.BooleanField("Is active", default=True)
    is_featured = models.BooleanField("Is featured", default=False)

    class Meta:
        verbose_name_plural = "Task Reference"

    def clean(self):
        """Validate TaskLinks model data"""
        from django.core.exceptions import ValidationError
        
        # Validate link format if provided
        if self.link and not self.link.startswith(('http://', 'https://')):
            raise ValidationError("Link must start with http:// or https://")
        
        # Validate password length if provided
        if self.linkpassword and self.linkpassword != "No Password Needed":
            if len(self.linkpassword) < 6:
                raise ValidationError("Password must be at least 6 characters long")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tasks")

    @property
    def video_linkname(self):
        if self.link_name.startswith("Req"):
            new_link = self.link_name
            number_str=int(split_num_str(new_link))
            return number_str

    @property
    def lowerlinkname(self):
        if self.link_name.startswith("Req"):
            new_link = self.link_name.lower().replace(" ", "")
            return new_link


class TaskHistory(models.Model):
    group = models.CharField(
        verbose_name=_("group"),
        help_text=_("Required"),
        max_length=255,
        default="Group A",
    )
    category = models.ForeignKey(
        to=TaskCategory, on_delete=models.CASCADE, default=TaskCategory.get_default_pk
    )
    # category = models.ManyToManyField(TaskCategory, blank=True)
    employee = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="history_user_assiged",
        default=999,
    )
    activity_name = models.CharField(
        verbose_name=_("Activity Name"),
        help_text=_("Required"),
        max_length=255,
    )
    description = models.TextField(
        verbose_name=_("description"),
        help_text=_("Not Required"),
        default="Add description on this activity",
    )
    # task_date=models.DateField(auto_now_add=Tru, default=)
    slug = models.SlugField(max_length=255, blank=True, default="slug")
    duration = models.PositiveIntegerField(
        # max_digits=3,
        help_text=_("Should be less than Maximum Points assigned"),
        error_messages={
            "name": {" max_length": ("Points must be less than Maximum Points")}
        },
        default=1,
    )
    point = models.DecimalField(
        max_digits=10,
        help_text=_("Should be less than Maximum Points assigned"),
        error_messages={
            "name": {" max_length": ("Points must be less than Maximum Points")}
        },
        decimal_places=2,
    )
    mxpoint = models.DecimalField(
        max_digits=10,
        help_text=_("Maximum 200"),
        error_messages={
            "name": {" max_length": ("The maximum points must be between 0 and 199")}
        },
        decimal_places=2,
    )
    mxearning = models.DecimalField(
        max_digits=10,
        help_text=_("Maximum 4999.99"),
        error_messages={
            "name": {" max_length": ("The earning must be between 0 and 4999.99")}
        },
        decimal_places=2,
    )
    submission = models.DateTimeField(
        help_text=_("Date formart :mm/dd/yyyy"), auto_now=True, editable=True, null=True
    )
    daf_date = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        help_text=_("Date formart :mm/dd/yyyy"), auto_now=True, editable=True, null=True
    )
    objects = TaskManager()
    
    def clean(self):
        """
        Validate TaskHistory model data.
        
        Validations:
        - point ≤ mxpoint
        - mxpoint > 0
        - daf_date is not in future
        - daf_date is not too old (>2 years)
        - daf_date is not missing
        """
        from django.core.exceptions import ValidationError
        from datetime import date
        
        # Validation 1: point ≤ mxpoint
        if self.point > self.mxpoint:
            raise ValidationError({
                'point': f'Point ({self.point}) cannot exceed maximum points ({self.mxpoint})'
            })
        
        # Validation 2: mxpoint > 0
        if self.mxpoint <= 0:
            raise ValidationError({
                'mxpoint': 'Maximum points must be greater than 0'
            })
        
        # Validation 3: point ≥ 0
        if self.point < 0:
            raise ValidationError({
                'point': 'Point cannot be negative'
            })
        
        # Validation 4: mxearning ≥ 0
        if self.mxearning < 0:
            raise ValidationError({
                'mxearning': 'Maximum earning cannot be negative'
            })
        
        # Validation 5: daf_date validation
        if not self.daf_date:
            raise ValidationError({
                'daf_date': 'daf_date is required for TaskHistory'
            })
        
        # Validation 6: daf_date is not in future
        if self.daf_date > date.today():
            raise ValidationError({
                'daf_date': f'daf_date ({self.daf_date}) cannot be in the future'
            })
        
        # Validation 7: daf_date is not too old (warning only, not error)
        two_years_ago = date.today().replace(year=date.today().year - 2)
        if self.daf_date < two_years_ago:
            # This is a warning, not an error - allow it but log it
            pass
    
    def save(self, *args, **kwargs):
        """Override save to call clean() validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "TaskHistory"
        ordering = ["-submission"]

    @property
    def submitted(self):
        submitted = datetime.date(self.submission)
        submitted_date=submitted-relativedelta(days=1)
        return submitted_date

    @property
    def deadline(self):
        today = datetime.today()
        deadline_date = datetime(
            today.year, today.month, calendar.monthrange(today.year, today.month)[-1]
        )
        deadline = datetime.date(deadline_date)
        end_date=deadline-relativedelta(months=1)
        return end_date

    @property
    def time_remaining(self):
        today = date.today()
        deadline_date = date(
            today.year, today.month, calendar.monthrange(today.year, today.month)[-1]
        )
        delta = deadline_date - today
        time_remaining = delta.days
        return time_remaining

    @property
    def late_penalty(self):
        if self.submitted > self.deadline:
            return 0.98
        else:
            return 1

    @property
    def get_pay(self):
        if self.point > self.mxpoint:
            return 0
        else:
            try:
                Earning = round(Decimal(self.point / self.mxpoint) * self.mxearning, 2)
            except Exception as ZeroDivisionError:
                Earning = 0.0
            compute_pay = Decimal(Earning) * Decimal(self.late_penalty)
            pay = round(compute_pay, 2)
            return pay

class Requirement(models.Model):
    # Apps
    Reporting = "Reporting"
    Website = "Website"
    ETL = "ETL"
    Database = "Database"
    Other = "Other"
    # Beneficiary
    Management = "Management"
    Client = "Client"
    Other = "Other"

    # Priority Status
    Critical= "Critical"
    High= "High"
    Medium= "Medium"
    Low= "Low"

    CAT_CHOICES = [
        (Reporting, "Reporting"),
        (ETL, "ETL"),
        (Database, "Database"),
        (Website, "Website"),
        (Other, "Other"),
    ]
    BEN_CHOICES = [
        (Management, "Management"),
        (Client, "Client"),
        (Other, "Other"),
    ]
    STATUS_CHOICES = [
        (Critical, "Critical"),
        (High, "High"),
        (Medium, "Medium"),
        (Low, "Low"),
    ]
    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default=Other,
    )
    requestor = models.CharField(
        max_length=25,
        choices=BEN_CHOICES,
        default=Other,
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default=Low,
    )
    creator = models.ForeignKey(
        User,
        verbose_name=_("creator"),
        related_name="creator",
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True) |Q(category__in=[1, 3, 4, 5, 6, 7]) | Q(is_admin=True) | Q(is_superuser=True)),  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=1,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True)),
    )
    company = models.CharField(max_length=255, default="CODA")
    created_by = models.CharField(max_length=255, default="admin")
    app = models.CharField(max_length=255, default="Data Analysis")
    duration = models.IntegerField(null=False, default=4)  # how long will it take
    delivery_date = models.DateTimeField(
        default=timezone.now
    )  # When should this be delivered
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    what = models.TextField()  # What is needed?
    why = models.TextField()  # Why do they need it ?
    how = (
        models.TextField()
    )  # how should it be delivered/Which platform or mode of delivery?
    comments = models.TextField(default='No Comment',null=True, blank=True)  # What is needed?
    doc = models.FileField(upload_to="Uploads/Support_Docs/", null=True, blank=True)
    pptlink = models.CharField(max_length=1000,null=True, blank=True)
    videolink = models.CharField(max_length=1000,null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_tested = models.BooleanField(default=True)
    is_reviewed = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Requirements"
        # ordering = ["-created_at","-updated_at"]

    @property
    def doc_url(self):
        if self.doc and hasattr(self.doc, 'url'):
            return self.doc.url
        
    @property
    def active(self):
        if self.is_active is False:
            return "Ready For Testing"
        else:
            return "Not Started"

    def get_absolute_url(self):
        return reverse("management:requirements")

    def __str__(self):
        return 'CODA000' + str(self.id)
    

class ProcessJustification(models.Model):
    requirements = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="Requirement_in_Process",
                                     null=True, blank=True)
    justification = models.CharField(max_length=255, null=True, blank=True)
    crated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class ProcessBreakdown(models.Model):
    process = models.ForeignKey(ProcessJustification, on_delete=models.CASCADE, related_name="Process_in_breakdown",
                                null=True, blank=True)
    breakdown = models.CharField(max_length=255, null=True, blank=True)
    time = models.PositiveIntegerField(null=True, blank=True)
    Quantity = models.PositiveIntegerField(null=True, blank=True)
    total = models.PositiveIntegerField(null=True, blank=True)
    crated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)


def task_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

pre_save.connect(task_pre_save_receiver, sender=Task)

class Advertisement(models.Model):
    # Twitter   
    twitter_api_key = models.CharField(max_length=500, null=True, blank=True)
    twitter_api_key_secret = models.CharField(max_length=500, null=True, blank=True)
    twitter_bearer_token = models.CharField(max_length=500, null=True, blank=True)
    twitter_access_token = models.CharField(max_length=500, null=True, blank=True)
    twitter_access_token_secret = models.CharField(
        max_length=500, null=True, blank=True
    )
    # Facebook
    facebook_access_token = models.CharField(max_length=500, null=True, blank=True)
    facebook_page_id = models.CharField(max_length=100, null=True, blank=True)
    page_name = models.CharField(max_length=100, null=True, blank=True)
    post_description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="Uploads/Facebook/", null=True, blank=True)
    author= models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # whatsapp
    whatapp_group_name = models.CharField(max_length=100, null=True, blank=True)
    whatapp_group_id = models.CharField(max_length=100, null=True, blank=True)
    whatapp_image_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.post_description
    

class Meetings(models.Model):
    Group = [
        ("clients", "clients"),
        ("internal", "internal"),
        ("external", "external"),
        ("Other", "Other"),
    ]
    class Frequecy(models.IntegerChoices):
        Daily = 1,
        Weekly = 2
        Bi_Weekly = 3
        Monthly = 4
        Yearly = 5
    department=models.ForeignKey(
        to=Department, on_delete=models.CASCADE, default=Department.get_default_pk)
    category = models.ForeignKey(
        to=TaskCategory, on_delete=models.CASCADE
    )
    group = models.CharField(
        max_length=255,
        choices=Group,
        default='Other'
    )
    meeting_topic = models.CharField(max_length=100, null=True, blank=True)
    meeting_id = models.CharField(max_length=100, null=True, blank=True)
    meeting_type = models.CharField(max_length=100, null=True, blank=True)
    meeting_link = models.CharField(max_length=500, null=True, blank=True)
    meeting_description = models.TextField(null=True, blank=True)
    meeting_time = models.TimeField(default=timezone.now)
    frequency = models.IntegerField(choices=Frequecy.choices, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    # def __str__(self):
    #     return self.meeting_topic
    def __str__(self):
        return self.meeting_topic or ""

class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    # def __str__(self):
    #     return f"{self.name} - {self.department}"
    def __str__(self):
        return self.name or ""

class Link(TimeStampedModel):
    name = models.CharField(max_length=255)
    url = models.URLField()
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meetings, on_delete=models.CASCADE,default=1)

    # def __str__(self):
    #     # return f"{self.name} - {str(self.subcategory)}-{str(self.meeting)}"
    #     return self.name if self.name is not None else "Unnamed Link"

    def __str__(self):
        return self.name or ""
    

class Grievance(models.Model):
    ISSUE_CHOICES = [
        ('threats', 'Threats'),
        ('insults', 'Insults'),
        ('stealing', 'Stealing'),
        ('other', 'other'),
    ]
    STATUS_CHOICES = [
            ('pending', 'Pending'), 
            ('in_progress', 'In Progress'), 
            ('resolved', 'Resolved')
    ]
    reporter = models.ForeignKey(
        User,
        verbose_name=_("reporting_person"),
        related_name="reporting_person",
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True)| Q(is_admin=True) | Q(is_superuser=True)),
    )
    issue = models.CharField(max_length=50, choices=ISSUE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=100,null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    description = models.TextField()
    members_involved = models.CharField(max_length=100)
    witnesses = models.CharField(max_length=100,null=True, blank=True)
    proposed_solution = models.TextField()
    reference_link = models.CharField(max_length=500,default='NoLink',null=True, blank=True)

    confidentiality = models.BooleanField(
        help_text=_("Keep Identity Confidential"),
        default=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,default='Pending')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Grievance Form - {self.issue}"



class Conflict_Resolution(models.Model):
    SEVERITY_CHOICES = [
       ('low', 'Low'),
       ('medium', 'Medium'),
       ('high', 'High')
    ]
    assigned_person = models.ForeignKey(
        User,
        verbose_name=_("assigned_person"),
        related_name="assigned_person",
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True)| Q(is_admin=True) | Q(is_superuser=True)),
    )
    accountable_person = models.ForeignKey(
        User,
        verbose_name=_("accountable_person"),
        related_name="accountable_person",
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
        and (Q(is_staff=True)| Q(is_admin=True) | Q(is_superuser=True)),
    )
    issue = models.ForeignKey(
        Grievance,
        null=True,
        blank=True,
        default=1,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_active=True)
    )
    severity_level = models.CharField(max_length=50, choices=SEVERITY_CHOICES)
    previous_actions = models.TextField(max_length=1000,null=True, blank=True)
    resolution_deadline = models.DateField()
    fine = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    additional_comments = models.TextField(null=True, blank=True)
    # reference_link = models.URLField(default='No Link',null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Conflict_Resolution - {self.issue}"
class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('interview_assignment', 'Interview Assignment'),
        ('resume', 'Resume'),
        # Add more types as needed
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('checked', 'Checked')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assignment_type = models.CharField(max_length=50, choices=ASSIGNMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    drive_file_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review = models.TextField(null=True, blank=True)
    review_available_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} - {self.assignment_type}"
