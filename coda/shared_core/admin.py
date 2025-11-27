"""
Shared Core Admin

Register models that are used across multiple apps via shared_core.
"""
from django.contrib import admin
from main.models import Company


# Register Company model in shared_core admin for easy access
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Company model"""
    list_display = [
        'name',
        'slug',
        'display_name',
        'website',
        'receipt_email',
        'sector',
        'relation',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active',
        'is_featured',
        'relation',
        'sector',
        'created_at'
    ]
    search_fields = [
        'name',
        'slug',
        'display_name',
        'website',
        'receipt_email',
        'sector'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'display_name', 'sector', 'mission', 'website', 'description')
        }),
        ('Receipt Branding', {
            'fields': ('logo', 'receipt_email', 'address'),
            'description': 'Configure how receipts will appear for this organization'
        }),
        ('Relationships', {
            'fields': ('location', 'user', 'relation')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

