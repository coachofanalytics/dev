from django.db import models

# Create your models here.
from django.conf import settings

# from dev.main.views import User
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils.text import slugify


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
    user = models.OneToOneField(User, on_delete=models.CASCADE,
    related_name="profile")
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


# Directory Member Model
class DirectoryMember(models.Model):
    CATEGORY_CHOICES = [
        ('tech', 'Tech & IT'),
        ('healthcare', 'Healthcare'),
        ('business', 'Business & Finance'),
        ('education', 'Education'),
        ('legal', 'Legal Services'),
        ('engineering', 'Engineering'),
        ('creative', 'Creative & Design'),
        ('other', 'Other'),
    ]
    
    MEMBERSHIP_CHOICES = [
        ('verified', 'Verified'),
        ('premium', 'Premium'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='directory_profiles', null=True, blank=True)
    full_name = models.CharField(max_length=150)
    profession = models.CharField(max_length=200)
    region = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='verified')
    expertise = models.TextField()
    profile_photo = models.ImageField(upload_to='directory_photos/', blank=True, null=True)
    
    # Auto-generated fields
    initials = models.CharField(max_length=5, blank=True)
    avatar_color = models.CharField(max_length=7, default='#059669')
    title_color = models.CharField(max_length=7, default='#059669')
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Generate initials from full name
        if self.full_name and not self.initials:
            name_parts = self.full_name.split()
            if len(name_parts) >= 2:
                self.initials = (name_parts[0][0] + name_parts[1][0]).upper()
            else:
                self.initials = name_parts[0][:2].upper()
        
        # Set is_premium based on membership_type
        self.is_premium = (self.membership_type == 'premium')
        
        
        if not self.avatar_color or self.avatar_color == '#059669':
            import random
            colors = ['#dc2626', '#059669', '#2563eb', '#7c3aed', '#ea580c', '#0891b2']
            self.avatar_color = random.choice(colors)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.profession}"