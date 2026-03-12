from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


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

        # added myself

        

class Consultation(models.Model):

    CONSULTATION_TYPES = [
        ('immigration', 'Immigration Visa'),
        ('asylum', 'Asylum'),
        ('family', 'Family Immigration'),
        ('work', 'Work Permit'),
        ('student', 'Student Visa'),
        ('legal', 'General Legal Advice'),
    ]

    full_name = models.CharField(max_length=200)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    country = models.CharField(max_length=100)

    consultation_type = models.CharField(
        max_length=100,
        choices=CONSULTATION_TYPES
    )

    description = models.TextField()

    document = models.FileField(
        upload_to='consultation_documents/',
        blank=True,
        null=True
    )

    preferred_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name