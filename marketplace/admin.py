from django.contrib import admin
from .models import BusinessProfile, InvestmentOpportunity, JobOpportunity, JobApplication, SavedItem


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'industry', 'funding_stage', 'profile_views', 'created_at')
    list_filter = ('industry', 'funding_stage', 'company_size', 'created_at')
    search_fields = ('company_name', 'user__username', 'user__email', 'industry')
    readonly_fields = ('profile_views', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'company_name', 'industry', 'company_size', 'founded_date')
        }),
        ('Financial Information', {
            'fields': ('investment_seeking', 'equity_offered', 'funding_stage', 'annual_revenue')
        }),
        ('Documents', {
            'fields': ('business_plan', 'pitch_deck', 'financial_statements'),
            'classes': ('collapse',)
        }),
        ('Metrics', {
            'fields': ('profile_views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InvestmentOpportunity)
class InvestmentOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'amount_seeking', 'equity_percentage', 'stage', 'status', 'views', 'created_at')
    list_filter = ('status', 'stage', 'industry', 'investment_type', 'created_at')
    search_fields = ('title', 'business__username', 'description', 'industry')
    readonly_fields = ('slug', 'views', 'saves', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('business', 'title', 'slug', 'description')
        }),
        ('Investment Details', {
            'fields': ('amount_seeking', 'minimum_investment', 'equity_percentage', 'investment_type')
        }),
        ('Categorization', {
            'fields': ('industry', 'stage')
        }),
        ('Status & Timing', {
            'fields': ('status', 'deadline')
        }),
        ('Metrics', {
            'fields': ('views', 'saves', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobOpportunity)
class JobOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'job_type', 'experience_level', 'location', 'status', 'applications_count', 'views', 'created_at')
    list_filter = ('status', 'job_type', 'experience_level', 'remote_option', 'created_at')
    search_fields = ('title', 'business__username', 'description', 'location')
    readonly_fields = ('slug', 'views', 'applications_count', 'saves', 'posted_date', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('business', 'title', 'slug', 'description')
        }),
        ('Job Details', {
            'fields': ('requirements', 'responsibilities', 'job_type', 'experience_level', 'location', 'remote_option')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency')
        }),
        ('Status & Timing', {
            'fields': ('status', 'posted_date', 'deadline')
        }),
        ('Metrics', {
            'fields': ('views', 'applications_count', 'saves', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__username', 'applicant__email', 'job__title', 'cover_letter')
    readonly_fields = ('applied_at', 'updated_at')
    date_hierarchy = 'applied_at'
    fieldsets = (
        ('Application Info', {
            'fields': ('job', 'applicant', 'status')
        }),
        ('Application Materials', {
            'fields': ('cover_letter', 'resume', 'portfolio_url')
        }),
        ('Employer Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'content_object', 'saved_at')
    list_filter = ('content_type', 'saved_at')
    search_fields = ('user__username', 'note')
    readonly_fields = ('saved_at',)
    date_hierarchy = 'saved_at'
