from django.contrib import admin
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html

from .models import (Policy, 
                     Rated, 
                     Reporting,
                     Trainee_Assessment,
                     Topic,
                     ApplicationWorkflow,
                     WorkflowStatusLog,
                     WorkflowCriteria)

# Register your models here.
admin.site.register(Rated)
admin.site.register(Policy)
admin.site.register(Reporting)
admin.site.register(Trainee_Assessment)
admin.site.register(Topic)


@admin.register(ApplicationWorkflow)
class ApplicationWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_username',
        'status',
        'promotion_type',
        'skills_score_display',
        'documents_completed',
        'interview_completed',
        'admin_approval',
        'workflow_duration',
        'applied_date',
    ]
    
    list_filter = [
        'status',
        'promotion_type',
        'documents_completed',
        'interview_completed',
        'admin_approval',
        'applied_date',
    ]
    
    search_fields = [
        'applicant__username',
        'applicant__first_name',
        'applicant__last_name',
        'applicant__email',
    ]
    
    readonly_fields = [
        'applied_date',
        'last_status_change',
        'completed_date',
        'workflow_duration_days',
        'is_eligible_for_promotion',
    ]
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant', 'status', 'promotion_type')
        }),
        ('Criteria Tracking', {
            'fields': (
                'documents_completed',
                'skills_assessment_score',
                'interview_completed',
                'admin_approval',
            )
        }),
        ('Scoring Thresholds', {
            'fields': ('min_skills_score', 'min_interview_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'applied_date',
                'last_status_change',
                'completed_date',
                'workflow_duration_days',
            ),
            'classes': ('collapse',)
        }),
        ('Admin Information', {
            'fields': ('reviewed_by', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def applicant_username(self, obj):
        return obj.applicant.username
    applicant_username.short_description = 'Applicant'
    
    def skills_score_display(self, obj):
        score = obj.skills_assessment_score
        min_score = obj.min_skills_score
        if score >= min_score:
            return format_html(
                '<span style="color: green;">{}/{} ✓</span>',
                score, min_score
            )
        else:
            return format_html(
                '<span style="color: red;">{}/{} ✗</span>',
                score, min_score
            )
    skills_score_display.short_description = 'Skills Score'
    
    def workflow_duration(self, obj):
        days = obj.workflow_duration_days
        if days <= 7:
            color = 'green'
        elif days <= 14:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} days</span>',
            color, days
        )
    workflow_duration.short_description = 'Duration'
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """Bulk approve selected workflows"""
        approved_count = 0
        for workflow in queryset:
            if workflow.status == ApplicationWorkflow.WorkflowStatus.FINAL_REVIEW:
                workflow.applicant.is_staff = True
                workflow.applicant.save()
                workflow.advance_status(
                    ApplicationWorkflow.WorkflowStatus.EMPLOYEE,
                    request.user,
                    "Bulk approval from admin"
                )
                approved_count += 1
        
        self.message_user(
            request,
            f"Successfully approved {approved_count} applications."
        )
    approve_selected.short_description = "Approve selected applications"
    
    def reject_selected(self, request, queryset):
        """Bulk reject selected workflows"""
        rejected_count = 0
        for workflow in queryset:
            if workflow.status != ApplicationWorkflow.WorkflowStatus.REJECTED:
                workflow.advance_status(
                    ApplicationWorkflow.WorkflowStatus.REJECTED,
                    request.user,
                    "Bulk rejection from admin"
                )
                rejected_count += 1
        
        self.message_user(
            request,
            f"Successfully rejected {rejected_count} applications."
        )
    reject_selected.short_description = "Reject selected applications"


@admin.register(WorkflowStatusLog)
class WorkflowStatusLogAdmin(admin.ModelAdmin):
    list_display = [
        'workflow_applicant',
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
    ]
    
    list_filter = [
        'new_status',
        'changed_at',
        'changed_by',
    ]
    
    search_fields = [
        'workflow__applicant__username',
        'workflow__applicant__first_name',
        'workflow__applicant__last_name',
    ]
    
    readonly_fields = ['changed_at']
    
    def workflow_applicant(self, obj):
        return obj.workflow.applicant.username
    workflow_applicant.short_description = 'Applicant'


@admin.register(WorkflowCriteria)
class WorkflowCriteriaAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'criteria_type',
        'min_value',
        'max_value',
        'required',
        'is_active',
    ]
    
    list_filter = [
        'criteria_type',
        'required',
        'is_active',
    ]
    
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Criteria Information', {
            'fields': ('name', 'criteria_type', 'description')
        }),
        ('Values', {
            'fields': ('min_value', 'max_value', 'required')
        }),
        ('Configuration', {
            'fields': ('is_active',)
        }),
    )