# from coda_project.application.views import first_interview
from django.db import models
from django.utils import timezone
from main.models import TimeStampedModel
from main.models import Assets
from django.db.models import Q
from django.contrib.auth import get_user_model

# from finance.utils import get_exchange_rate
# from coda_project.storage import GoogleDriveStorage
# application/models.py
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Policy(models.Model):
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
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    upload_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    policy_type = models.CharField(
        max_length=25,
        choices=CHOICES,
        default=Other,
    )
    description = models.TextField()
    policy_doc = models.FileField(
        upload_to="policy/doc/", default=None, null=True, blank=True
    )

    def __str__(self):
        return f"{self.id} policy"

class Rated(models.Model):
    Type = [
        ("Exam", "Exam"),
        ("Symbosium", "Symbosium"),
        ("Exam_ChatGPT", "Exam_ChatGPT"),
        ("Other", "Other"),
    ]
    TOOL_CHOICES = [
            ("Alteryx", "Alteryx"),
            ("Tableau", "Tableau"),
            ("Database", "Database"),
            ("Python", "Python"),
            ("SAS", "SAS"),
            ("Other", "Other"),
        ]
    TOPIC_CHOICES = [
        ("English", "English"),
        ("Kiswahili", "Kiswahili"),
        ("Math", "Math"),
        ("Business", "Business"),
        ("Physics", "Physics"),
        ("Chemistry", "Chemistry"),
        ("Biology", "Biology"),
        ("GHC", "GHC"),
        ("History", "History"),
        ("CRE", "CRE"),
        ("Agriculture", "Agriculture"),
        ("Other", "Other"),
    ]
    id = models.AutoField(primary_key=True)
    employeename =  models.ForeignKey(
                    "accounts.CustomerUser", limit_choices_to=Q(is_staff=True)|Q(category=1),  # Job_Applicant category
                    on_delete=models.CASCADE, related_name="rating_empname",default=1,blank=True)
    type = models.CharField(
        max_length=255,
        choices=Type,
        default='Other'
    )
    topic = models.CharField(
        max_length=255,
        choices=TOPIC_CHOICES,
        default='Other'
    )
    data_tools = models.CharField(
        max_length=255,
        choices=TOOL_CHOICES,
        default='Other'
    )
    uploadlinkurl = models.CharField(max_length=1000,blank=True, null=True)
    rating_date = models.DateTimeField(default=timezone.now)
    projectDescription = models.BooleanField(default=False)# 2
    requirementsAnalysis  = models.BooleanField(default=False)# 3
    development = models.BooleanField(default=False)# 5
    testing = models.BooleanField(default=False)# 3
    deployment = models.BooleanField(default=False)# 2
    totalpoints = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id} Rating"

    def clean(self):
        """Validate Rated model data"""
        from django.core.exceptions import ValidationError
        
        # Calculate expected total points
        expected_points = 0
        if self.projectDescription:
            expected_points += 2
        if self.requirementsAnalysis:
            expected_points += 3
        if self.development:
            expected_points += 5
        if self.testing:
            expected_points += 3
        if self.deployment:
            expected_points += 2
        
        # Validate total points
        if self.totalpoints != expected_points:
            raise ValidationError(f"Total points should be {expected_points}, not {self.totalpoints}")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)


class Reporting(models.Model):
    internal = "Internal Interview"
    first_interview = "First Interview"
    second_interview = "Second Interview"
    third_interview = "Third Interview"
    Other = "Other"
    direct = "Direct"
    indirect = "Indirect"

    INTERVIEW_CHOICES = [
        (internal, "Internal Interview"),
        (first_interview, "First Interview"),
        (second_interview, "Second Interview"),
        (third_interview, "Third Interview"),
        (Other, "Other"),
    ]
    METHOD_CHOICES = [
        (direct, "Direct"),
        (indirect, "Indirect"),
    ]
    id = models.AutoField(primary_key=True)
    reporter = models.ForeignKey(
        "accounts.CustomerUser",
        related_name="reporting_user",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name=models.CharField(max_length=50,null=True,blank=True)
    rate=models.CharField(max_length=50,null=True,blank=True)
    interview_type = models.CharField(
        max_length=25,
        choices=INTERVIEW_CHOICES,
        default="other"
    )
    method = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        choices=METHOD_CHOICES,
    )
    reporting_date = models.DateTimeField(
        "Reporting Date(mm/dd/yyyy)",
        auto_now_add=False,
        auto_now=False,
        blank=True,
        null=True,
    )
    update_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    comment = models.TextField()
    link=models.CharField(max_length=500,null=True,blank=True)

    def __str__(self):
        return f"{self.id} Reporting"

    def clean(self):
        """Validate Reporting model data"""
        from django.core.exceptions import ValidationError
        
        # Validate reporting date
        if self.reporting_date and self.reporting_date > timezone.now():
            raise ValidationError("Reporting date cannot be in the future")
        
        # Validate link format if provided
        if self.link and not self.link.startswith(('http://', 'https://')):
            raise ValidationError("Link must start with http:// or https://")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)
    
class Topic(models.Model):
    TOPIC_CHOICES=[
        ("projectDescription","projectDescription"),
        ("requirementsAnalysis ","requirementsAnalysis "),
        ("development","development"),
        ("testing","testing"),
        ("deployment","deployment"),
    ]
    topic_name = models.CharField(
        max_length=255,
        choices=TOPIC_CHOICES,
        default='Other'
    )
    # name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.topic_name
    
class Trainee_Assessment(TimeStampedModel):
    class Score(models.IntegerChoices):
        Excellent = 1 
        very_good = 2
        good = 3
        below_average = 4

    class Audibility(models.IntegerChoices):
        Excellent = 1
        very_good = 2
        good = 3
        below_average = 4

    TOOL_CHOICES = [
            ("ETL", "ETL"),
            ("Reporting", "Reporting"),
            ("Database", "Database"),#Snowflake,SQL,POSTGRES
            ("Website", "Website"),
            ("SAS", "SAS"),
            ("Other", "Other"),
        ]

    assessor =  models.ForeignKey(
                    "accounts.CustomerUser", 
                    limit_choices_to=Q(is_staff=True), 
                    on_delete=models.CASCADE, 
                    related_name="assessor_username",
                    default=1,blank=True)

    trainee_username =  models.ForeignKey(
                    "accounts.CustomerUser", limit_choices_to=Q(is_staff=True)|Q(category=1),  # Job_Applicant category
                    on_delete=models.CASCADE, related_name="trainee_username",default=1,blank=True)
    topic = models.ManyToManyField(Topic, blank=True)
    data_tools = models.CharField(
        max_length=255,
        choices=TOOL_CHOICES,
        default='Other'
    )
    audibility = models.IntegerField(choices=Audibility.choices, default=999)
    score = models.IntegerField(choices=Score.choices, default=999)
    duration = models.IntegerField(default=0)
    uploadlinkurl = models.CharField(max_length=1000,blank=True, null=True)
    # completed_on=models.DateField(blank=None,null=None)
    def __str__(self):
        return f"{self.id} assessment"

    def clean(self):
        """Validate Trainee_Assessment model data"""
        from django.core.exceptions import ValidationError
        
        # Validate score
        if self.score == 999:
            raise ValidationError("Score must be selected")
        
        # Validate audibility
        if self.audibility == 999:
            raise ValidationError("Audibility must be selected")
        
        # Validate duration
        if self.duration < 0:
            raise ValidationError("Duration cannot be negative")
        
        # Validate upload link if provided
        if self.uploadlinkurl and not self.uploadlinkurl.startswith(('http://', 'https://')):
            raise ValidationError("Upload link must start with http:// or https://")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)


# ==================== NEW AUTOMATED WORKFLOW MODELS ====================

class ApplicationWorkflow(TimeStampedModel):
    """
    Automated workflow for applicant-to-employee promotion
    Tracks the entire process from application to employee status
    """
    
    class WorkflowStatus(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        UNDER_REVIEW = 'under_review', 'Under Review'
        INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
        INTERVIEW_COMPLETED = 'interview_completed', 'Interview Completed'
        SKILLS_ASSESSMENT = 'skills_assessment', 'Skills Assessment'
        ASSESSMENT_COMPLETED = 'assessment_completed', 'Assessment Completed'
        FINAL_REVIEW = 'final_review', 'Final Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EMPLOYEE = 'employee', 'Employee'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class PromotionType(models.TextChoices):
        AUTOMATIC = 'automatic', 'Automatic (Criteria Met)'
        MANUAL = 'manual', 'Manual (Admin Override)'
        HYBRID = 'hybrid', 'Hybrid (Criteria + Admin Approval)'
    
    # Core fields
    applicant = models.OneToOneField(
        "accounts.CustomerUser",
        on_delete=models.CASCADE,
        related_name="workflow",
        limit_choices_to={"category": 1, "is_active": True},  # Only applicants
        help_text="The applicant going through the workflow"
    )
    
    # Workflow tracking
    status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.APPLIED,
        help_text="Current status in the workflow"
    )
    
    promotion_type = models.CharField(
        max_length=10,
        choices=PromotionType.choices,
        default=PromotionType.HYBRID,
        help_text="Type of promotion process"
    )
    
    # Criteria tracking
    documents_completed = models.BooleanField(default=False, help_text="All required documents submitted")
    skills_assessment_score = models.IntegerField(default=0, help_text="Total skills assessment score")
    interview_completed = models.BooleanField(default=False, help_text="Interview process completed")
    admin_approval = models.BooleanField(default=False, help_text="Admin approval given")
    
    # Scoring thresholds
    min_skills_score = models.IntegerField(default=12, help_text="Minimum skills score required")
    min_interview_score = models.IntegerField(default=8, help_text="Minimum interview score required")
    
    # Dates and tracking
    applied_date = models.DateTimeField(auto_now_add=True)
    last_status_change = models.DateTimeField(auto_now=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Admin fields
    reviewed_by = models.ForeignKey(
        "accounts.CustomerUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_staff": True},
        related_name="reviewed_workflows",
        help_text="Admin who reviewed this application"
    )
    
    notes = models.TextField(blank=True, help_text="Admin notes about the application")
    
    class Meta:
        db_table = 'application_workflow'
        verbose_name = 'Application Workflow'
        verbose_name_plural = 'Application Workflows'
        ordering = ['-applied_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['applicant']),
            models.Index(fields=['applied_date']),
            models.Index(fields=['promotion_type']),
        ]
    
    def __str__(self):
        return f"{self.applicant.username} - {self.get_status_display()}"
    
    @property
    def is_eligible_for_promotion(self):
        """Check if applicant meets all criteria for automatic promotion"""
        return (
            self.documents_completed and
            self.skills_assessment_score >= self.min_skills_score and
            self.interview_completed and
            self.status in [self.WorkflowStatus.FINAL_REVIEW, self.WorkflowStatus.ASSESSMENT_COMPLETED]
        )
    
    @property
    def workflow_duration_days(self):
        """Calculate workflow duration in days"""
        if self.completed_date:
            return (self.completed_date - self.applied_date).days
        return (timezone.now() - self.applied_date).days
    
    def advance_status(self, new_status, admin_user=None, notes=""):
        """Advance workflow status with logging"""
        old_status = self.status
        self.status = new_status
        self.last_status_change = timezone.now()
        
        if admin_user:
            self.reviewed_by = admin_user
        
        if notes:
            self.notes = notes
        
        # Set completion date if final status
        if new_status in [self.WorkflowStatus.EMPLOYEE, self.WorkflowStatus.REJECTED, self.WorkflowStatus.CANCELLED]:
            self.completed_date = timezone.now()
        
        self.save()
        
        # Log the status change
        WorkflowStatusLog.objects.create(
            workflow=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=admin_user,
            notes=notes
        )
        
        return True
    
    def promote_to_employee(self, admin_user=None):
        """Promote applicant to employee (set is_staff=True)"""
        if self.status != self.WorkflowStatus.EMPLOYEE:
            self.advance_status(self.WorkflowStatus.EMPLOYEE, admin_user, "Promoted to employee")
        
        # Set is_staff=True
        self.applicant.is_staff = True
        self.applicant.save()
        
        return True


class WorkflowStatusLog(models.Model):
    """
    Audit log for workflow status changes
    Tracks all status changes with timestamps and admin actions
    """
    
    workflow = models.ForeignKey(
        ApplicationWorkflow,
        on_delete=models.CASCADE,
        related_name="status_logs"
    )
    
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    
    changed_by = models.ForeignKey(
        "accounts.CustomerUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Admin who made the change"
    )
    
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'application_workflow_status_log'
        verbose_name = 'Workflow Status Log'
        verbose_name_plural = 'Workflow Status Logs'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.workflow.applicant.username}: {self.old_status} → {self.new_status}"


class WorkflowCriteria(models.Model):
    """
    Configurable criteria for workflow automation
    Allows admin to set different criteria for different applicant types
    """
    
    class CriteriaType(models.TextChoices):
        DOCUMENTS = 'documents', 'Document Completion'
        SKILLS_SCORE = 'skills_score', 'Skills Assessment Score'
        INTERVIEW_SCORE = 'interview_score', 'Interview Score'
        ADMIN_APPROVAL = 'admin_approval', 'Admin Approval Required'
        TIME_BASED = 'time_based', 'Time-based Criteria'
    
    name = models.CharField(max_length=100, unique=True, help_text="Criteria name")
    criteria_type = models.CharField(max_length=20, choices=CriteriaType.choices)
    
    # Criteria values
    min_value = models.IntegerField(null=True, blank=True, help_text="Minimum value required")
    max_value = models.IntegerField(null=True, blank=True, help_text="Maximum value allowed")
    required = models.BooleanField(default=True, help_text="Is this criteria required?")
    
    # Configuration
    is_active = models.BooleanField(default=True, help_text="Is this criteria active?")
    description = models.TextField(help_text="Description of the criteria")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'application_workflow_criteria'
        verbose_name = 'Workflow Criteria'
        verbose_name_plural = 'Workflow Criteria'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_criteria_type_display()})"