"""
Notification models for department dashboards
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class DepartmentNotification(models.Model):
    """
    Model for department-specific notifications
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    department = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    
    # Targeting
    target_users = models.ManyToManyField(User, blank=True, help_text="Specific users to notify")
    target_roles = models.JSONField(default=list, blank=True, help_text="Roles to target (admin, staff, etc.)")
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Action
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Tracking
    viewed_by = models.ManyToManyField(User, related_name='viewed_notifications', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notifications')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Department Notification'
        verbose_name_plural = 'Department Notifications'
    
    def __str__(self):
        return f"{self.department}: {self.title}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_visible(self):
        return self.is_active and not self.is_expired
    
    def mark_as_viewed(self, user):
        """Mark notification as viewed by user"""
        self.viewed_by.add(user)


class DepartmentAnnouncement(models.Model):
    """
    Model for department-wide announcements
    """
    department = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    show_on_dashboard = models.BooleanField(default=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Author
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Department Announcement'
        verbose_name_plural = 'Department Announcements'
    
    def __str__(self):
        return f"{self.department}: {self.title}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_visible(self):
        return self.is_active and not self.is_expired


class UserDashboardPreferences(models.Model):
    """
    Model for user dashboard preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    department_notifications = models.JSONField(default=list, help_text="List of departments to receive notifications for")
    
    # Display preferences
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ])
    layout = models.CharField(max_length=20, default='grid', choices=[
        ('grid', 'Grid'),
        ('list', 'List'),
        ('compact', 'Compact'),
    ])
    
    # Auto-refresh settings
    auto_refresh = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=300, help_text="Refresh interval in seconds")
    
    # Search preferences
    search_history = models.JSONField(default=list, blank=True)
    favorite_links = models.JSONField(default=list, blank=True)
    
    # Analytics
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Dashboard Preferences'
        verbose_name_plural = 'User Dashboard Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def increment_access(self):
        """Increment access count"""
        self.access_count += 1
        self.save(update_fields=['access_count', 'last_accessed'])
    
    def add_to_favorites(self, link_data):
        """Add link to favorites"""
        if link_data not in self.favorite_links:
            self.favorite_links.append(link_data)
            self.save(update_fields=['favorite_links'])
    
    def remove_from_favorites(self, link_data):
        """Remove link from favorites"""
        if link_data in self.favorite_links:
            self.favorite_links.remove(link_data)
            self.save(update_fields=['favorite_links'])
