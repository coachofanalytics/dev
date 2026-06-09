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
admin.site.register(TrainingCourse)
admin.site.register(Testimonial)
admin.site.register(Governance)
admin.site.register(Gallery)
admin.site.register(GetHelp)
admin.site.register(Faq)
admin.site.register(DonationOrganization)


# admin.site.register(Testimonial)
from .models import ConsularAssistancePage
admin.site.register(ConsularAssistancePage)

admin.site.register(AppointmentRequest)
admin.site.register(Doctor)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
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
    list_filter = [
        'status',
        'service_type',
        'consultation_type',
        'urgency',
        'assigned_to',
        'created_at',
    ]
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

    # Custom display methods

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

    def status_colored(self, obj):
        colors = {
            'new': '#2563eb',
            'in_review': '#b8860b',
            'responded': '#16a34a',
            'closed': '#6b7280',
        }
        labels = {
            'new': 'New',
            'in_review': 'In Review',
            'responded': 'Responded',
            'closed': 'Closed',
        }
        color = colors.get(obj.status, 'gray')
        label = labels.get(obj.status, obj.status)
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, label)
    status_colored.short_description = 'Status'

    def days_old(self, obj):
        days = obj.days_since_created()
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        return f'{days} days'
    days_old.short_description = 'Age'

    # Bulk actions

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
                    html_template='email/consultation_reply.html',
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


@admin.register(ExpertInquiry)
class ExpertInquiryAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'priority_colored', 
        'sla_status_colored',
        'assigned_to',
        'interested_plan', 
        'created_at', 
        'response_time_display',
        'days_old',
        'status_colored',
        'is_contacted'  # Added is_contacted to list_display
    ]
    list_filter = [
        'is_contacted', 
        'assigned_to', 
        'escalated' ,
        'created_at', 
        'interested_plan'
        ]
    search_fields = ['full_name', 'email', 'question', 'notes']
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'priority_display', 
        'days_old_display',
        'sla_deadline_display',
        'response_time_display',
        'escalated_display'
        ]
    list_editable = ['is_contacted']  # Now this is in list_display, so it's fine
    actions = [
        'mark_as_contacted', 
        'add_urgent_note', 
        'send_reminder',
        'assign_to_me',
        'escalated_selected'
        ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Inquiry Details', {
            'fields': ('question', 'interested_plan', 'notes')
        }),
        ('SLA & Assignment', {
            'fields': (
                'assigned_to',
                'sla_deadline',
                'first_response_time',
                'escalated',
                'escalated_to',
            ),
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

     # NEW METHODS FOR SLA DISPLAY
    
    def sla_status_colored(self, obj):
        """Display SLA status with colors"""
        status = obj.get_sla_status()
        if "🔴" in status:
            return format_html(f'<span style="color: red; font-weight: bold;">{status}</span>')
        elif "🟠" in status:
            return format_html(f'<span style="color: orange; font-weight: bold;">{status}</span>')
        elif "🟡" in status:
            return format_html(f'<span style="color: #b8860b; font-weight: bold;">{status}</span>')
        else:
            return format_html(f'<span style="color: green; font-weight: bold;">{status}</span>')
    sla_status_colored.short_description = 'SLA Status'
    
    def response_time_display(self, obj):
        """Display response time"""
        return obj.get_response_time()
    response_time_display.short_description = 'Response Time'
    
    def sla_deadline_display(self, obj):
        """Display SLA deadline"""
        if obj.sla_deadline:
            return obj.sla_deadline.strftime('%Y-%m-%d %H:%M')
        return "Not set"
    sla_deadline_display.short_description = 'SLA Deadline'
    
    def escalated_display(self, obj):
        """Display escalation status"""
        if obj.escalated:
            return f"🚨 Escalated to {obj.escalated_to} at {obj.escalated_at.strftime('%H:%M %d/%m')}"
        return "No"
    escalated_display.short_description = 'Escalated'
    
    # NEW ACTIONS
    
    def assign_to_me(self, request, queryset):
        """Assign selected inquiries to current user"""
        for inquiry in queryset:
            inquiry.assigned_to = request.user
            inquiry.save()
            inquiry.add_note(f"Assigned to {request.user.username}")
        self.message_user(request, f"Assigned {queryset.count()} inquiries to you")
    assign_to_me.short_description = "Assign to me"
    
    def escalate_selected(self, request, queryset):
        """Manually escalate selected inquiries"""
        from django.utils import timezone
        for inquiry in queryset:
            inquiry.escalated = True
            inquiry.escalated_at = timezone.now()
            inquiry.escalated_to = request.user
            inquiry.save()
            inquiry.add_note(f"🚨 Manually escalated by {request.user.username}")
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


# ============================================
# COMMUNITIES APP MODELS ADMIN REGISTRATION
# ============================================

@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'user', 'profession', 'region', 'is_verified', 'is_public_directory', 'date_joined']
    list_filter = ['is_verified', 'is_public_directory', 'region', 'date_joined']
    search_fields = ['name', 'email', 'profession', 'specialization', 'region']
    readonly_fields = ['date_joined', 'last_updated']
    raw_id_fields = ['user']
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'user', 'profession')
        }),
        ('Profile Details', {
            'fields': ('region', 'specialization', 'bio', 'website', 'profile_picture')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_public_directory')
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DirectoryProfile)
class DirectoryProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'profession', 'region_city', 'category', 'membership_type', 'is_approved', 'is_published']
    list_filter = ['is_approved', 'is_published', 'category', 'membership_type', 'region_city']
    search_fields = ['full_name', 'profession', 'category', 'expertise_summary']
    fieldsets = (
        ('Profile Information', {
            'fields': ('community_member', 'full_name', 'profession', 'region_city')
        }),
        ('Expertise', {
            'fields': ('category', 'membership_type', 'expertise_summary', 'profile_photo')
        }),
        ('Publishing', {
            'fields': ('is_approved', 'is_published')
        }),
    )


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'category')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(CommentP)
class CommentPAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_at']
    list_filter = ['post', 'author', 'created_at']
    search_fields = ['content', 'post__title', 'author__username']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Comment', {
            'fields': ('post', 'author', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventCalendar)
class EventCalendarAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'location']
    list_filter = ['start_date', 'end_date', 'location']
    search_fields = ['name', 'description', 'location']
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'location', 'description')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(CommunityMessage)
class CommunityMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__name', 'recipient__name', 'subject', 'body']
    readonly_fields = ['created_at']
    raw_id_fields = ['sender', 'recipient', 'parent_message']
    fieldsets = (
        ('Participants', {
            'fields': ('sender', 'recipient')
        }),
        ('Content', {
            'fields': ('subject', 'body', 'parent_message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )


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

