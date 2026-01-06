from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
# Assuming these imports based on typical project structure; ignoring if not strictly needed for minimal restore
from accounts.models import Department, CustomerUser

User = settings.AUTH_USER_MODEL

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Company(TimeStampedModel):
    name = models.CharField(max_length=255)
    def __str__(self): return self.name

class BudgetCategory(TimeStampedModel):
    name = models.CharField(max_length=255)
    def __str__(self): return self.name

class BudgetSubCategory(TimeStampedModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    def __str__(self): return self.name

class Budget(TimeStampedModel):
    budget_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budgets')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(BudgetSubCategory, on_delete=models.SET_NULL, null=True)
    item = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    receipt_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.item

class CodaBudget(Budget):
    class Meta:
        proxy = True

class Transaction(TimeStampedModel):
    receiver = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    method = models.CharField(max_length=50, blank=True)
    # Adding fields likely present based on form usage
    
    def __str__(self):
        return f"Transaction {self.id}"

class Payment_Information(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Add other likely fields
    
class Payment_History(TimeStampedModel):
    payment = models.ForeignKey(Payment_Information, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)

class Default_Payment_Fees(TimeStampedModel):
    fee_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

class FinancialServiceRequest(TimeStampedModel):
    SERVICE_CHOICES = [
        ('investment', 'Investment Advice and Planning'),
        ('currency', 'Currency Exchange Information'),
        ('remittance', 'Reliable Remittance Assistance'),
        ('tax', 'Tax and Compliance Guidance'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_requests', null=True, blank=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    details = models.TextField(help_text="Please provide more details about your request.")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_service_type_display()} ({self.status})"
