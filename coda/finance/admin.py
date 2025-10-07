"""
Clean Admin Interface for Organized Finance Models
Only includes models that exist in the organized structure
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
        'interest_rate', 'min_term_months', 'max_term_months', 'is_active'
    ]
    
    list_filter = [
        'product_type', 'is_active'
    ]
    
    search_fields = ['name', 'description']
    
    readonly_fields = []  # No timestamp fields in this model
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'product_type', 'status')
        }),
        ('Financial Terms', {
            'fields': ('min_amount', 'max_amount', 'interest_rate', 'interest_type', 
                      'min_term_months', 'max_term_months')
        }),
        ('Fees', {
            'fields': ('processing_fee', 'late_fee')
        }),
        ('Eligibility', {
            'fields': ('min_credit_score', 'min_income', 'employment_required')
        }),
        ('Settings', {
            'fields': ('requires_collateral', 'auto_approve')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    """Admin interface for loan applications"""
    
    list_display = [
        'application_number', 'borrower', 'loan_product', 'amount_requested',
        'status', 'created_at'
    ]
    
    list_filter = [
        'status', 'loan_product', 'created_at'
    ]
    
    search_fields = [
        'application_number', 'borrower__first_name', 'borrower__last_name',
        'purpose'
    ]
    
    readonly_fields = ['application_number', 'created_at', 'updated_at', 'submitted_at']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('application_id', 'applicant', 'loan_product', 'purpose')
        }),
        ('Loan Terms', {
            'fields': ('requested_amount', 'approved_amount', 'term_months')
        }),
        ('Status', {
            'fields': ('status', 'priority')
        }),
        ('Financial Information', {
            'fields': ('monthly_income', 'monthly_expenses', 'credit_score')
        }),
        ('Employment', {
            'fields': ('employer', 'employment_type', 'employment_duration')
        }),
        ('Approval', {
            'fields': ('reviewed_by', 'approved_by', 'approved_at')
        }),
        ('Disbursement', {
            'fields': ('disbursed_at', 'disbursement_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetRequest)
class BudgetRequestAdmin(admin.ModelAdmin):
    """Admin interface for budget requests"""
    
    list_display = [
        'purpose', 'budget_category', 'amount', 'status', 
        'priority', 'requester', 'created_at'
    ]
    
    list_filter = [
        'status', 'priority', 'budget_category', 'created_at'
    ]
    
    search_fields = [
        'purpose', 'requester__first_name', 
        'requester__last_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'request_date']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('title', 'description', 'category', 'subcategory')
        }),
        ('Financial', {
            'fields': ('requested_amount', 'currency')
        }),
        ('Status', {
            'fields': ('status', 'priority')
        }),
        ('Requestor', {
            'fields': ('requested_by', 'department')
        }),
        ('Approval', {
            'fields': ('approval_policy', 'approved_by', 'approved_at')
        }),
        ('Justification', {
            'fields': ('justification', 'business_case')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ApprovalPolicy)
class ApprovalPolicyAdmin(admin.ModelAdmin):
    """Admin interface for approval policies"""
    
    list_display = [
        'name', 'min_amount', 'max_amount', 'auto_approve',
        'requires_otp', 'is_active'
    ]
    
    list_filter = [
        'is_active', 'auto_approve', 'requires_otp'
    ]
    
    search_fields = ['name', 'description']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Policy Details', {
            'fields': ('name', 'description', 'policy_type', 'approval_level')
        }),
        ('Amount Thresholds', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Restrictions', {
            'fields': ('categories', 'departments')
        }),
        ('Approvers', {
            'fields': ('approvers',)
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_justification', 'auto_approve_under_threshold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin interface for budgets"""
    
    list_display = [
        'item_name', 'category', 'subcategory', 'estimated_amount',
        'actual_spent', 'status', 'budget_lead', 'created_at'
    ]
    
    list_filter = [
        'status', 'budget_type', 'category', 'created_at'
    ]
    
    search_fields = [
        'item_name', 'description', 'budget_lead__first_name',
        'budget_lead__last_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        ('Budget Details', {
            'fields': ('item_name', 'description', 'category', 'subcategory')
        }),
        ('Financial', {
            'fields': ('estimated_amount', 'actual_spent', 'quantity', 
                      'unit_price', 'cases')
        }),
        ('Status', {
            'fields': ('budget_type', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Approval', {
            'fields': ('requires_approval', 'approved_by', 'approved_at')
        }),
        ('Responsibility', {
            'fields': ('budget_lead',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetEstimateProjection)
class BudgetEstimateProjectionAdmin(admin.ModelAdmin):
    """Admin interface for budget estimate projections"""
    
    list_display = [
        'budget', 'projection_method', 'projected_amount',
        'confidence_score', 'projection_date', 'created_at'
    ]
    
    list_filter = [
        'projection_method', 'projection_date', 'created_at'
    ]
    
    search_fields = ['notes']
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Projection Details', {
            'fields': ('projection_name', 'description', 'status')
        }),
        ('Estimation', {
            'fields': ('estimation_method', 'estimation_source', 'estimation_confidence')
        }),
        ('Results', {
            'fields': ('total_estimated_amount', 'projection_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for transactions"""
    
    list_display = [
        'vendor', 'amount', 'currency', 'category', 'transaction_type',
        'status', 'transaction_date', 'created_at'
    ]
    
    list_filter = [
        'category', 'transaction_type', 'status', 'currency', 'transaction_date'
    ]
    
    search_fields = [
        'receiver', 'description', 'reference', 'created_by__first_name',
        'created_by__last_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('receiver', 'description', 'reference', 'amount', 'currency')
        }),
        ('Classification', {
            'fields': ('category', 'type', 'budget_category', 'budget_subcategory')
        }),
        ('Status', {
            'fields': ('status', 'transaction_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'receipt_link', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    """Admin interface for budget categories"""
    
    list_display = ['name', 'description', 'category_type']
    list_filter = ['category_type']
    search_fields = ['name', 'description']
    readonly_fields = []  # No timestamp fields in this model


@admin.register(BudgetSubCategory)
class BudgetSubCategoryAdmin(admin.ModelAdmin):
    """Admin interface for budget subcategories"""
    
    list_display = ['name', 'category', 'sub_category_type']
    list_filter = ['category', 'sub_category_type']
    search_fields = ['name']
    readonly_fields = []  # No timestamp fields in this model


@admin.register(BudgetItemLibrary)
class BudgetItemLibraryAdmin(admin.ModelAdmin):
    """Admin interface for budget item library"""
    
    list_display = [
        'item_name', 'category', 'subcategory', 'typical_amount',
        'unit_type', 'usage_count', 'is_active'
    ]
    
    list_filter = [
        'category', 'subcategory', 'unit_type', 'is_active'
    ]
    
    search_fields = ['item_name', 'description']
    
    list_editable = ['is_active']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Item Details', {
            'fields': ('item_name', 'description', 'category', 'subcategory')
        }),
        ('Pricing', {
            'fields': ('typical_amount', 'unit_type')
        }),
        ('Usage', {
            'fields': ('usage_count', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
