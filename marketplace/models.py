from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from decimal import Decimal


class BusinessProfile(models.Model):
    """Extended profile for Business category users"""
    
    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('500+', '500+ employees'),
    ]
    
    FUNDING_STAGE_CHOICES = [
        ('idea', 'Idea Stage'),
        ('seed', 'Seed'),
        ('series_a', 'Series A'),
        ('series_b', 'Series B'),
        ('series_c', 'Series C+'),
        ('profitable', 'Profitable'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, default='1-10')
    founded_date = models.DateField(null=True, blank=True)
    investment_seeking = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Amount seeking in USD")
    equity_offered = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))], help_text="Equity %")
    funding_stage = models.CharField(max_length=20, choices=FUNDING_STAGE_CHOICES, default='idea')
    annual_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Annual revenue USD")
    business_plan = models.FileField(upload_to='business_documents/plans/', null=True, blank=True)
    pitch_deck = models.FileField(upload_to='business_documents/pitch_decks/', null=True, blank=True)
    financial_statements = models.FileField(upload_to='business_documents/financials/', null=True, blank=True)
    profile_views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profiles"
    
    def __str__(self):
        return f"{self.company_name} ({self.user.username})"
    
    def increment_views(self):
        self.profile_views += 1
        self.save(update_fields=['profile_views'])


class InvestmentOpportunity(models.Model):
    """Investment opportunities posted by businesses"""
    
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('funded', 'Funded')]
    INVESTMENT_TYPE_CHOICES = [('equity', 'Equity'), ('debt', 'Debt'), ('convertible', 'Convertible'), ('revenue_share', 'Revenue Share')]
    
    business = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_opportunities')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    amount_seeking = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount seeking USD")
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2, help_text="Min investment USD")
    equity_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))], help_text="Equity %")
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPE_CHOICES, default='equity')
    industry = models.CharField(max_length=100)
    stage = models.CharField(max_length=20, choices=BusinessProfile.FUNDING_STAGE_CHOICES, default='seed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    deadline = models.DateField(null=True, blank=True)
    views = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Investment Opportunity"
        verbose_name_plural = "Investment Opportunities"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            counter = 1
            original_slug = self.slug
            while InvestmentOpportunity.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class JobOpportunity(models.Model):
    """Job opportunities posted by businesses"""
    
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('filled', 'Filled')]
    JOB_TYPE_CHOICES = [('full_time', 'Full-time'), ('part_time', 'Part-time'), ('contract', 'Contract'), ('internship', 'Internship'), ('freelance', 'Freelance')]
    EXPERIENCE_LEVEL_CHOICES = [('entry', 'Entry'), ('mid', 'Mid'), ('senior', 'Senior'), ('lead', 'Lead'), ('executive', 'Executive')]
    
    business = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_opportunities')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    requirements = models.TextField(help_text="Required skills")
    responsibilities = models.TextField(help_text="Job responsibilities")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='mid')
    location = models.CharField(max_length=255)
    remote_option = models.BooleanField(default=False)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    views = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Job Opportunity"
        verbose_name_plural = "Job Opportunities"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            counter = 1
            original_slug = self.slug
            while JobOpportunity.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class JobApplication(models.Model):
    """Job applications submitted by individuals"""
    
    STATUS_CHOICES = [('pending', 'Pending'), ('reviewing', 'Reviewing'), ('shortlisted', 'Shortlisted'), ('interview', 'Interview'), ('offered', 'Offered'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn')]
    
    job = models.ForeignKey(JobOpportunity, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='job_applications/resumes/')
    portfolio_url = models.URLField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"
        ordering = ['-applied_at']
        unique_together = ['job', 'applicant']
    
    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"


class SavedItem(models.Model):
    """Generic saved items for users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    note = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Saved Item"
        verbose_name_plural = "Saved Items"
        ordering = ['-saved_at']
        unique_together = ['user', 'content_type', 'object_id']
    
    def __str__(self):
        return f"{self.user.username} saved {self.content_object}"
