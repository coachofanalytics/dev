"""
Shared Core Admin

Register models that are used across multiple apps via shared_core.
Note: Company is already registered in main/admin.py, so we don't register it here
to avoid duplicate registration errors.
"""
from django.contrib import admin

# Note: Company model is registered in main/admin.py
# If you need custom admin for Company in shared_core, you can:
# 1. Unregister from main/admin.py and register here, OR
# 2. Use admin.site.unregister() and re-register with custom admin class

# For now, Company is accessible via main admin.
# If needed, uncomment below and remove from main/admin.py:
#
# from main.models import Company
# 
# @admin.register(Company)
# class CompanyAdmin(admin.ModelAdmin):
#     """Admin interface for Company model"""
#     list_display = [
#         'name',
#         'slug',
#         'display_name',
#         'website',
#         'receipt_email',
#         'sector',
#         'relation',
#         'is_active',
#         'created_at'
#     ]
#     list_filter = [
#         'is_active',
#         'is_featured',
#         'relation',
#         'sector',
#         'created_at'
#     ]
#     search_fields = [
#         'name',
#         'slug',
#         'display_name',
#         'website',
#         'receipt_email',
#         'sector'
#     ]
#     readonly_fields = ['created_at', 'updated_at']
#     
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'slug', 'display_name', 'sector', 'mission', 'website', 'description')
#         }),
#         ('Receipt Branding', {
#             'fields': ('logo', 'receipt_email', 'address'),
#             'description': 'Configure how receipts will appear for this organization'
#         }),
#         ('Relationships', {
#             'fields': ('location', 'user', 'relation')
#         }),
#         ('Status', {
#             'fields': ('is_active', 'is_featured')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

