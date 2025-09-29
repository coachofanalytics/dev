"""
Enhanced Budget Model for CODA Finance System

Consolidates Budget, CodaBudget, and web_budget models into a single,
comprehensive budget management system with:
- Multi-timeframe planning (weekly, monthly, yearly, multi-year)
- Project type support (general, website development, operations)
- Automated estimation from transaction history
- Approval workflows
- Investment planning
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()

class EnhancedBudget(models.Model):
    """
    Enhanced Budget Model consolidating Budget, CodaBudget, and web_budget
    
    Supports:
    - General budget planning
    - Website development cost estimation
    - Multi-timeframe planning
    - Automated estimation from transaction history
    - Approval workflows
    - Investment planning
    """
    
    # Budget Type Choices
    BUDGET_TYPE_CHOICES = [
        ('general', 'General Budget'),
        ('website_development', 'Website Development'),
        ('operations', 'Operations'),
        ('marketing', 'Marketing'),
        ('infrastructure', 'Infrastructure'),
        ('investment', 'Investment'),
    ]
    
    # Timeframe Choices
    TIMEFRAME_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('multi_year', 'Multi-Year (2-5 years)'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Estimation Method Choices
    ESTIMATION_METHOD_CHOICES = [
        ('manual', 'Manual Entry'),
        ('transaction_based', 'Transaction History'),
        ('coda_estimation', 'CODA Development Estimation'),
        ('trend_analysis', 'Trend Analysis'),
        ('ai_prediction', 'AI Prediction'),
    ]
    
    # Basic Information
    company = models.ForeignKey(
        'main.Company', 
        on_delete=models.CASCADE, 
        related_name="enhanced_budgets"
    )
    department = models.ForeignKey(
        'main.Department', 
        on_delete=models.CASCADE, 
        related_name="enhanced_budgets"
    )
    budget_lead = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="enhanced_budgets",
        limit_choices_to={'is_staff': True, 'is_active': True}
    )
    
    # Budget Classification
    budget_type = models.CharField(
        max_length=30, 
        choices=BUDGET_TYPE_CHOICES, 
        default='general',
        help_text="Type of budget (general, website development, etc.)"
    )
    timeframe = models.CharField(
        max_length=20, 
        choices=TIMEFRAME_CHOICES, 
        default='monthly',
        help_text="Budget timeframe"
    )
    
    # Categories
    category = models.ForeignKey(
        'BudgetCategory', 
        on_delete=models.CASCADE, 
        related_name="enhanced_budgets",
        blank=True, null=True
    )
    subcategory = models.ForeignKey(
        'BudgetSubCategory', 
        on_delete=models.CASCADE, 
        related_name="enhanced_budgets",
        blank=True, null=True
    )
    
    # Project Information (for website development)
    project_name = models.CharField(
        max_length=200, 
        blank=True, null=True,
        help_text="Project name (for website development budgets)"
    )
    project_description = models.TextField(
        max_length=2000, 
        blank=True, null=True,
        help_text="Detailed project description"
    )
    
    # Budget Details
    item_name = models.CharField(
        max_length=200, 
        help_text="Budget item name"
    )
    description = models.TextField(
        max_length=2000, 
        help_text="Detailed description of the budget item"
    )
    
    # Quantity and Pricing
    cases = models.PositiveIntegerField(
        default=1, 
        help_text="Number of cases/units"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Quantity of items"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Price per unit"
    )
    
    # Time Period
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="Budget start date"
    )
    end_date = models.DateTimeField(
        help_text="Budget end date"
    )
    
    # Estimation Information
    estimation_method = models.CharField(
        max_length=30, 
        choices=ESTIMATION_METHOD_CHOICES, 
        default='manual',
        help_text="Method used for budget estimation"
    )
    estimated_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, blank=True,
        help_text="Estimated total amount"
    )
    estimation_confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence level of estimation (0-100%)"
    )
    estimation_source = models.CharField(
        max_length=200, 
        blank=True, null=True,
        help_text="Source of estimation data"
    )
    
    # Status and Approval
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        help_text="Current budget status"
    )
    requires_approval = models.BooleanField(
        default=True,
        help_text="Whether this budget requires approval"
    )
    approval_policy = models.ForeignKey(
        'ApprovalPolicy', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        help_text="Approval policy for this budget"
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name="approved_budgets",
        help_text="User who approved this budget"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Date when budget was approved"
    )
    
    # Investment Planning
    is_investment = models.BooleanField(
        default=False,
        help_text="Whether this is an investment budget"
    )
    investment_type = models.CharField(
        max_length=50, 
        blank=True, null=True,
        help_text="Type of investment (equipment, software, etc.)"
    )
    expected_roi = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, blank=True,
        help_text="Expected return on investment (%)"
    )
    payback_period = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Expected payback period in months"
    )
    
    # Tracking and Control
    actual_spent = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Actual amount spent"
    )
    variance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Variance from budget (positive = over budget)"
    )
    variance_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Variance percentage"
    )
    
    # Additional Information
    receipt_link = models.URLField(
        max_length=500, 
        blank=True, null=True,
        help_text="Link to receipt or documentation"
    )
    notes = models.TextField(
        max_length=2000, 
        blank=True, null=True,
        help_text="Additional notes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at', 'start_date']
        verbose_name = "Enhanced Budget"
        verbose_name_plural = "Enhanced Budgets"
        indexes = [
            models.Index(fields=['company', 'department']),
            models.Index(fields=['budget_type', 'timeframe']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.get_budget_type_display()} ({self.get_timeframe_display()})"
    
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


class BudgetEstimationTemplate(models.Model):
    """
    Template for automated budget estimation
    
    Stores estimation templates for different types of budgets,
    including the CODA development estimation logic
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=1000)
    budget_type = models.CharField(
        max_length=30, 
        choices=EnhancedBudget.BUDGET_TYPE_CHOICES
    )
    
    # Estimation Configuration
    estimation_config = models.JSONField(
        help_text="JSON configuration for estimation parameters"
    )
    
    # CODA Development Estimation (from coda_budget_estimation)
    development_tasks = models.JSONField(
        default=dict,
        help_text="Development task configuration (createview, updateview, etc.)"
    )
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=30.00,
        help_text="Default hourly rate for development tasks"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Budget Estimation Template"
        verbose_name_plural = "Budget Estimation Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_budget_type_display()})"
    
    def get_development_estimation(self, app_models_count):
        """Calculate development cost estimation"""
        total_cost = 0
        for task_name, task_config in self.development_tasks.items():
            task_cost = (
                task_config.get('quantity', 1) * 
                task_config.get('hours', 1) * 
                self.hourly_rate
            )
            total_cost += task_cost
        
        return total_cost * app_models_count


class MultiYearBudgetPlan(models.Model):
    """
    Multi-year budget planning (1-year, 2-year, 5-year plans)
    
    Links multiple EnhancedBudget instances to create long-term plans
    """
    
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    company = models.ForeignKey(
        'main.Company', 
        on_delete=models.CASCADE, 
        related_name="multi_year_plans"
    )
    department = models.ForeignKey(
        'main.Department', 
        on_delete=models.CASCADE, 
        related_name="multi_year_plans"
    )
    
    # Plan Duration
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('1_year', '1 Year Plan'),
            ('2_year', '2 Year Plan'),
            ('5_year', '5 Year Plan'),
            ('custom', 'Custom Duration'),
        ]
    )
    
    # Investment Planning
    total_investment_required = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Total investment required for the plan"
    )
    funding_sources = models.JSONField(
        default=list,
        help_text="List of funding sources and amounts"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('in_review', 'In Review'),
            ('approved', 'Approved'),
            ('active', 'Active'),
            ('completed', 'Completed'),
        ],
        default='draft'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="created_plans"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Multi-Year Budget Plan"
        verbose_name_plural = "Multi-Year Budget Plans"
    
    def __str__(self):
        return f"{self.name} ({self.start_year}-{self.end_year})"
    
    @property
    def duration_years(self):
        """Calculate plan duration in years"""
        return self.end_year - self.start_year + 1
    
    def get_budgets_for_year(self, year):
        """Get all budgets for a specific year"""
        return self.enhanced_budgets.filter(
            start_date__year=year
        )
    
    def calculate_total_investment(self):
        """Calculate total investment required"""
        total = sum(
            budget.total_amount for budget in self.enhanced_budgets.all()
            if budget.is_investment
        )
        self.total_investment_required = total
        self.save(update_fields=['total_investment_required'])
        return total
