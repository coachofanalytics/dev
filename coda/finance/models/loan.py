# -*- coding: utf-8 -*-
"""
Loan-specific models for loan applications, products, and payments.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from main.models import Company
except ImportError:
    Company = None


class LoanProduct(models.Model):
    """Loan product/plan definitions."""
    
    # Product types
    PRODUCT_TYPE_CHOICES = [
        ('Personal', 'Personal Loan'),
        ('Business', 'Business Loan'),
        ('Emergency', 'Emergency Loan'),
        ('Asset', 'Asset Finance'),
        ('Working Capital', 'Working Capital'),
    ]
    
    # Interest types
    INTEREST_TYPE_CHOICES = [
        ('Fixed', 'Fixed Rate'),
        ('Variable', 'Variable Rate'),
        ('Reducing', 'Reducing Balance'),
    ]
    
    # Product status
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='loan_products',
        help_text="Company offering this loan product"
    )
    
    # Product details
    name = models.CharField(
        max_length=100,
        help_text="Name of the loan product"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the loan product"
    )
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        help_text="Type of loan product"
    )
    
    # Financial terms
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Minimum loan amount"
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Maximum loan amount"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual interest rate (percentage)"
    )
    interest_type = models.CharField(
        max_length=20,
        choices=INTEREST_TYPE_CHOICES,
        default='Fixed',
        help_text="Type of interest calculation"
    )
    
    # Term options
    min_term_months = models.IntegerField(
        help_text="Minimum loan term in months"
    )
    max_term_months = models.IntegerField(
        help_text="Maximum loan term in months"
    )
    
    # Fees
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Processing fee"
    )
    late_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Late payment fee"
    )
    
    # Eligibility criteria
    min_credit_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum credit score required"
    )
    min_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum income required"
    )
    employment_required = models.BooleanField(
        default=True,
        help_text="Whether employment is required"
    )
    
    # Product settings
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        help_text="Product status"
    )
    requires_collateral = models.BooleanField(
        default=False,
        help_text="Whether collateral is required"
    )
    auto_approve = models.BooleanField(
        default=False,
        help_text="Whether to auto-approve eligible applications"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Loan Product")
        verbose_name_plural = _("Loan Products")
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['product_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.min_amount} to {self.max_amount}"
    
    @property
    def is_active(self):
        """Check if product is active."""
        return self.status == 'Active'
    
    def calculate_monthly_payment(self, amount, term_months):
        """Calculate monthly payment for given amount and term."""
        if self.interest_type == 'Fixed':
            # Simple interest calculation
            total_interest = (amount * self.interest_rate * term_months) / (100 * 12)
            return (amount + total_interest) / term_months
        else:
            # For variable/reducing balance, use more complex calculation
            # This is a simplified version
            monthly_rate = self.interest_rate / (100 * 12)
            if monthly_rate == 0:
                return amount / term_months
            return amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)


class LoanApplication(models.Model):
    """Clean loan application model."""
    
    # Application status
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Disbursed', 'Disbursed'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Defaulted', 'Defaulted'),
        ('Cancelled', 'Cancelled'),
    ]
    
    # Application priority
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    # Unique identifier
    application_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique application identifier"
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='loan_applications',
        help_text="Company this application belongs to"
    )
    
    # Applicant details
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loan_applications',
        help_text="User applying for the loan"
    )
    
    # Loan product
    loan_product = models.ForeignKey(
        LoanProduct,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="Loan product being applied for"
    )
    
    # Loan details
    requested_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount requested"
    )
    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount approved"
    )
    term_months = models.IntegerField(
        help_text="Loan term in months"
    )
    purpose = models.TextField(
        help_text="Purpose of the loan"
    )
    
    # Application metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft',
        help_text="Application status"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium',
        help_text="Application priority"
    )
    
    # Financial information
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Applicant's monthly income"
    )
    monthly_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Applicant's monthly expenses"
    )
    credit_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Applicant's credit score"
    )
    
    # Employment information
    employer = models.CharField(
        max_length=200,
        blank=True,
        help_text="Current employer"
    )
    employment_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of employment"
    )
    employment_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Employment duration in months"
    )
    
    # Approval workflow
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loan_applications',
        help_text="User who reviewed the application"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loan_applications',
        help_text="User who approved the application"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the application was approved"
    )
    
    # Disbursement
    disbursed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the loan was disbursed"
    )
    disbursement_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Method of disbursement"
    )
    
    # Additional fields
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the application was submitted"
    )
    
    class Meta:
        verbose_name = _("Loan Application")
        verbose_name_plural = _("Loan Applications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['loan_product']),
            models.Index(fields=['application_id']),
        ]
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.requested_amount} ({self.status})"
    
    @property
    def is_pending(self):
        """Check if application is pending."""
        return self.status in ['Submitted', 'Under Review']
    
    @property
    def is_approved(self):
        """Check if application is approved."""
        return self.status == 'Approved'
    
    @property
    def is_active(self):
        """Check if loan is active."""
        return self.status in ['Disbursed', 'Active']
    
    @property
    def monthly_payment(self):
        """Calculate monthly payment."""
        if self.approved_amount and self.loan_product:
            return self.loan_product.calculate_monthly_payment(
                self.approved_amount, 
                self.term_months
            )
        return Decimal('0.00')
    
    @property
    def total_interest(self):
        """Calculate total interest."""
        if self.approved_amount and self.loan_product:
            return (self.approved_amount * self.loan_product.interest_rate * self.term_months) / (100 * 12)
        return Decimal('0.00')
    
    def submit(self):
        """Submit the application for review."""
        self.status = 'Submitted'
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at'])
    
    def approve(self, approver, approved_amount=None):
        """Approve the application."""
        self.status = 'Approved'
        self.approved_by = approver
        self.approved_at = timezone.now()
        if approved_amount:
            self.approved_amount = approved_amount
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'approved_amount'])
    
    def reject(self, reviewer, reason):
        """Reject the application."""
        self.status = 'Rejected'
        self.reviewed_by = reviewer
        self.rejection_reason = reason
        self.save(update_fields=['status', 'reviewed_by', 'rejection_reason'])
    
    def disburse(self, disbursement_method):
        """Disburse the loan."""
        self.status = 'Disbursed'
        self.disbursed_at = timezone.now()
        self.disbursement_method = disbursement_method
        self.save(update_fields=['status', 'disbursed_at', 'disbursement_method'])
    
    def get_absolute_url(self):
        """Get URL for loan application detail view."""
        from django.urls import reverse
        return reverse('finance:loan-application-detail', kwargs={'pk': self.pk})


class LoanPayment(models.Model):
    """Simple loan payment tracking."""
    
    # Payment types
    PAYMENT_TYPE_CHOICES = [
        ('Principal', 'Principal'),
        ('Interest', 'Interest'),
        ('Fee', 'Fee'),
        ('Penalty', 'Penalty'),
        ('Full', 'Full Payment'),
    ]
    
    # Payment status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    loan_application = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Loan application this payment belongs to"
    )
    
    # Payment details
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        help_text="Type of payment"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Payment amount"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Payment currency"
    )
    
    # Payment metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Payment status"
    )
    due_date = models.DateField(
        help_text="Payment due date"
    )
    paid_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was made"
    )
    
    # Payment method
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Method of payment"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment reference"
    )
    
    # Late payment tracking
    is_late = models.BooleanField(
        default=False,
        help_text="Whether payment is late"
    )
    late_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Late payment fee"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Loan Payment")
        verbose_name_plural = _("Loan Payments")
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['loan_application', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.loan_application} - {self.amount} ({self.status})"
    
    @property
    def is_overdue(self):
        """Check if payment is overdue."""
        return self.due_date < timezone.now().date() and self.status != 'Completed'
    
    def mark_paid(self, payment_method=None, reference=None):
        """Mark payment as completed."""
        self.status = 'Completed'
        self.paid_date = timezone.now()
        if payment_method:
            self.payment_method = payment_method
        if reference:
            self.reference = reference
        self.save(update_fields=['status', 'paid_date', 'payment_method', 'reference'])


class LoanCollateral(models.Model):
    """Enhanced collateral management with smart tracking features."""
    
    # Collateral types
    COLLATERAL_TYPE_CHOICES = [
        ('Real Estate', 'Real Estate'),
        ('Vehicle', 'Vehicle'),
        ('Equipment', 'Equipment'),
        ('Inventory', 'Inventory'),
        ('Securities', 'Securities'),
        ('Cash', 'Cash'),
        ('Other', 'Other'),
    ]
    
    # Collateral status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Released', 'Released'),
    ]
    
    loan_application = models.OneToOneField(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name='loan_collateral',
        help_text="Loan application this collateral secures"
    )
    
    # Collateral details
    collateral_type = models.CharField(
        max_length=20,
        choices=COLLATERAL_TYPE_CHOICES,
        help_text="Type of collateral"
    )
    description = models.TextField(
        help_text="Description of the collateral"
    )
    estimated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Estimated value of collateral"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency of estimated value"
    )
    
    # Collateral status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Collateral status"
    )
    
    # Verification
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_collaterals',
        help_text="User who verified the collateral"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When collateral was verified"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Notes from verification"
    )
    
    # Documentation
    documents = models.JSONField(
        default=list,
        blank=True,
        help_text="Links to collateral documents"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Loan Collateral")
        verbose_name_plural = _("Loan Collaterals")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.collateral_type} - {self.estimated_value} ({self.status})"
    
    @property
    def is_verified(self):
        """Check if collateral is verified."""
        return self.status == 'Verified'
    
    @property
    def is_accepted(self):
        """Check if collateral is accepted."""
        return self.status == 'Accepted'
    
    def verify(self, verifier, notes=None):
        """Verify the collateral."""
        self.status = 'Verified'
        self.verified_by = verifier
        self.verified_at = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save(update_fields=['status', 'verified_by', 'verified_at', 'verification_notes'])
    
    def accept(self):
        """Accept the collateral."""
        self.status = 'Accepted'
        self.save(update_fields=['status'])
    
    def reject(self, reason):
        """Reject the collateral."""
        self.status = 'Rejected'
        self.verification_notes = f"Rejected: {reason}"
        self.save(update_fields=['status', 'verification_notes'])
