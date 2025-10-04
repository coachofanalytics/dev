# -*- coding: utf-8 -*-
"""
Notification models for finance-related alerts and communications.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from main.models import Company
except ImportError:
    Company = None

# Import core models
from .core import Budget, Transaction
from .budget import BudgetRequest
from .loan import LoanApplication


class FinanceNotification(models.Model):
    """General finance notifications."""
    
    # Notification types
    NOTIFICATION_TYPE_CHOICES = [
        ('Budget', 'Budget Notification'),
        ('Transaction', 'Transaction Notification'),
        ('Loan', 'Loan Notification'),
        ('Payment', 'Payment Notification'),
        ('System', 'System Notification'),
        ('Alert', 'Alert'),
        ('Reminder', 'Reminder'),
    ]
    
    # Notification priority
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    # Notification status
    STATUS_CHOICES = [
        ('Unread', 'Unread'),
        ('Read', 'Read'),
        ('Archived', 'Archived'),
    ]
    
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='finance_notifications',
        help_text="Company this notification belongs to"
    )
    
    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='finance_notifications',
        help_text="User receiving the notification"
    )
    
    # Notification details
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="Type of notification"
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message"
    )
    
    # Priority and status
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium',
        help_text="Notification priority"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Unread',
        help_text="Notification status"
    )
    
    # Related objects (generic foreign key approach)
    related_object_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of related object"
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of related object"
    )
    
    # Action required
    requires_action = models.BooleanField(
        default=False,
        help_text="Whether notification requires action"
    )
    action_url = models.URLField(
        blank=True,
        help_text="URL for required action"
    )
    action_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text for action button"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read"
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was archived"
    )
    
    class Meta:
        verbose_name = _("Finance Notification")
        verbose_name_plural = _("Finance Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'recipient']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    @property
    def is_unread(self):
        """Check if notification is unread."""
        return self.status == 'Unread'
    
    @property
    def is_urgent(self):
        """Check if notification is urgent."""
        return self.priority == 'Urgent'
    
    def mark_read(self):
        """Mark notification as read."""
        self.status = 'Read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_archived(self):
        """Mark notification as archived."""
        self.status = 'Archived'
        self.archived_at = timezone.now()
        self.save(update_fields=['status', 'archived_at'])
    
    def get_related_object(self):
        """Get the related object if it exists."""
        if not self.related_object_type or not self.related_object_id:
            return None
        
        try:
            if self.related_object_type == 'Budget':
                return Budget.objects.get(id=self.related_object_id)
            elif self.related_object_type == 'Transaction':
                return Transaction.objects.get(id=self.related_object_id)
            elif self.related_object_type == 'BudgetRequest':
                return BudgetRequest.objects.get(id=self.related_object_id)
            elif self.related_object_type == 'LoanApplication':
                return LoanApplication.objects.get(id=self.related_object_id)
        except:
            return None
        
        return None


class BudgetAlert(models.Model):
    """Budget-specific alerts and warnings."""
    
    # Alert types
    ALERT_TYPE_CHOICES = [
        ('Over Budget', 'Over Budget'),
        ('Approaching Limit', 'Approaching Limit'),
        ('Variance', 'Variance Alert'),
        ('Approval Required', 'Approval Required'),
        ('Deadline', 'Deadline Alert'),
        ('Threshold', 'Threshold Alert'),
    ]
    
    # Alert severity
    SEVERITY_CHOICES = [
        ('Info', 'Information'),
        ('Warning', 'Warning'),
        ('Critical', 'Critical'),
        ('Emergency', 'Emergency'),
    ]
    
    # Alert status
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Acknowledged', 'Acknowledged'),
        ('Resolved', 'Resolved'),
        ('Dismissed', 'Dismissed'),
    ]
    
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='budget_alerts',
        help_text="Company this alert belongs to"
    )
    
    # Related budget
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='alerts',
        help_text="Budget this alert relates to"
    )
    
    # Alert details
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type of alert"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='Warning',
        help_text="Alert severity"
    )
    title = models.CharField(
        max_length=200,
        help_text="Alert title"
    )
    message = models.TextField(
        help_text="Alert message"
    )
    
    # Alert thresholds
    threshold_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Threshold amount that triggered alert"
    )
    threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Threshold percentage that triggered alert"
    )
    
    # Alert status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        help_text="Alert status"
    )
    
    # Recipients
    recipients = models.ManyToManyField(
        User,
        related_name='budget_alerts',
        help_text="Users who should receive this alert"
    )
    
    # Acknowledgment
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_budget_alerts',
        help_text="User who acknowledged the alert"
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When alert was acknowledged"
    )
    
    # Resolution
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_budget_alerts',
        help_text="User who resolved the alert"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When alert was resolved"
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes about how alert was resolved"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Alert")
        verbose_name_plural = _("Budget Alerts")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['budget', 'alert_type']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.budget.item_name} ({self.severity})"
    
    @property
    def is_active(self):
        """Check if alert is active."""
        return self.status == 'Active'
    
    @property
    def is_critical(self):
        """Check if alert is critical."""
        return self.severity in ['Critical', 'Emergency']
    
    @property
    def is_acknowledged(self):
        """Check if alert is acknowledged."""
        return self.status == 'Acknowledged'
    
    @property
    def is_resolved(self):
        """Check if alert is resolved."""
        return self.status == 'Resolved'
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.status = 'Acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])
    
    def resolve(self, user, notes=None):
        """Resolve the alert."""
        self.status = 'Resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_notes'])
    
    def dismiss(self, user):
        """Dismiss the alert."""
        self.status = 'Dismissed'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])
    
    def get_absolute_url(self):
        """Get URL for budget alert detail view."""
        from django.urls import reverse
        return reverse('finance:budget-alert-detail', kwargs={'pk': self.pk})
