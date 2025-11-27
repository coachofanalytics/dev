# -*- coding: utf-8 -*-
"""
Finance Loan Models

Loan-related models including LoanProduct, LoanApplication, LoanPayment, and related models.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal

# Get the User model
User = get_user_model()


# =============================================================================
# LOAN MODELS
# =============================================================================

class LoanProduct(models.Model):
    """Loan product/plan definitions"""
    
    name = models.CharField(max_length=100, help_text="Name of the loan product")
    description = models.TextField(help_text="Detailed description of the loan product")
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum loan amount")
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum loan amount")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Interest rate percentage")
    term_months = models.PositiveIntegerField(help_text="Loan term in months")
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional fees")
    is_active = models.BooleanField(default=True, help_text="Whether this product is available")
    min_credit_score = models.PositiveIntegerField(blank=True, null=True, help_text="Minimum credit score required")
    
    # Additional fields for better product categorization
    product_type = models.CharField(
        max_length=50, 
        choices=[
            ('staff_emergency', 'Staff Emergency'),
            ('staff_development', 'Staff Development'),
            ('kcc_premium', 'KCC Premium'),
            ('business_startup', 'Business Startup'),
            ('education', 'Education'),
            ('home_improvement', 'Home Improvement'),
            ('medical_emergency', 'Medical Emergency'),
            ('vehicle_purchase', 'Vehicle Purchase'),
            ('debt_consolidation', 'Debt Consolidation'),
            ('wedding_events', 'Wedding & Events'),
            ('general', 'General Purpose'),
        ],
        default='general',
        help_text="Type/category of loan product"
    )
    requirements = models.TextField(
        blank=True, 
        null=True,
        help_text="Requirements and eligibility criteria for this loan product"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Loan Product'
        verbose_name_plural = 'Loan Products'
    
    def __str__(self):
        return f"{self.name} ({self.interest_rate}% for {self.term_months} months)"
    
    def calculate_monthly_payment(self, principal, term_months):
        """Calculate monthly payment using simple interest formula"""
        if term_months == 0:
            return principal
        
        # SIMPLE INTEREST CALCULATION: Principal + (Principal × Rate) = Total Payable
        # For monthly payments, divide total by number of months
        interest_amount = principal * (self.interest_rate / 100)
        total_payable = principal + interest_amount
        monthly_payment = total_payable / term_months
        
        return round(monthly_payment, 2)
    
    def calculate_simple_interest_payment(self, principal, term_weeks):
        """Calculate payment using simple interest for weekly terms (KCC loans)"""
        if term_weeks == 0:
            return principal
        
        # SIMPLE INTEREST: Principal + (Principal × Rate) = Total Payable
        interest_amount = principal * (self.interest_rate / 100)
        total_payable = principal + interest_amount
        weekly_payment = total_payable / term_weeks
        
        return round(weekly_payment, 2)
    
    def calculate_total_payable(self, principal, term_weeks=None, term_months=None):
        """Calculate total payable amount using simple interest"""
        if term_weeks is None and term_months is None:
            term_weeks = 1  # Default to 1 week if no term specified
        
        # SIMPLE INTEREST: Principal + (Principal × Rate) = Total Payable
        interest_amount = principal * (self.interest_rate / 100)
        total_payable = principal + interest_amount
        
        return round(total_payable, 2)

    @property
    def min_term_months(self):
        """
        Backwards-compatible accessor for legacy code paths.
        Production schema only stores `term_months`.
        """
        return self.term_months

    @property
    def max_term_months(self):
        """
        Backwards-compatible accessor for legacy code paths.
        Production schema only stores `term_months`.
        """
        return self.term_months


class LoanApplication(models.Model):
    """Clean loan application model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_guarantor', 'Pending Guarantor Approval'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('repaid', 'Repaid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    application_number = models.CharField(max_length=20, unique=True, blank=True, help_text="Auto-generated application number")
    # loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE, help_text="Selected loan product")
    loan_product = models.ForeignKey(
            LoanProduct, 
            on_delete=models.CASCADE, 
            null=True,  # Add this
            blank=True,  # Add this
            help_text="Selected loan product"
    )
    loan_plan_id = models.IntegerField(default=1, help_text="Legacy loan plan ID")
    borrower = models.ForeignKey("accounts.CustomerUser", on_delete=models.CASCADE, related_name='loan_applications')
    
    # Guarantor fields
    guarantor = models.ForeignKey(
        'accounts.CustomerUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='guaranteed_loans',
        help_text="Guarantor for this loan"
    )
    guarantor_relationship = models.CharField(
        max_length=100, 
        choices=[
            ('family', 'Family Member'),
            ('friend', 'Friend'),
            ('colleague', 'Colleague'),
            ('employer', 'Employer'),
            ('other', 'Other')
        ],
        blank=True,
        help_text="Relationship to guarantor"
    )
    guarantor_consent_date = models.DateTimeField(null=True, blank=True, help_text="When guarantor gave consent")
    guarantor_eligibility_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Guarantor eligibility score (0-100)"
    )
    guarantor_approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved by Guarantor'),
            ('rejected', 'Rejected by Guarantor'),
            ('expired', 'Approval Expired')
        ],
        default='pending',
        help_text="Current guarantor approval status"
    )
    
    # Loan details
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount requested (stored in USD)")
    purpose = models.TextField(help_text="Purpose of the loan")
    collateral = models.TextField(blank=True, null=True, help_text="Additional collateral information")
    duration = models.PositiveIntegerField(default=12, help_text="Loan duration in months")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="Interest rate percentage")
    
    # Financial calculations
    total_payable = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey("accounts.CustomerUser", on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    
    # Eligibility Information
    credit_score = models.PositiveIntegerField(blank=True, null=True, help_text="Applicant's credit score")
    employment_status = models.CharField(max_length=20, choices=[
        ('employed', 'Employed'),
        ('self_employed', 'Self Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('retired', 'Retired'),
    ], blank=True, help_text="Current employment status")
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Monthly income amount")
    is_eligible = models.BooleanField(default=True, help_text="Whether applicant meets basic eligibility criteria")
    
    # Status fields
    is_active = models.BooleanField(default=True, help_text="Whether this loan application is active")
    is_featured = models.BooleanField(default=False, help_text="Whether this loan application is featured")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'

    def save(self, *args, **kwargs):
        """Auto-generate application number and calculate financial terms"""
        if not self.application_number:
            today = timezone.now().strftime('%Y%m%d')
            last_app = LoanApplication.objects.filter(
                application_number__startswith='LA-{}'.format(today)
            ).order_by('-application_number').first()
            
            if last_app:
                last_num = int(last_app.application_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.application_number = 'LA-{}-{:04d}'.format(today, new_num)
        
        # Calculate financial terms
        if not self.total_payable and self.loan_product:
            interest_amount = self.amount_requested * (self.loan_product.interest_rate / 100)
            self.total_payable = self.amount_requested + interest_amount
        
        if not self.monthly_payment and self.loan_product:
            self.monthly_payment = self.loan_product.calculate_monthly_payment(self.amount_requested, self.loan_product.term_months)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} - {} - {}".format(self.application_number, self.borrower.username, self.amount_requested)
    
    @property
    def term_months(self):
        """Get term months from loan product"""
        return self.loan_product.term_months if self.loan_product else 0
    
    @property
    def balance_amount(self):
        """Calculate remaining balance for payroll deductions.
        For active loans (active, approved, disbursed), this represents the amount still owed."""
        # Check if loan is in an active state that can have payments
        # This matches the logic in views: status__in=['active', 'approved', 'disbursed']
        active_statuses = ['active', 'approved', 'disbursed']
        if self.status in active_statuses:
            # Calculate total paid from payments
            total_paid = self.total_paid
            # Return remaining balance
            if self.total_payable:
                return max(Decimal('0.00'), self.total_payable - total_paid)
            # If total_payable is not set, return 0 (shouldn't happen for active loans)
            return Decimal('0.00')
        return Decimal('0.00')
    
    @property
    def total_paid(self):
        """Calculate total amount paid from all payments"""
        return sum(payment.amount for payment in self.loan_payments.all())
    
    @property
    def next_payment_date(self):
        """Calculate next payment date based on loan start and term"""
        if self.status == 'active' and self.approved_at:
            # For now, return None - this can be enhanced later with payment scheduling
            return None
        return None
    
    @property
    def is_outstanding(self):
        """Check if loan has outstanding balance for payroll purposes"""
        return self.status == 'active' and self.balance_amount > Decimal('0.00')
    
    @property
    def user_currency(self):
        """Get the user's preferred currency based on their country"""
        from .utils import get_user_currency
        return get_user_currency(self.borrower)
    
    @property
    def is_kcc_loan(self):
        """Check if this is a KCC member loan"""
        try:
            if hasattr(self.borrower, 'profile') and self.borrower.profile:
                return self.borrower.profile.is_karen_country_club_member
            return False
        except Exception:
            return False
    
    @property
    def kcc_performance_tier(self):
        """Get KCC performance tier from user profile"""
        try:
            if hasattr(self.borrower, 'profile') and self.borrower.profile:
                return self.borrower.profile.kcc_performance_tier
            return None
        except Exception:
            return None
    
    @property
    def kcc_benefits(self):
        """Get KCC benefits for this loan"""
        try:
            if hasattr(self.borrower, 'profile') and self.borrower.profile:
                return self.borrower.profile.kcc_benefits
            return None
        except Exception:
            return None
    
    def send_guarantor_approval_request(self):
        """Send email to guarantor requesting approval with verification"""
        if self.guarantor and self.guarantor.email:
            from .utils import send_guarantor_approval_email
            return send_guarantor_approval_email(self)
        return False

    def process_guarantor_approval(self, approved, guarantor_user):
        """Process guarantor's approval decision"""
        if approved:
            self.guarantor_approval_status = 'approved'
            self.guarantor_consent_date = timezone.now()
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.approved_by = guarantor_user
            # Send approval notification to borrower
            from .utils import send_loan_approved_notification
            send_loan_approved_notification(self)
        else:
            self.guarantor_approval_status = 'rejected'
            self.status = 'pending_guarantor'
            # Send rejection notification to borrower with suggested guarantors
            from .utils import send_guarantor_rejection_notification
            send_guarantor_rejection_notification(self)
        
        self.save()


class LoanPayment(models.Model):
    """Simple loan payment tracking"""
    
    PAYMENT_TYPE_CHOICES = [
        ('regular', 'Regular Payment'),
        ('extra', 'Extra Payment'),
        ('late_fee', 'Late Fee'),
    ]
    
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name="loan_payments")
    payment_date = models.DateField(help_text="Date payment was made")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='regular')
    reference_number = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Payment reference number")
    notes = models.TextField(blank=True, null=True, help_text="Payment notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Loan Payment'
        verbose_name_plural = 'Loan Payments'
    
    def save(self, *args, **kwargs):
        """Auto-generate reference number"""
        if not self.reference_number:
            self.reference_number = "PAY-{}".format(timezone.now().strftime('%Y%m%d%H%M%S'))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "{} - {} - {}".format(self.reference_number, self.loan_application.application_number, self.amount)


class LoanCollateral(models.Model):
    """Enhanced collateral management with smart tracking features"""
    
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan_collateral')
    
    # Collateral type
    collateral_type = models.CharField(
        max_length=20,
        choices=[
            ('vehicle', 'Vehicle'),
            ('land_title', 'Land Title'),
            ('equipment', 'Equipment'),
            ('jewelry', 'Jewelry'),
            ('other', 'Other')
        ]
    )
    
    # Collateral details
    description = models.TextField()
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    
    # Vehicle-specific fields
    vehicle_make = models.CharField(max_length=50, blank=True, null=True)
    vehicle_model = models.CharField(max_length=50, blank=True, null=True)
    vehicle_year = models.IntegerField(blank=True, null=True)
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True)
    vehicle_title_number = models.CharField(max_length=50, blank=True, null=True)
    
    # SMART VEHICLE TRACKING FIELDS
    gps_tracking_enabled = models.BooleanField(default=False, help_text="Enable GPS tracking for vehicle collateral")
    gps_device_id = models.CharField(max_length=100, blank=True, null=True, help_text="GPS device identifier")
    gps_install_date = models.DateTimeField(blank=True, null=True, help_text="When GPS was installed")
    gps_last_location = models.CharField(max_length=200, blank=True, null=True, help_text="Last known GPS location")
    gps_last_update = models.DateTimeField(blank=True, null=True, help_text="Last GPS update timestamp")
    gps_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('offline', 'Offline'),
            ('tampered', 'Tampered')
        ],
        default='inactive',
        help_text="Current GPS tracking status"
    )
    
    # Land-specific fields
    land_location = models.CharField(max_length=200, blank=True, null=True)
    land_size = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2 acres"
    land_title_number = models.CharField(max_length=50, blank=True, null=True)
    
    # SMART LAND TITLE VERIFICATION
    title_deed_verified = models.BooleanField(default=False, help_text="Land title deed verified with government registry")
    title_deed_number = models.CharField(max_length=100, blank=True, null=True, help_text="Official title deed number")
    title_deed_verification_date = models.DateTimeField(blank=True, null=True, help_text="When title was verified")
    land_survey_done = models.BooleanField(default=False, help_text="Professional land survey completed")
    land_survey_report = models.FileField(upload_to='collateral/surveys/', blank=True, null=True, help_text="Land survey report file")
    land_photos = models.JSONField(default=list, blank=True, help_text="Array of land photo URLs")
    
    # Equipment-specific fields
    equipment_type = models.CharField(max_length=100, blank=True, null=True)
    equipment_condition = models.CharField(max_length=50, blank=True, null=True)
    
    # SMART EQUIPMENT TRACKING
    equipment_serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Equipment serial number")
    equipment_condition_report = models.FileField(upload_to='collateral/equipment/', blank=True, null=True, help_text="Equipment condition assessment report")
    equipment_photos = models.JSONField(default=list, blank=True, help_text="Array of equipment photo URLs")
    
    # REAL-TIME MONITORING
    monitoring_enabled = models.BooleanField(default=False, help_text="Enable real-time monitoring of collateral")
    monitoring_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('real_time', 'Real-time')
        ],
        default='weekly',
        help_text="How often to monitor collateral"
    )
    last_monitoring_check = models.DateTimeField(blank=True, null=True, help_text="Last monitoring check performed")
    monitoring_alerts = models.JSONField(default=list, blank=True, help_text="Array of monitoring alerts and notifications")
    
    # RISK ASSESSMENT
    risk_score = models.IntegerField(default=0, help_text="Collateral risk score (0-100)")
    risk_factors = models.JSONField(default=list, blank=True, help_text="Identified risk factors")
    mitigation_measures = models.TextField(blank=True, null=True, help_text="Risk mitigation measures implemented")
    
    # Verification details
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collateral_verifications')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Collateral'
        verbose_name_plural = 'Loan Collaterals'
    
    def __str__(self):
        return "{} - {} - ${}".format(self.get_collateral_type_display(), self.loan_application.borrower.username, self.estimated_value)
    
    def enable_gps_tracking(self, device_id, install_date=None):
        """Enable GPS tracking for vehicle collateral"""
        if self.collateral_type != 'vehicle':
            return False, "GPS tracking only available for vehicle collateral"
        
        self.gps_tracking_enabled = True
        self.gps_device_id = device_id
        self.gps_install_date = install_date or timezone.now()
        self.gps_status = 'active'
        self.save()
        
        return True, "GPS tracking enabled successfully"
    
    def update_gps_location(self, location, timestamp=None):
        """Update GPS location for vehicle collateral"""
        if not self.gps_tracking_enabled:
            return False, "GPS tracking not enabled"
        
        self.gps_last_location = location
        self.gps_last_update = timestamp or timezone.now()
        self.save()
        
        return True, "GPS location updated"
    
    def verify_title_deed(self, deed_number, verification_date=None):
        """Verify land title deed with government registry"""
        if self.collateral_type != 'land_title':
            return False, "Title deed verification only available for land collateral"
        
        self.title_deed_verified = True
        self.title_deed_number = deed_number
        self.title_deed_verification_date = verification_date or timezone.now()
        self.save()
        
        return True, "Title deed verified successfully"
    
    def add_land_survey(self, survey_report):
        """Add professional land survey report"""
        if self.collateral_type != 'land_title':
            return False, "Land survey only available for land collateral"
        
        self.land_survey_done = True
        self.land_survey_report = survey_report
        self.save()
        
        return True, "Land survey added successfully"
    
    def add_monitoring_alert(self, alert_type, message, severity='medium'):
        """Add monitoring alert for collateral"""
        alert = {
            'timestamp': timezone.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        
        if not self.monitoring_alerts:
            self.monitoring_alerts = []
        
        self.monitoring_alerts.append(alert)
        self.save()
        
        return True, "Monitoring alert added"
    
    def calculate_risk_score(self):
        """Calculate risk score based on collateral type and verification status"""
        score = 0
        
        # Base score by collateral type
        type_scores = {
            'vehicle': 30,
            'land_title': 20,
            'equipment': 40,
            'jewelry': 50,
            'other': 60
        }
        score += type_scores.get(self.collateral_type, 50)
        
        # Verification status bonus
        if self.verification_status == 'verified':
            score -= 20
        elif self.verification_status == 'rejected':
            score += 30
        
        # Smart tracking bonus
        if self.collateral_type == 'vehicle' and self.gps_tracking_enabled:
            score -= 15
        elif self.collateral_type == 'land_title' and self.title_deed_verified:
            score -= 10
        
        # Monitoring bonus
        if self.monitoring_enabled:
            score -= 5
        
        # Ensure score is within bounds
        self.risk_score = max(0, min(100, score))
        self.save(update_fields=['risk_score'])
        
        return self.risk_score


class LoanRollover(models.Model):
    """Manage loan rollovers for KCC members"""
    
    original_loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='rollovers')
    rollover_number = models.IntegerField(default=1)  # 1st, 2nd rollover
    
    # Rollover terms
    new_due_date = models.DateField()
    rollover_fee = models.DecimalField(max_digits=10, decimal_places=2)
    rollover_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=22.00)  # 22% for rollovers
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('repaid', 'Repaid'),
            ('defaulted', 'Defaulted')
        ],
        default='active'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Rollover'
        verbose_name_plural = 'Loan Rollovers'
        unique_together = ['original_loan', 'rollover_number']
    
    def __str__(self):
        return "{} - Rollover #{}".format(self.original_loan.id, self.rollover_number)
    
    @property
    def is_max_rollovers_reached(self):
        """Check if maximum rollovers (2) reached"""
        return self.rollover_number >= 2


class LoanConfiguration(models.Model):
    """Unified loan configuration with user type logic and performance scaling"""
    
    LOAN_TYPE_CHOICES = [
        ('emergency', 'Emergency Loan'),
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('payday', 'Payday Loan'),
        ('installment', 'Installment Loan'),
        ('salary_advance', 'Salary Advance'),
        ('working_capital', 'Working Capital'),
    ]
    
    # Core identification
    name = models.CharField(max_length=100, unique=True, help_text="Configuration name")
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES, help_text="Type of loan")
    
    # Base limits (standard user)
    base_min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Base minimum loan amount"
    )
    base_max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Base maximum loan amount"
    )
    
    # Interest and terms
    base_interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Base interest rate (%)"
    )
    base_min_term = models.PositiveIntegerField(help_text="Base minimum term in weeks")
    base_max_term = models.PositiveIntegerField(help_text="Base maximum term in weeks")
    
    # User type multipliers (extends base limits)
    staff_multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.00,
        help_text="Multiplier for staff users (1.00 = no change)"
    )
    kcc_multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.00,
        help_text="Multiplier for KCC members (1.00 = no change)"
    )
    external_multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.80,
        help_text="Multiplier for external users (0.80 = 20% reduction)"
    )
    
    # Performance tier modifiers (JSON field for flexibility)
    tier_modifiers = models.JSONField(
        default=dict,
        help_text="Performance tier multipliers (e.g., {'gold': 1.50, 'platinum': 2.00})"
    )
    
    # Business rules
    requires_guarantor = models.BooleanField(default=False, help_text="Requires guarantor")
    requires_collateral = models.BooleanField(default=False, help_text="Requires collateral")
    requires_approval = models.BooleanField(default=True, help_text="Requires approval")
    
    # Eligibility requirements
    min_monthly_income = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Minimum monthly income required"
    )
    min_employment_months = models.PositiveIntegerField(
        default=0,
        help_text="Minimum months of employment"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True, help_text="Is this configuration active?")
    description = models.TextField(blank=True, help_text="Configuration description")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_loanconfiguration'
        verbose_name = 'Loan Configuration'
        verbose_name_plural = 'Loan Configurations'
        ordering = ['name']
    
    def __str__(self):
        return "{} ({})".format(self.name, self.get_loan_type_display())
    
    def get_limits_for_user(self, user, user_profile=None):
        """Get loan limits for a specific user with all modifiers applied"""
        
        # Start with base limits
        limits = {
            'min_amount': self.base_min_amount,
            'max_amount': self.base_max_amount,
            'interest_rate': self.base_interest_rate,
            'min_term': self.base_min_term,
            'max_term': self.base_max_term,
            'requires_guarantor': self.requires_guarantor,
            'requires_collateral': self.requires_collateral,
            'requires_approval': self.requires_approval,
        }
        
        # Determine user type and apply multiplier
        user_type = self._get_user_type(user)
        base_multiplier = self._get_user_type_multiplier(user_type)
        
        # Apply performance tier modifier if available
        performance_multiplier = self._get_performance_multiplier(user_profile)
        
        # Calculate final multiplier
        final_multiplier = base_multiplier * performance_multiplier
        
        # Apply multipliers to amounts
        limits['max_amount'] = (self.base_max_amount * final_multiplier).quantize(Decimal('0.01'))
        
        # Apply inverse relationship to interest rate (better terms = lower rate)
        limits['interest_rate'] = max(
            (self.base_interest_rate * (2 - final_multiplier)).quantize(Decimal('0.01')),
            Decimal('5.00')  # Minimum 5% interest
        )
        
        # Extend terms for better users
        if final_multiplier > 1.00:
            extension_weeks = int((final_multiplier - 1.00) * 4)  # 4 weeks per 0.25 multiplier
            limits['max_term'] = min(self.base_max_term + extension_weeks, 52)  # Cap at 1 year
        
        return limits
    
    def _get_user_type(self, user):
        """Determine user type for multiplier application"""
        if user.category == 2:
            return 'staff'
        elif hasattr(user, 'profile') and user.profile and user.profile.is_karen_country_club_member:
            return 'kcc_member'
        else:
            return 'external'
    
    def _get_user_type_multiplier(self, user_type):
        """Get multiplier for user type"""
        if user_type == 'staff':
            return self.staff_multiplier
        elif user_type == 'kcc_member':
            return self.kcc_multiplier
        else:
            return self.external_multiplier
    
    def _get_performance_multiplier(self, user_profile):
        """Get performance tier multiplier"""
        if not user_profile or not hasattr(user_profile, 'kcc_performance_tier'):
            return Decimal('1.00')
        
        tier = user_profile.kcc_performance_tier
        return self.tier_modifiers.get(tier, Decimal('1.00'))


class LoanDecisionAudit(models.Model):
    """Audit trail for loan decisions"""
    
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='decision_audits')
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    reason = models.TextField(blank=True, null=True)
    decided_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey("accounts.CustomerUser", on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_decisions')

    class Meta:
        ordering = ['-decided_at']
        verbose_name = 'Loan Decision Audit'
        verbose_name_plural = 'Loan Decision Audits'


class LoanPerformance(models.Model):
    """Unified loan performance tracking for ALL users (staff, KCC, external) - THIN MODEL"""
    
    PAYMENT_TIMING_CHOICES = [
        ('early', 'Early Payment'),      # +20% scaling
        ('on_time', 'On Time Payment'),  # +20% scaling
        ('late', 'Late Payment'),        # -20% scaling
        ('defaulted', 'Defaulted')       # Reset to tier minimum
    ]
    
    TIER_PROGRESSION_CHOICES = [
        ('within_tier', 'Within Tier'),
        ('tier_upgrade', 'Tier Upgrade'),
        ('tier_downgrade', 'Tier Downgrade')
    ]
    
    user = models.ForeignKey("accounts.CustomerUser", on_delete=models.CASCADE, related_name='loan_performances')
    loan_application = models.ForeignKey("LoanApplication", on_delete=models.CASCADE, related_name='performance_records')
    
    # Core performance metrics (for ALL users)
    payment_timing = models.CharField(
        max_length=20,
        choices=PAYMENT_TIMING_CHOICES,
        default='on_time'
    )
    
    performance_score = models.IntegerField(default=100)  # 0-100 scale
    consecutive_successful_loans = models.IntegerField(default=0)
    consecutive_late_payments = models.IntegerField(default=0)
    
    # KCC-specific fields (only populated for KCC members)
    scaling_factor_applied = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Scaling factor applied (e.g., 1.20 for +20%) - KCC only"
    )
    
    next_loan_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calculated next loan amount after scaling - KCC only"
    )
    
    tier_progression = models.CharField(
        max_length=20,
        choices=TIER_PROGRESSION_CHOICES,
        null=True,
        blank=True,
        help_text="Tier progression status - KCC only"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Performance'
        verbose_name_plural = 'Loan Performances'
        db_table = 'finance_loanperformance'
    
    def __str__(self):
        return "{} - Loan {} - {}".format(self.user.username, self.loan_application.id, self.payment_timing)
    
    # SIMPLE COMPUTED PROPERTIES ONLY (no business logic)
    @property
    def user_type(self):
        """Simple computed property - no business logic"""
        if self.user.category == 2:  # Staff
            return 'staff'
        elif self.user.profile.is_karen_country_club_member:
            return 'kcc_member'
        else:
            return 'external'
    
    @property
    def is_kcc_member(self):
        """Simple boolean check"""
        return self.user_type == 'kcc_member'
    
    @property
    def is_staff(self):
        """Simple boolean check"""
        return self.user_type == 'staff'
    
    @property
    def has_kcc_benefits(self):
        """Check if KCC fields are populated"""
        return self.scaling_factor_applied is not None and self.next_loan_amount is not None
    
    @property
    def performance_category(self):
        """Simple categorization based on score"""
        if self.performance_score >= 80:
            return 'excellent'
        elif self.performance_score >= 60:
            return 'good'
        elif self.performance_score >= 40:
            return 'fair'
        else:
            return 'poor'
