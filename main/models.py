from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser

# from tableauhyperapi import DatabaseName

User = get_user_model()
# Create your models here.

class Page(models.Model):
    page_name = models.CharField(max_length=200)

    def __str__(self):
        return self.page_name

class Description(models.Model):
    page = models.ForeignKey(Page, related_name='descriptions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,null=False, blank=False) 
    content = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.name} for {self.page.page_name}"


class Content(models.Model):
    SECTION_CHOICES = [
        ('Our Story', 'Our Story'),
        ('Newsletter', 'Newsletter'),
        ('Blog', 'Blog'),
    ]

    section = models.CharField(max_length=50, choices=SECTION_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.section} - {self.title if self.title else 'Content'}"
class Assets(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(default='background',max_length=200,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        image_1=self.name.split("_")[0]
        image_2=self.name.split("_")[1]
        image_name=image_1,image_2

        return image_name

    def __str__(self):
        return self.name
    

class Feedback(models.Model):
    user= models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # category = models.ForeignKey(UserCategory,null=True,blank=True,on_delete=models.CASCADE)
    topic = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class SubService(models.Model):
    service = models.ForeignKey(Service, related_name='subservices', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} - {self.service}"
    
    
class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    link = models.URLField(null=True,blank=True)
    published_date = models.DateField()
    is_event = models.BooleanField(default=False)
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)  # Add this line for image field

    def __str__(self):
        return self.title    
    
class Team(models.Model):
    ROLE_CHOICES = [
        ('Governor', 'Governor'),
        ('Deputy Governor', 'Deputy Governor'),
        ('Regional Coordinator', 'Regional Coordinator'),
        ('Team Member', 'Team Member'),
    ]

    LEADERSHIP_CHOICES = [
        ('Local', 'Local'),
        ('Global', 'Global'),
    ]

    name = models.CharField(max_length=255)
    leadership = models.CharField(max_length=50, choices=LEADERSHIP_CHOICES, default='Local')  # or another default value
    facebook_link = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='people/')
    bio = models.TextField()

    def __str__(self):
        return self.name



from django.db import models

class Gallery_image(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()

    def __str__(self):
        return self.title






class ContactUs(models.Model):
    name = models.CharField(max_length=100, help_text="Full name of the user.")
    email = models.EmailField(help_text="Email address for correspondence.")
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, 
        help_text="Phone number of the user (optional)."
    )
    message = models.TextField(help_text="Message or inquiry from the user.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the message was submitted.")
    is_resolved = models.BooleanField(default=False, help_text="Flag to mark whether the query has been addressed.")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    


# donation model
class Donation_organisation(models.Model):
    # DONATION_TYPE_CHOICES = [
    #     ('One-Time', 'One-Time'),
    #     ('Monthly', 'Monthly'),
    #     ('Yearly', 'Yearly'),
    # ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The user who made the donation (if applicable)."
    )
    donor_name = models.CharField(max_length=100, help_text="Full name of the donor.")
    email = models.EmailField(help_text="Email address of the donor.")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount donated.")
    # donation_type = models.CharField(
    #     max_length=20, 
    #     choices=DONATION_TYPE_CHOICES, 
    #     default='One-Time',
    #     help_text="Type of donation."
    # )
    message = models.TextField(blank=True, null=True, help_text="Optional message from the donor.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the donation was made.")
    # is_anonymous = models.BooleanField(default=False, help_text="Flag to indicate if the donor wants to remain anonymous.")

    def __str__(self):
        return f"Donation of {self.amount} by {self.donor_name} ({self.email})"  
# contact Message model
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} => ({self.message})"


class Donation_organization(models.Model):
    donor_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor_name} - {self.amount}"



#<<<<<<< 25.10_DC48_UAT_UO
# Stores email subscriptions for Safety Alerts
class SafetyAlertSubscription(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# Emergency help line configuration
class EmergencyHotline(models.Model):
    name = models.CharField(max_length=100, help_text="Display label, e.g., Global Hotline")
    number = models.CharField(max_length=32, help_text="E.164 like +15551234567 or local format")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.name} ({self.number})"


class StaffContact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    notify_via_email = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class EmergencyHelpActivation(models.Model):
    EVENT_CHOICES = (
        ("call_link_clicked", "Call Link Clicked"),
        ("callback_requested", "Callback Requested"),
    )
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
=======

# Medical Resource Inquiry model at top-level
class MedicalResourceInquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


# scholarship model

class Scholarship(models.Model):
    #start with filter
    LEVEL_CHOICES =[
        ('Undergraduate', 'Undergraduate'),
        ('Masters','Masters'),
        ('PhD', 'PhD'),
        ('Vocational', 'Vocational'),
    ]
    FIELDS_CHOICES =[
        ('STEM', 'STEM'),
        ('Humanities','Humanities'),
        ('Business', 'Business'),
        ('Arts', 'Arts'),
    ]
    LOCATION_CHOICES =[
        ('Kenya', 'Kenya'),
        ('Global','Global'),
        ('UK', 'UK'),
        ('USA', 'USA'),
    ]
    STATUS_CHOICES =[
        ('Open','Open'),
        ('Closing Soon','Closing Soon'),
        ('Closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=200)
    level = models.CharField(max_length=200, choices=LEVEL_CHOICES)
    field = models.CharField(max_length=200, choices= FIELDS_CHOICES)
    location = models.CharField(max_length=200,choices=LOCATION_CHOICES)
    amount = models.CharField(max_length= 100)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices= STATUS_CHOICES)
    class Meta:
        ordering =['deadline']
    def __str__(self):
        return self.title
    
#>>>>>>> 25.10_DC48_UAT_ND
