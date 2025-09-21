from django.db import models
from datetime import datetime, date
from decimal import *
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django_countries.fields import CountryField
import logging
from django.db.models import Sum

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from investing.models import Investment_rates
except ImportError:
    Investment_rates = None

try:
    from main.models import Company, Service, ServiceCategory, TimeStampedModel
except ImportError:
    Company = Service = ServiceCategory = TimeStampedModel = None

try:
    from main.utils import dates_functionality, date_converter, PayChoices
except ImportError:
    dates_functionality = date_converter = PayChoices = None

try:
    from accounts.models import Department
except ImportError:
    Department = None

# Initialize variables if imports fail
if dates_functionality:
    ytd_duration, current_year, first_date = dates_functionality()
else:
    ytd_duration = current_year = first_date = None

# Create your models here.
class Payment_Information(models.Model):
    customer_id = models.ForeignKey(
        "accounts.CustomerUser",
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
        related_name="customer")
    payment_fees=models.IntegerField()
    down_payment=models.IntegerField(default=500)
    student_bonus=models.IntegerField(null=True,blank=True)
    # fee_balance field removed - using property instead
    plan = models.IntegerField() # assuming service_category id
    subplan = models.IntegerField(default=1,null=True, blank=True)
    pricing_plan = models.IntegerField(default=1,null=True, blank=True)
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(max_length=1000, default=None,null=True, blank=True)
    is_active = models.BooleanField('active', default=True)
    is_featured = models.BooleanField('featured', default=True)

    def __str__(self):
        return str(self.customer_id)
    
    @property
    def fee_balance(self):
        try:
            stu_bal = self.payment_fees - (int(self.down_payment) + int(self.student_bonus))
            return stu_bal
        except:
            return redirect('finance:pay')
        
    @property
    def jobsupport_balance(self):
        try:
            support_bal = self.payment_fees - int(self.down_payment) 
            return support_bal
        except:
            return redirect('finance:pay')


class Payment_History(models.Model):
    # id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        User,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
        related_name="customer_payment_history")
    payment_fees=models.IntegerField()
    down_payment=models.IntegerField(default=500)
    student_bonus=models.IntegerField(null=True,blank=True)
    # fee_balance=models.IntegerField(default=None)
    down_payment = models.IntegerField(default=500)
    student_bonus = models.IntegerField(null=True, blank=True)
    # fee_balance = models.IntegerField(default=None)
    plan = models.IntegerField() # assuming service_category id
    subplan = models.IntegerField(default=1,null=True, blank=True)
    pricing_plan = models.IntegerField(default=1,null=True, blank=True)
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(max_length=1000, default=None,null=True, blank=True)
    is_active = models.BooleanField('active', default=True)
    is_featured = models.BooleanField('featured', default=True)

    @property
    def fee_balance(self):
        try:
            # Ensure None values are handled correctly
            down_payment = int(self.down_payment or 0)
            student_bonus = int(self.student_bonus or 0)
            return self.payment_fees - (down_payment + student_bonus)
        except (TypeError, ValueError) as e:
            logger.error(f"Error calculating fee balance for Payment_History ID {self.id}: {str(e)}")
            return 0  # Return a default integer instead of a redirect

    @property
    def notification_days(self):
        last_notification_sent=date_converter(self.rep_date)
        try:
            Number_notification_days = (datetime.now().date() - last_notification_sent.date()).days
        except:
            Number_notification_days = 0

        return Number_notification_days
    
    @property
    def notification_flag(self):
        last_notification_sent=date_converter(self.rep_date)
        try:
            Number_notification_days = (datetime.now().date() - last_notification_sent.date()).days
        except:
            Number_notification_days = 0
        flag=True if Number_notification_days <7 else False
        return flag
        
    def __str__(self):
        return str(self.customer)
    

class DeletedPaymentHistory(models.Model):
    customer = models.ForeignKey(
        User,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,)
    payment_fees=models.IntegerField()
    down_payment=models.IntegerField(default=500)
    student_bonus=models.IntegerField(null=True,blank=True)
    # fee_balance=models.IntegerField(default=None)
    down_payment = models.IntegerField(default=500)
    student_bonus = models.IntegerField(null=True, blank=True)
    # fee_balance = models.IntegerField(default=None)
    plan = models.IntegerField()
    subplan = models.IntegerField(null=True)
    pricing_plan = models.IntegerField(null=True)
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.customer

class Default_Payment_Fees(models.Model):
    job_down_payment_per_month = models.IntegerField(default=500)
    job_plan_hours_per_month = models.IntegerField(default=40)
    student_down_payment_per_month = models.IntegerField(default=500)
    student_bonus_payment_per_month = models.IntegerField(default=250)

    # loan_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)

    def __str__(self):
        return str(self.id)


class PayslipConfig(models.Model):
    """Model for payslip configuration"""
    user = models.ForeignKey("accounts.CustomerUser", on_delete=models.CASCADE, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loan_repayment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rp_starting_period = models.CharField(max_length=20, null=True, blank=True)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    installment_date = models.DateField(null=True, blank=True)
    web_pay_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    web_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    laptop_status = models.BooleanField("Laptop Status", default=True)  # Added missing field

    # configs for loan
    loan_status = models.BooleanField(default=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)
    loan_repayment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.20)
    
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    installment_date = models.DateField(default=first_date,null=True,blank=True)
    # configs for laptop service
    laptop_status = models.BooleanField(default=True)
    lb_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    ls_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    ls_max_limit = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)

    # configs for retirement package
    rp_starting_period = models.CharField(max_length=10)
    rp_starting_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    rp_increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)
    rp_increment_max_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)
    rp_increment_percentage_increment = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)
    rp_increment_percentage_increment_cycle = models.IntegerField(default=12)

    # configs for bonus
    holiday_pay = models.DecimalField(max_digits=10, decimal_places=2, default=3000.00)
    night_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    # configs for deductions
    computer_maintenance = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    food_accommodation = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    health = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    kra = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)

    # employee of the month, quarter and year
    eom_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    eoq_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    eoy_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)

    # # website configs
    web_pay_hour = models.DecimalField(max_digits=10, decimal_places=2, default=30.00)
    web_delta = models.DecimalField(max_digits=10, decimal_places=2, default=3.00)

    def __str__(self):
        return str(self.loan_amount)

# ================================LOAN MODELS================================
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
    
    # LEGACY COMPLEX CALCULATION (COMMENTED OUT FOR REFERENCE)
    # def calculate_monthly_payment_legacy(self, principal, term_months):
    #     """LEGACY: Calculate monthly payment using standard loan formula"""
    #     if term_months == 0:
    #         return principal
    #     
    #     monthly_rate = self.interest_rate / 100 / 12
    #     if monthly_rate == 0:
    #         return principal / term_months
    #     
    #     # Standard loan payment formula
    #     payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    #     return round(payment, 2)


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
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE, help_text="Selected loan product")
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
                application_number__startswith=f'LA-{today}'
            ).order_by('-application_number').first()
            
            if last_app:
                last_num = int(last_app.application_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.application_number = f'LA-{today}-{new_num:04d}'
        
        # Calculate financial terms
        if not self.total_payable and self.loan_product:
            interest_amount = self.amount_requested * (self.loan_product.interest_rate / 100)
            self.total_payable = self.amount_requested + interest_amount
        
        if not self.monthly_payment and self.loan_product:
            self.monthly_payment = self.loan_product.calculate_monthly_payment(self.amount_requested, self.loan_product.term_months)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_number} - {self.borrower.username} - {self.amount_requested}"
    
    # interest_rate is now a database field, property removed to avoid conflict
    
    @property
    def term_months(self):
        """Get term months from loan product"""
        return self.loan_product.term_months if self.loan_product else 0
    
    @property
    def balance_amount(self):
        """Calculate remaining balance for payroll deductions.
        For active loans, this represents the amount still owed."""
        if self.status == 'active':
            # Calculate total paid from payments
            total_paid = self.total_paid
            # Return remaining balance
            return max(Decimal('0.00'), self.total_payable - total_paid)
        return Decimal('0.00')
    
    @property
    def total_paid(self):
        """Calculate total amount paid from all payments"""
        return sum(payment.amount for payment in self.payments.all())
    
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
    # KCC-related properties (calculated, not stored)
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
    
    @property
    def effective_interest_rate(self):
        """Calculate effective interest rate after KCC discounts"""
        if not self.is_kcc_loan or not self.kcc_benefits:
            return self.interest_rate
        
        # Apply KCC interest rate discount
        discount = self.kcc_benefits['interest_rate_discount']
        effective_rate = self.interest_rate - discount
        
        # Ensure rate doesn't go below minimum (e.g., 5%)
        return max(effective_rate, Decimal('5.00'))
    
    @property
    def effective_loan_limit(self):
        """Calculate effective loan limit based on KCC tier"""
        if not self.is_kcc_loan or not self.kcc_benefits:
            return self.loan_product.max_amount if self.loan_product else Decimal('0.00')
        
        # KCC tier may allow higher loan amounts
        kcc_limit = self.kcc_benefits['max_loan']
        product_limit = self.loan_product.max_amount if self.loan_product else Decimal('0.00')
        
        # Use the higher of the two limits
        return max(kcc_limit, product_limit)
    
    @property
    def processing_fee_discount(self):
        """Get processing fee discount for KCC members"""
        if not self.is_kcc_loan or not self.kcc_benefits:
            return Decimal('0.00')
        
        return self.kcc_benefits['processing_fee_discount']
    
    def calculate_kcc_benefits(self):
        """Calculate and apply KCC benefits to this loan"""
        if not self.is_kcc_loan:
            return {
                'interest_rate_discount': Decimal('0.00'),
                'processing_fee_discount': Decimal('0.00'),
                'max_loan_increase': Decimal('0.00'),
                'total_benefits': Decimal('0.00')
            }
        
        try:
            benefits = self.kcc_benefits
            if not benefits:
                return {
                    'interest_rate_discount': Decimal('0.00'),
                    'processing_fee_discount': Decimal('0.00'),
                    'max_loan_increase': Decimal('0.00'),
                    'total_benefits': Decimal('0.00')
                }
            
            # Calculate benefits
            interest_discount = benefits['interest_rate_discount']
            processing_discount = benefits['processing_fee_discount']
            
            # Calculate loan amount increase
            base_limit = self.loan_product.max_amount if self.loan_product else Decimal('0.00')
            kcc_limit = benefits['max_loan']
            loan_increase = max(Decimal('0.00'), kcc_limit - base_limit)
            
            # Calculate total monetary benefit
            total_benefits = interest_discount + processing_discount + (loan_increase * Decimal('0.01'))
            
            return {
                'interest_rate_discount': interest_discount,
                'processing_fee_discount': processing_discount,
                'max_loan_increase': loan_increase,
                'total_benefits': total_benefits
            }
            
        except Exception as e:
            logger.error(f"Error calculating KCC benefits for loan {self.id}: {e}")
            return {
                'interest_rate_discount': Decimal('0.00'),
                'processing_fee_discount': Decimal('0.00'),
                'max_loan_increase': Decimal('0.00'),
                'total_benefits': Decimal('0.00')
            }

    def amount_in_user_currency(self):
        """Get the loan amount in the user's preferred currency"""
        from .utils import convert_from_usd
        return convert_from_usd(self.amount_requested, self.user_currency)
    
    @property
    def total_payable_in_user_currency(self):
        """Get the total payable amount in the user's preferred currency"""
        from .utils import convert_from_usd
        if self.total_payable:
            return convert_from_usd(self.total_payable, self.user_currency)
        return Decimal('0.00')
    
    @property
    def monthly_payment_in_user_currency(self):
        """Get the monthly payment in the user's preferred currency"""
        from .utils import convert_from_usd
        if self.monthly_payment:
            return convert_from_usd(self.monthly_payment, self.user_currency)
        return Decimal('0.00')
    
    @property
    def balance_in_user_currency(self):
        """Get the balance amount in the user's preferred currency"""
        from .utils import convert_from_usd
        return convert_from_usd(self.balance_amount, self.user_currency)
    
    def format_amount_for_user(self, amount, show_symbol=True):
        """Format an amount in the user's preferred currency"""
        from .utils import format_currency_amount
        user_currency = self.user_currency
        if user_currency != 'USD':
            amount = convert_from_usd(amount, user_currency)
        return format_currency_amount(amount, user_currency, show_symbol)
    
    def calculate_monthly_deduction(self, salary_amount, percentage):
        """Calculate monthly deduction amount based on salary and percentage"""
        deduction = salary_amount * (Decimal(str(percentage)) / Decimal('100'))
        return min(deduction, self.balance_amount)
    
    def make_payment(self, amount):
        """Record a payment against this loan"""
        from .models import LoanPayment
        LoanPayment.objects.create(
            loan_application=self,
            payment_date=timezone.now().date(),
            amount=amount,
            payment_type='regular',
            notes=f'Payroll deduction - {timezone.now().strftime("%Y-%m")}'
        )
    
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
    
    def validate_eligibility(self):
        """Validate loan eligibility based on criteria
        - Must have a product
        - Enforce product min credit score if provided
        - Unemployed applicants are not eligible
        - Basic affordability: income >= 3x monthly_payment when income provided
        - Staff policy:
          * Compute/accept monthly_income
          * General cap = 2x monthly_income
          * If monthly_income < $50, cap = min($100, 2x monthly_income)
          Note: Exceeding staff cap no longer hard-fails eligibility; it will be handled in decision layer.
        """
        if not self.loan_product:
            return False, "No loan product selected"
        
        # Check credit score if required
        if self.loan_product.min_credit_score and self.credit_score:
            if self.credit_score < self.loan_product.min_credit_score:
                return False, f"Credit score {self.credit_score} below minimum {self.loan_product.min_credit_score}"
        
        # Check employment status
        if self.employment_status == 'unemployed':
            return False, "Unemployed applicants are not eligible"
        
        # Staff-specific caps (advisory - decision handled later)
        try:
            borrower_category = getattr(self.borrower, 'category', None)
        except Exception:
            borrower_category = None
        if borrower_category == 2 and self.monthly_income is not None:
            try:
                income = Decimal(self.monthly_income)
                cap = income * Decimal('2')
                if income < Decimal('50'):
                    cap = min(Decimal('100'), cap)
                if self.amount_requested > cap:
                    # Advisory message; do not fail eligibility
                    return True, f"Requested amount {self.amount_requested} exceeds staff cap {cap} based on income {income}"
            except Exception:
                pass
        
        # Affordability check when income provided
        if self.monthly_income and self.loan_product.min_amount:
            if self.monthly_income < (self.monthly_payment * 3):
                return False, "Monthly income insufficient for loan amount"
        
        return True, "Eligibility criteria met"

    def _compute_average_monthly_income_last_3_months(self) -> Decimal:
        """Compute average of last 3 calendar months income from TaskHistory.get_pay.
        Returns None if no records are found or average is zero, so caller can route to under_review.
        Prefer using management.utils.emp_average_earnings to avoid duplicating logic.
        If that yields no data, fall back to scanning the last 12 months and averaging the most recent
        3 active months (months with any earnings > 0).
        """
        # Preferred path: use existing helper if available
        try:
            from management.models import TaskHistory
            from management.utils import emp_average_earnings
            avg = emp_average_earnings(None, TaskHistory, 0, self.borrower)
            try:
                avg_dec = Decimal(str(avg))
            except Exception:
                avg_dec = None
            if not avg_dec or avg_dec <= 0:
                avg_dec = None
            if avg_dec:
                return avg_dec.quantize(Decimal('0.01'))
        except Exception:
            TaskHistory = None  # will try fallback

        # Fallback: direct computation via TaskHistory query over last 12 months,
        # averaging the most recent 3 active months
        try:
            if TaskHistory is None:
                from management.models import TaskHistory
        except Exception:
            return None
        now = timezone.now()
        lookback_start = (now - relativedelta(months=12)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        try:
            tasks = TaskHistory.objects.filter(
                employee=self.borrower,
                submission__gte=lookback_start,
                submission__lte=now,
            )
        except Exception:
            return None
        month_totals = {}
        for t in tasks:
            try:
                dt = t.submission
                key = (dt.year, dt.month)
                month_totals.setdefault(key, Decimal('0'))
                month_totals[key] += Decimal(t.get_pay or 0)
            except Exception:
                continue
        if not month_totals:
            return None
        # Sort by year, month descending and take the most recent 3 active months
        active_months = [(ym, total) for ym, total in month_totals.items() if total and total > 0]
        if not active_months:
            return None
        active_months.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
        top3 = active_months[:3]
        if not top3:
            return None
        avg = sum(total for _, total in top3) / Decimal(len(top3))
        if avg <= 0:
            return None
        return avg.quantize(Decimal('0.01'))
    
    def submit_application(self):
        """Submit the application for review"""
        if self.status == 'draft':
            # Validate eligibility before submission
            is_eligible, message = self.validate_eligibility()
            if not is_eligible:
                raise ValueError(f"Application not eligible: {message}")
            
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()
    
    def approve_application(self, approved_by_user):
        """Approve the application"""
        if self.status == 'submitted':
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.approved_by = approved_by_user
            self.save()
    
    def reject_application(self, reason):
        """Reject the application with reason"""
        if self.status == 'submitted':
            self.status = 'rejected'
            self.save()

    def auto_decide_application(self):
        """Automatically decide application status based on eligibility and borrower profile.
        - If not eligible -> rejected
        - If eligible and borrower is staff (category 2):
            - If monthly_income is provided or computable:
                - If income < $50, cap = min($100, 2*income)
                - If requested > cap -> rejected
                - Else -> approved
            - If income missing/unavailable -> under_review
        - Else -> under_review
        """
        is_eligible, _ = self.validate_eligibility()
        if not is_eligible:
            if self.status != 'rejected':
                prev = self.status
                self.status = 'rejected'
                self.save()
                try:
                    self.log_decision(prev, 'rejected', reason='Eligibility check failed')
                except Exception:
                    pass
            return 'rejected'

        try:
            borrower_category = getattr(self.borrower, 'category', None)
        except Exception:
            borrower_category = None

        if borrower_category == 2:  # staff
            # If income missing, derive from TaskHistory average of last 3 months
            income = None
            if self.monthly_income is None:
                try:
                    income = self._compute_average_monthly_income_last_3_months()
                    self.monthly_income = income
                except Exception:
                    income = None
            else:
                try:
                    income = Decimal(self.monthly_income)
                except Exception:
                    income = None

            if income is None:
                if self.status != 'under_review':
                    prev = self.status
                    self.status = 'under_review'
                    self.save()
                    try:
                        self.log_decision(prev, 'under_review', reason='No income history available')
                    except Exception:
                        pass
                return 'under_review'

            # Enforce staff cap using computed income
            cap = income * Decimal('2')
            if income < Decimal('50'):
                cap = min(Decimal('100'), cap)
            if self.amount_requested > cap:
                prev = self.status
                self.status = 'rejected'
                self.save()
                try:
                    self.log_decision(prev, 'rejected', reason=f'Requested {self.amount_requested} exceeds staff cap {cap} with income {income}')
                except Exception:
                    pass
                return 'rejected'

            # Auto-approve within staff policy
            prev = self.status
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.approved_by = None
            self.save()
            try:
                self.log_decision(prev, 'approved', reason=f'Auto-approve within cap {cap} and income {income}')
            except Exception:
                pass
            return 'approved'

        # Default: mark for manual review
        if self.status != 'under_review':
            prev = self.status
            self.status = 'under_review'
            self.save()
            try:
                self.log_decision(prev, 'under_review', reason='Non-staff auto-review')
            except Exception:
                pass
        return 'under_review'

    def compute_staff_cap(self, income: Decimal):
        try:
            income = Decimal(income)
        except Exception:
            return None
        cap = income * Decimal('2')
        if income < Decimal('50'):
            cap = min(Decimal('100'), cap)
        return cap

    @property
    def staff_cap(self):
        try:
            if getattr(self.borrower, 'category', None) == 2 and self.monthly_income is not None:
                return self.compute_staff_cap(self.monthly_income)
        except Exception:
            pass
        return None

    def log_decision(self, previous_status: str, new_status: str, reason: str = '', decided_by=None):
        try:
            LoanDecisionAudit.objects.create(
                loan_application=self,
                previous_status=previous_status,
                new_status=new_status,
                reason=reason,
                decided_by=decided_by
            )
        except Exception:
            # Do not fail main flow due to audit issues
            pass

    def recompute_and_decide(self, decided_by=None):
        prev_status = self.status
        # Recompute income
        income = self._compute_average_monthly_income_last_3_months()
        if income is None:
            # Always set to under_review when no history
            new_status = 'under_review'
            if self.status != new_status:
                self.status = new_status
                self.save()
            self.log_decision(prev_status, self.status, reason='Recompute: no income history; setting under_review', decided_by=decided_by)
            return {
                'status': self.status,
                'monthly_income': None,
                'cap': None,
                'reason': 'No income history for last periods'
            }
        # Set income and decide
        self.monthly_income = income
        is_eligible, message = self.validate_eligibility()
        new_status = self.auto_decide_application()
        cap = self.staff_cap
        reason = f"Recompute: income={income}; cap={cap}; eligibility={message}"
        self.log_decision(prev_status, new_status, reason=reason, decided_by=decided_by)
        return {
            'status': new_status,
            'monthly_income': income,
            'cap': cap,
            'reason': reason
        }


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
    reference_number = models.CharField(max_length=50, unique=True, help_text="Payment reference number")
    notes = models.TextField(blank=True, null=True, help_text="Payment notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Loan Payment'
        verbose_name_plural = 'Loan Payments'
    
    def save(self, *args, **kwargs):
        """Auto-generate reference number"""
        if not self.reference_number:
            self.reference_number = f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reference_number} - {self.loan_application.application_number} - {self.amount}"


# -------------------------------------CASH FLOW MODEL---------------------------------------
class Inflow(models.Model):
    def get_paychoices_display_name(self):
        return dict(PayChoices.choices).get(self.category, 'Unknown')
       
    # Period of Payment
    PERIOD_CHOICES = [
        ("Weekly", "Weekly"),
        ("Bi_Weekly", "Bi_Weekly"),
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    ]
    method =models.IntegerField(choices=PayChoices.choices, default=999)
    period = models.CharField(max_length=25,choices=PERIOD_CHOICES,default="Other")
    receiver = models.ForeignKey("accounts.CustomerUser", 
                                 on_delete=models.CASCADE,
                                 limit_choices_to={"is_staff": True, "is_active": True}, 
                                 related_name="inflows")
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_name",default=1)
    category = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="category_name",default=1)
    subcategory = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="subcategory_name",default=1)
    country = CountryField(blank=True, null=True)
    sender = models.CharField(max_length=100, null=True, default=None)
    phone = models.CharField(max_length=50, null=True, default=None)
    transaction_date = models.DateTimeField(default=timezone.now)
    item = models.CharField(max_length=255, blank=True, null=True)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    transaction_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )
    description = models.TextField(max_length=1000, default=None)

    class Meta:
        ordering = ["transaction_date"]

    def get_absolute_url(self):
        return reverse("management:inflow-detail", kwargs={"pk": self.pk})

    @property
    def end(self):
        # date_time = datetime.datetime.now() + datetime.timedelta(hours=2)
        date_time = self.login_date + datetime.timedelta(hours=0)
        endtime = date_time.strftime("%H:%M")
        return endtime
    
    # Computing total payment
    @property
    def total_payment(self):
        if self.amount and self.qty:
            return round(Decimal(self.amount) * Decimal(self.qty), 2)
        return Decimal('0.00')
    
    @property
    def total_paid(self):
        if self.has_paid==True:
            total_amt_paid =  round(Decimal(self.amount), 2)
            return total_amt_paid


class DC48_Inflow(models.Model):
    CLIENTS_CHOICES = [
        ("DYC", "Diaspora Youth Caucus"),
        ("DC48KENYA", "DC48KENYA"),
        ("Other", "Other"),
    ]

    PERIOD_CHOICES = [
        ("Weekly", "Weekly"),
        ("Bi_Weekly", "Bi_Weekly"),
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    ]
    CAT_CHOICES = [
        ("Registration Fee", "Registration Fee"),
        ("Contributions", "Contributions"),
        ("Donations", "Donations"),
        ("GC Application", "GC Application"),
        ("Business", "Business"),
        ("Tourism", "Tourism"),
        ("Stocks", "Stocks"),
        ("Other", "Other"),
    ]

    PAY_CHOICES = [
        ("Cash", "Cash"),
        ("Mpesa", "Mpesa"),
        ("Check", "Check"),
        ("Cashapp", "Cashapp"),
        ("Zelle", "Zelle"),
        ("Venmo", "Venmo"),
        ("Paypal", "Paypal"),
        ("Other", "Other"),
    ]

    clients_category = models.CharField(
        max_length=25,
        choices=CLIENTS_CHOICES,
        default="Other",
    )

    category = models.CharField(
        max_length=25,
        choices=CAT_CHOICES,
        default="Other",
        
    )
    method = models.CharField(
        max_length=25,
        choices=PAY_CHOICES,
        default="Other",
    )

    period = models.CharField(
        max_length=25,
        choices=PERIOD_CHOICES,
        default="Other",
    )
    sender = models.ForeignKey(
        "accounts.CustomerUser", 
        on_delete=models.CASCADE, 
        limit_choices_to=(Q(sub_category=6) |Q(sub_category=7)|Q(is_superuser=True)),
        # limit_choices_to={"category": 4, "is_active": True },
        related_name="dc_inflows")
    receiver = models.CharField(max_length=100, null=True, default=None)
    phone = models.CharField(max_length=50, null=True, default=None)
    transaction_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    transaction_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )
    description = models.TextField(max_length=1000, default=None)
    is_active=models.BooleanField(default=True,null=True,blank=True)
    has_paid=models.BooleanField(default=False,null=True,blank=True)

    class Meta:
        ordering = ["transaction_date"]

    def get_absolute_url(self):
        return reverse("management:inflow-detail", kwargs={"pk": self.pk})

    @property
    def end(self):
        # date_time = datetime.datetime.now() + datetime.timedelta(hours=2)
        date_time = self.login_date + datetime.timedelta(hours=0)
        endtime = date_time.strftime("%H:%M")
        return endtime
    # Computing total payment
    @property
    def receipturl(self):
        if self.receipt_link is not None:
            urlreceipt = self.receipt_link
            return urlreceipt
        else:
            return redirect('main:layout')

    @property
    def total_payment(self):
        total_amount = round(Decimal(self.amount), 2)
        return total_amount

    @property
    def total_paid(self):
        if self.has_paid:
            try:
                total_amt_paid =  round(Decimal(self.amount), 2)
            except:
                total_amt_paid=0.00
            return total_amt_paid
            
class BudgetCategory(models.Model):
    name = models.CharField(max_length=100,null=True,blank=True,default='Operations')
    description = models.TextField(max_length=1000,null=True,blank=True)

    class Meta:
        verbose_name = _("Budget Category")
        verbose_name_plural = _("Budget Categories")
        ordering = ['name']

    def __str__(self):
        return self.name
    
class BudgetSubCategory(models.Model):
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("Budget Sub category")
        verbose_name_plural = _("Budget Sub categories")
        ordering = ['category', 'name']

    def __str__(self):
        # return f"{self.category.name}-{self.name}"
        return f"{self.name}"


class Transaction(models.Model):
    # # Method of Category
    CAT_CHOICES = [
        ("Salary", "Salary"),
        ("Health", "Health"),
        ("Transport", "Transport"),
        ("Food_Accomodation", "Food & Accomodation"),
        ("Internet_Airtime", "Internet & Airtime"),
        ("Recruitment", "Recruitment"),
        ("Labour", "Labour"),
        ("Management", "Management"),
        ("Electricity", "Electricity"),
        ("Construction", "Construction"),
        ("Other", "Other"),
    ]
    # Method of Payment
    PAY_CHOICES = [
        ("Cash", "Cash"),
        ("Mpesa", "Mpesa"),
        ("Check", "Check"),
        ("Other", "Other"),
    ]
    sender = models.ForeignKey(
         User,
         verbose_name=_("sender"),
         related_name="sender", 
         null=True, blank=True,
         on_delete=models.SET_NULL,
         limit_choices_to={"is_staff": True, "is_active": True},
         )
    vendor_supplier = models.ForeignKey(
         User,
         verbose_name=_("vendor_supplier"),
         related_name="vendor_supplier", 
         null=True, blank=True,
         on_delete=models.SET_NULL,
        #  limit_choices_to={"is_staff": True, "is_active": True},
         limit_choices_to=Q(is_active=True) & (Q(is_staff=True) | Q(category=6)),
         )
    receiver = models.CharField(max_length=100, null=True, default=None)
    phone = models.CharField(max_length=50, null=True, default=None)
    department = models.ForeignKey(
        to=Department, on_delete=models.CASCADE, default=None
        )
    
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE, 
        related_name="transaction_category",
        blank=True, null=True)
    
    subcategory = models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE, 
        related_name="transaction_subcategory",
        blank=True, null=True)
    
    # type = models.CharField(max_length=100, default=None, null=True)
    type = models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default="Other",
    )
    transaction_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    transaction_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )
    description = models.TextField(max_length=1000,blank=True, null=True, default=None)

    payment_method = models.CharField(
        max_length=25,
        choices=PAY_CHOICES,
        default="Other",
    )

    @property
    def total_payment(self):
        total_payment = self.amount * self.qty
        return total_payment
    
    def get_absolute_url(self):
        return reverse("management:transaction-detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "Transactions"
        ordering = ["-transaction_date"]

    def __str__(self):
        return f"{self.id} Transactions"
    
class CodaBudget(TimeStampedModel):
    budget_lead = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        limit_choices_to=(Q(is_staff=True, is_active=True, category=2) | Q(is_superuser=True)),
        related_name="lead"
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_budgets')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='department_budgets')
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE, 
        related_name="budgetcategory",
        blank=True, null=True)
    
    subcategory = models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE, 
        related_name="budget_subcategory",
        blank=True, null=True)
    
    item = models.CharField(max_length=100, null=True, default=None)
    cases = models.PositiveIntegerField(default=1, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    description = models.TextField(max_length=1000, default=None)
    receipt_link = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.department.name} - {self.category.name} - {self.subcategory.name}-{self.created_at}"

    class Meta:
        verbose_name = _("Coda Budget")
        verbose_name_plural = _("Coda Budget")
        ordering = ['department','created_at', 'category', 'subcategory']

    @property
    def amount(self):
        if self.unit_price and self.qty:
            return round(Decimal(self.unit_price) * Decimal(self.qty), 2)
        return Decimal('0.00')


class Budget(models.Model):
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name="company_type",
        default=1)
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name="department_type",
        default=1)
    
    budget_lead = models.ForeignKey(
        "accounts.CustomerUser", 
        on_delete=models.CASCADE, 
        limit_choices_to=(Q(is_staff=True,is_active=True,category=2)|Q(is_superuser=True)),
        related_name="budget_lead")
    
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE, 
        related_name="category_type",
        blank=True, null=True)
    
    subcategory= models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE, 
        related_name="sub_category_type",
        blank=True, null=True)
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    item = models.CharField(max_length=100, null=True, default=None)
    cases = models.PositiveIntegerField(default=1,null=True,blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    description = models.TextField(max_length=1000, default=None)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    is_active=models.BooleanField(default=True,null=True,blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.item
    
    def get_absolute_url(self):
        return reverse("management:inflow-detail", kwargs={"pk": self.pk})

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
            return redirect('main:layout')

    @property
    def amount(self):
        try:
            # total_amount = round(Decimal(self.unit_price * self.qty * self.days), 2)
            total_amount = round(Decimal(self.unit_price * self.cases* self.qty), 2)
        except:
            total_amount = 0
        return total_amount
    

# ========================Food Models============================

class Supplier(models.Model):
    added_by= models.ForeignKey(
        User,
        verbose_name=_("staff"),
        related_name="staff",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        limit_choices_to={"is_staff": True, "is_active": True},
    )
    supplier = models.CharField(
        max_length=255,
    )
    slug = models.SlugField(blank=True, null=True)
    phone = models.CharField(default="90001",
            max_length=100,
            help_text=_("Start with Country Code ie 254******"),
    )
    location = models.CharField(max_length=255,default='Makutano')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    featured=models.BooleanField(default=True)
    active=models.BooleanField(default=True)

    def get_absolute_url(self):
        return "/services/{slug}/".format(slug=self.slug)

    def __str__(self):
        return self.supplier

class Food(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.RESTRICT,
        limit_choices_to=Q(active=True)
    )
    office_location = models.CharField(
        max_length=255,       
        default= 'makutano'       
    )
    item = models.CharField(
        max_length=255,
        unique=True,
    )
    unit_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    slug = models.SlugField(blank=True, null=True)
    qty=models.PositiveIntegerField()
    bal_qty=models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    featured=models.BooleanField(default=False)
    active=models.BooleanField(default=True)

    def get_absolute_url(self):
        return "/services/{slug}/".format(slug=self.slug)

    def __str__(self):
        return self.item
    
    @property
    def budgeted_items(self):
        budgeted_qty=self.qty-self.bal_qty
        return budgeted_qty

    @property
    def total_amount(self):
        total_amount=Decimal(self.qty)*self.unit_amt
        return total_amount

    @property
    def additional_amount(self):
        additional_amount=Decimal(self.qty-self.bal_qty)*self.unit_amt
        return additional_amount

class FoodHistory(models.Model):
    item = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='history')
    supplier = models.ForeignKey(Supplier, on_delete=models.RESTRICT)
    office_location = models.CharField(max_length=255, default='makutano')
   # item = models.CharField(max_length=255)
    unit_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qty = models.PositiveIntegerField()
    bal_qty = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField()
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    history_date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return f"History of {self.item.item} on {self.history_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-history_date']  # Order by most recent changes first
        
class Field_Expense(models.Model):
    category = models.CharField(max_length=255, blank=True, default="")
    subcategory = models.CharField(max_length=255, blank=True, default="")
    phase = models.CharField(max_length=255, blank=True, default="")
    sender = models.ForeignKey(
        User,
        verbose_name=_("Sender"),
        related_name="field_expenses", 
        blank=True,
        null=True,  # This allows the field to contain NULL values
        on_delete=models.SET_NULL,
        limit_choices_to={"is_staff": True, "is_active": True},
    )
    cost_type = models.CharField(max_length=100, blank=True, default="")
    date = models.DateTimeField(default=timezone.now)
    qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    # unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    transaction_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )
    description = models.TextField(max_length=1000, blank=True, default="")

    @property
    def transactions_amt(self):
        amount = self.amount if self.amount is not None else 0.0
        transaction_cost = self.transaction_cost if self.transaction_cost is not None else 0.0
        qty = self.qty if self.qty is not None else 0.0
        return (amount * qty)
    
    class Meta:
        verbose_name_plural = "Field Expenses"
        ordering = ["-date"]

    def __str__(self):
        return f"Expense {self.id} on {self.date}"
    

class BalanceSheetCategory(models.Model):
    CATEGORY_TYPES = [
        ('Asset', 'Asset'),
        ('Long-term Asset', 'Long-term Asset'),
        ('Liability', 'Liability'),
        ('Long-term Liability', 'Long-term Liability'),
        ('Revenue', 'Revenue'),
        ('Expenses', 'Expenses'),
        ('Cash Inflows for Investing Activities', 'Cash Inflows for Investing Activities'),
        ('Cash Outflows for Investing Activities', 'Cash Outflows for Investing Activities'),
        ('Cash Inflows for Financing Activities', 'Cash Inflows for Financing Activities'),
        ('Cash Outflows for Financing Activities', 'Cash Outflows for Financing Activities'),
    ]

    name = models.CharField(max_length=255)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, default='Asset')
    amount = models.DecimalField(max_digits=20, decimal_places=2,null=True)
    description = models.TextField(max_length=1000, default=None,null=True, blank=True)

    class Meta:
        unique_together = ('name', 'category_type')
        verbose_name_plural = "Balance Sheet Categories"

    def __str__(self):
        return f"{self.name} ({self.category_type})"


# ==================================Web Site Budget====================================

class WebCategory(models.Model):
    name = models.CharField(max_length=100,null=True,blank=True,default='Operations')
    description = models.TextField(max_length=1000,null=True,blank=True)

    class Meta:
        verbose_name = _("Web Category")
        verbose_name_plural = _("Web Categories")
        ordering = ['name']

    def __str__(self):
        return self.name
    
class WebSubCategory(models.Model):
    category = models.ForeignKey(WebCategory, on_delete=models.CASCADE, related_name='web_subcategories')
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = _("Web Sub category")
        verbose_name_plural = _("Web Subcategories")
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category.name}-{self.name}"

class web_budget(TimeStampedModel):
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name="company_site",
        blank=True, null=True)
    
    category = models.ForeignKey(
        WebCategory, 
        on_delete=models.CASCADE, 
        related_name="WebCategory",
        blank=True, null=True)
    
    subcategory = models.ForeignKey(
        WebSubCategory, 
        on_delete=models.CASCADE, 
        related_name="web_budget_subcategory",
        blank=True, null=True)
    
    name = models.CharField(max_length=25,null=True,blank=True)
    description = models.TextField(max_length=1000,null=True,blank=True)
    cases = models.PositiveIntegerField(default=1,null=True,blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=None
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    link = models.CharField(max_length=100, blank=True, null=True)
    
    @property
    def amount(self):
        try:
            total_amount = self.cases * self.qty * self.unit_price
            return total_amount
        except:
            total_amount=0.00
            # return redirect('finance:pay')

    @property    
    def number_days(self):
        start=str(self.start_date)
        end=str(self.end_date)
        try:
            # Ensure dates are in datetime format
            # start = datetime.strptime(start, "%Y-%m-%d")
            # end = datetime.strptime(end, "%Y-%m-%d")
            start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S%z")
            end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S%z")

            # Calculate the difference between the end date and start date
            total_days = (end - start).days
            return total_days
        
        except Exception as e:
            print(f"Error calculating days: {e}")
            # Return 0 or an appropriate value indicating the error
            return 0
        
    def __str__(self):
        return self.name  

class LoanDecisionAudit(models.Model):
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

# KCC Loan Performance Tracking



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
        return f"{self.user.username} - Loan {self.loan_application.id} - {self.payment_timing}"
    
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



# class KCCLoanPerformance(models.Model):
#     """Enhanced KCC member loan performance tracking for hybrid scaling system"""
    
#     PAYMENT_TIMING_CHOICES = [
#         ('early', 'Early Payment'),      # +20% scaling
#         ('on_time', 'On Time Payment'),  # +20% scaling
#         ('late', 'Late Payment'),        # -20% scaling
#         ('defaulted', 'Defaulted')       # Reset to tier minimum
#     ]
    
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kcc_performance')
#     loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='kcc_performance')
    
#     # Enhanced performance metrics
#     payment_timing = models.CharField(
#         max_length=20,
#         choices=PAYMENT_TIMING_CHOICES,
#         default='on_time'
#     )
    
#     # NEW HYBRID: Scaling calculations
#     scaling_factor_applied = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         help_text="Scaling factor applied (e.g., 1.20 for +20%)"
#     )
    
#     next_loan_amount = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         null=True,
#         blank=True,
#         help_text="Calculated next loan amount after scaling"
#     )
    
#     tier_progression = models.CharField(
#         max_length=20,
#         choices=[
#             ('within_tier', 'Within Tier'),
#             ('tier_upgrade', 'Tier Upgrade'),
#             ('tier_downgrade', 'Tier Downgrade')
#         ],
#         default='within_tier'
#     )
    
#     # Performance scoring
#     performance_score = models.IntegerField(default=100)  # 0-100 scale
#     consecutive_successful_loans = models.IntegerField(default=0)
#     consecutive_late_payments = models.IntegerField(default=0)
    
#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = 'KCC Loan Performance'
#         verbose_name_plural = 'KCC Loan Performances'
    
#     def __str__(self):
#         return f"{self.user.username} - {self.loan_application.id} - {self.payment_timing}"
    
#     def calculate_next_loan_amount(self):
#         """Calculate next loan amount based on performance and tier scaling"""
#         try:
#             # Get user's current tier configuration
#             profile = self.user.profile
#             if not profile or not profile.is_karen_country_club_member:
#                 return None
            
#             current_tier = profile.kcc_performance_tier
#             tier_config = KCCLoanConfiguration.objects.get(
#                 performance_tier=current_tier,
#                 is_active=True
#             )
            
#             # Calculate based on payment timing
#             if self.payment_timing == 'early':
#                 scaling_multiplier = tier_config.scaling_factor  # +20%
#             elif self.payment_timing == 'on_time':
#                 scaling_multiplier = tier_config.scaling_factor  # +20%
#             elif self.payment_timing == 'late':
#                 scaling_multiplier = 2 - tier_config.scaling_factor  # -20%
#             else:  # defaulted
#                 scaling_multiplier = 1.0  # No change
            
#             # Apply scaling to current loan amount
#             current_amount = self.loan_application.amount_requested
#             next_amount = current_amount * scaling_multiplier
            
#             # Enforce tier limits
#             next_amount = max(tier_config.min_amount, min(next_amount, tier_config.max_amount))
            
#             # Update the model
#             self.scaling_factor_applied = scaling_multiplier
#             self.next_loan_amount = next_amount.quantize(Decimal('0.01'))
#             self.save()
            
#             return self.next_loan_amount
            
#         except Exception as e:
#             logger.error(f"Error calculating next loan amount: {e}")
#             return None



# Physical Collateral Management
class LoanCollateral(models.Model):
    """Manage physical collateral for KCC loans"""
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
    
    # Land-specific fields
    land_location = models.CharField(max_length=200, blank=True, null=True)
    land_size = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2 acres"
    land_title_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Equipment-specific fields
    equipment_type = models.CharField(max_length=100, blank=True, null=True)
    equipment_condition = models.CharField(max_length=50, blank=True, null=True)
    
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
        return f"{self.collateral_type} - {self.loan_application.id} - ${self.estimated_value}"

# KCC Loan Rollover Management
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
        return f"{self.original_loan.id} - Rollover #{self.rollover_number}"
    
    @property
    def is_max_rollovers_reached(self):
        """Check if maximum rollovers (2) reached"""
        return self.rollover_number >= 2


# ==================== UNIFIED LOAN CONFIGURATION ====================

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
        return f"{self.name} ({self.get_loan_type_display()})"
    
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
        """Get performance-based multiplier from tier modifiers"""
        if not user_profile or not self.tier_modifiers:
            return Decimal('1.00')
        
        performance_tier = getattr(user_profile, 'performance_tier', 'new')
        return self.tier_modifiers.get(performance_tier, Decimal('1.00'))
    
    def get_user_type_summary(self):
        """Get summary of user type multipliers"""
        return {
            'staff': self.staff_multiplier,
            'kcc_member': self.kcc_multiplier,
            'external': self.external_multiplier
        }
    
    def get_tier_modifiers_summary(self):
        """Get summary of performance tier modifiers"""
        return self.tier_modifiers or {}
    
    def is_eligible_for_user(self, user, user_profile=None):
        """Check if user is eligible for this loan configuration"""
        # Check basic requirements
        if not self.is_active:
            return False
        
        # Check employment requirement
        if self.min_employment_months > 0:
            if not user_profile or not user_profile.employment_start_date:
                return False
            
            employment_months = user_profile.employment_months
            if employment_months < self.min_employment_months:
                return False
        
        # Check income requirement
        if self.min_monthly_income:
            if not user_profile or not user_profile.monthly_income:
                return False
            
            if user_profile.monthly_income < self.min_monthly_income:
                return False
        
        return True


# ==================== PAYMENT MODELS ====================

class Payment(models.Model):
    """Payment model for loan repayments"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other'),
    ]
    
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.id} - {self.amount} for Loan {self.loan.id}"
    
    def clean(self):
        """Validate payment data"""
        if self.amount <= 0:
            raise ValidationError('Payment amount must be greater than zero')
        
        if self.payment_date > timezone.now():
            raise ValidationError('Payment date cannot be in the future')
    
    def save(self, *args, **kwargs):
        """Custom save method with validation"""
        self.clean()
        super().save(*args, **kwargs)
