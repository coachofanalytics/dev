from django.contrib import admin
from .models import *

class DescriptionAdmin(admin.ModelAdmin):
    list_display = ("page", "name", "content")

    search_fields = ("page", "name")
    list_filter = ("name",)
    ordering = ("name",)
    filter_horizontal = ()


class DescriptionGovernance(admin.ModelAdmin):
    list_display = ("governance_category", "members", "title", "ui_order")

    # search_fields = ("page", "name")
    list_filter = ("governance_category",)
    # ordering = ("name",)
    # filter_horizontal = ()


class LegalServiceAdmin(admin.ModelAdmin):
    """Admin interface for managing Legal & Immigration Services"""
    list_display = ['title', 'category', 'is_active', 'order', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'description', 'order')
        }),
        ('Media & Content', {
            'fields': ('image_url', 'features')
        }),
        ('Call-to-Action', {
            'fields': ('cta_button_text', 'cta_button_url')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

# Register your models here.
# admin.site.register(Assets)
#admin.site.register(Feedback)
admin.site.register(Description, DescriptionAdmin)
# admin.site.register(Page)
#admin.site.register(Team)
#admin.site.register(Content)
#admin.site.register(Service)
#admin.site.register(SubService)
admin.site.register(News)
admin.site.register(Gallery)
admin.site.register(ContactUs)
#admin.site.register(Faq)
admin.site.register(GetHelp)
admin.site.register(Governance, DescriptionGovernance)
#admin.site.register(DonationOrganization)

# Consular Assistance & Legal Services
admin.site.register(ConsularAssistancePage)
admin.site.register(LegalService, LegalServiceAdmin)
