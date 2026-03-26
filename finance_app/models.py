from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings


class PaymentInformation(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('MPESA', 'MPESA'),
        ('PAYPAL', 'PayPal'),
        ('STRIPE', 'Stripe'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]

   
    payment_fees = models.IntegerField(
        null=False,
        help_text="Total amount of fees due"
    )

    down_payment = models.IntegerField(
        null=False,
        help_text="Amount paid upfront"
    )

    student_bonus = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="Discount or bonus for student"
    )

    fee_balance = models.IntegerField(
        null=False,
        help_text="Remaining balance (auto-calculated)"
    )

   
    plan = models.IntegerField(
        null=False,
        help_text="Selected plan number"
    )

    subplan = models.IntegerField(
        null=True,
        blank=True,
        help_text="Optional subplan number"
    )

    pricing_plan = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        help_text="Plan tier code (1 digit)"
    )

    
    payment_method = models.CharField(
        max_length=100,
        choices=PAYMENT_METHOD_CHOICES,
        null=False,
        help_text="Payment method used"
    )

    
    contract_submitted_date = models.DateTimeField(
        null=False,
        help_text="Date when contract was submitted"
    )

    client_signature = models.CharField(
        max_length=1000,
        null=False,
        help_text="Client digital or written signature"
    )

    company_rep = models.CharField(
        max_length=1000,
        null=False,
        help_text="Company representative name"
    )

    client_date = models.CharField(
        max_length=100,
        null=False,
        help_text="Date signed by client"
    )

   
    description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Optional notes or details"
    )

    
    is_active = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

   
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True
    )

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

   
    def save(self, *args, **kwargs):
        bonus = self.student_bonus or 0
        self.fee_balance = self.payment_fees - self.down_payment - bonus
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment - {self.user} | Balance: {self.fee_balance}"
