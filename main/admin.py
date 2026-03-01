from django.contrib import admin
from django.utils.html import format_html
from .models import *

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
admin.site.register(ContactUs)
#<<<<<<< 25.10_DC48_UAT_UO
admin.site.register(SafetyAlertSubscription)
admin.site.register(EmergencyHotline)
admin.site.register(StaffContact)
#admin.site.register(EmergencyHelpActivation)

admin.site.register(Donation_organisation)
admin.site.register(ContactMessage)
admin.site.register(Donation_organization)
admin.site.register(Scholarship)
admin.site.register(Testimonial)
admin.site.register(Governance)


# admin.site.register(Testimonial)
from .models import ConsularAssistancePage
admin.site.register(ConsularAssistancePage)

admin.site.register(AppointmentRequest)
admin.site.register(Doctor)



@admin.register(ExpertInquiry)
class ExpertInquiryAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'priority_colored', 
        'interested_plan', 
        'created_at', 
        'days_old',
        'status_colored',
        'is_contacted'  # Added is_contacted to list_display
    ]
    list_filter = ['is_contacted', 'created_at', 'interested_plan']
    search_fields = ['full_name', 'email', 'question', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'priority_display', 'days_old_display']
    list_editable = ['is_contacted']  # Now this is in list_display, so it's fine
    actions = ['mark_as_contacted', 'add_urgent_note', 'send_reminder']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Inquiry Details', {
            'fields': ('question', 'interested_plan', 'notes')
        }),
        ('Status', {
            'fields': ('is_contacted', 'created_at', 'updated_at')
        }),
        ('Auto-generated Info', {
            'classes': ('collapse',),
            'fields': ('priority_display', 'days_old_display')
        }),
    )
    
    def priority_colored(self, obj):
        priority = obj.get_priority()
        colors = {
            'URGENT': 'red',
            'HIGH': 'orange',
            'NORMAL': 'green'
        }
        color = colors.get(priority, 'gray')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{priority}</span>')
    priority_colored.short_description = 'Priority'
    
    def status_colored(self, obj):
        if obj.is_contacted:
            return format_html('<span style="color: green;">✓ Contacted</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    status_colored.short_description = 'Status'
    
    def days_old(self, obj):
        days = obj.days_since_created()
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        else:
            return f'{days} days'
    days_old.short_description = 'Age'
    
    def priority_display(self, obj):
        return obj.get_priority()
    priority_display.short_description = 'Priority'
    
    def days_old_display(self, obj):
        return f"{obj.days_since_created()} days"
    days_old_display.short_description = 'Days Old'
    
    def mark_as_contacted(self, request, queryset):
        for inquiry in queryset:
            inquiry.mark_as_contacted(notes="Marked via bulk action")
        self.message_user(request, f"{queryset.count()} inquiries marked as contacted.")
    mark_as_contacted.short_description = "Mark selected as contacted"
    
    def add_urgent_note(self, request, queryset):
        for inquiry in queryset:
            inquiry.add_note("⚠️ Marked as urgent by admin")
        self.message_user(request, f"Added urgent note to {queryset.count()} inquiries.")
    add_urgent_note.short_description = "Add urgent note"
    
    def send_reminder(self, request, queryset):
        for inquiry in queryset:
            # You can implement reminder email logic here
            pass
        self.message_user(request, f"Reminders sent for {queryset.count()} inquiries.")
    send_reminder.short_description = "Send reminder"


@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ['provider_name', 'plan_name', 'network', 'max_benefit', 'score', 'is_active']
    list_editable = ['score', 'is_active']
    list_filter = ['is_active', 'provider_name']
    search_fields = ['provider_name', 'plan_name']


@admin.register(AIRecommendationRule)
class AIRecommendationRuleAdmin(admin.ModelAdmin):
    list_display = ['age_bracket', 'residence', 'priority', 'recommended_plan', 'is_active']
    list_filter = ['age_bracket', 'residence', 'priority', 'is_active']
    search_fields = ['recommendation_text']
