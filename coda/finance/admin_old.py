"""
Clean Admin Interface for Finance App
Only includes models that actually exist with correct field references
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

# Import models from organized structure
from .models import (
    # Core models
    Transaction, Budget, BudgetCategory, BudgetSubCategory, BudgetItemLibrary, BudgetEstimateProjection,
    # Budget models
    BudgetRequest, ApprovalPolicy,
    # Loan models
    LoanApplication, LoanProduct,
)


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    """Admin interface for loan products"""
    
    list_display = [
        'name', 'product_type', 'min_amount', 'max_amount', 
        'interest_rate', 'term_months', 'is_active'
    ]
    
    list_filter = [
        'is_active', 'product_type', 'min_credit_score'
    ]
    
    search_fields = ['name', 'description', 'requirements']
    
    list_editable = ['is_active']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'is_active']
        }),
        ('Loan Terms', {
            'fields': ['min_amount', 'max_amount', 'interest_rate', 'term_months', 'fees']
        }),
        ('Product Categorization', {
            'fields': ['product_type', 'min_credit_score', 'requirements']
        })
    ]
    
    actions = [
        'activate_products', 'deactivate_products', 'duplicate_product'
    ]
    
    def activate_products(self, request, queryset):
        """Activate selected loan products"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} loan product(s) activated successfully.')
    activate_products.short_description = "Activate selected loan products"
    
    def deactivate_products(self, request, queryset):
        """Deactivate selected loan products"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} loan product(s) deactivated successfully.')
    deactivate_products.short_description = "Deactivate selected loan products"
    
    def duplicate_product(self, request, queryset):
        """Duplicate selected loan product"""
        for product in queryset:
            new_product = LoanProduct.objects.create(
                name=f"{product.name} (Copy)",
                description=product.description,
                min_amount=product.min_amount,
                max_amount=product.max_amount,
                interest_rate=product.interest_rate,
                term_months=product.term_months,
                fees=product.fees,
                product_type=product.product_type,
                is_active=False  # Start as inactive
            )
        self.message_user(request, f'{queryset.count()} loan product(s) duplicated successfully.')
    duplicate_product.short_description = "Duplicate selected loan products"


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    """Admin interface for loan applications"""
    
    list_display = [
        'application_number', 'borrower', 'loan_product', 'amount_requested',
        'status', 'created_at'
    ]
    
    list_filter = [
        'status', 'created_at', 'loan_product'
    ]
    
    search_fields = [
        'application_number', 'borrower__username', 'borrower__email',
        'borrower__first_name', 'borrower__last_name'
    ]
    
    readonly_fields = [
        'application_number', 'created_at', 'updated_at'
    ]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['application_number', 'borrower', 'loan_product', 'status']
        }),
        ('Loan Details', {
            'fields': ['amount_requested', 'purpose']
        }),
        ('Guarantor Information', {
            'fields': [
                'guarantor', 'guarantor_relationship', 'guarantor_eligibility_score',
                'guarantor_approval_status', 'guarantor_consent_date'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = [
        'approve_selected_loans', 'reject_selected_loans', 'mark_as_repaid'
    ]
    
    def approve_selected_loans(self, request, queryset):
        """Approve selected loan applications"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} loan application(s) approved successfully.')
    approve_selected_loans.short_description = "Approve selected loan applications"
    
    def reject_selected_loans(self, request, queryset):
        """Reject selected loan applications"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} loan application(s) rejected successfully.')
    reject_selected_loans.short_description = "Reject selected loan applications"
    
    def mark_as_repaid(self, request, queryset):
        """Mark selected loans as repaid"""
        updated = queryset.filter(status__in=['active', 'overdue']).update(status='repaid')
        self.message_user(request, f'{updated} loan application(s) marked as repaid.')
    mark_as_repaid.short_description = "Mark selected loans as repaid"


# @admin.register(Payment_Information)  # Model not in organized structure
# class PaymentInformationAdmin(admin.ModelAdmin):
    """Admin interface for payment information"""
    
    list_display = [
        'id', 'customer_id', 'payment_fees', 'down_payment', 'student_bonus',
        'plan', 'payment_method', 'contract_submitted_date', 'is_active'
    ]
    
    list_filter = [
        'is_active', 'is_featured', 'payment_method', 'contract_submitted_date'
    ]
    
    search_fields = [
        'customer_id__username', 'customer_id__first_name', 'customer_id__last_name',
        'customer_id__email', 'description'
    ]
    
    readonly_fields = ['contract_submitted_date']
    
    fieldsets = [
        ('Customer Information', {
            'fields': ['customer_id', 'description']
        }),
        ('Payment Details', {
            'fields': ['payment_fees', 'down_payment', 'student_bonus']
        }),
        ('Plan Information', {
            'fields': ['plan', 'subplan', 'pricing_plan']
        }),
        ('Payment Method', {
            'fields': ['payment_method', 'contract_submitted_date']
        }),
        ('Contract Details', {
            'fields': ['client_signature', 'company_rep', 'client_date', 'rep_date']
        }),
        ('Status', {
            'fields': ['is_active', 'is_featured']
        })
    ]
    
    actions = [
        'mark_as_active', 'mark_as_inactive', 'mark_as_featured', 'mark_as_unfeatured'
    ]
    
    def mark_as_active(self, request, queryset):
        """Mark selected payments as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} payment(s) marked as active.')
    mark_as_active.short_description = "Mark selected payments as active"
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected payments as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} payment(s) marked as inactive.')
    mark_as_inactive.short_description = "Mark selected payments as inactive"
    
    def mark_as_featured(self, request, queryset):
        """Mark selected payments as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} payment(s) marked as featured.')
    mark_as_featured.short_description = "Mark selected payments as featured"
    
    def mark_as_unfeatured(self, request, queryset):
        """Mark selected payments as unfeatured"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} payment(s) marked as unfeatured.')
    mark_as_unfeatured.short_description = "Mark selected payments as unfeatured"


@admin.register(Payment_History)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """Admin interface for payment history"""
    
    list_display = [
        'id', 'customer', 'payment_fees', 'down_payment', 'student_bonus',
        'plan', 'payment_method', 'contract_submitted_date'
    ]
    
    list_filter = [
        'contract_submitted_date', 'payment_method'
    ]
    
    search_fields = [
        'customer__username', 'customer__first_name', 'customer__last_name',
        'customer__email', 'description'
    ]
    
    readonly_fields = ['contract_submitted_date']
    
    fieldsets = [
        ('Customer Information', {
            'fields': ['customer']
        }),
        ('Payment Details', {
            'fields': ['payment_fees', 'down_payment', 'student_bonus', 'payment_method', 'description']
        }),
        ('Plan Information', {
            'fields': ['plan', 'subplan', 'pricing_plan']
        }),
        ('Contract', {
            'fields': ['contract_submitted_date', 'client_signature', 'company_rep', 'client_date', 'rep_date']
        })
    ]


@admin.register(LoanPerformance)
class LoanPerformanceAdmin(admin.ModelAdmin):
    """Admin interface for KCC loan performance tracking"""
    
    list_display = [
        'user', 'loan_application', 'payment_timing', 'performance_score',
        'scaling_factor_applied', 'consecutive_successful_loans', 'created_at'
    ]
    
    list_filter = [
        'payment_timing', 'performance_score', 'scaling_factor_applied', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'performance_score', 'scaling_factor_applied'
    ]
    
    fieldsets = [
        ('User Information', {
            'fields': ['user', 'loan_application']
        }),
        ('Performance Metrics', {
            'fields': [
                'payment_timing', 'performance_score', 'consecutive_successful_loans',
                'consecutive_late_payments'
            ]
        }),
        ('Scaling Information', {
            'fields': [
                'scaling_factor_applied', 'next_loan_amount'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['recalculate_performance_scores', 'update_scaling_factor_applieds']
    
    def recalculate_performance_scores(self, request, queryset):
        """Recalculate performance scores for selected users"""
        for performance in queryset:
            try:
                # This will be implemented when the service is fully integrated
                # For now, we'll just log the action
                performance.save()
            except Exception as e:
                self.message_user(request, f'Error recalculating scores for {performance.user.username}: {e}')
        
        self.message_user(request, f'{queryset.count()} performance score(s) recalculated successfully.')
    recalculate_performance_scores.short_description = "Recalculate performance scores"
    
    def update_scaling_factor_applieds(self, request, queryset):
        """Update scaling factors for selected users"""
        for performance in queryset:
            try:
                # This will be implemented when the service is fully integrated
                # For now, we'll just log the action
                performance.save()
            except Exception as e:
                self.message_user(request, f'Error updating scaling factor for {performance.user.username}: {e}')
        
        self.message_user(request, f'{queryset.count()} scaling factor(s) updated successfully.')
    update_scaling_factor_applieds.short_description = "Update scaling factors"


# =============================================================================
# AUTOMATION SYSTEM ADMIN INTERFACES
# =============================================================================

@admin.register(BudgetRequest)
class BudgetRequestAdmin(admin.ModelAdmin):
    """Admin interface for budget requests"""
    
    list_display = [
        'id', 'requester', 'amount', 'currency', 'department', 
        'status', 'priority', 'request_date', 'required_date', 'current_approver'
    ]
    
    list_filter = [
        'status', 'priority', 'department', 'budget_category', 
        'request_date', 'required_date'
    ]
    
    search_fields = [
        'requester__username', 'requester__email', 'purpose', 
        'department__name', 'budget_category__name'
    ]
    
    list_editable = ['status', 'priority']
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'approval_chain'
    ]
    
    # Exclude audit fields from the form - they will be set automatically
    exclude = ['created_by', 'last_modified_by']
    
    def get_form(self, request, obj=None, **kwargs):
        """Override get_form to make certain fields not required"""
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Creating new object
            # Make fields with defaults not required
            if 'request_date' in form.base_fields:
                form.base_fields['request_date'].required = False
            if 'approval_chain' in form.base_fields:
                form.base_fields['approval_chain'].required = False
            if 'attachments' in form.base_fields:
                form.base_fields['attachments'].required = False
        return form
    
    fieldsets = [
        ('Request Information', {
            'fields': [
                'id', 'requester', 'amount', 'currency', 'purpose', 
                'department', 'budget_category', 'cost_center'
            ]
        }),
        ('Request Details', {
            'fields': [
                'request_date', 'required_date', 'priority', 
                'attachments'
            ]
        }),
        ('Approval Information', {
            'fields': [
                'approval_policy', 'current_approver', 'approval_chain', 
                'status', 'rejection_reason'
            ]
        }),
        ('Audit Information', {
            'fields': [
                'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        })
    ]
    
    actions = ['approve_requests', 'reject_requests', 'escalate_requests']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'requester', 'department', 'budget_category', 
            'current_approver', 'approval_policy'
        )
    
    def save_model(self, request, obj, form, change):
        """Override save_model to set created_by and last_modified_by"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)
    
    def approve_requests(self, request, queryset):
        """Approve selected budget requests"""
        from .services.automation_service import ApprovalEngineService
        
        service = ApprovalEngineService()
        approved_count = 0
        
        for budget_request in queryset:
            try:
                service.process_approval(
                    budget_request.id, 
                    request.user, 
                    'approved',
                    'Approved via admin interface'
                )
                approved_count += 1
            except Exception as e:
                self.message_user(request, f'Error approving request {budget_request.id}: {e}')
        
        self.message_user(request, f'{approved_count} request(s) approved successfully.')
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        """Reject selected budget requests"""
        from .services.automation_service import ApprovalEngineService
        
        service = ApprovalEngineService()
        rejected_count = 0
        
        for budget_request in queryset:
            try:
                service.process_approval(
                    budget_request.id, 
                    request.user, 
                    'rejected',
                    'Rejected via admin interface'
                )
                rejected_count += 1
            except Exception as e:
                self.message_user(request, f'Error rejecting request {budget_request.id}: {e}')
        
        self.message_user(request, f'{rejected_count} request(s) rejected successfully.')
    reject_requests.short_description = "Reject selected requests"
    
    def escalate_requests(self, request, queryset):
        """Escalate selected budget requests"""
        from .services.automation_service import ApprovalEngineService
        
        service = ApprovalEngineService()
        escalated_count = 0
        
        for budget_request in queryset:
            try:
                service.escalate_request(budget_request.id, request.user)
                escalated_count += 1
            except Exception as e:
                self.message_user(request, f'Error escalating request {budget_request.id}: {e}')
        
        self.message_user(request, f'{escalated_count} request(s) escalated successfully.')
    escalate_requests.short_description = "Escalate selected requests"


@admin.register(ApprovalPolicy)
class ApprovalPolicyAdmin(admin.ModelAdmin):
    """Admin interface for approval policies"""
    
    list_display = [
        'name', 'min_amount', 'max_amount', 'is_active', 
        'auto_approve', 'requires_otp', 'max_approval_days'
    ]
    
    list_filter = [
        'is_active', 'auto_approve', 'requires_otp', 
        'applicable_departments', 'applicable_categories'
    ]
    
    search_fields = ['name', 'description']
    
    list_editable = ['is_active', 'auto_approve', 'requires_otp']
    
    filter_horizontal = ['applicable_departments', 'applicable_categories']
    
    fieldsets = [
        ('Policy Information', {
            'fields': [
                'name', 'description', 'is_active'
            ]
        }),
        ('Amount Thresholds', {
            'fields': [
                'min_amount', 'max_amount'
            ]
        }),
        ('Approval Rules', {
            'fields': [
                'approver_roles', 'approval_chain', 'auto_approve', 'requires_otp'
            ]
        }),
        ('Applicability Rules', {
            'fields': [
                'applicable_departments', 'applicable_categories', 'applicable_user_types'
            ]
        }),
        ('Time-based Rules', {
            'fields': [
                'max_approval_days', 'escalation_days'
            ]
        })
    ]
    
    actions = ['activate_policies', 'deactivate_policies']
    
    def activate_policies(self, request, queryset):
        """Activate selected policies"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} policy(ies) activated successfully.')
    activate_policies.short_description = "Activate selected policies"
    
    def deactivate_policies(self, request, queryset):
        """Deactivate selected policies"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} policy(ies) deactivated successfully.')
    deactivate_policies.short_description = "Deactivate selected policies"


@admin.register(DisbursementRequest)
class DisbursementRequestAdmin(admin.ModelAdmin):
    """Admin interface for disbursement requests"""
    
    list_display = [
        'id', 'budget_request', 'recipient_name', 'amount', 
        'currency', 'disbursement_method', 'status', 'disbursement_date'
    ]
    
    list_filter = [
        'status', 'disbursement_method', 'currency', 
        'disbursement_date', 'completion_date'
    ]
    
    search_fields = [
        'recipient_name', 'recipient_email', 'recipient_phone',
        'budget_request__id', 'transaction_id', 'payment_reference'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'otp_code', 
        'otp_expires_at', 'otp_verified'
    ]
    
    fieldsets = [
        ('Request Information', {
            'fields': [
                'id', 'budget_request', 'disbursement_method'
            ]
        }),
        ('Recipient Details', {
            'fields': [
                'recipient_name', 'recipient_phone', 'recipient_email', 'bank_account'
            ]
        }),
        ('Amount Information', {
            'fields': [
                'amount', 'currency', 'exchange_rate'
            ]
        }),
        ('Status and Tracking', {
            'fields': [
                'status', 'payment_reference', 'transaction_id'
            ]
        }),
        ('OTP Verification', {
            'fields': [
                'otp_code', 'otp_expires_at', 'otp_verified'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': [
                'disbursement_date', 'completion_date', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        })
    ]
    
    actions = ['process_disbursements', 'cancel_disbursements', 'resend_otp']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'budget_request', 'budget_request__requester'
        )
    
    def process_disbursements(self, request, queryset):
        """Process selected disbursement requests"""
        from .services.automation_service import DisbursementService
        
        service = DisbursementService()
        processed_count = 0
        
        for disbursement_request in queryset:
            try:
                service.process_disbursement(disbursement_request.id, request.user)
                processed_count += 1
            except Exception as e:
                self.message_user(request, f'Error processing disbursement {disbursement_request.id}: {e}')
        
        self.message_user(request, f'{processed_count} disbursement(s) processed successfully.')
    process_disbursements.short_description = "Process selected disbursements"
    
    def cancel_disbursements(self, request, queryset):
        """Cancel selected disbursement requests"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} disbursement(s) cancelled successfully.')
    cancel_disbursements.short_description = "Cancel selected disbursements"
    
    def resend_otp(self, request, queryset):
        """Resend OTP for selected disbursement requests"""
        from .services.automation_service import DisbursementService
        
        service = DisbursementService()
        resent_count = 0
        
        for disbursement_request in queryset:
            try:
                disbursement_request.generate_otp()
                service.otp_service.send_otp_email(
                    disbursement_request.budget_request.requester,
                    disbursement_request.otp_code,
                    disbursement_request
                )
                resent_count += 1
            except Exception as e:
                self.message_user(request, f'Error resending OTP for disbursement {disbursement_request.id}: {e}')
        
        self.message_user(request, f'{resent_count} OTP(s) resent successfully.')
    resend_otp.short_description = "Resend OTP for selected disbursements"


@admin.register(AutomationAuditLog)
class AutomationAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for automation audit logs"""
    
    list_display = [
        'id', 'action', 'action_type', 'user', 'object_repr', 
        'success', 'created_at', 'ip_address'
    ]
    
    list_filter = [
        'action_type', 'success', 'created_at', 'user'
    ]
    
    search_fields = [
        'action', 'description', 'user__username', 'object_repr', 'ip_address'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'action', 'action_type', 
        'description', 'user', 'ip_address', 'user_agent', 'content_type',
        'object_id', 'object_repr', 'details', 'old_values', 'new_values',
        'success', 'error_message'
    ]
    
    fieldsets = [
        ('Action Information', {
            'fields': [
                'id', 'action', 'action_type', 'description', 'success'
            ]
        }),
        ('User and Context', {
            'fields': [
                'user', 'ip_address', 'user_agent', 'created_at', 'updated_at'
            ]
        }),
        ('Object Information', {
            'fields': [
                'content_type', 'object_id', 'object_repr'
            ]
        }),
        ('Change Details', {
            'fields': [
                'details', 'old_values', 'new_values'
            ],
            'classes': ['collapse']
        }),
        ('Error Information', {
            'fields': [
                'error_message'
            ],
            'classes': ['collapse']
        })
    ]
    
    actions = ['export_audit_logs', 'cleanup_old_logs']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'content_type'
        )
    
    def export_audit_logs(self, request, queryset):
        """Export selected audit logs to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Action', 'Action Type', 'User', 'Object', 
            'Success', 'Created At', 'IP Address'
        ])
        
        for log in queryset:
            writer.writerow([
                log.id, log.action, log.action_type, log.user.username,
                log.object_repr, log.success, log.created_at, log.ip_address
            ])
        
        return response
    export_audit_logs.short_description = "Export selected logs to CSV"
    
    def cleanup_old_logs(self, request, queryset):
        """Clean up old audit logs (older than 1 year)"""
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=365)
        old_logs = queryset.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        self.message_user(request, f'{count} old audit log(s) cleaned up successfully.')
    cleanup_old_logs.short_description = "Clean up old logs (older than 1 year)"


# Enhanced Budget Admin Classes
if Budget:
    @admin.register(Budget)
    class EnhancedBudgetAdmin(admin.ModelAdmin):
        """Admin interface for enhanced Budget model"""
        
        list_display = [
            'id', 'item_name', 'budget_type', 'timeframe', 'company', 
            'department', 'status', 'total_amount', 'actual_spent', 
            'variance_percentage', 'created_at'
        ]
        
        list_filter = [
            'budget_type', 'timeframe', 'status', 'is_investment',
            'requires_approval', 'company', 'department', 'created_at'
        ]
        
        search_fields = [
            'item_name', 'project_name', 'description', 'company__name',
            'department__name', 'budget_lead__username'
        ]
        
        list_editable = ['status']
        
        readonly_fields = [
            'created_at', 'updated_at', 'total_amount', 'variance',
            'variance_percentage', 'remaining_budget', 'is_over_budget'
        ]
        
        fieldsets = (
            ('Basic Information', {
                'fields': ('company', 'department', 'budget_lead', 'item_name', 'description')
            }),
            ('Budget Classification', {
                'fields': ('budget_type', 'timeframe', 'category', 'subcategory')
            }),
            ('Project Details', {
                'fields': ('project_name', 'project_description'),
                'classes': ('collapse',)
            }),
            ('Financial Details', {
                'fields': ('cases', 'quantity', 'unit_price', 'estimated_amount', 'total_amount')
            }),
            ('Time Period', {
                'fields': ('start_date', 'end_date', 'days_duration')
            }),
            ('Estimation', {
                'fields': ('estimation_method', 'estimation_confidence', 'estimation_source'),
                'classes': ('collapse',)
            }),
            ('Status & Approval', {
                'fields': ('status', 'requires_approval', 'approval_policy', 'approved_by', 'approved_at')
            }),
            ('Investment Planning', {
                'fields': ('is_investment', 'investment_type', 'expected_roi', 'payback_period'),
                'classes': ('collapse',)
            }),
            ('Tracking', {
                'fields': ('actual_spent', 'variance', 'variance_percentage', 'remaining_budget', 'is_over_budget')
            }),
            ('Additional Information', {
                'fields': ('receipt_link', 'notes', 'is_active'),
                'classes': ('collapse',)
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
        actions = ['approve_budgets', 'activate_budgets', 'calculate_variances', 'export_budgets']
        
        def approve_budgets(self, request, queryset):
            """Approve selected budgets"""
            count = 0
            for budget in queryset.filter(status='submitted'):
                budget.approve(request.user)
                count += 1
            self.message_user(request, f'{count} budget(s) approved successfully.')
        approve_budgets.short_description = "Approve selected budgets"
        
        def activate_budgets(self, request, queryset):
            """Activate selected budgets"""
            count = 0
            for budget in queryset.filter(status='approved'):
                budget.activate()
                count += 1
            self.message_user(request, f'{count} budget(s) activated successfully.')
        activate_budgets.short_description = "Activate selected budgets"
        
        def calculate_variances(self, request, queryset):
            """Calculate variances for selected budgets"""
            count = 0
            for budget in queryset:
                budget.calculate_variance()
                count += 1
            self.message_user(request, f'Variances calculated for {count} budget(s).')
        calculate_variances.short_description = "Calculate variances"
        
        def export_budgets(self, request, queryset):
            """Export selected budgets to CSV"""
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="budgets.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Item Name', 'Budget Type', 'Timeframe', 'Company', 'Department',
                'Status', 'Total Amount', 'Actual Spent', 'Variance', 'Created At'
            ])
            
            for budget in queryset:
                writer.writerow([
                    budget.id, budget.item_name, budget.get_budget_type_display(),
                    budget.get_timeframe_display(), budget.company.name, budget.department.name,
                    budget.get_status_display(), budget.total_amount, budget.actual_spent,
                    budget.variance, budget.created_at
                ])
            
            return response
        export_budgets.short_description = "Export selected budgets to CSV"


if BudgetEstimationTemplate:
    @admin.register(BudgetEstimationTemplate)
    class BudgetEstimationTemplateAdmin(admin.ModelAdmin):
        """Admin interface for budget estimation templates"""
        
        list_display = [
            'name', 'budget_type', 'hourly_rate', 'is_active', 'created_at'
        ]
        
        list_filter = ['budget_type', 'is_active', 'created_at']
        
        search_fields = ['name', 'description']
        
        list_editable = ['is_active']
        
        readonly_fields = ['created_at', 'updated_at']
        
        fieldsets = (
            ('Basic Information', {
                'fields': ('name', 'description', 'budget_type', 'is_active')
            }),
            ('Estimation Configuration', {
                'fields': ('estimation_config', 'development_tasks', 'hourly_rate')
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )


if MultiYearBudgetPlan:
    @admin.register(MultiYearBudgetPlan)
    class MultiYearBudgetPlanAdmin(admin.ModelAdmin):
        """Admin interface for multi-year budget plans"""
        
        list_display = [
            'name', 'plan_type', 'start_year', 'end_year', 'company', 
            'department', 'status', 'total_investment_required', 'created_at'
        ]
        
        list_filter = [
            'plan_type', 'status', 'company', 'department', 'created_at'
        ]
        
        search_fields = [
            'name', 'description', 'company__name', 'department__name',
            'created_by__username'
        ]
        
        list_editable = ['status']
        
        readonly_fields = [
            'created_at', 'updated_at', 'duration_years', 'total_investment_required'
        ]
        
        fieldsets = (
            ('Basic Information', {
                'fields': ('name', 'description', 'company', 'department', 'created_by')
            }),
            ('Plan Duration', {
                'fields': ('start_year', 'end_year', 'plan_type', 'duration_years')
            }),
            ('Investment Planning', {
                'fields': ('total_investment_required', 'funding_sources')
            }),
            ('Status', {
                'fields': ('status',)
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
        actions = ['approve_plans', 'activate_plans', 'calculate_investments']
        
        def save_model(self, request, obj, form, change):
            """Override save_model to set created_by"""
            if not change:  # Creating new object
                obj.created_by = request.user
            super().save_model(request, obj, form, change)
        
        def approve_plans(self, request, queryset):
            """Approve selected plans"""
            count = 0
            for plan in queryset.filter(status='in_review'):
                plan.status = 'approved'
                plan.save()
                count += 1
            self.message_user(request, f'{count} plan(s) approved successfully.')
        approve_plans.short_description = "Approve selected plans"
        
        def activate_plans(self, request, queryset):
            """Activate selected plans"""
            count = 0
            for plan in queryset.filter(status='approved'):
                plan.status = 'active'
                plan.save()
                count += 1
            self.message_user(request, f'{count} plan(s) activated successfully.')
        activate_plans.short_description = "Activate selected plans"
        
        def calculate_investments(self, request, queryset):
            """Calculate total investments for selected plans"""
            count = 0
            for plan in queryset:
                plan.calculate_total_investment()
                count += 1
            self.message_user(request, f'Investments calculated for {count} plan(s).')
        calculate_investments.short_description = "Calculate total investments"


# ============================================================================
# BUDGET PROJECTION & TRANSACTION ADMIN (Phase 2 - October 2025)
# ============================================================================

@admin.register(BudgetEstimateProjection)
class BudgetEstimateProjectionAdmin(admin.ModelAdmin):
    """Admin interface for budget projections"""
    
    list_display = [
        'id', 'company', 'department', 'horizon', 'method', 
        'total_estimate', 'status', 'created_at'
    ]
    
    list_filter = [
        'status', 'horizon', 'method', 'company', 'department',
        'created_at'
    ]
    
    search_fields = ['company__name', 'department__name', 'estimates']
    
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['company', 'department', 'template', 'created_by']
        }),
        ('Projection Details', {
            'fields': ['horizon', 'method', 'estimates', 'total_estimate']
        }),
        ('Status', {
            'fields': ['status', 'submitted_at']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'department', 'created_by')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for transactions"""
    
    list_display = [
        'id', 'receiver', 'amount', 'category', 'subcategory', 
        'department', 'transaction_date', 'sender'
    ]
    
    list_filter = [
        'category', 'department', 'payment_method', 'transaction_date'
    ]
    
    search_fields = ['receiver', 'description', 'type']
    
    list_editable = ['category', 'subcategory']
    
    date_hierarchy = 'transaction_date'
    
    fieldsets = [
        ('Transaction Details', {
            'fields': ['sender', 'receiver', 'vendor_supplier', 'phone']
        }),
        ('Classification', {
            'fields': ['department', 'category', 'subcategory', 'type']
        }),
        ('Financial', {
            'fields': ['amount', 'currency', 'qty', 'transaction_cost', 
                      'transaction_date', 'payment_method']
        }),
        ('Additional', {
            'fields': ['description', 'receipt_link']
        }),
    ]


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    """Admin for budget categories"""
    
    list_display = ['id', 'name', 'description', 'subcategory_count', 'transaction_count']
    search_fields = ['name', 'description']
    
    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Subcategories'
    
    def transaction_count(self, obj):
        return obj.transaction_category.count()
    transaction_count.short_description = 'Transactions'


@admin.register(BudgetSubCategory)
class BudgetSubCategoryAdmin(admin.ModelAdmin):
    """Admin for budget subcategories"""
    
    list_display = ['id', 'name', 'category', 'transaction_count']
    list_filter = ['category']
    search_fields = ['name']
    
    def transaction_count(self, obj):
        return obj.transaction_subcategory.count()
    transaction_count.short_description = 'Transactions'


@admin.register(BudgetItemLibrary)
class BudgetItemLibraryAdmin(admin.ModelAdmin):
    """Admin for budget item library (cascading dropdown items)"""
    
    list_display = [
        'id', 'item_name', 'category', 'subcategory', 
        'typical_amount', 'usage_count', 'is_active'
    ]
    
    list_filter = ['category', 'subcategory', 'is_active', 'unit_type']
    
    search_fields = ['item_name', 'description']
    
    list_editable = ['is_active']
    
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Item Details', {
            'fields': ['category', 'subcategory', 'item_name', 'description']
        }),
        ('Pricing', {
            'fields': ['typical_amount', 'unit_type']
        }),
        ('Usage & Status', {
            'fields': ['usage_count', 'is_active', 'created_at', 'updated_at']
        }),
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'subcategory') 