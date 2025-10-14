from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('Salary', 'Salary'),
        ('Health', 'Health'),
        ('Transport', 'Transport'),
        ('Training', 'Training'),
        ('Other', 'Other'),
    ]

    transaction_type = models.CharField(
        max_length=10,
        choices=[('Inflow', 'Inflow'), ('Outflow', 'Outflow')],
        default='Inflow'
    )
    category = models.CharField(max_length=25, choices=CATEGORY_CHOICES, default='Other')
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.category} - {self.amount}"
