from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

# class DocumentApplication(models.Model):
#     STATUS_CHOICES = [
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected')
#         ]
#     SERVICE_CHOICES = [
#         ('nid_replacement', 'National id Replacement'),
#         ('passport', 'Passport Application'),
#     ]
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     id_number = models.CharField(max_length=30)
#     sub_county = models.CharField(max_length=50)
#     reason = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
#     fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     submitted_at = models.DateTimeField(auto_now_add=True)
#     last_modified = models.DateTimeField(auto_now=True)
from django.db import models
from django.conf import settings

class Document_Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('paid', 'Paid'),
        ('approved', 'Approved')
    ]
    SERVICE_CHOICES = [
        ('nid_replacement', 'National ID Replacement'),
        ('passport', 'Passport Application')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    district = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)