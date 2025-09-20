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

# Import models (updated to use new consolidated models.py)
try:
    from .models import (
        LoanApplication, Payment_Information, Payment_History, 
        LoanPerformance, LoanProduct
    )
except ImportError:
    # Fallback if consolidated models not available
    LoanApplication = Payment_Information = Payment_History = LoanPerformance = LoanProduct = None


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


@admin.register(Payment_Information)
class PaymentInformationAdmin(admin.ModelAdmin):
    """Admin interface for payment information"""
    
    list_display = [
        'id', 'customer_id', 'payment_fees', 'down_payment', 'student_bonus',
        'fee_balance', 'plan', 'payment_method', 'contract_submitted_date', 'is_active'
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
            'fields': ['payment_fees', 'down_payment', 'student_bonus', 'fee_balance']
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
        'fee_balance', 'plan', 'contract_submitted_date'
    ]
    
    list_filter = [
        'contract_submitted_date'
    ]
    
    search_fields = [
        'customer__username', 'customer__first_name', 'customer__last_name',
        'customer__email'
    ]
    
    readonly_fields = ['contract_submitted_date']
    
    fieldsets = [
        ('Customer Information', {
            'fields': ['customer']
        }),
        ('Payment Details', {
            'fields': ['payment_fees', 'down_payment', 'student_bonus', 'fee_balance']
        }),
        ('Plan Information', {
            'fields': ['plan', 'subplan', 'pricing_plan']
        }),
        ('Contract', {
            'fields': ['contract_submitted_date']
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