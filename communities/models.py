from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class CommunityMember(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # ADD DEFAULT VALUES for new fields
    profession = models.CharField(max_length=100, default="Not Specified")
    region = models.CharField(max_length=100, default="Not Specified")
    specialization = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='member_profiles/', blank=True, null=True)
    
    # Status fields
    is_verified = models.BooleanField(default=True)  # Changed to True
    is_public_directory = models.BooleanField(default=True)  # Changed to True
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.profession}"
    
    class Meta:
        ordering = ['-date_joined']


class DirectoryProfile(models.Model):
    MEMBERSHIP_CHOICES = [
        ('verified', 'Verified (Free)'),
        ('premium', 'Premium ($9/mo)'),
    ]
    
    CATEGORY_CHOICES = [
        ('tech', 'Tech & IT'),
        ('legal', 'Legal'),
        ('finance', 'Finance & Accounting'),
        ('health', 'Healthcare'),
        ('education', 'Education'),
        ('business', 'Business & Consulting'),
        ('creative', 'Creative & Media'),
        ('engineering', 'Engineering'),
        ('other', 'Other'),
    ]
    
    # Link to basic CommunityMember
    community_member = models.OneToOneField(
        CommunityMember,  # Use the class directly since it's defined above
        on_delete=models.CASCADE,
        related_name='directory_profile'
    )
    
    # Form fields
    full_name = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    region_city = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='verified')
    expertise_summary = models.TextField()
    profile_photo = models.ImageField(upload_to='directory_profiles/', blank=True, null=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.profession}"
    
    def save(self, *args, **kwargs):
        # Update the main CommunityMember if needed
        if self.community_member:
            self.community_member.name = self.full_name
            self.community_member.profession = self.profession
            self.community_member.region = self.region_city
            self.community_member.save()
        super().save(*args, **kwargs)


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
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    # Removed duplicate __str__ method


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