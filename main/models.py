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
    

        
class membershirp_registration(models.Model):
    email = models.EmailField(null=False, blank=False)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    gender = models.CharField(max_length=1, null=False, blank=False, choices=[('M', 'Male'), ('F', 'Female')])
    phone_number = models.CharField(max_length=15, null=False, blank=False)
    country = models.CharField(max_length=50, null=False, blank=False)
    city = models.CharField(max_length=50, null=False, blank=False)
    
    agree = models.BooleanField(null=False, blank=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"






class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.CharField(max_length=50)

    def __str__(self):
        return self.name       





from django.db import models

class Gallerys(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()  # Removed extra space

    def __str__(self):
        return self.title





from django.db import models

class News_papers(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    publish_date = models.DateField()  # Changed from TextField to DateField
    is_event = models.BooleanField(default=False)  # Corrected "defficult" to "default"
    image = models.ImageField(upload_to='news_image/', blank=True, null=True)  # Fixed syntax error

    def __str__(self):
        return self.title



        from django.db import models

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateField()
    is_event = models.BooleanField(default=False)
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)

    def __str__(self):
        return self.title





class Testimonial(models.Model):
    name = models.CharField(max_length=100)  # Corrected 'charfield' to 'CharField'
    position = models.CharField(max_length=100)  # Corrected 'charfield' to 'CharField'
    organisation = models.CharField(max_length=100)  # Corrected 'charfield' to 'CharField'
    testimonial = models.TextField(null=False)  # Corrected 'Testminals' and fixed 'null=False'
    image = models.ImageField(null=True, blank=True)  # 'null=True' and 'blank=True' for optional image field
    date = models.DateField(null=False)  # Fixed 'null=False' here

    def __str__(self):
        return self.name







class ContactMessage(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    submitted_at = models.DateTimeField(auto_now_add=True)  # Automatically sets the timestamp when created

    def __str__(self):
        return f"Message from {self.name} - {self.email}"










