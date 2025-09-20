from django.db import models
from django.conf import settings
from django.utils import timezone


class DashboardWidget(models.Model):
    """Widget configuration for user dashboards"""
    WIDGET_TYPES = [
        ('quick_action', 'Quick Action'),
        ('service_card', 'Service Card'),
        ('analytics_chart', 'Analytics Chart'),
        ('recent_activity', 'Recent Activity'),
        ('notification', 'Notification'),
        ('iframe_embed', 'Iframe Embed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, help_text="Widget-specific configuration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position', 'created_at']
        unique_together = ['user', 'position']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserDashboardPreferences(models.Model):
    """User preferences for dashboard customization"""
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'Auto (System)'),
    ]
    
    LAYOUT_CHOICES = [
        ('grid', 'Grid Layout'),
        ('list', 'List Layout'),
        ('compact', 'Compact Layout'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_preferences')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='grid')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    auto_refresh = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=300, help_text="Refresh interval in seconds")
    sidebar_collapsed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Dashboard Preferences"


class DashboardService(models.Model):
    """Available services that can be added to dashboards"""
    SERVICE_CATEGORIES = [
        ('finance', 'Finance'),
        ('investing', 'Investing'),
        ('management', 'Management'),
        ('ai_services', 'AI Services'),
        ('professional_services', 'Professional Services'),
        ('hr', 'Human Resources'),
        ('analytics', 'Analytics'),
        ('admin', 'Administration'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES)
    url = models.URLField()
    icon = models.CharField(max_length=50, default='fas fa-cog')
    is_active = models.BooleanField(default=True)
    requires_permission = models.CharField(max_length=100, blank=True, help_text="Permission required to access this service")
    user_roles = models.JSONField(default=list, help_text="List of user roles that can access this service")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class UserServiceAccess(models.Model):
    """Track user access to different services"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_access')
    service = models.ForeignKey(DashboardService, on_delete=models.CASCADE)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'service']
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name}"


class DashboardAnalytics(models.Model):
    """Analytics data for dashboard usage"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_analytics')
    session_id = models.CharField(max_length=100)
    page_views = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    widgets_used = models.JSONField(default=list)
    services_accessed = models.JSONField(default=list)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.page_views} views"