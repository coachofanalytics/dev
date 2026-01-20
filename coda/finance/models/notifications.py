# -*- coding: utf-8 -*-
"""
Finance Notification Models

Notification-related models including FinanceNotification, BudgetAlert, LoanNotification, and related models.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()


# =============================================================================
# NOTIFICATION MODELS
# =============================================================================

class FinanceNotification(models.Model):
    """General finance notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('reminder', 'Reminder'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Core notification data
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Targeting
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='finance_notifications')
    is_read = models.BooleanField(default=False)
    
    # Action
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Finance Notification'
        verbose_name_plural = 'Finance Notifications'
    
    def __str__(self):
        return "{} - {}".format(self.title, self.user.username)
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_expired(self):
        """Check if notification is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class BudgetAlert(models.Model):
    """Budget-related alerts and notifications"""
    
    ALERT_TYPE_CHOICES = [
        ('budget_exceeded', 'Budget Exceeded'),
        ('budget_warning', 'Budget Warning'),
        ('budget_approved', 'Budget Approved'),
        ('budget_rejected', 'Budget Rejected'),
        ('budget_due', 'Budget Due'),
        ('variance_high', 'High Variance'),
        ('variance_low', 'Low Variance'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    # Alert data
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related budget
    budget = models.ForeignKey('Budget', on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    budget_category = models.ForeignKey('BudgetCategory', on_delete=models.CASCADE, null=True, blank=True)
    
    # Thresholds
    threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    threshold_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_budget_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Alert'
        verbose_name_plural = 'Budget Alerts'
    
    def __str__(self):
        budget_name = self.budget.item_name if self.budget else 'No Budget'
        return "{} - {}".format(self.get_alert_type_display(), budget_name)
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['is_acknowledged', 'acknowledged_by', 'acknowledged_at'])
    
    def resolve(self):
        """Resolve the alert"""
        self.is_active = False
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_active', 'resolved_at'])


class LoanNotification(models.Model):
    """Loan-related notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('application_submitted', 'Application Submitted'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('payment_due', 'Payment Due'),
        ('payment_overdue', 'Payment Overdue'),
        ('payment_received', 'Payment Received'),
        ('loan_disbursed', 'Loan Disbursed'),
        ('loan_completed', 'Loan Completed'),
        ('guarantor_request', 'Guarantor Request'),
        ('guarantor_approved', 'Guarantor Approved'),
        ('guarantor_rejected', 'Guarantor Rejected'),
    ]
    
    # Notification data
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related loan
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='loan_notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Delivery
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Action
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Notification'
        verbose_name_plural = 'Loan Notifications'
    
    def __str__(self):
        return "{} - {}".format(self.get_notification_type_display(), self.loan_application.application_number)
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self, delivery_method=None):
        """Mark notification as sent"""
        self.is_sent = True
        self.sent_at = timezone.now()
        
        if delivery_method == 'email':
            self.email_sent = True
        elif delivery_method == 'sms':
            self.sms_sent = True
        elif delivery_method == 'push':
            self.push_sent = True
        
        self.save(update_fields=['is_sent', 'sent_at', 'email_sent', 'sms_sent', 'push_sent'])


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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_notifications')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Department Notification'
        verbose_name_plural = 'Department Notifications'
    
    def __str__(self):
        return "{}: {}".format(self.department, self.title)
    
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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Department Announcement'
        verbose_name_plural = 'Department Announcements'
    
    def __str__(self):
        return "{}: {}".format(self.department, self.title)
    
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
        return "Preferences for {}".format(self.user.username)
    
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
