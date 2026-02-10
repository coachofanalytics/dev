"""
Shareholders Management System - Django Admin Configuration

Admin interfaces for pilot verification and data inspection.
Migrated from shareholders app to investing app.
"""

from django.contrib import admin
from investing.models_shareholders import (
    Deal, DealConfig, DealWeights, Member, LedgerEntry, LedgerEvidence,
    EquitySnapshot, EquitySnapshotLine, SnapshotAuditLog, AuditLog
)


# =============================================================================
# DEAL ADMIN
# =============================================================================

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    """Admin interface for Deal management"""
    
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DealConfig)
class DealConfigAdmin(admin.ModelAdmin):
    """Admin interface for Deal Configuration"""
    
    list_display = ['deal', 'base_currency', 'fx_mode', 'fx_peg_rate', 'next_snapshot_date']
    list_filter = ['fx_mode', 'base_currency']
    search_fields = ['deal__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Deal', {
            'fields': ('deal',)
        }),
        ('Currency & Exchange', {
            'fields': ('base_currency', 'fx_mode', 'fx_peg_rate')
        }),
        ('System Settings', {
            'fields': ('dispute_window_days', 'next_snapshot_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DealWeights)
class DealWeightsAdmin(admin.ModelAdmin):
    """Admin interface for Deal Weights"""
    
    list_display = ['deal', 'cash_weight', 'in_kind_weight', 'time_weight', 'work_weight', 'is_active', 'effective_date']
    list_filter = ['is_active', 'effective_date']
    search_fields = ['deal__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Deal', {
            'fields': ('deal', 'is_active', 'effective_date')
        }),
        ('Tier Weights (%)', {
            'fields': ('cash_weight', 'in_kind_weight', 'time_weight', 'work_weight'),
            'description': 'Weights must sum to 100%'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make deal readonly after creation"""
        if obj:  # Editing existing
            return self.readonly_fields + ['deal']
        return self.readonly_fields


# =============================================================================
# MEMBER ADMIN
# =============================================================================

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member management"""
    
    list_display = ['legal_name', 'deal', 'member_type', 'role_title', 'email', 'verified', 'is_archived', 'joined_date']
    list_filter = ['deal', 'member_type', 'verified', 'is_archived', 'joined_date']
    search_fields = ['legal_name', 'email', 'phone', 'role_title']
    readonly_fields = ['joined_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Deal', {
            'fields': ('deal',)
        }),
        ('Member Information', {
            'fields': ('member_type', 'legal_name', 'role_title', 'email', 'phone', 'bio')
        }),
        ('Status', {
            'fields': ('verified', 'is_archived')
        }),
        ('Timestamps', {
            'fields': ('joined_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['archive_members', 'unarchive_members', 'mark_verified']
    
    def archive_members(self, request, queryset):
        """Bulk archive members"""
        count = queryset.update(is_archived=True)
        self.message_user(request, f"{count} member(s) archived.")
    archive_members.short_description = "Archive selected members"
    
    def unarchive_members(self, request, queryset):
        """Bulk unarchive members"""
        count = queryset.update(is_archived=False)
        self.message_user(request, f"{count} member(s) unarchived.")
    unarchive_members.short_description = "Unarchive selected members"
    
    def mark_verified(self, request, queryset):
        """Bulk mark as verified"""
        count = queryset.update(verified=True)
        self.message_user(request, f"{count} member(s) marked as verified.")
    mark_verified.short_description = "Mark as verified"


# =============================================================================
# LEDGER ADMIN
# =============================================================================

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    """Admin interface for Ledger Entries"""
    
    list_display = ['tx_id', 'contributor', 'tier', 'asset_class', 'value_usd', 'status', 'date', 'has_proof']
    list_filter = ['deal', 'tier', 'status', 'date', 'created_at']
    search_fields = ['tx_id', 'contributor__legal_name', 'asset_class', 'notes']
    readonly_fields = ['tx_id', 'has_proof', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Transaction', {
            'fields': ('deal', 'tx_id', 'contributor', 'date', 'status')
        }),
        ('Contribution Details', {
            'fields': ('tier', 'asset_class', 'internal_units_value', 'internal_units_label')
        }),
        ('Valuation', {
            'fields': ('value_usd', 'currency', 'exchange_rate')
        }),
        ('Additional Information', {
            'fields': ('notes', 'has_proof')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_entries', 'mark_submitted']
    
    def approve_entries(self, request, queryset):
        """Bulk approve entries (Phase 1: status change only)"""
        count = queryset.update(status='APPROVED')
        self.message_user(request, f"{count} entry/entries marked as approved.")
    approve_entries.short_description = "Mark as approved"
    
    def mark_submitted(self, request, queryset):
        """Bulk mark as submitted"""
        count = queryset.update(status='SUBMITTED')
        self.message_user(request, f"{count} entry/entries marked as submitted.")
    mark_submitted.short_description = "Mark as submitted"
    
    def get_readonly_fields(self, request, obj=None):
        """Make deal and contributor readonly after creation"""
        if obj:  # Editing existing
            return self.readonly_fields + ['deal', 'contributor']
        return self.readonly_fields


@admin.register(LedgerEvidence)
class LedgerEvidenceAdmin(admin.ModelAdmin):
    """Admin interface for Ledger Evidence"""
    
    list_display = ['ledger_entry', 'file', 'uploaded_by', 'uploaded_at', 'description']
    list_filter = ['uploaded_at']
    search_fields = ['ledger_entry__tx_id', 'description', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'uploaded_by']
    
    fieldsets = (
        ('Evidence', {
            'fields': ('ledger_entry', 'file', 'description')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set uploaded_by to current user"""
        if not change:  # Only on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# SNAPSHOT ADMIN (Phase 2)
# =============================================================================

class EquitySnapshotLineInline(admin.TabularInline):
    """Inline for viewing snapshot lines within snapshot admin"""
    model = EquitySnapshotLine
    extra = 0
    readonly_fields = [
        'member', 'member_name', 'member_type', 'member_role',
        'cash_usd', 'inkind_usd', 'time_usd', 'work_usd',
        'weighted_total_usd', 'equity_percentage'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EquitySnapshot)
class EquitySnapshotAdmin(admin.ModelAdmin):
    """Admin interface for Equity Snapshots"""
    
    list_display = [
        'version_id', 'deal', 'snapshot_date', 'status', 'is_locked',
        'members_count', 'total_valuation_usd', 'created_by'
    ]
    list_filter = ['status', 'is_locked', 'deal', 'snapshot_date']
    search_fields = ['version_id', 'notes', 'checksum']
    readonly_fields = [
        'version_id', 'checksum', 'auto_lock_date',
        'total_cash_usd', 'total_inkind_usd', 'total_time_usd',
        'total_work_usd', 'total_valuation_usd', 'members_count',
        'created_at', 'updated_at', 'locked_at'
    ]
    
    inlines = [EquitySnapshotLineInline]
    
    fieldsets = (
        ('Snapshot Identity', {
            'fields': ('deal', 'version_id', 'snapshot_date', 'period_start', 'period_end')
        }),
        ('Status', {
            'fields': ('status', 'is_locked', 'locked_by', 'locked_at')
        }),
        ('Dispute Window', {
            'fields': ('dispute_window_days', 'auto_lock_date')
        }),
        ('Aggregated Totals', {
            'fields': (
                'members_count',
                'total_cash_usd', 'total_inkind_usd',
                'total_time_usd', 'total_work_usd',
                'total_valuation_usd'
            ),
            'classes': ('collapse',)
        }),
        ('Integrity', {
            'fields': ('checksum',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of locked snapshots"""
        if obj and obj.is_locked:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(EquitySnapshotLine)
class EquitySnapshotLineAdmin(admin.ModelAdmin):
    """Admin interface for Snapshot Lines"""
    
    list_display = [
        'snapshot', 'member_name', 'equity_percentage',
        'weighted_total_usd', 'member_type'
    ]
    list_filter = ['snapshot__deal', 'member_type']
    search_fields = ['member_name', 'snapshot__version_id']
    readonly_fields = [
        'snapshot', 'member', 'member_name', 'member_type', 'member_role',
        'cash_usd', 'inkind_usd', 'time_usd', 'work_usd',
        'weighted_total_usd', 'equity_percentage', 'created_at'
    ]
    
    fieldsets = (
        ('Snapshot', {
            'fields': ('snapshot',)
        }),
        ('Member', {
            'fields': ('member', 'member_name', 'member_type', 'member_role')
        }),
        ('Contributions (USD)', {
            'fields': ('cash_usd', 'inkind_usd', 'time_usd', 'work_usd')
        }),
        ('Equity', {
            'fields': ('weighted_total_usd', 'equity_percentage')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of snapshot lines"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of snapshot lines"""
        return False


@admin.register(SnapshotAuditLog)
class SnapshotAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for Snapshot Audit Logs"""
    
    list_display = [
        'snapshot', 'action', 'performed_by', 'created_at', 'ip_address'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['snapshot__version_id', 'performed_by__username']
    readonly_fields = [
        'snapshot', 'action', 'performed_by', 'details',
        'ip_address', 'created_at'
    ]
    
    fieldsets = (
        ('Audit Entry', {
            'fields': ('snapshot', 'action', 'performed_by', 'created_at')
        }),
        ('Details', {
            'fields': ('details', 'ip_address')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs"""
        return False


# =============================================================================
# COMPREHENSIVE AUDIT LOG ADMIN
# =============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for system-wide Audit Logs (Read-Only)"""
    
    list_display = [
        'timestamp', 'actor', 'action_type', 'entity_type', 
        'entity_reference', 'status', 'ip_address'
    ]
    list_filter = [
        'action_type', 'entity_type', 'status', 
        'timestamp', 'request_source'
    ]
    search_fields = [
        'entity_reference', 'description', 'actor__username',
        'entity_id', 'ip_address'
    ]
    readonly_fields = [
        'deal', 'timestamp', 'actor', 'action_type', 'entity_type',
        'entity_id', 'entity_reference', 'description', 'ip_address',
        'request_source', 'status', 'details', 'old_values', 'new_values'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Entry', {
            'fields': (
                'deal', 'timestamp', 'actor', 'action_type', 
                'entity_type', 'entity_id', 'entity_reference'
            )
        }),
        ('Description', {
            'fields': ('description', 'status')
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'request_source')
        }),
        ('Change Tracking', {
            'fields': ('old_values', 'new_values', 'details'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs"""
        return False
