# -*- coding: utf-8 -*-
"""
Budget-specific models for approval workflows and variance tracking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from main.models import Company, Department
except ImportError:
    Company = Department = None

# Import core models
from .core import Budget, BudgetCategory, BudgetSubCategory


class ApprovalPolicy(models.Model):
    """Defines approval policies for budget requests."""
    
    # Policy types
    POLICY_TYPE_CHOICES = [
        ('Amount', 'Amount-based'),
        ('Category', 'Category-based'),
        ('Department', 'Department-based'),
        ('Combined', 'Combined criteria'),
    ]
    
    # Approval levels
    APPROVAL_LEVEL_CHOICES = [
        ('Single', 'Single approval'),
        ('Multi', 'Multi-level approval'),
        ('Committee', 'Committee approval'),
    ]
    
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='approval_policies',
        help_text="Company this policy applies to"
    )
    
    # Policy details
    name = models.CharField(
        max_length=200,
        help_text="Name of the approval policy"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the policy"
    )
    
    # Policy criteria
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPE_CHOICES,
        help_text="Type of approval policy"
    )
    approval_level = models.CharField(
        max_length=20,
        choices=APPROVAL_LEVEL_CHOICES,
        default='Single',
        help_text="Level of approval required"
    )
    
    # Amount thresholds
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum amount requiring approval"
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum amount for this policy"
    )
    
    # Category restrictions
    categories = models.ManyToManyField(
        BudgetCategory,
        blank=True,
        help_text="Categories this policy applies to"
    )
    
    # Department restrictions
    departments = models.ManyToManyField(
        'accounts.Department',
        blank=True,
        help_text="Departments this policy applies to"
    )
    
    # Approvers
    approvers = models.ManyToManyField(
        User,
        related_name='approval_policies',
        help_text="Users who can approve requests under this policy"
    )
    
    # Policy settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this policy is active"
    )
    requires_justification = models.BooleanField(
        default=True,
        help_text="Whether justification is required"
    )
    auto_approve_under_threshold = models.BooleanField(
        default=False,
        help_text="Auto-approve requests under minimum threshold"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Approval Policy")
        verbose_name_plural = _("Approval Policies")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.policy_type}"
    
    def applies_to_request(self, request):
        """Check if this policy applies to a budget request."""
        # Check amount thresholds
        if self.min_amount and request.total_amount < self.min_amount:
            return False
        if self.max_amount and request.total_amount > self.max_amount:
            return False
        
        # Check category restrictions
        if self.categories.exists():
            if not self.categories.filter(id=request.category.id).exists():
                return False
        
        # Check department restrictions
        if self.departments.exists():
            if not self.departments.filter(id=request.department.id).exists():
                return False
        
        return True


class BudgetRequest(models.Model):
    """Budget requests that go through approval workflow."""
    
    # Request status
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    
    # Request priority
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='budget_requests',
        help_text="Company this request belongs to"
    )
    
    # Request details
    title = models.CharField(
        max_length=200,
        help_text="Title of the budget request"
    )
    description = models.TextField(
        help_text="Detailed description of the request"
    )
    
    # Budget categorization
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        related_name='budget_requests',
        help_text="Budget category"
    )
    subcategory = models.ForeignKey(
        BudgetSubCategory,
        on_delete=models.CASCADE,
        related_name='budget_requests',
        help_text="Budget subcategory"
    )
    
    # Financial details
    requested_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount being requested"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency of the request"
    )
    
    # Request metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft',
        help_text="Request status"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium',
        help_text="Request priority"
    )
    
    # Requestor
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budget_requests',
        help_text="User who made the request"
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budget_requests',
        help_text="Department making the request"
    )
    
    # Approval workflow
    approval_policy = models.ForeignKey(
        ApprovalPolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budget_requests',
        help_text="Approval policy for this request"
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
        help_text="When the request was approved"
    )
    
    # Justification
    justification = models.TextField(
        blank=True,
        help_text="Justification for the request"
    )
    business_case = models.TextField(
        blank=True,
        help_text="Business case for the request"
    )
    
    # Additional fields
    supporting_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="Links to supporting documents"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was submitted"
    )
    
    class Meta:
        verbose_name = _("Budget Request")
        verbose_name_plural = _("Budget Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['requested_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.requested_amount} ({self.status})"
    
    @property
    def total_amount(self):
        """Get total amount (alias for requested_amount for consistency)."""
        return self.requested_amount
    
    @property
    def is_pending(self):
        """Check if request is pending approval."""
        return self.status in ['Submitted', 'Under Review']
    
    @property
    def is_approved(self):
        """Check if request is approved."""
        return self.status == 'Approved'
    
    @property
    def is_rejected(self):
        """Check if request is rejected."""
        return self.status == 'Rejected'
    
    def submit_for_approval(self):
        """Submit the request for approval."""
        self.status = 'Submitted'
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at'])
    
    def approve(self, approver):
        """Approve the request."""
        self.status = 'Approved'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])
    
    def reject(self, approver, reason=None):
        """Reject the request."""
        self.status = 'Rejected'
        self.approved_by = approver
        self.approved_at = timezone.now()
        if reason:
            self.notes = f"Rejection reason: {reason}"
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'notes'])
    
    def get_absolute_url(self):
        """Get URL for budget request detail view."""
        from django.urls import reverse
        return reverse('finance:budget-request-detail', kwargs={'pk': self.pk})


class BudgetVariance(models.Model):
    """Track budget variances and their explanations."""
    
    # Variance types
    VARIANCE_TYPE_CHOICES = [
        ('Favorable', 'Favorable'),
        ('Unfavorable', 'Unfavorable'),
        ('Neutral', 'Neutral'),
    ]
    
    # Variance reasons
    REASON_CHOICES = [
        ('Volume', 'Volume variance'),
        ('Price', 'Price variance'),
        ('Timing', 'Timing variance'),
        ('Scope', 'Scope change'),
        ('External', 'External factors'),
        ('Other', 'Other'),
    ]
    
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='variances',
        help_text="Budget this variance relates to"
    )
    
    # Variance details
    variance_type = models.CharField(
        max_length=20,
        choices=VARIANCE_TYPE_CHOICES,
        help_text="Type of variance"
    )
    variance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount of variance"
    )
    variance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Variance as percentage"
    )
    
    # Variance explanation
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        help_text="Primary reason for variance"
    )
    explanation = models.TextField(
        help_text="Detailed explanation of the variance"
    )
    
    # Impact assessment
    impact_assessment = models.TextField(
        blank=True,
        help_text="Assessment of the impact of this variance"
    )
    corrective_action = models.TextField(
        blank=True,
        help_text="Corrective actions taken or planned"
    )
    
    # Reporting
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_variances',
        help_text="User who reported this variance"
    )
    reported_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the variance was reported"
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_variances',
        help_text="User who reviewed this variance"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the variance was reviewed"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the review"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Variance")
        verbose_name_plural = _("Budget Variances")
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['budget', 'variance_type']),
            models.Index(fields=['reported_at']),
        ]
    
    def __str__(self):
        return f"{self.budget.item_name} - {self.variance_amount} ({self.variance_type})"
    
    @property
    def is_favorable(self):
        """Check if variance is favorable."""
        return self.variance_type == 'Favorable'
    
    @property
    def is_unfavorable(self):
        """Check if variance is unfavorable."""
        return self.variance_type == 'Unfavorable'
    
    def mark_reviewed(self, reviewer, notes=None):
        """Mark variance as reviewed."""
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.review_notes = notes
        self.save(update_fields=['reviewed_by', 'reviewed_at', 'review_notes'])
