from django.db import models
from django.apps import apps


# Create your models here.

class Loan(models.Model):
    Status_Choices = [
        ('approved','approved'),
        ('pending','pending'),
        ('rejected','rejected')
    ]
    loan_id = models.AutoField(primary_key=True, null=False)
    customer = models.ForeignKey('accounts.CustomerUser', on_delete=models.CASCADE, null=False, related_name='loans')
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    repayment_period = models.IntegerField(null=False)
    interest_rate = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    status = models.CharField(choices=Status_Choices,max_length=100, null=False)
    approval_date = models.DateTimeField(auto_now_add=True, null=True)
    total_payable = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    next_loan_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weekly_installments = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    income_source = models.CharField(max_length=100, null=True)
    security_item = models.CharField(max_length=100, null=True)
    security_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    referee = models.ForeignKey('accounts.CustomerUser', on_delete=models.CASCADE, null=True,related_name='referred_loans')
    due_date = models.DateTimeField(auto_now_add=True, null=False)
    referee_income_source = models.CharField(max_length=100, null=True)
    days_to_due = models.IntegerField(null=False)
    days_past_due = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)