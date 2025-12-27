from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, date
from decimal import *
from enum import unique
from django.shortcuts import redirect, render
from django.db.models import Q
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import CustomerUser, Department
# from finance.utils import get_exchange_rate
User = get_user_model()

# Create your models here.


class Payment_Information(models.Model):
    # id = models.AutoField(primary_key=True)
    customer_id = models.ForeignKey(
        "accounts.CustomerUser",
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
        related_name="customer")
  
    
    plan = models.IntegerField(null=True,blank=True)
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)

    @property
    def student_balance(self):
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
        CustomerUser,
        verbose_name=("Client Name"),
        on_delete=models.CASCADE,
        related_name="customer_payment_history")
    payment_fees=models.IntegerField()
    down_payment=models.IntegerField(default=500)
    student_bonus=models.IntegerField(null=True,blank=True)
    fee_balance=models.IntegerField(default=None)
    down_payment = models.IntegerField(default=500)
    student_bonus = models.IntegerField(null=True, blank=True)
    fee_balance = models.IntegerField(default=None)
    plan = models.IntegerField()
    payment_method = models.CharField(max_length=100)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000)
    company_rep = models.CharField(max_length=1000)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)

class Default_Payment_Fees(models.Model):
    # id = models.AutoField(primary_key=True)
    job_down_payment_per_month = models.IntegerField(default=500)
    job_plan_hours_per_month = models.IntegerField(default=40)
    student_down_payment_per_month = models.IntegerField(default=500)
    student_bonus_payment_per_month = models.IntegerField(default=250)

    # loan_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)

    def __str__(self):
        return str(self.id)

class Transaction(models.Model):
    CLIENTS_CHOICES = [
        ("DYC", "Diaspora Youth Caucus"),
        # ("DC48KENYA", "DC48KENYA"),
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
    related_name="transaction_sender",
    default=1)

    receiver = models.CharField(max_length=100, null=True, default=None)
    phone = models.CharField(max_length=50, null=True, default=None)
    sender_phone = models.CharField(max_length=50, null=True, default=None)
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
        

class Budget(models.Model):
    # company = models.ForeignKey(
    #     Company, 
    #     on_delete=models.CASCADE, 
    #     related_name="company_type",
    #     default=1)
    
    # department = models.ForeignKey(
    #     Department, 
    #     on_delete=models.CASCADE, 
    #     related_name="department_type",
    #     default=1)
    
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
    
    subcategory = models.CharField(max_length=25,null=True,blank=True)
    
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
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        abstract = True  

class Company(TimeStampedModel):
    """Company Table will provide a list of the different company affiliated with CODA"""
    name = models.CharField(max_length=100,null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    sector = models.CharField(max_length=100,null=True, blank=True)
    mission = models.CharField(max_length=100,null=True, blank=True)
    website = models.CharField(max_length=100,null=True, blank=True)
  
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        # default=1,
        null=True, 
        blank=True
    )
    description = models.TextField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

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
        return f"{self.category.name}-{self.name}"           
class CodaBudget(TimeStampedModel):
    budget_lead = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        limit_choices_to=(Q(is_staff=True, is_active=True, category=2) | Q(is_superuser=True)),
        related_name="lead"
    )
    #company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_budgets')
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