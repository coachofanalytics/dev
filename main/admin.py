from django.contrib import admin
from django.utils.html import format_html
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

# Consular Assistance
from .models import ConsularAssistancePage, LegalService
admin.site.register(ConsularAssistancePage)

@admin.register(LegalService)
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


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    """Admin for Consular consultation requests (and other future service requests)."""
    list_display = [
        'reference_number',
        'full_name',
        'email',
        'service_type',
        'consultation_type',
        'urgency_colored',
        'status',
        'assigned_to',
        'created_at',
        'days_old',
    ]
    list_filter = ['status', 'service_type', 'consultation_type', 'urgency', 'assigned_to', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'question', 'admin_notes', 'location']
    readonly_fields = ['created_at', 'updated_at', 'replied_at']
    list_editable = ['status']
    list_per_page = 25
    date_hierarchy = 'created_at'

    actions = [
        'mark_as_in_review',
        'mark_as_responded',
        'mark_as_closed',
        'assign_to_me',
        'send_reply_email',
    ]

    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone', 'location', 'preferred_language')
        }),
        ('Request Details', {
            'fields': ('service_type', 'consultation_type', 'urgency', 'question', 'additional_notes')
        }),
        ('Workflow', {
            'fields': ('status', 'assigned_to', 'admin_notes')
        }),
        ('Reply', {
            'fields': ('reply_message', 'replied_at'),
            'description': 'Write a reply and use the "Send reply email" action to email it to the user.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def reference_number(self, obj):
        return f'CR-{obj.id:05d}'
    reference_number.short_description = 'Ref #'

    def urgency_colored(self, obj):
        colors = {
            'Emergency': 'red',
            'Very Urgent': 'orange',
            'Moderately Urgent': '#b8860b',
            'Not Urgent': 'green',
        }
        color = colors.get(obj.urgency, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.urgency)
    urgency_colored.short_description = 'Urgency'

    def days_old(self, obj):
        days = obj.days_since_created()
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        return f'{days} days'
    days_old.short_description = 'Age'

    def mark_as_in_review(self, request, queryset):
        for req in queryset:
            req.status = 'in_review'
            req.save(update_fields=['status', 'updated_at'])
            req.add_note(f"Marked In Review by {request.user.username}")
        self.message_user(request, f"{queryset.count()} request(s) marked as In Review.")
    mark_as_in_review.short_description = "Mark selected as In Review"

    def mark_as_responded(self, request, queryset):
        for req in queryset:
            req.mark_responded()
        self.message_user(request, f"{queryset.count()} request(s) marked as Responded.")
    mark_as_responded.short_description = "Mark selected as Responded"

    def mark_as_closed(self, request, queryset):
        for req in queryset:
            req.mark_closed()
        self.message_user(request, f"{queryset.count()} request(s) marked as Closed.")
    mark_as_closed.short_description = "Mark selected as Closed"

    def assign_to_me(self, request, queryset):
        for req in queryset:
            req.assigned_to = request.user
            req.save(update_fields=['assigned_to', 'updated_at'])
            req.add_note(f"Assigned to {request.user.username}")
        self.message_user(request, f"Assigned {queryset.count()} request(s) to you.")
    assign_to_me.short_description = "Assign to me"

    def send_reply_email(self, request, queryset):
        """Send the reply_message field content as an email to the user."""
        from mail.custom_email import send_email
        sent_count = 0
        for req in queryset:
            if not req.reply_message.strip():
                continue
            try:
                send_email(
                    category=0,
                    to_email=[req.email],
                    subject=f'Response to Your Consultation Request (CR-{req.id:05d}) - DC48K',
                    html_template='main/email/consultation_reply.html',
                    context={
                        'purpose': 'consultation_reply',
                        'full_name': req.full_name,
                        'reply_message': req.reply_message.replace('\n', '<br>'),
                        'reference_number': f'CR-{req.id:05d}',
                        'consultation_type': req.consultation_type,
                    },
                    from_name="Diaspora County 048 - Consular Services"
                )
                req.mark_responded()
                req.add_note(f"Reply email sent by {request.user.username}")
                sent_count += 1
            except Exception as e:
                req.add_note(f"Failed to send reply email: {e}")
        self.message_user(request, f"Sent reply emails for {sent_count} request(s).")
    send_reply_email.short_description = "Send reply email to selected"
