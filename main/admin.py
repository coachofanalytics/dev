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

# Healthcare models
from django.utils.html import format_html
admin.site.register(AppointmentRequest)
admin.site.register(Doctor)

@admin.register(ExpertInquiry)
class ExpertInquiryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'priority_colored', 'sla_status_colored', 'assigned_to', 'interested_plan', 'created_at', 'response_time_display', 'days_old', 'status_colored', 'is_contacted']
    list_filter = ['is_contacted', 'assigned_to', 'escalated', 'created_at', 'interested_plan']
    search_fields = ['full_name', 'email', 'question', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'priority_display', 'days_old_display', 'sla_deadline_display', 'response_time_display', 'escalated_display']
    list_editable = ['is_contacted']
    actions = ['mark_as_contacted', 'add_urgent_note', 'send_reminder', 'assign_to_me', 'escalate_selected']

    fieldsets = (
        ('Contact Information', {'fields': ('full_name', 'email', 'phone')}),
        ('Inquiry Details', {'fields': ('question', 'interested_plan', 'notes')}),
        ('SLA & Assignment', {'fields': ('assigned_to', 'sla_deadline', 'first_response_time', 'escalated', 'escalated_to')}),
        ('Status', {'fields': ('is_contacted', 'created_at', 'updated_at')}),
        ('Auto-generated Info', {'classes': ('collapse',), 'fields': ('priority_display', 'days_old_display')}),
    )

    def priority_colored(self, obj):
        priority = obj.get_priority()
        colors = {'URGENT': 'red', 'HIGH': 'orange', 'NORMAL': 'green'}
        color = colors.get(priority, 'gray')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{priority}</span>')
    priority_colored.short_description = 'Priority'

    def status_colored(self, obj):
        if obj.is_contacted:
            return format_html('<span style="color: green;">Contacted</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">Overdue</span>')
        else:
            return format_html('<span style="color: orange;">Pending</span>')
    status_colored.short_description = 'Status'

    def days_old(self, obj):
        days = obj.days_since_created()
        if days == 0: return 'Today'
        elif days == 1: return 'Yesterday'
        else: return f'{days} days'
    days_old.short_description = 'Age'

    def priority_display(self, obj): return obj.get_priority()
    priority_display.short_description = 'Priority'

    def days_old_display(self, obj): return f"{obj.days_since_created()} days"
    days_old_display.short_description = 'Days Old'

    def sla_status_colored(self, obj):
        status = obj.get_sla_status()
        if "Breached" in status:
            return format_html(f'<span style="color: red; font-weight: bold;">{status}</span>')
        elif "Critical" in status:
            return format_html(f'<span style="color: orange; font-weight: bold;">{status}</span>')
        elif "Risk" in status:
            return format_html(f'<span style="color: #b8860b; font-weight: bold;">{status}</span>')
        else:
            return format_html(f'<span style="color: green; font-weight: bold;">{status}</span>')
    sla_status_colored.short_description = 'SLA Status'

    def response_time_display(self, obj): return obj.get_response_time()
    response_time_display.short_description = 'Response Time'

    def sla_deadline_display(self, obj):
        if obj.sla_deadline: return obj.sla_deadline.strftime('%Y-%m-%d %H:%M')
        return "Not set"
    sla_deadline_display.short_description = 'SLA Deadline'

    def escalated_display(self, obj):
        if obj.escalated:
            return f"Escalated to {obj.escalated_to} at {obj.escalated_at.strftime('%H:%M %d/%m')}"
        return "No"
    escalated_display.short_description = 'Escalated'

    def mark_as_contacted(self, request, queryset):
        for inquiry in queryset:
            inquiry.mark_as_contacted(notes="Marked via bulk action")
        self.message_user(request, f"{queryset.count()} inquiries marked as contacted.")
    mark_as_contacted.short_description = "Mark selected as contacted"

    def add_urgent_note(self, request, queryset):
        for inquiry in queryset:
            inquiry.add_note("Marked as urgent by admin")
        self.message_user(request, f"Added urgent note to {queryset.count()} inquiries.")
    add_urgent_note.short_description = "Add urgent note"

    def send_reminder(self, request, queryset):
        for inquiry in queryset:
            pass
        self.message_user(request, f"Reminders sent for {queryset.count()} inquiries.")
    send_reminder.short_description = "Send reminder"

    def assign_to_me(self, request, queryset):
        for inquiry in queryset:
            inquiry.assigned_to = request.user
            inquiry.save()
            inquiry.add_note(f"Assigned to {request.user.username}")
        self.message_user(request, f"Assigned {queryset.count()} inquiries to you")
    assign_to_me.short_description = "Assign to me"

    def escalate_selected(self, request, queryset):
        from django.utils import timezone
        for inquiry in queryset:
            inquiry.escalated = True
            inquiry.escalated_at = timezone.now()
            inquiry.escalated_to = request.user
            inquiry.save()
            inquiry.add_note(f"Manually escalated by {request.user.username}")
        self.message_user(request, f"Escalated {queryset.count()} inquiries")
    escalate_selected.short_description = "Escalate selected"


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
