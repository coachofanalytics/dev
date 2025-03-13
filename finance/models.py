from django.db import models
from accounts.models import CustomerUser

# Create your models here.
class Loan(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('Approved', 'Approved'),
        ('Recovery', 'Recovery'),
        ('Fully-paid', 'Fully-paid'),
        ('Default', 'Default')
    ]
    loan_id = models.AutoField(primary_key=True)
    loanee_id = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, null=False)
    loan_amount = models.DecimalField(max_digits=20, null=False, decimal_places=2)
    repayment_period = models.IntegerField(null=False)
    interest_rate = models.DecimalField(null=False, decimal_places=2, max_digits=20)
    status = models.CharField(choices=STATUS_CHOICES, max_length=255, null=False)
    approval_date = models.DateField(null=True)
    total_payable = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    next_loan_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    weekly_installments = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    income_source = models.CharField(max_length=255, null=True)
    security_item = models.CharField(max_length=255, null=True)
    security_value = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    referee_id = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='referee')
    due_date = models.DateField(null=True)
    referee_income_source = models.CharField(max_length=255, null=True)
    days_to_due = models.IntegerField(null=True, default=0)
    days_past_due = models.IntegerField(null=True, default=0)
    created_at = models.DateTimeField(null=False)


    def __str__(self):
        return f"{self.loan_id} approved on {self.approval_date}"
