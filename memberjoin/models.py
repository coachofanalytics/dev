from django.db import models

# Create your models here.
class MembershipRegistration(models.Model):
    #Membership Types
    MEMBERSHIP_CHOICES = [
        ('individual', 'Individual'),
        ('leader', 'Leader'),
        ('organization', 'Organization'),
    ]
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES)
    # Optional fields
    organization_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=60)
    email = models.EmailField()
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"
    