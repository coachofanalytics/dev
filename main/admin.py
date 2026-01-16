from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Assets)
admin.site.register(Feedback)
admin.site.register(Description)
admin.site.register(Page)
admin.site.register(Team)
admin.site.register(Content)
class SubServiceInline(admin.TabularInline):
    model = SubService
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'ordering', 'slug')
    inlines = [SubServiceInline]

# admin.site.register(Service) # Replaced by ServiceAdmin
# admin.site.register(SubService) # Inline in ServiceAdmin
admin.site.register(News)
admin.site.register(Gallery_image)
admin.site.register(ContactUs)
admin.site.register(SafetyAlertSubscription)
admin.site.register(EmergencyHot)
admin.site.register(StaffContact)
admin.site.register(EmergencyHelpActivations)
admin.site.register(Donation_organisation)
admin.site.register(ContactMessage)
admin.site.register(Donation_organization)
admin.site.register(Scholarship)

@admin.register(DocumentationRequest)
class DocumentationRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name','email','phone','document_type','package_type','destination_country','status','created_at')
    list_filter = ('status','document_type','package_type','created_at')
    search_fields = ('full_name','email','phone','document_type','destination_country','status','created_at')
    readonly_fields = ('created_at',)
    list_per_page = 25
    ordering = ('-created_at',)
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name','email','phone')
        }),
        ('Request Details', {
            'fields': ('document_type','package_type','destination_country','description','consent')
        }),
        ('Status & Tracking', {
            'fields': ('status','created_at')
        }),
    )