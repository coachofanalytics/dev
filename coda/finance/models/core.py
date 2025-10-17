# -*- coding: utf-8 -*-
"""
Finance Core Models

Core models for the finance app including Transaction, Inflow, and basic payment models.
"""

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
    from main.models import Company, Service, ServiceCategory, TimeStampedModel, ContractBase, StatusMixin
except ImportError:
    Company = Service = ServiceCategory = TimeStampedModel = ContractBase = StatusMixin = None

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


# =============================================================================
# CORE FINANCE MODELS
# =============================================================================

class PaymentBase(ContractBase):
    """Base model for payment-related models"""
    
    # Payment Status Choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Method Choices
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]
    
    # Basic payment fields
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text="Payment amount"
    )
    currency = models.CharField(
        max_length=3, 
        default='KES', 
        help_text="Currency code (ISO 4217)"
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='mpesa',
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Payment status"
    )
    transaction_id = models.CharField(
        max_length=100, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="External transaction ID"
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time of payment"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional payment notes"
    )
    
    class Meta:
        abstract = True
        ordering = ['-payment_date']
    
    def __str__(self):
        return "{} {} - {}".format(self.amount, self.currency, self.get_status_display())


class Payment_Information(PaymentBase):
    """Payment information for users"""
    
    customer = models.ForeignKey(
        User,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
    )
    payment_fees = models.IntegerField()
    down_payment = models.IntegerField(default=500)
    student_bonus = models.IntegerField(null=True, blank=True)
    plan = models.IntegerField()
    subplan = models.IntegerField(null=True)
    pricing_plan = models.IntegerField(null=True)
    client_signature = models.CharField(max_length=1000)
    
    @property
    def fee_balance(self):
        """Calculate fee_balance dynamically - column doesn't exist in database"""
        return self.payment_fees - self.down_payment

    def __str__(self):
        return "Payment Info for {} - Plan {}".format(self.customer.username, self.plan)


class Payment_History(PaymentBase):
    """Payment history tracking"""
    
    customer = models.ForeignKey(
        User,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
    )
    payment_fees = models.IntegerField()
    down_payment = models.IntegerField(default=500)
    fee_balance = models.IntegerField(default=0, help_text="Calculated as payment_fees - down_payment")
    student_bonus = models.IntegerField(null=True, blank=True)
    plan = models.IntegerField()
    subplan = models.IntegerField(null=True)
    pricing_plan = models.IntegerField(null=True)

    def __str__(self):
        return "Payment History for {} - Plan {}".format(self.customer.username, self.plan)


class DeletedPaymentHistory(models.Model):
    """Deleted payment history for audit purposes"""
    
    customer = models.ForeignKey(
        User,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
    )
    payment_fees = models.IntegerField()
    down_payment = models.IntegerField(default=500)
    student_bonus = models.IntegerField(null=True, blank=True)
    plan = models.IntegerField()
    subplan = models.IntegerField(null=True)
    pricing_plan = models.IntegerField(null=True)
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)

    def __str__(self):
        return "Deleted Payment for {} - Plan {}".format(self.customer.username, self.plan)


class Default_Payment_Fees(models.Model):
    """Default payment fees configuration"""
    
    plan = models.IntegerField()
    payment_fees = models.IntegerField()
    down_payment = models.IntegerField(default=500)
    
    # Additional fields that exist in database
    job_plan_hours_per_month = models.IntegerField(default=0, help_text="Hours per month for job plan")
    student_down_payment_per_month = models.IntegerField(default=500, help_text="Down payment per month for students")
    student_bonus_payment_per_month = models.IntegerField(default=0, help_text="Bonus payment per month for students")
    job_down_payment_per_month = models.IntegerField(default=500, help_text="Down payment per month for job plan")
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Loan amount")

    def __str__(self):
        return "Plan {} - Fees: {}".format(self.plan, self.payment_fees)


class PayslipConfig(models.Model):
    """Model for payslip configuration"""
    
    user = models.ForeignKey("accounts.CustomerUser", on_delete=models.CASCADE, null=True, blank=True)
    
    # Basic salary configuration
    web_pay_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    web_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    laptop_status = models.BooleanField("Laptop Status", default=True)
    
    # Loan configuration
    loan_status = models.BooleanField(default=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)
    loan_repayment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.20)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    installment_date = models.DateField(null=True, blank=True)
    
    # Laptop service configuration
    lb_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    ls_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    ls_max_limit = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)
    
    # Retirement package configuration
    rp_starting_period = models.CharField(max_length=10)
    rp_starting_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    rp_increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)
    rp_increment_max_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)
    rp_increment_percentage_increment = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)
    rp_increment_percentage_increment_cycle = models.IntegerField(default=12)
    
    # Bonus configuration
    holiday_pay = models.DecimalField(max_digits=10, decimal_places=2, default=3000.00)
    night_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    
    # Deductions configuration
    computer_maintenance = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    food_accommodation = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    health = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    def __str__(self):
        return "Payslip Config for {}".format(self.user.username if self.user else 'N/A')


class Inflow(models.Model):
    """Cash inflow tracking - Maps to existing finance_inflow table"""
    
    # Inflow Type Choices
    TYPE_CHOICES = [
        ('revenue', 'Revenue'),
        ('investment', 'Investment'),
        ('loan', 'Loan'),
        ('grant', 'Grant'),
        ('other', 'Other'),
    ]
    
    # Inflow Status Choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Map to existing columns in database
    sender = models.CharField(max_length=100, help_text="Sender/Source of inflow")
    receiver = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    method = models.CharField(max_length=50, default='mpesa')
    period = models.CharField(max_length=50, blank=True, null=True)
    item = models.CharField(max_length=200, blank=True, null=True)
    
    transaction_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=500, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    
    # Additional tracking fields
    total_payment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Total payment (calculated as qty * amount)")
    currency = models.CharField(max_length=3, default='KES', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = "Cash Inflow"
        verbose_name_plural = "Cash Inflows"
    
    def __str__(self):
        return "{} {} - {} ({})".format(self.amount, self.currency or 'KES', self.method, self.sender)


class DC48_Inflow(models.Model):
    """DC48 specific inflow tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=200, blank=True, null=True)
    received_date = models.DateTimeField(default=timezone.now)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-received_date']
        verbose_name = "DC48 Inflow"
        verbose_name_plural = "DC48 Inflows"
    
    def __str__(self):
        return "DC48: {} {} - {}".format(self.amount, self.currency, self.user.username)


class Transaction(models.Model):
    """
    Production-ready Transaction model with proper relationships.
    Maps to existing database columns using db_column parameter.
    """
    
    # Category Choices
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
    
    # Payment Method Choices
    PAY_CHOICES = [
        ("Cash", "Cash"),
        ("Mpesa", "Mpesa"),
        ("Check", "Check"),
        ("Other", "Other"),
    ]
    
    # User Relationships - Map to existing sender_id column
    sender = models.ForeignKey(
        User,
        verbose_name=_("sender"),
        related_name="sent_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='sender_id',
        limit_choices_to={"is_staff": True, "is_active": True},
    )
    
    # Vendor/Supplier - Map to existing vendor_supplier_id column
    vendor_supplier = models.ForeignKey(
        User,
        verbose_name=_("vendor_supplier"),
        related_name="vendor_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='vendor_supplier_id',
        limit_choices_to=Q(is_active=True) & (Q(is_staff=True) | Q(category=6)),
    )
    
    # Basic Fields (no db_column needed - names match)
    receiver = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    
    # Department & Category Relationships - Map to existing columns
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='department_id'
    )
    
    category = models.ForeignKey(
        'BudgetCategory',
        on_delete=models.CASCADE,
        related_name="transactions",
        blank=True,
        null=True,
        db_column='category_id'
    )
    
    subcategory = models.ForeignKey(
        'BudgetSubCategory',
        on_delete=models.CASCADE,
        related_name="transactions",
        blank=True,
        null=True,
        db_column='subcategory_id'
    )
    
    # Transaction Details
    type = models.CharField(
        max_length=100,
        choices=CAT_CHOICES,
        default="Other",
    )
    
    transaction_date = models.DateTimeField(default=timezone.now)
    receipt_link = models.CharField(max_length=100, blank=True, null=True)
    
    qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=1
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    transaction_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        null=True
    )
    
    payment_method = models.CharField(
        max_length=25,
        choices=PAY_CHOICES,
        default="Other",
    )
    
    # Additional Fields (keeping from existing schema)
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='KES')
    original_currency = models.CharField(max_length=3, default='USD', help_text="Original currency of the transaction")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Computed Property
    @property
    def total_payment(self):
        """Calculate total payment amount"""
        if self.amount and self.qty:
            return self.amount * self.qty
        return self.amount or 0
    
    def get_absolute_url(self):
        return reverse("finance:transaction-detail", kwargs={"pk": self.pk})
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-transaction_date"]
    
    def __str__(self):
        return f"Transaction #{self.id} - {self.type}"


class CodaBudget(TimeStampedModel):
    """Coda-specific budget model"""
    
    # Budget Status Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Company relationship
    company = models.ForeignKey('main.Company', on_delete=models.CASCADE, default=1, help_text="Company this budget belongs to")
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Budget period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_budgets')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_budgets', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Coda Budget"
        verbose_name_plural = "Coda Budgets"
    
    def __str__(self):
        return "{} - {} {}".format(self.name, self.total_amount, self.currency)


class Field_Expense(models.Model):
    """Field expense tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    expense_date = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_expenses', null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-expense_date']
        verbose_name = "Field Expense"
        verbose_name_plural = "Field Expenses"
    
    def __str__(self):
        return "Field Expense: {} {} - {}".format(self.amount, self.currency, self.user.username)


class BalanceSheetCategory(models.Model):
    """Balance sheet category classification"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category_type = models.CharField(
        max_length=20,
        choices=[
            ('asset', 'Asset'),
            ('liability', 'Liability'),
            ('equity', 'Equity'),
        ]
    )
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Amount for this category")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Balance Sheet Category"
        verbose_name_plural = "Balance Sheet Categories"
    
    def __str__(self):
        return self.name


class WebCategory(models.Model):
    """Web-based category classification"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Web Category"
        verbose_name_plural = "Web Categories"
    
    def __str__(self):
        return self.name


class WebSubCategory(models.Model):
    """Web-based subcategory classification"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(WebCategory, on_delete=models.CASCADE, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'category']
        verbose_name = "Web Subcategory"
        verbose_name_plural = "Web Subcategories"
    
    def __str__(self):
        return "{} - {}".format(self.category.name, self.name)


class web_budget(TimeStampedModel):
    """Web-based budget model"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='KES')
    
    # Budget period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_web_budgets')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Web Budget"
        verbose_name_plural = "Web Budgets"
    
    def __str__(self):
        return "{} - {} {}".format(self.name, self.total_amount, self.currency)


class Supplier(models.Model):
    """Supplier/vendor information"""
    
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
    
    def __str__(self):
        return self.name


class Food(models.Model):
    """Food item tracking"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"
    
    @property
    def total_amount(self):
        """Calculate total amount (for compatibility with other models)"""
        return self.unit_price or 0
    
    def __str__(self):
        return "{} - {} {}".format(self.name, self.unit_price, self.currency)


class FoodHistory(models.Model):
    """Food purchase history"""
    
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_date = models.DateTimeField(default=timezone.now)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = "Food Purchase History"
        verbose_name_plural = "Food Purchase History"
    
    def __str__(self):
        return "{} - {} units - {}".format(self.food.name, self.quantity, self.total_amount)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
