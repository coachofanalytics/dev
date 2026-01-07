"""
KYC Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import KYCDocument, KYCVerificationLevel


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    """Admin interface for KYC Document verification."""

    list_display = [
        'user_link',
        'document_type',
        'status_badge',
        'is_scanned',
        'uploaded_at',
        'verified_by',
        'verified_at',
        'action_buttons',
    ]
    list_filter = [
        'status',
        'document_type',
        'is_scanned',
        'uploaded_at',
        'verified_at',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'document_number',
        'issuing_authority',
    ]
    readonly_fields = [
        'id',
        'uploaded_at',
        'updated_at',
        'is_scanned',
        'scan_result',
        'is_encrypted',
    ]
    fieldsets = (
        ('Document Information', {
            'fields': (
                'id',
                'user',
                'document_type',
                'document_file',
            )
        }),
        ('Document Details', {
            'fields': (
                'document_number',
                'issue_date',
                'expiry_date',
                'issuing_authority',
            )
        }),
        ('Verification', {
            'fields': (
                'status',
                'verified_by',
                'verified_at',
                'verification_notes',
            )
        }),
        ('Security', {
            'fields': (
                'is_scanned',
                'scan_result',
                'is_encrypted',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                'uploaded_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    date_hierarchy = 'uploaded_at'
    actions = ['approve_documents', 'reject_documents', 'mark_under_review']

    def user_link(self, obj):
        """Link to user admin page."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': 'warning',
            'under_review': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'expired': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def action_buttons(self, obj):
        """Quick action buttons."""
        if obj.status in ['pending', 'under_review']:
            return format_html(
                '<a class="button" href="{}">Review</a>',
                reverse('admin:kyc_kycdocument_change', args=[obj.pk])
            )
        return '-'
    action_buttons.short_description = 'Actions'

    def approve_documents(self, request, queryset):
        """Bulk approve documents."""
        count = 0
        for doc in queryset.filter(status__in=['pending', 'under_review']):
            doc.approve(request.user, 'Bulk approved by admin')
            count += 1
        self.message_user(request, f'Successfully approved {count} documents.')
    approve_documents.short_description = 'Approve selected documents'

    def reject_documents(self, request, queryset):
        """Bulk reject documents."""
        count = 0
        for doc in queryset.filter(status__in=['pending', 'under_review']):
            doc.reject(request.user, 'Bulk rejected by admin')
            count += 1
        self.message_user(request, f'Successfully rejected {count} documents.')
    reject_documents.short_description = 'Reject selected documents'

    def mark_under_review(self, request, queryset):
        """Mark documents as under review."""
        count = 0
        for doc in queryset.filter(status='pending'):
            doc.mark_under_review(request.user)
            count += 1
        self.message_user(request, f'{count} documents marked as under review.')
    mark_under_review.short_description = 'Mark as under review'


@admin.register(KYCVerificationLevel)
class KYCVerificationLevelAdmin(admin.ModelAdmin):
    """Admin interface for KYC Verification Levels."""

    list_display = [
        'user_link',
        'level_badge',
        'email_verified_icon',
        'phone_verified_icon',
        'identity_verified_icon',
        'address_verified_icon',
        'business_verified_icon',
        'transaction_limit_daily',
        'can_invest',
        'can_receive_investment',
    ]
    list_filter = [
        'level',
        'email_verified',
        'phone_verified',
        'identity_verified',
        'address_verified',
        'business_verified',
        'can_invest',
        'can_receive_investment',
    ]
    search_fields = [
        'user__username',
        'user__email',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Verification Level', {
            'fields': ('level',)
        }),
        ('Verification Status', {
            'fields': (
                'email_verified',
                'phone_verified',
                'identity_verified',
                'address_verified',
                'business_verified',
            )
        }),
        ('Permissions & Limits', {
            'fields': (
                'transaction_limit_daily',
                'can_invest',
                'can_receive_investment',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    actions = ['update_levels']

    def user_link(self, obj):
        """Link to user admin page."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def level_badge(self, obj):
        """Display level with colored badge."""
        colors = {
            'basic': 'secondary',
            'standard': 'info',
            'enhanced': 'primary',
            'premium': 'success',
        }
        color = colors.get(obj.level, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_level_display()
        )
    level_badge.short_description = 'Level'

    def _verification_icon(self, verified):
        """Helper to display verification status."""
        if verified:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')

    def email_verified_icon(self, obj):
        return self._verification_icon(obj.email_verified)
    email_verified_icon.short_description = 'Email'

    def phone_verified_icon(self, obj):
        return self._verification_icon(obj.phone_verified)
    phone_verified_icon.short_description = 'Phone'

    def identity_verified_icon(self, obj):
        return self._verification_icon(obj.identity_verified)
    identity_verified_icon.short_description = 'ID'

    def address_verified_icon(self, obj):
        return self._verification_icon(obj.address_verified)
    address_verified_icon.short_description = 'Address'

    def business_verified_icon(self, obj):
        return self._verification_icon(obj.business_verified)
    business_verified_icon.short_description = 'Business'

    def update_levels(self, request, queryset):
        """Recalculate verification levels."""
        for level in queryset:
            level.update_level()
        self.message_user(request, 'Verification levels updated.')
    update_levels.short_description = 'Recalculate verification levels'
