from django.contrib import admin

from .models import *
from .models import Donation

# Register your models here.
admin.site.register(Assets)
admin.site.register(Feedback)
admin.site.register(Description)
admin.site.register(Page)
admin.site.register(Team)
admin.site.register(Content)
admin.site.register(Service)
admin.site.register(SubService)
admin.site.register(News)
admin.site.register(Gallery_image)
admin.site.register(Donation)       
admin.site.register(ContactUs)
#<<<<<<< 25.10_DC48_UAT_UO
admin.site.register(SafetyAlertSubscription)
admin.site.register(EmergencyHotlines)
admin.site.register(StaffContact)
admin.site.register(EmergencyHelpActivations)

#=======
admin.site.register(Donation_organisation)
admin.site.register(ContactMessage)
admin.site.register(Donation_organization)
admin.site.register(Scholarship)
#>>>>>>> 25.10_DC48_UAT_ND

# Legal Immigration & Consular Services Admin (moved from communities)
@admin.register(ConsularService)
class ConsularServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'country_coverage', 'is_featured', 'updated_at']
    list_filter = ['service_type', 'is_featured', 'country_coverage']
    search_fields = ['name', 'description', 'services_offered']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'service_type', 'description')
        }),
        ('Contact Details', {
            'fields': ('website', 'phone', 'email', 'address')
        }),
        ('Service Details', {
            'fields': ('country_coverage', 'services_offered')
        }),
        ('Settings', {
            'fields': ('is_featured',)
        }),
    )

@admin.register(LegalImmigrationResource)
class LegalImmigrationResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_critical', 'updated_at']
    list_filter = ['category', 'is_critical']
    search_fields = ['title', 'content', 'keywords']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'category', 'content')
        }),
        ('Additional Information', {
            'fields': ('external_url', 'related_service', 'keywords')
        }),
        ('Settings', {
            'fields': ('is_critical',)
        }),
    )
admin.site.register(NetworkItem)

