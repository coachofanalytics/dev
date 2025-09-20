from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import *
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.urls import reverse
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from professional_services.modelmanager import(InterviewQuerySet,RoleQuerySet,InterviewManager,RoleManager,
                              CategoryManager,SubCategoryManager,ActivityManager)

# User=settings.AUTH_USER_MODEL
from accounts.models import CustomerUser
User = get_user_model()

    
#Interview Model
class JobRoles(models.Model):
    CAT_CHOICES = [
        ('Project Management', 'Project Management'),
        ('Business Analysis', 'Business Analysis'),
        ('Quality Assurance', 'Quality Assurance'),
        ('User Experience', 'User Experience'),
        ('Reporting', 'Reporting'),
        ('ETL', 'ETL'),
        ('Database', 'Database'),
        ('Python', 'Python'),
        ('Other', 'Other'),
    ]

    upload_date = models.DateTimeField(default=timezone.now,null=True,blank=True)
    category= models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default='Other',
    )
    description=models.TextField(max_length=1000,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    is_tech=models.BooleanField(default=True)

    objects=RoleManager()

    class Meta:
        verbose_name_plural = 'IT Roles'
        db_table = 'data_jobroles'  # Use existing table name from old data app

    def __str__(self):
        return f"{self.category}"
    
    def get_url(self):
        return reverse("professional_services:question-detail", args=[self.category])
    
    
#Interview Model
class JobRole(models.Model):
    # Job Category.
    Project_Management = 'Project Management'
    Business_Analysis = 'Business Analyst'
    Quality_Assurance = 'Quality Assurance'
    User_Experience = 'User Interface'
    Reporting = 'Reporting'
    ETL = 'ETL'
    Database = 'Database'
    Python = 'Python'
    Other = 'Other'

    # Question Type
    Introduction = 'introduction'
    Project_Story = 'Project Story'
    Performance = 'performance'
    Methodology = 'methodology'
    SDLC = 'sdlc'
    Testing = 'testing'
    Environment = 'environment'
    Resume = 'resume'

    CAT_CHOICES = [
        (Project_Management, 'Project Management'),
        (Business_Analysis, 'Business Analysis'),
        (Quality_Assurance, 'Quality Assurance'),
        (User_Experience, 'User Experience'),
        (Reporting, 'Reporting'),
        (ETL, 'ETL'),
        (Database, 'Database'),
        (Python, 'Python'),
        (Other, 'Other'),
    ]
    
    QUESTION_CHOICES = [
    (Introduction , 'introduction'),
    (Project_Story , 'project story'),
    (Performance , 'performance'),
    (Methodology , 'methodology'),
    (SDLC , 'sdlc'),
    (Testing , 'testing'),
    (Environment , 'environment'),
    (Resume , 'resume'),
    (Other, 'Other'),
    ]
    user= models.ForeignKey(
                            User,
                            verbose_name=_("Client"),
                            related_name="Client_Name",
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,
                            limit_choices_to={"category__in": [1, 3, 4, 5, 6, 7], "is_active": True},  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
                           )
    upload_date = models.DateTimeField(default=timezone.now,null=True,blank=True)
    category= models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default=Other,
    )
    question_type= models.CharField(
        max_length=100,
        choices=QUESTION_CHOICES,
        default=Other,
    )
    doc=models.FileField(default="None",upload_to='Uploads/doc/')
    videolink=models.CharField(max_length=255,blank=True, null=True)
    doclink=models.CharField(max_length=255,blank=True, null=True)
    desc1=models.TextField(max_length=1000,blank=True, null=True)
    desc2=models.TextField(max_length=1000,blank=True, null=True)
    is_active=models.BooleanField(default=True)

    objects=RoleManager()

    class Meta:
        verbose_name_plural = 'Roles'
        db_table = 'data_jobrole'  # Use existing table name from old data app

    def __str__(self):
        return f"{self.question_type}"
    
    def uploaded_doc(self):
        if self.doc is None or self.doc == "None":
            return reverse("main:404error")
        else:
            return self.doc

    def get_url(self):
        return reverse("professional_services:question-detail", args=[self.question_type])
    

# Interviews Model
class Interviews(models.Model):
    # Job Category.
    Project_Management = "Project Management"
    Business_Analysis = "Business Analyst"
    Quality_Assurance = "Quality Assurance"
    User_Experience = "User Interface"
    Reporting = "Reporting"
    ETL = "ETL"
    Database = "Database"
    Python = "Python"
    Other = "Other"
    # Question Type
    Introduction = "introduction"
    Project_Story = "Project Story"
    Performance = "performance"
    Methodology = "methodology"
    SDLC = "sdlc"
    Testing = "testing"
    Environment = "environment"
    Resume = "resume"

    CAT_CHOICES = [
        (Project_Management, "Project Management"),
        (Business_Analysis, "Business Analysis"),
        (Quality_Assurance, "Quality Assurance"),
        (User_Experience, "User Experience"),
        (Reporting, "Reporting"),
        (ETL, "ETL"),
        (Database, "Database"),
        (Python, "Python"),
        (Other, "Other"),
    ]

    QUESTION_CHOICES = [
        (Introduction, "introduction"),
        (Project_Story, "project story"),
        (Performance, "performance"),
        (Methodology, "methodology"),
        (SDLC, "sdlc"),
        (Testing, "testing"),
        (Environment, "environment"),
        (Resume, "resume"),
        (Other, "Other"),
    ]
    client = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="client_assiged", default=1
    )
    upload_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    category = models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default=Other,
    )
    question_type = models.CharField(
        max_length=100,
        choices=QUESTION_CHOICES,
        default=Other,
    )
    comment = models.TextField()
    doc = models.FileField(default="None", upload_to="Uploads/doc/",blank=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    dynamic_fields = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = InterviewManager()

    class Meta:
        verbose_name_plural = "Interview_Responses"
        db_table = 'data_interviews'  # Use existing table name from old data app

    def __str__(self):
        return f"{self.client}-{self.question_type}"


class Training_Responses(models.Model):
    user = models.ForeignKey(
        CustomerUser, on_delete=models.CASCADE, related_name="user_assigned", null=True, blank=True
    )
    title = models.CharField(max_length=1000,null=True, blank=True)
    response = models.CharField(max_length=1000,null=True, blank=True)
    question = models.CharField(max_length=1055,null=True, blank=True)
    question1 = models.TextField(default='Write Your Reponse')
    is_active = models.BooleanField(default=True)
    review = models.TextField(null=True, blank=True)
    link = models.CharField(max_length=500,null=True, blank=True)
    comment = models.TextField()
    score = models.PositiveIntegerField(null=True, blank=True)
    upload_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    first_displayed_at = models.DateTimeField(null=True, blank=True)
    seen_notifications = models.BooleanField(default=False)

    class Meta:
        db_table = 'data_training_responses'  # Use existing table name
        verbose_name_plural = 'Training Responses'

    def __str__(self):
        return f"{self.user}- {self.title}"
    
    @property
    def notification_days(self):
        # last_updated=date_converter(self.upload_date)
        last_updated=self.upload_date
        try:
            Number_notification_days = (datetime.now().date() - last_updated.date()).days
        except:
            Number_notification_days = 0

        return Number_notification_days
    
    @property
    def notification_flag(self):
        last_updated=self.upload_date
        try:
            Number_notification_days = (datetime.now().date() - last_updated.date()).days
        except:
            Number_notification_days = 0
        flag=True if Number_notification_days >7 else False
        return flag
    @property
    def notification_time(self):
        if self.first_displayed_at:
            now = timezone.now()
            time_difference = now - self.first_displayed_at
            
            # If the notification was first displayed within the last 24 hours, show the time
            if time_difference < timedelta(hours=24):
                return self.first_displayed_at.strftime('%I:%M %p')  # Format as HH:MM AM/PM

            # Otherwise, show the date
            return self.first_displayed_at.strftime('%b %d, %Y')  # Format as e.g., Sep 11, 2024
        
        # If `first_displayed_at` is not set, return None
        return None
    def review_indicator(self):
        word_count = len(self.review.split()) if self.review else 0
        indicator=True if word_count < 25 else False
        return indicator
    
class Prep_Questions(models.Model):
    questioner= models.ForeignKey(
                            User,
                            verbose_name=_("questioner"),
                            related_name="questioner",
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,
                            limit_choices_to=Q(category__in=[1, 3, 4, 5, 6, 7]) | Q(is_staff=True)| Q(is_superuser=True)  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
                           )
    position= models.CharField(max_length=100, choices=JobRoles.CAT_CHOICES,null=True,blank=True)
    category=models.CharField(max_length=100, choices=JobRole.QUESTION_CHOICES,null=True,blank=True)
    company=models.CharField(max_length=100,blank=True, null=True)
    question=models.CharField(max_length=500,blank=True, null=True)
    date = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    response=models.TextField(max_length=1000,blank=True, null=True) 
    is_answered=models.BooleanField(default=False,blank=True, null=True)
    is_active=models.BooleanField(default=False,blank=True, null=True)
    is_featured=models.BooleanField(default=False,blank=True, null=True)
    is_tech=models.BooleanField(default=False,blank=True, null=True)

    class Meta:
        verbose_name_plural = 'prep_questions'
        ordering = ["date"]
        db_table = 'data_prep_questions'  # Use existing table name from old data app

    def __str__(self):
        return f'{self.id} prep_questions'

class UserAnswerStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Prep_Questions, on_delete=models.CASCADE)
    role = models.CharField(
                                max_length=500,
                                blank=True, null=True,
                                default="Data Analyst"
                             )
    answer = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)
    is_answered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s answer for Question {self.question.id}"

    class Meta:
        db_table = 'data_useranswerstatus'  # Use existing table name from old data app

    
# # ==================================BACKGROUND CHECKS====================================
class BackgroundCheck(models.Model):
    id = models.AutoField(primary_key=True)
    candidate =models.ForeignKey(
                            User,
                            # verbose_name=_("candidate"),
                            # related_name="candidate",
                            # null=True,
                            # blank=True,
                            on_delete=models.CASCADE,
                            # default=1,
                            # limit_choices_to=Q(is_client=True) | Q(is_staff=True)| Q(is_superuser=True)
                           )
    end_client= models.CharField(max_length=255)
    role= models.CharField(max_length=255)
    recruiting_agency= models.CharField(max_length=255)
    job_offer_letter= models.CharField(max_length=255)
    academic_documents= models.CharField(max_length=255)
    hiring_company= models.CharField(max_length=255)
    education_level= models.CharField(max_length=255)
    past_employers= models.CharField(max_length=255)
    reference_contacts= models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, In Progress, Completed
    
    def __str__(self):
        return f'{self.end_client}'

    class Meta:
        db_table = 'data_backgroundcheck'  # Use existing table name from old data app
    
class JobDetails(models.Model):
    background_check = models.ForeignKey(BackgroundCheck, on_delete=models.CASCADE, related_name='job_details')
    job_offer_letter = models.FileField(upload_to='job_offers/')
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f'Job Details for {self.background_check.candidate}'

    class Meta:
        db_table = 'data_jobdetails'  # Use existing table name from old data app
    
class Correct_answers(models.Model):
    SECTION_CHOICES = [
        ('performance', 'performance'),
        ('testing', 'testing'),
        ('Project Story', 'Project Story'),
        ('methodology', 'methodology'),
        ('sdlc', 'sdlc'),
    ]
    section = models.CharField(max_length=50, choices=SECTION_CHOICES,default='performance')  # Section name (e.g., Performance, Testing)
    categories = models.CharField(max_length=255 ,null= True)  # Category within the section (e.g., tableau, Description, Challenges)
    content = models.TextField(null=True) 
    def __str__(self):
        return f"{self.section} - {self.categories}"
    
    class Meta:
        db_table = 'data_correct_answers'  # Use existing table name from old data app
  
class FeaturedCategory(models.Model):
    # Job Category.
    Course_Overview = "Course Overview"
    Planning = "Initiation & Planning"
    Development = "Development"
    Testing = "Testing"
    Deployment = "Deployment"
    # VIDEOS = "VIDEOS"
    # POWER_POINTS = "POWER POINTS"
    Other = "Other"

    CAT_CHOICES = [
        (Course_Overview, "Course Overview"),
        (Planning, "Initiation & Planning"),
        (Development, "Development"),
        (Testing, "Testing"),
        # (VIDEOS, "VIDEOS"),
        # (POWER_POINTS, "POWER POINTS"),
        (Deployment, "Deployment"),
        (Other, "Other"),
    ]

    title = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        unique=True,
        default=Other,
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.IntegerField(default=1)

    objects=CategoryManager()

    class Meta:
        db_table = 'data_featuredcategory'  # Use existing table name from old data app
        verbose_name_plural = "Categories"

    @classmethod
    def get_default_pk(cls):
        cat, created = cls.objects.get_or_create(
            title=" ", defaults=dict(description="this is not an cat")
        )
        return cat.pk

    # def get_absolute_url(self):
    #     return reverse("bitraining")

    def get_url(self):
        return reverse("professional_services:category-detail", args=[self.title])

    def __str__(self):
        return self.title


class FeaturedSubCategory(models.Model):
    featuredcategory = models.ForeignKey(
        to=FeaturedCategory,
        on_delete=models.CASCADE,
        default=FeaturedCategory.get_default_pk,
    )
    order = models.IntegerField(blank=True, null=True)
    # category = models.ManyToManyField(Cat, blank=True,related_name='cats')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(default="General")
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    # is_active = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    objects=SubCategoryManager()

    class Meta:
        db_table = 'data_featuredsubcategory'  # Fixed: actual table name
        verbose_name_plural = "Subcategories"

    # def get_absolute_url(self):
        # return reverse('professional_services:subcategory-detail', kwargs={'title': self.title})
    
    def subcat_url(self):
        return reverse("professional_services:subcategory-detail", args=[self.title])

    def __str__(self):
        return self.title
    def __str__(self):
        return f"{self.title} - {self.featuredcategory}"
    
class FeaturedActivity(models.Model):
    # SubCategory = models.ForeignKey(to=SubCategory, on_delete=models.CASCADE,default=SubCategory.get_default_pk)
    featuredsubcategory = models.ManyToManyField(
        FeaturedSubCategory, blank=True, related_name="subcategories_fetured"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_name = models.CharField(max_length=255)
    # slug = models.SlugField(max_length=255, blank=True, default="slug")
    description = models.TextField()
    guiding_question = models.TextField(blank=True,null=True)
    interview_question = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.IntegerField(default=1)

    objects=ActivityManager()

    class Meta:
        db_table = 'data_featuredactivity'  # Fixed: actual table name
        verbose_name_plural = "activities"
    
    def activity_url(self):
        return reverse("professional_services:activity-detail", args=[self.slug])

    @property
    def question(self):
        if self.guiding_question != None:
            available_question=self.guiding_question
            return available_question

    def __str__(self):
        return self.activity_name

class ActivityLinks(models.Model):
    Activity = models.ManyToManyField(
        FeaturedActivity, blank=True, related_name="activity_featured"
    )
    Featuredsubcategory = models.ForeignKey(
        FeaturedSubCategory, 
        blank=True, 
        null=True, 
        on_delete=models.SET_NULL,
        related_name="subcategorie_fetured"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    link_name = models.CharField(max_length=255, default="General")
    # description=models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    doc = models.FileField(default="None", upload_to="training/docs/")
    link = models.CharField(max_length=1000, blank=True, null=True)
    is_active = models.IntegerField(default=1)

    class Meta:
        db_table = 'data_activitylinks'  # Fixed: actual table name
        verbose_name_plural = "links"

    def get_absolute_url(self):
        return reverse("bitraining")

    def get_link_url(self):
        return self.link

    def __str__(self):
        return self.link_name


# class UserLevel(models.Model):
#     # Levels
#     A = "Level A"
#     B = "Level B"
#     C = "Level C"
#     D = "Level D"
#     E = "Level E"
#     O = "Other"

#     LEVEL_CHOICES = [
#         (A, "Level A"),
#         (B, "Level B"),
#         (C, "Level C"),
#         (D, "Level D"),
#         (E, "Level E"),
#         (O, "Other"),
#     ]

#     level = models.CharField(
#         max_length=25,
#         choices=LEVEL_CHOICES,
#         unique=True,
#         default=A,
#     )
#     created_by = models.ForeignKey(User, on_delete=models.CASCADE)
#     description = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     is_active = models.IntegerField(default=1)

#     class Meta:
#         verbose_name_plural = "levels"

#     def get_absolute_url(self):
#         return reverse("bitraining")

#     def __str__(self):
#         return self.level


class DSU(models.Model):
    # Job Category.
    Interview = "Interview"
    BI_Training = "BI Training"
    Job_Support = "Job Support"
    Other = "Other"

    CAT_CHOICES = [
        (Interview, "Interview"),
        (BI_Training, "BI Training"),
        (Job_Support, "Job Support"),
        (Other, "Other"),
    ]
    # Client/Employee
    client = "client"
    Staff = "Staff"
    Other = "Other"

    TYPE_CHOICES = [
        (client, "client"),
        (Staff, "Staff"),
        (Other, "Other"),
    ]
    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default=Other,
    )
    type = models.CharField(
        max_length=25,
        choices=TYPE_CHOICES,
        default=Other,
    )
    trained_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=Q(is_staff=True)
        | Q(category__in=[1, 3, 4, 5, 6, 7])  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        | Q(is_admin=True)
        | Q(is_superuser=True),
    )
    subcategory = models.CharField(max_length=255, default="data")
    client_name = models.CharField(max_length=255, default="admin")
    task = models.TextField()
    plan = models.TextField()
    challenge = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded = models.BooleanField(default=False)
    cohort = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'data_dsu'  # Use existing table name from old data app
        verbose_name_plural = "DSU"

    def get_absolute_url(self):
        return reverse("professional_services:bitraining")

    def __str__(self):
        return self.category


class ClientAssessment(models.Model):
    # Job Category.
    CAT_CHOICES = [
        ("Interview", "Interview"),
        ("BI Training", "BI Training"),
        ("Job Support", "Job Support"),
        ("Other", "Other"),
    ]
    # Education Level .
    EDU_CHOICES = [
        ("Degree", "Degree"),
        ("Some College", "Some College"),
        ("High School", "High School"),
        ("Other", "Other"),
    ]
    TYPE_CHOICES = [
        ("client", "client"),
        ("Staff", "Staff"),
        ("Other", "Other"),
    ]
    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="Other",
    )
    type = models.CharField(
        max_length=25,
        choices=TYPE_CHOICES,
        default="Other",
    )
    education = models.CharField(
        max_length=25,
        choices=EDU_CHOICES,
        default="Other",
    )
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    education = models.CharField(
        max_length=25,
        choices=EDU_CHOICES,
        default="Other",
    )
    rating_date = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    skills = models.TextField(default="word,excel,powerpoints and data tools etc")
    experience = models.TextField(default="Tell us more on your experience(internships,projects,current work etc)")
    non_it_exp = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 2
    it_exp = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 2
    projectmanagement = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 2
    requirementsAnalysis  = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 3
    reporting = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 5
    etl = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 5
    database = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 5
    testing = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 3
    deployment = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 2
    frontend = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 5
    backend = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])# 5
    totalpoints = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id} ClientAsessment"

    class Meta:
        db_table = 'data_clientassessment'  # Fixed: actual table name from database


class Job_Tracker(models.Model):
    # Job Status.
    screening_call = "screening call"
    first_interview = "1st interview"
    second_interview = "2nd interview"
    third_interview = "3rd interview"
    Other = "Other"
    STATUS_CHOICES = [
        (screening_call, "screening call"),
        (first_interview, "1st interview"),
        (second_interview, "2nd interview"),
        (third_interview, "3rd interview"),
        (Other, "Other"),
    ]
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, blank=True, null=True)
    recruiter = models.CharField(max_length=100, blank=True, null=True)
    vendor_phone = models.CharField(max_length=100, blank=True, null=True)
    primary_tool = models.CharField(max_length=100, blank=True, null=True)
    secondary_tool = models.CharField(max_length=100, blank=True, null=True)
    job_location = models.CharField(max_length=100, blank=True, null=True)
    offer = models.DecimalField(
        max_digits=10,
        error_messages={
            "name": {" max_length": ("The earning must be between 0 and 4999.99")}
        },
        decimal_places=2,
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="other")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_resume = models.FileField(default="None", upload_to="training/docs/")
    resume_url=models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'data_job_tracker'  # Use existing table name from old data app
        verbose_name_plural = "jobs"

    def get_absolute_url(self):
        return reverse("jobtracker")

    def __str__(self):
        return self.position


class TrainingResponsesTracking(models.Model):
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    featuredsubcategory = models.ForeignKey(FeaturedSubCategory, on_delete=models.CASCADE)
    course_overview = models.CharField(max_length=254, null=True, blank=True)

    class Meta:
        db_table = 'data_training_responses_tracking'  # Use existing table name from old data app

    def __str__(self):
        return str(self.user)