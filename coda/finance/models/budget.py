# -*- coding: utf-8 -*-
"""
Finance Budget Models

Budget-related models including Budget, BudgetCategory, BudgetRequest, and related models.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from shared_core.models import TimeStampedModel, StatusMixin
except ImportError:
    TimeStampedModel = StatusMixin = None

try:
    from shared_core.users import Department
except ImportError:
    Department = None

# Note: Company is referenced as string 'main.Company' to avoid import issues during migrations


# =============================================================================
# BUDGET MODELS
# =============================================================================

class BudgetCategory(models.Model):
    """
    Budget category classification with intelligent approval tier system.
    
    Phase 1: Basic categorization
    Phase 2: Data-driven tier classification for automated approvals
    
    Tiers:
    - A: Known/Recurring (auto-approve if within variance)
    - B: Variable/Operational (priority-based routing)
    - C: Strategic/Discretionary (assessment required)
    """
    
    # Basic Fields
    name = models.CharField(max_length=100, null=True, blank=True, default='Operations')
    description = models.TextField(max_length=1000, null=True, blank=True)
    
    # Phase 2: Intelligent Approval Tier System (Oct 2025)
    approval_tier = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Tier A - Known/Recurring (Auto-Approve)'),
            ('B', 'Tier B - Variable/Operational (Priority-Based)'),
            ('C', 'Tier C - Strategic/Discretionary (Assessment Required)'),
        ],
        default='C',
        help_text="Approval tier determined by spending pattern analysis"
    )
    
    auto_approve_enabled = models.BooleanField(
        default=False,
        help_text="Finance Manager can enable/disable auto-approval for this category"
    )
    
    typical_monthly_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Typical monthly spending for this category (calculated from transaction data)"
    )
    
    variance_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="Percentage variance from typical that triggers manual review (default: 20%)"
    )
    
    is_recurring = models.BooleanField(
        default=False,
        help_text="Whether this category has recurring spending patterns (detected from data)"
    )
    
    last_pattern_analysis = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time spending pattern analysis was run for this category"
    )

    class Meta:
        verbose_name = _("Budget Category")
        verbose_name_plural = _("Budget Categories")
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def needs_pattern_analysis(self):
        """Check if pattern analysis needs to be run/updated"""
        if not self.last_pattern_analysis:
            return True
        # Re-analyze if older than 30 days
        from datetime import timedelta
        return (timezone.now() - self.last_pattern_analysis) > timedelta(days=30)
    
    def is_within_variance(self, amount):
        """Check if amount is within acceptable variance of typical monthly amount"""
        if not self.typical_monthly_amount:
            return False
        
        variance = abs(amount - self.typical_monthly_amount) / self.typical_monthly_amount * 100
        return variance <= self.variance_threshold
    
    def should_auto_approve(self, amount):
        """
        Determine if a request for this amount should be auto-approved.
        
        Returns: (should_approve: bool, reason: str)
        """
        if not self.auto_approve_enabled:
            return False, "Auto-approval disabled for this category"
        
        if self.approval_tier != 'A':
            return False, f"Tier {self.approval_tier} requires manual approval"
        
        if not self.typical_monthly_amount:
            return False, "No typical amount data - requires manual review"
        
        if self.is_within_variance(amount):
            return True, f"Amount within {self.variance_threshold}% of typical ${self.typical_monthly_amount}"
        else:
            variance = abs(amount - self.typical_monthly_amount) / self.typical_monthly_amount * 100
            return False, f"Amount {variance:.1f}% variance - exceeds threshold {self.variance_threshold}%"


class BudgetSubCategory(models.Model):
    """Budget subcategory classification"""
    
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("Budget Sub category")
        verbose_name_plural = _("Budget Sub categories")
        ordering = ['category', 'name']

    def __str__(self):
        return "{}".format(self.name)


class BudgetItemLibrary(models.Model):
    """
    Master library of budget items for all categories
    Enables cascading dropdowns: Category → Subcategory → Item
    Tracks usage and typical amounts from historical data
    """
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='items',
        help_text="Budget category this item belongs to"
    )
    subcategory = models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='items',
        help_text="Budget subcategory this item belongs to"
    )
    item_name = models.CharField(
        max_length=200,
        help_text="Name of the budget item (e.g., 'Safaricom internet subscription')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the item"
    )
    typical_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Typical/average amount based on historical data"
    )
    unit_type = models.CharField(
        max_length=50,
        blank=True,
        default='each',
        help_text="Unit of measurement (each, month, year, etc.)"
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this item has been used (for sorting)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this item is active and available for selection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Item")
        verbose_name_plural = _("Budget Item Library")
        ordering = ['-usage_count', 'item_name']
        unique_together = ['category', 'subcategory', 'item_name']
    
    def __str__(self):
        cat_name = self.category.name if self.category else 'No Category'
        subcat_name = self.subcategory.name if self.subcategory else 'No Subcategory'
        return "{} → {} → {}".format(cat_name, subcat_name, self.item_name)
    
    def increment_usage(self):
        """Increment usage count when item is selected"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def update_typical_amount(self, new_amount):
        """Update typical amount (moving average)"""
        if self.typical_amount and self.usage_count > 0:
            # Calculate moving average
            total = (self.typical_amount * self.usage_count) + new_amount
            self.typical_amount = total / (self.usage_count + 1)
        else:
            self.typical_amount = new_amount
        self.save(update_fields=['typical_amount'])


class Budget(models.Model):
    """Main budget model"""
    
    company = models.ForeignKey(
        'main.Company', 
        on_delete=models.CASCADE, 
        related_name="company_type",
        default=1
    )
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name="department_type",
        default=1
    )
    
    budget_lead = models.ForeignKey(
        "accounts.CustomerUser", 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        limit_choices_to=(Q(is_staff=True, is_active=True, category=2) | Q(is_superuser=True)),
        related_name="budget_lead"
    )
    
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE, 
        related_name="category_type",
        blank=True, null=True
    )
    
    subcategory = models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE, 
        related_name="sub_category_type",
        blank=True, null=True
    )
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    item_name = models.CharField(max_length=100, null=True, default=None)
    cases = models.PositiveIntegerField(default=1, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    description = models.TextField(max_length=1000, default=None)
    receipt_link = models.URLField(max_length=500, blank=True, null=True, help_text='Link to receipt or documentation')
    is_active = models.BooleanField(default=True, null=True, blank=True)
    
    # Enhanced Budget Fields (added by migration)
    budget_type = models.CharField(
        max_length=30,
        choices=[
            ('general', 'General Budget'),
            ('website_development', 'Website Development'),
            ('operations', 'Operations'),
            ('marketing', 'Marketing'),
            ('infrastructure', 'Infrastructure'),
            ('investment', 'Investment'),
        ],
        default='general',
        help_text="Type of budget (e.g., General, Website Development)"
    )
    timeframe = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
            ('multi_year', 'Multi-Year'),
        ],
        default='monthly',
        help_text="Timeframe for the budget"
    )
    project_name = models.CharField(max_length=200, blank=True, null=True, help_text="Name of the project if applicable")
    project_description = models.TextField(blank=True, null=True, help_text="Description of the project")

    # Estimation fields
    estimation_method = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('average_3_months', 'Average of Last 3 Months'),
            ('average_6_months', 'Average of Last 6 Months'),
            ('last_year_actual', 'Last Year Actual'),
            ('trend_analysis', 'Trend Analysis'),
            ('coda_development', 'CODA Development Estimation'),
        ],
        default='manual',
        help_text="Method used for budget estimation"
    )
    estimated_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Automatically estimated amount")
    estimation_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Confidence score for automated estimation (0-100)")
    estimation_source = models.CharField(max_length=255, blank=True, null=True, help_text="Source of the estimation data (e.g., Transaction history)")

    # Status and Approval fields
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
            ('approved', 'Approved'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        help_text="Current status of the budget"
    )
    requires_approval = models.BooleanField(default=True, help_text="Does this budget require approval?")
    approval_policy = models.ForeignKey(
        'ApprovalPolicy', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        help_text="The approval policy applicable to this budget"
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='approved_budgets',
        help_text="User who approved the budget"
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of approval")

    # Investment Planning fields
    is_investment = models.BooleanField(default=False, help_text="Is this budget related to an investment?")
    investment_type = models.CharField(
        max_length=50,
        choices=[
            ('equity', 'Equity Investment'),
            ('debt', 'Debt Investment'),
            ('capital_expenditure', 'Capital Expenditure'),
            ('r&d', 'Research & Development'),
            ('other', 'Other Investment'),
        ],
        blank=True, null=True,
        help_text="Type of investment if applicable"
    )
    expected_roi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Expected Return on Investment (%)")
    payback_period = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Expected payback period in months")

    # Tracking fields
    actual_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Actual amount spent against this budget")
    variance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Variance (Actual - Budgeted)")
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Variance as a percentage")
    
    # Additional fields
    notes = models.TextField(blank=True, null=True, help_text="Any additional notes for the budget")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.item_name or "Budget {}".format(self.id)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("management:inflow-detail", kwargs={"pk": self.pk})
    
    # Enhanced Budget Methods
    @property
    def total_amount(self):
        """Calculate total budget amount"""
        if self.unit_price and self.quantity:
            return round(Decimal(self.unit_price) * Decimal(self.quantity) * Decimal(self.cases), 2)
        return Decimal('0.00')
    
    @property
    def days_duration(self):
        """Calculate budget duration in days"""
        if self.end_date and self.start_date:
            return (self.end_date - self.start_date).days
        return 0
    
    @property
    def is_over_budget(self):
        """Check if actual spending exceeds budget"""
        return self.actual_spent > self.total_amount
    
    @property
    def remaining_budget(self):
        """Calculate remaining budget amount"""
        return max(Decimal('0.00'), self.total_amount - self.actual_spent)
    
    def calculate_variance(self):
        """Calculate variance from budget"""
        self.variance = self.actual_spent - self.total_amount
        if self.total_amount > 0:
            self.variance_percentage = (self.variance / self.total_amount) * 100
        else:
            self.variance_percentage = 0
        self.save(update_fields=['variance', 'variance_percentage'])
    
    def approve(self, approved_by_user):
        """Approve the budget"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])
    
    def activate(self):
        """Activate the budget"""
        self.status = 'active'
        self.save(update_fields=['status'])
    
    def complete(self):
        """Mark budget as completed"""
        self.status = 'completed'
        self.calculate_variance()
        self.save(update_fields=['status'])

    @property
    def days(self):
        days = (self.end_date - self.start_date).days
        return days
    
    @property
    def receipturl(self):
        if self.receipt_link is not None:
            urlreceipt = self.receipt_link
            return urlreceipt
        else:
            from django.shortcuts import redirect
            return redirect('main:layout')

    @property
    def amount(self):
        try:
            total_amount = round(Decimal(self.unit_price * self.cases * self.quantity), 2)
        except:
            total_amount = 0
        return total_amount


class BudgetEstimationTemplate(models.Model):
    """Template for budget estimation methods"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    estimation_method = models.CharField(
        max_length=50,
        choices=[
            ('average_3_months', 'Average of Last 3 Months'),
            ('average_6_months', 'Average of Last 6 Months'),
            ('last_year_actual', 'Last Year Actual'),
            ('trend_analysis', 'Trend Analysis'),
            ('coda_development', 'CODA Development Estimation'),
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Budget Estimation Template"
        verbose_name_plural = "Budget Estimation Templates"
    
    def __str__(self):
        return self.name


class BudgetEstimateProjection(models.Model):
    """Budget estimate projections and forecasts"""
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True, related_name='projections')
    projection_date = models.DateField()
    projected_amount = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    projection_method = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-projection_date']
        verbose_name = "Budget Estimate Projection"
        verbose_name_plural = "Budget Estimate Projections"
    
    def __str__(self):
        budget_name = self.budget.item_name if self.budget else 'No Budget'
        return "{} - {} - {}".format(budget_name, self.projection_date, self.projected_amount)


class MultiYearBudgetPlan(models.Model):
    """Multi-year budget planning"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()
    total_budget = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_year']
        verbose_name = "Multi-Year Budget Plan"
        verbose_name_plural = "Multi-Year Budget Plans"
    
    def __str__(self):
        return "{} ({}-{})".format(self.name, self.start_year, self.end_year)


class BudgetRequest(TimeStampedModel, StatusMixin):
    """Budget request submission and tracking for automation system"""
    
    # Request Status Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('disbursed', 'Disbursed'),
    ]
    
    # Priority Choices
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Request Information
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budget_requests',
        help_text="User who submitted the request"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Requested amount"
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        help_text="Currency code"
    )
    purpose = models.TextField(
        help_text="Purpose of the budget request"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Department requesting the budget"
    )
    
    # Request Details
    request_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date when request was submitted"
    )
    required_date = models.DateField(
        help_text="Date when budget is required"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        help_text="Priority level of the request"
    )
    
    # Approval Information
    approval_policy = models.ForeignKey(
        'ApprovalPolicy', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Approval policy applied to this request"
    )
    current_approver = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pending_approvals',
        help_text="Current approver in the chain"
    )
    approval_chain = models.JSONField(
        default=list,
        help_text="List of approvers in the approval chain"
    )
    
    # Status Tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        help_text="Current status of the request"
    )
    rejection_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Reason for rejection if applicable"
    )
    
    # Financial Information
    budget_category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Budget category for this request"
    )
    cost_center = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Cost center for the request"
    )
    
    # Attachments
    attachments = models.JSONField(
        default=list,
        help_text="List of attached documents"
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='created_budget_requests',
        help_text="User who created the request"
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='modified_budget_requests',
        help_text="User who last modified the request"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budget_requests',
        help_text="User who approved the request"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of approval"
    )
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_budget_requests',
        help_text="User who rejected the request"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of rejection"
    )
    
    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requester']),
            models.Index(fields=['department']),
            models.Index(fields=['request_date']),
            models.Index(fields=['priority']),
        ]
        verbose_name = "Budget Request"
        verbose_name_plural = "Budget Requests"
    
    def __str__(self):
        return "Budget Request #{} - {} - ${}".format(self.id, self.requester.username, self.amount)
    
    def get_approval_chain_display(self):
        """Get human-readable approval chain"""
        return ["{}: {}".format(approver['role'], approver['user']) for approver in self.approval_chain]
    
    def is_overdue(self):
        """Check if request is overdue"""
        return self.required_date < timezone.now().date() and self.status not in ['approved', 'rejected', 'disbursed']


class ApprovalPolicy(TimeStampedModel):
    """Configurable approval policies and rules for automation system"""
    
    # Policy Information
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Name of the approval policy"
    )
    description = models.TextField(
        help_text="Description of the policy"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this policy is active"
    )
    
    # Amount Thresholds
    min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum amount for this policy to apply"
    )
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum amount for this policy to apply"
    )
    
    # Approval Rules
    approver_roles = models.JSONField(
        default=list,
        help_text="List of roles that can approve under this policy"
    )
    approval_chain = models.JSONField(
        default=list,
        help_text="Sequential approval chain configuration"
    )
    auto_approve = models.BooleanField(
        default=False,
        help_text="Whether to auto-approve requests under this policy"
    )
    requires_otp = models.BooleanField(
        default=True,
        help_text="Whether OTP verification is required"
    )
    
    # Department and Category Rules
    applicable_departments = models.ManyToManyField(
        Department, 
        blank=True,
        help_text="Departments this policy applies to"
    )
    applicable_categories = models.ManyToManyField(
        BudgetCategory, 
        blank=True,
        help_text="Budget categories this policy applies to"
    )
    
    # User Type Rules
    applicable_user_types = models.JSONField(
        default=list,
        help_text="User types this policy applies to (Staff, KCC, External)"
    )
    
    # Time-based Rules
    max_approval_days = models.PositiveIntegerField(
        default=7,
        help_text="Maximum days for approval"
    )
    escalation_days = models.PositiveIntegerField(
        default=3,
        help_text="Days before escalation"
    )
    
    class Meta:
        ordering = ['min_amount']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['min_amount']),
        ]
        verbose_name = "Approval Policy"
        verbose_name_plural = "Approval Policies"
    
    def __str__(self):
        return "{} (${} - ${})".format(self.name, self.min_amount, self.max_amount or '∞')
    
    def is_applicable(self, request):
        """Check if this policy applies to a request"""
        # Check amount range
        if request.amount < self.min_amount:
            return False
        if self.max_amount and request.amount > self.max_amount:
            return False
        
        # Check department
        if self.applicable_departments.exists() and request.department not in self.applicable_departments.all():
            return False
        
        # Check category
        if self.applicable_categories.exists() and request.budget_category not in self.applicable_categories.all():
            return False
        
        # Check user type
        if self.applicable_user_types:
            user_type = self.get_user_type(request.requester)
            if user_type not in self.applicable_user_types:
                return False
        
        return True
    
    def get_user_type(self, user):
        """Get user type for policy matching"""
        if user.is_staff:
            return 'Staff'
        elif hasattr(user, 'profile') and user.profile.is_karen_country_club_member:
            return 'KCC'
        else:
            return 'External'


class DisbursementRequest(TimeStampedModel, StatusMixin):
    """Disbursement request for approved budget requests"""
    
    # Disbursement Status Choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    # Request Information
    budget_request = models.ForeignKey(
        BudgetRequest, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='disbursement_requests',
        help_text="Associated budget request"
    )
    requested_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount to be disbursed"
    )
    disbursement_method = models.CharField(
        max_length=50,
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('mpesa', 'M-Pesa'),
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('other', 'Other'),
        ],
        default='bank_transfer',
        help_text="Method of disbursement"
    )
    
    # Disbursement Details
    disbursement_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Actual disbursement date"
    )
    transaction_reference = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Transaction reference number"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes for disbursement"
    )
    
    # Status Tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of the disbursement"
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='created_disbursement_requests',
        help_text="User who created the disbursement request"
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_disbursements',
        help_text="User who approved the disbursement"
    )
    disbursed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='disbursed_requests',
        help_text="User who processed the disbursement"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['budget_request']),
            models.Index(fields=['disbursement_date']),
        ]
        verbose_name = "Disbursement Request"
        verbose_name_plural = "Disbursement Requests"
    
    def __str__(self):
        return "Disbursement #{} - {} - ${}".format(self.id, self.budget_request.requester.username, self.requested_amount)
    
    def approve(self, approved_by_user):
        """Approve the disbursement request"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.save(update_fields=['status', 'approved_by'])
    
    def disburse(self, disbursed_by_user, transaction_reference=None):
        """Process the disbursement"""
        self.status = 'disbursed'
        self.disbursed_by = disbursed_by_user
        self.disbursement_date = timezone.now()
        if transaction_reference:
            self.transaction_reference = transaction_reference
        self.save(update_fields=['status', 'disbursed_by', 'disbursement_date', 'transaction_reference'])


class AutomationAuditLog(TimeStampedModel):
    """Audit log for automation system actions"""
    
    # Action Types
    ACTION_CHOICES = [
        ('budget_request_created', 'Budget Request Created'),
        ('budget_request_approved', 'Budget Request Approved'),
        ('budget_request_rejected', 'Budget Request Rejected'),
        ('disbursement_requested', 'Disbursement Requested'),
        ('disbursement_processed', 'Disbursement Processed'),
        ('policy_applied', 'Policy Applied'),
        ('escalation_triggered', 'Escalation Triggered'),
        ('notification_sent', 'Notification Sent'),
    ]
    
    # Log Information
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    description = models.TextField(
        help_text="Detailed description of the action"
    )
    
    # Related Objects
    budget_request = models.ForeignKey(
        BudgetRequest, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    disbursement_request = models.ForeignKey(
        DisbursementRequest, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    
    # User Information
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who performed the action (null for system actions)"
    )
    
    # Additional Data
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the action"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Automation Audit Log"
        verbose_name_plural = "Automation Audit Logs"
    
    def __str__(self):
        username = self.user.username if self.user else 'System'
        return "{} - {} - {}".format(self.get_action_display(), username, self.created_at.strftime('%Y-%m-%d %H:%M'))
