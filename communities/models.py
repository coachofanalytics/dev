from django.db import models
# Create your models here.
from django.contrib.auth import get_user_model # Sg  add this import
from django.conf import settings

User = get_user_model() # Sg add this line
# Community member
class CommunityMember(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

class ForumCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class CommentP(models.Model):
    post = models.ForeignKey(Post, related_name='comments_p', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    def __str__(self):
        return self.title
class EventCalendar(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email}) on {self.created_at}"

class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    
    full_name = models.CharField(max_length=150, blank=True, null=True)
    
    contact_email = models.EmailField(blank=True, null=True)
    
    county_city = models.CharField(max_length=120, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):

        return f"{self.user.username} Profile"

class UserSettings(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    
    enable_notifications = models.BooleanField(default=True)
    
    enable_2fa = models.BooleanField(default=False)
    
    allow_marketing_emails = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
    
       return f"{self.user.username} Settings"
    
class UserPreferences(models.Model):

     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
     
     interest_area = models.CharField(max_length=150, blank=True, null=True)
     
     communication_channel = models.CharField(
     
     max_length=50,
     
        choices=[
            ("Email", "Email"),  
            ("SMS", "SMS"),
            ("WhatsApp", "WhatsApp"),
            ("Telegram", "Telegram"),
        ],
        default="Email"
        
        )
     
     profile_visibility = models.BooleanField(default=True)
     
     updated_at = models.DateTimeField(auto_now=True)
     
     def __str__(self):
     
        return f"{self.user.username} Preferences"