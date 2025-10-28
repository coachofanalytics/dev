from django.contrib import admin
from ai_services.models import (
	CashappMail, DynamicExcelData, GotoMeetings,ReplyMail,
    Editable,UseCase,CaseCategory,OpenaiPrompt,UpworkConnects,
    # New Phase 1 models
    Meeting, MeetingAttendee, OAuthToken, MeetingActivityMapping
)

class CaseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )

# Register your models here.
admin.site.register(CaseCategory, CaseCategoryAdmin)
admin.site.register(CashappMail)
admin.site.register(ReplyMail)
admin.site.register(Editable)
admin.site.register(OpenaiPrompt)
admin.site.register(UseCase)
admin.site.register(UpworkConnects)
admin.site.register(DynamicExcelData)
admin.site.register(GotoMeetings)  # Legacy - keep for backward compatibility


# ==================== NEW PHASE 1 ADMIN REGISTRATIONS ====================

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Admin interface for Meeting model"""
    list_display = (
        'meeting_id',
        'topic',
        'meeting_type',
        'start_time',
        'duration_minutes',
        'attendee_count',
        'is_recorded',
    )
    list_filter = (
        'meeting_type',
        'is_recorded',
        'start_time',
    )
    search_fields = (
        'meeting_id',
        'topic',
        'meeting_type',
    )
    readonly_fields = (
        'meeting_id',
        'created_at',
        'updated_at',
        'attendee_count',
        'average_attendance_duration',
    )
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    fieldsets = (
        ('Meeting Information', {
            'fields': ('meeting_id', 'topic', 'meeting_type')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration_minutes')
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url', 'download_url', 'google_drive_url')
        }),
        ('Statistics', {
            'fields': ('attendee_count', 'average_attendance_duration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class MeetingAttendeeInline(admin.TabularInline):
    """Inline display of attendees in Meeting admin"""
    model = MeetingAttendee
    extra = 0
    readonly_fields = ('attendance_percentage', 'qualifies_for_points')
    fields = ('attendee_name', 'attendee_email', 'duration_minutes', 'user', 'task_points_awarded')


@admin.register(MeetingAttendee)
class MeetingAttendeeAdmin(admin.ModelAdmin):
    """Admin interface for MeetingAttendee model"""
    list_display = (
        'attendee_name',
        'attendee_email',
        'meeting',
        'duration_minutes',
        'attendance_percentage',
        'task_points_awarded',
    )
    list_filter = (
        'task_points_awarded',
        'is_organizer',
        'meeting__start_time',
    )
    search_fields = (
        'attendee_name',
        'attendee_email',
        'meeting__topic',
    )
    readonly_fields = (
        'attendance_percentage',
        'qualifies_for_points',
        'created_at',
        'updated_at',
    )
    raw_id_fields = ('meeting', 'user')
    
    fieldsets = (
        ('Attendee Information', {
            'fields': ('attendee_name', 'attendee_email', 'user')
        }),
        ('Meeting', {
            'fields': ('meeting',)
        }),
        ('Attendance', {
            'fields': ('duration_minutes', 'attendance_percentage', 'is_organizer')
        }),
        ('Task Integration', {
            'fields': ('qualifies_for_points', 'task_points_awarded')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    """Admin interface for OAuthToken model"""
    list_display = (
        'service_name',
        'token_type',
        'expires_at',
        'is_expired',
        'needs_refresh',
        'is_valid',
        'last_refreshed_at',
    )
    list_filter = (
        'service_name',
        'token_type',
        'is_valid',
    )
    search_fields = (
        'service_name',
    )
    readonly_fields = (
        'is_expired',
        'needs_refresh',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Service', {
            'fields': ('service_name', 'token_type', 'scope')
        }),
        ('Tokens', {
            'fields': ('access_token', 'refresh_token'),
            'description': 'Tokens are encrypted before storage'
        }),
        ('Validity', {
            'fields': ('expires_at', 'is_valid', 'is_expired', 'needs_refresh', 'last_refreshed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make tokens read-only in change form for security"""
        if obj:  # Editing existing token
            return self.readonly_fields + ('access_token', 'refresh_token')
        return self.readonly_fields


@admin.register(MeetingActivityMapping)
class MeetingActivityMappingAdmin(admin.ModelAdmin):
    """Admin interface for MeetingActivityMapping model"""
    list_display = (
        'meeting_id_pattern',
        'activity_name',
        'task_points',
        'min_duration_minutes',
        'is_active',
    )
    list_filter = (
        'is_active',
    )
    search_fields = (
        'meeting_id_pattern',
        'activity_name',
        'description',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Mapping', {
            'fields': ('meeting_id_pattern', 'activity_name', 'description')
        }),
        ('Task Points', {
            'fields': ('task_points', 'min_duration_minutes')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )