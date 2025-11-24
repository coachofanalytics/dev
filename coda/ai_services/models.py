from django.db import models
from datetime import datetime,date
from shared_core.models import TimeStampedModel
# AI Services app migrated to use shared_core - 25.11_AI_SERVICES_DEV_CM test change
from management.models import Requirement
from professional_services.models import Prep_Questions,JobRole
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model
from main.utils import all_applications,unique_slug_generator,slug_pre_save_receiver

#User=settings.AUTH_USER_MODEL
User = get_user_model()


class OpenaiPrompt(models.Model):
    DEFAULT_CONTEXT_DESCRIPTION = "Domain such as IT Project Experice on roles such as Project Manager, Business Analysis"
    DEFAULT_ROLE = "Expert in IT Field"
    DEFAULT_CLARIFICATION_DESCRIPTION = "Utilize professional diction,Maintain a formal,friendly and helpful tone and Keep the response concise to maintain the reader's engagement"

    category = models.CharField(max_length=250, help_text="What category", null=True, blank=True)
    subcategory=models.CharField(
          						max_length=100,
                                choices=JobRole.QUESTION_CHOICES,
                                default=1,
                                null=True,blank=True)
    topic = models.CharField(max_length=250, help_text="What topic", null=True, blank=True)
    expert_question = models.CharField(max_length=250, help_text="Describe your question", null=True, blank=True)
    context_description = models.TextField(help_text="Provide context if possible", null=True, blank=True,
                                            default=DEFAULT_CONTEXT_DESCRIPTION)
    role = models.CharField(max_length=250, help_text="Explain your role", default=DEFAULT_ROLE, null=True, blank=True)
    clarification_description = models.TextField(help_text="Provide clarification or use default", null=True, blank=True,
                                                  default=DEFAULT_CLARIFICATION_DESCRIPTION)
    
    words = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.category} - {self.topic}-words:{( str(self.words))}"

    class Meta:
        db_table = 'getdata_openaiprompt'  # Use existing table name from old getdata app

class CashappMail(models.Model):
	id = models.CharField(max_length=30, unique=True, primary_key=True)
	from_mail = models.CharField(max_length=255)
	to_mail = models.CharField(max_length=255)
	subject = models.CharField(max_length=255)
	file_name = models.CharField(max_length=50)
	full_path = models.CharField(max_length=255)
	text_mail = models.TextField()
	received_date = models.CharField(max_length=255)
	parsed_date = models.DateTimeField(auto_now_add=True)
	amount = models.CharField(max_length=255,blank=True,null=True)
	destination = models.CharField(max_length=255,blank=True,null=True)

	class Meta:
		db_table = 'getdata_cashappmail'  # Use existing table name from old getdata app
		verbose_name_plural = "Cashapp"

	def __str__(self):
		return self.subject
	
	@property
	def received_date_format(self):
		time_text_date = self.received_date.replace(" ", "").split(",")[-1]
		new_received_date=datetime.strptime(time_text_date,'%d%b%Y%H:%M:%S+0000').date()
		return new_received_date

class ReplyMail(models.Model):
	id = models.CharField(max_length=30, unique=True, primary_key=True)
	from_mail = models.CharField(max_length=255)
	to_mail = models.CharField(max_length=255)
	subject = models.CharField(max_length=255)
	text_mail = models.TextField()
	received_date = models.CharField(max_length=255)

	class Meta:
		db_table = 'getdata_replymail'  # Use existing table name from old getdata app
		verbose_name_plural = "ReplyMail"

	def __str__(self):
		return self.subject

class Editable(models.Model):
	name = models.CharField(max_length=255,blank=True,null=True)
	value = models.JSONField(null=True)
	threshhold = models.CharField(max_length=250,blank=True,null=True)
	# callsrow = models.PositiveIntegerField(blank=True,null=True)

	class Meta:
		db_table = 'getdata_editable'  # Use existing table name from old getdata app
		verbose_name_plural = "General"

	def __str__(self):
		return self.name
	
class GotoMeetings(models.Model):
    """DEPRECATED: Legacy model - kept for backward compatibility during migration"""
    meeting_topic = models.CharField(max_length=250, null=True, blank=True)
    meeting_id = models.CharField(max_length=100, null=True, blank=True)
    meeting_type = models.CharField(max_length=100, null=True, blank=True)
    recording = models.CharField(max_length=500, null=True, blank=True)
    meeting_start_time = models.CharField(max_length=250, null=True, blank=True)
    meeting_end_time = models.CharField(max_length=250, null=True, blank=True)
    meeting_duration = models.CharField(max_length=100, null=True, blank=True)
    meeting_email = models.CharField(max_length=150, null=True, blank=True)
    attendee_name = models.CharField(max_length=150, null=True, blank=True)
    attendee_email = models.CharField(max_length=150, null=True, blank=True)
    download_url = models.URLField(max_length=1000, null=True, blank=True)
    attendee_duration = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    def __str__(self):
        return self.meeting_topic or "Untitled Meeting"

    class Meta:
        db_table = 'getdata_gotomeetings'  # Use existing table name from old getdata app


# ==================== NEW NORMALIZED MODELS (Phase 1) ====================

class Meeting(models.Model):
    """
    Normalized meeting model - one record per meeting.
    Replaces denormalized GotoMeetings model.
    """
    meeting_id = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique GoToMeeting ID"
    )
    topic = models.CharField(
        max_length=500,
        help_text="Meeting subject/topic"
    )
    meeting_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of meeting (e.g., General Meeting, 1-1 session)"
    )
    start_time = models.DateTimeField(
        db_index=True,
        help_text="Meeting start time (UTC)"
    )
    end_time = models.DateTimeField(
        help_text="Meeting end time (UTC)"
    )
    duration_minutes = models.IntegerField(
        default=0,
        help_text="Total meeting duration in minutes"
    )
    recording_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="URL to meeting recording"
    )
    download_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Direct download URL for recording"
    )
    is_recorded = models.BooleanField(
        default=False,
        help_text="Whether meeting was recorded"
    )
    google_drive_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Google Drive URL if recording uploaded"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gotomeeting_meeting'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['meeting_id']),
            models.Index(fields=['start_time']),
            models.Index(fields=['-start_time']),
        ]
        verbose_name = "GoToMeeting"
        verbose_name_plural = "GoToMeetings"

    def __str__(self):
        return f"{self.topic} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def attendee_count(self):
        """Return number of attendees"""
        return self.attendees.count()
    
    @property
    def average_attendance_duration(self):
        """Return average attendance duration in minutes"""
        from django.db.models import Avg
        avg = self.attendees.aggregate(Avg('duration_minutes'))
        return avg['duration_minutes__avg'] or 0


class MeetingAttendee(models.Model):
    """
    Individual attendee record for each meeting.
    Normalized - no duplication of meeting data.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='attendees',
        help_text="Meeting this attendee participated in"
    )
    user = models.ForeignKey(
        'accounts.CustomerUser',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='meeting_attendances',
        help_text="Linked CODA user (if matched)"
    )
    attendee_name = models.CharField(
        max_length=200,
        help_text="Attendee's display name"
    )
    attendee_email = models.EmailField(
        help_text="Attendee's email address"
    )
    duration_minutes = models.IntegerField(
        default=0,
        help_text="How long attendee stayed in meeting (minutes)"
    )
    is_organizer = models.BooleanField(
        default=False,
        help_text="Whether attendee was the meeting organizer"
    )
    task_points_awarded = models.BooleanField(
        default=False,
        help_text="Whether task points were awarded for this attendance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gotomeeting_attendee'
        unique_together = [('meeting', 'attendee_email')]
        ordering = ['-duration_minutes']
        indexes = [
            models.Index(fields=['attendee_email']),
            models.Index(fields=['user']),
        ]
        verbose_name = "Meeting Attendee"
        verbose_name_plural = "Meeting Attendees"

    def __str__(self):
        return f"{self.attendee_name} ({self.meeting.topic})"
    
    @property
    def attendance_percentage(self):
        """Calculate what percentage of meeting attendee participated in"""
        if self.meeting.duration_minutes > 0:
            return (self.duration_minutes / self.meeting.duration_minutes) * 100
        return 0
    
    @property
    def qualifies_for_points(self):
        """Check if attendance qualifies for task points (>3 minutes)"""
        return self.duration_minutes > 3


class OAuthToken(models.Model):
    """
    Secure storage for OAuth tokens.
    Replaces cache-based token storage for persistence across restarts.
    """
    service_name = models.CharField(
        max_length=50,
        default='gotomeeting',
        unique=True,
        help_text="Service name (gotomeeting, google_drive, etc.)"
    )
    access_token = models.TextField(
        help_text="Encrypted access token"
    )
    refresh_token = models.TextField(
        help_text="Encrypted refresh token"
    )
    token_type = models.CharField(
        max_length=50,
        default='Bearer',
        help_text="Token type"
    )
    expires_at = models.DateTimeField(
        help_text="When access token expires"
    )
    scope = models.TextField(
        blank=True,
        help_text="Token scope/permissions"
    )
    is_valid = models.BooleanField(
        default=True,
        help_text="Whether token is currently valid"
    )
    last_refreshed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When token was last refreshed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'oauth_token'
        verbose_name = "OAuth Token"
        verbose_name_plural = "OAuth Tokens"

    def __str__(self):
        return f"{self.service_name} token (expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        from django.utils import timezone
        return timezone.now() >= self.expires_at
    
    @property
    def needs_refresh(self):
        """Check if token should be refreshed (expires in <5 minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() >= (self.expires_at - timedelta(minutes=5))


class MeetingActivityMapping(models.Model):
    """
    Configurable mapping between meetings and task activities.
    Replaces hardcoded activity_mapping dictionary.
    """
    meeting_id_pattern = models.CharField(
        max_length=100,
        unique=True,
        help_text="Meeting ID or pattern to match"
    )
    activity_name = models.CharField(
        max_length=200,
        help_text="Activity name for task management"
    )
    task_points = models.IntegerField(
        default=0,
        help_text="Task points to award for attendance"
    )
    min_duration_minutes = models.IntegerField(
        default=3,
        help_text="Minimum attendance duration to qualify for points"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this mapping is currently active"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this meeting type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meeting_activity_mapping'
        ordering = ['activity_name']
        verbose_name = "Meeting Activity Mapping"
        verbose_name_plural = "Meeting Activity Mappings"

    def __str__(self):
        return f"{self.meeting_id_pattern} → {self.activity_name}"
	
class upwork_Transanctions(models.Model):
    date= models.CharField(max_length=250, null=True, blank=True)
    ref_Id= models.CharField(max_length=250, null=True, blank=True)
    type= models.CharField(max_length=500, null=True, blank=True)
    description= models.CharField(max_length=250, null=True, blank=True)
    agency= models.CharField(max_length=250, null=True, blank=True)
    freelancer= models.CharField(max_length=250, null=True, blank=True)
    team= models.CharField(max_length=250, null=True, blank=True)
    account_name= models.CharField(max_length=250, null=True, blank=True)
    amount= models.CharField(max_length=250, null=True, blank=True)
    balance= models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.ref_Id

    class Meta:
        db_table = 'getdata_upwork_transactions'  # Use existing table name from old getdata app
class UpworkConnects(models.Model):
    PAYMENT_CHOICES = [
        ('50-80', '50 to 80 dollars'),
        ('80+', 'More than 80 dollars'),
    ]
    DURATION_CHOICES = [
        ('1-3 months', '1 month to 3 months'),
        ('3-6 months', '3 months to 6 months'),
        ('6-12 months', '6 months to 1 year'),
        ('1 year+', 'More than 1 year'),
    ]
    
    PROJECT_TYPE_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('from scratch', 'From Scratch'),
    ]
    PROJECT_CATEGORY_CHOICES = [
        ('ERP SYSTEM', 'ERP SYSTEM'),
        ('SAAS', 'SAAS'),
        ('TRAINING', 'TRAINING'),
        ('WEB DEVELOPMENT', 'Web Development'),
        ('BLOCKCHAIN', 'Blockchain'),
    ]
    title = models.CharField(max_length=1000)
    description = models.TextField()
    skills = models.CharField(max_length=1000)
    payment_range = models.CharField(max_length=200, choices=PAYMENT_CHOICES)
    duration_range = models.CharField(max_length=200, choices=DURATION_CHOICES)
    project_type = models.CharField(max_length=200, choices=PROJECT_TYPE_CHOICES) 
    project_category = models.CharField(max_length=200, choices=PROJECT_CATEGORY_CHOICES)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'getdata_upwork_connects'  # Use existing table name from old getdata app

class Logs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_logs", null=True, blank=True)
    location_in_code = models.CharField(max_length=255, null=True, blank=True)
    reason_code_crash = models.CharField(max_length=255, null=True, blank=True)
    exception = models.CharField(max_length=255, null=True, blank=True)
    api = models.URLField(max_length=255, null=True, blank=True)
    crated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'getdata_logs'  # Use existing table name from old getdata app
        verbose_name_plural = "Logs"
		

class CaseCategory(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'getdata_case_category'  # Use existing table name from old getdata app
        verbose_name_plural = "UseCase Categories"

    # def get_absolute_url(self):
    #     return reverse("main:display_usecases", slug=self.title )

    def __str__(self):
        return self.title
    
class UseCase(TimeStampedModel):
    *_,APP_CHOICES = all_applications()
    DEFAULT_HARDWARE_REQUIREMENTS = "To implement this requirement, we need to install/access the following : 1. CODA Website, 2. CODA Google Drive, 3. Chatgpt, 3. Openai Key 4. Install ,Python, Postgres,VS CODE, and GIT, and finally create an account with GitHub, and Heroku you will also need access to AWS."
    app= models.CharField(
        max_length=100,
        choices=APP_CHOICES,
        default="Other",
    )
    category=models.ForeignKey(CaseCategory, on_delete=models.CASCADE,null=True, blank=True,default=40)
    title = models.CharField(max_length=100, blank=True, null=True)
    requirements_id = models.ForeignKey(Requirement, on_delete=models.CASCADE,null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    installation = models.TextField(help_text="Provide tools used", null=True, blank=True,
                                            default=DEFAULT_HARDWARE_REQUIREMENTS)
    usage_link=models.CharField(max_length=255,blank=True, null=True)
    deployment = models.CharField(max_length=255,blank=True, null=True)
    license = models.CharField(max_length=255,blank=True, null=True)
    credits = models.CharField(max_length=255,blank=True, null=True)
    contact = models.CharField(max_length=255,blank=True, null=True)
    additional_sections = models.TextField(blank=True, null=True)
    links = models.CharField(max_length=255,blank=True, null=True)

    class Meta:
        db_table = 'getdata_usecase'  # Use existing table name from old getdata app
        verbose_name_plural = "UseCase"

    def get_absolute_url(self):
        return reverse("main:display_usecases", slug=self.title )
         
    def __str__(self):
        return self.title or "UseCase Entry"

# ==============================PRESAVE SLUG GENERATORS====================================
# def Readme_pre_save_receiver(sender,instance,*args,**kwargs):
#     if not instance.slug:
#         instance.slug=unique_slug_generator

# def UseCase_pre_save_receiver(sender,instance,*args,**kwargs):
#     if not instance.slug:
#         instance.slug=unique_slug_generator

# pre_save.connect(UseCase_pre_save_receiver,sender=UseCase)

# def servicecategory_pre_save_receiver(sender, instance, *args, **kwargs):
#     if not instance.slug:
#         if instance.name:
#             instance.slug = unique_slug_generator(instance)

# pre_save.connect(servicecategory_pre_save_receiver, sender=ServiceCategory)

# pre_save.connect(Readme_pre_save_receiver,sender=Readme)


#excel data fetching model
class DynamicExcelData(models.Model):
    data = models.JSONField() 

    class Meta:
        db_table = 'getdata_dynamic_excel_data'  # Use existing table name from old getdata app

    @staticmethod
    def get_column_names():
        if DynamicExcelData.objects.exists():
            return DynamicExcelData.objects.first().data.keys()
        return []

# ==============================DIASPORA AI PLATFORM MODELS=============================

class DiasporaAnalysisTypes(models.TextChoices):
    """Analysis types with proper naming (not demo_model/table)"""
    REMITTANCE_ANALYSIS = 'remittance_analysis', 'Remittance Analysis'
    TRADE_FACILITATION = 'trade_facilitation', 'Trade Facilitation'
    INVESTMENT_OPPORTUNITIES = 'investment_opportunities', 'Investment Opportunities'
    EDUCATION_PATHWAYS = 'education_pathways', 'Education Pathways'
    HEALTHCARE_ACCESS = 'healthcare_access', 'Healthcare Access'

class AIModelTypes(models.TextChoices):
    """AI Model types with proper naming"""
    GPT4_PRIMARY = 'gpt4_primary', 'GPT-4 Primary Model'
    GPT35_FALLBACK = 'gpt35_fallback', 'GPT-3.5 Fallback Model'
    CLAUDE3_BACKUP = 'claude3_backup', 'Claude-3 Backup Model'
    LOCAL_OFFLINE = 'local_offline', 'Local Offline Model'

class DiasporaAnalysisData(models.Model):
    """Main model for storing diaspora analysis data"""
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diaspora_analyses')
    analysis_type = models.CharField(max_length=50, choices=DiasporaAnalysisTypes.choices)
    user_input = models.JSONField()
    ai_prediction = models.JSONField()
    model_used = models.CharField(max_length=100, choices=AIModelTypes.choices)
    confidence_score = models.FloatField()
    processing_time = models.FloatField()
    fallback_used = models.BooleanField(default=False)
    is_real_ai = models.BooleanField(default=False, help_text="Whether this used real AI or fallback data")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'diaspora_analysis_data'
        indexes = [
            models.Index(fields=['session_id', 'analysis_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['model_used']),
        ]
    
    def __str__(self):
        return f"{self.analysis_type} - {self.session_id}"

class AnalysisSession(models.Model):
    """Session management for analysis users"""
    STAKEHOLDER_TYPES = [
        ('investor', 'Investor'),
        ('government', 'Government Representative'),
        ('diaspora', 'Diaspora Member'),
        ('general', 'General Public'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_analyses = models.IntegerField(default=0)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    presentation_mode = models.BooleanField(default=False)
    stakeholder_type = models.CharField(max_length=50, choices=STAKEHOLDER_TYPES, null=True, blank=True)
    is_authenticated_session = models.BooleanField(default=False, help_text="Whether this is an authenticated user session")
    
    class Meta:
        db_table = 'analysis_session'
    
    def __str__(self):
        return f"Session {self.session_id} - {self.stakeholder_type}"

class UserBehaviorAnalytics(models.Model):
    """Enhanced user behavior tracking for analytics"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('form_start', 'Form Started'),
        ('form_submit', 'Form Submitted'),
        ('analysis_complete', 'Analysis Completed'),
        ('result_view', 'Results Viewed'),
        ('download', 'File Downloaded'),
        ('share', 'Content Shared'),
        ('error', 'Error Encountered'),
        ('session_start', 'Session Started'),
        ('session_end', 'Session Ended'),
    ]
    
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='behavior_analytics')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    page_url = models.URLField(blank=True, null=True)
    analysis_type = models.CharField(max_length=50, choices=DiasporaAnalysisTypes.choices, blank=True, null=True)
    event_data = models.JSONField(default=dict, help_text="Additional event-specific data")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    country = models.CharField(max_length=100, null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)  # mobile, desktop, tablet
    browser = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'user_behavior_analytics'
        indexes = [
            models.Index(fields=['session_id', 'event_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['analysis_type']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.session_id} - {self.timestamp}"

class AIModelConfiguration(models.Model):
    """Configuration for AI models and fallback strategies"""
    model_name = models.CharField(max_length=100, choices=AIModelTypes.choices)
    is_active = models.BooleanField(default=True)
    priority_order = models.IntegerField(default=1)
    api_endpoint = models.URLField(null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    max_tokens = models.IntegerField(default=1000)
    temperature = models.FloatField(default=0.3)
    timeout_seconds = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_model_configuration'
        ordering = ['priority_order']
    
    def __str__(self):
        return f"{self.model_name} (Priority: {self.priority_order})"
