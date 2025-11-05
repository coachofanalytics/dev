from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import (
    UserGroups,
    CustomerUser,
    Tracker,
    LoginHistory,
    Credential,
    CredentialCategory,
    Department,
    Team_Members,
    UserProfile,
    TeamProfile,
)
from .user_utils import (
    get_user_employment_status,
    get_user_client_status,
    get_user_applicant_status,
    get_user_lifecycle_stage,
)


# admin.site.register(CustomerUser)
class CustomerAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm

    # Override filter_horizontal to only include groups (not user_permissions)
    filter_horizontal = ("groups",)

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "category",
        "sub_category",
        "get_employment_status",
        "get_client_status",
        "get_applicant_status",
        "get_lifecycle_stage",
        "is_active",
        "is_staff",
        "is_admin",
    )

    list_filter = (
        "category",
        "sub_category",
        "is_active",
        "is_staff",
        "is_admin",
        "is_superuser",
        "date_joined",
        "last_login",
    )

    search_fields = ("username", "last_name", "email", "first_name")

    readonly_fields = (
        "get_employment_status",
        "get_client_status",
        "get_applicant_status",
        "get_lifecycle_stage",
        "date_joined",
        "last_login",
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    ) + (
        (
            "CODA User Information",
            {
                "fields": (
                    "gender",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "category",
                    "sub_category",
                    "is_admin",
                    "resume_file",
                    "email_verified",
                    "verification_token",
                )
            },
        ),
        (
            "Computed Status (Read-only)",
            {
                "fields": (
                    "get_employment_status",
                    "get_client_status",
                    "get_applicant_status",
                    "get_lifecycle_stage",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    ) + (
        (
            "CODA User Information",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "gender",
                    "category",
                    "sub_category",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "is_admin",
                    "resume_file",
                    "email_verified",
                    "verification_token",
                )
            },
        ),
    )

    # Computed columns for admin list display
    def get_employment_status(self, obj):
        """Display employment status in admin list"""
        return get_user_employment_status(obj)

    get_employment_status.short_description = "Employment Status"
    get_employment_status.admin_order_field = "category"

    def get_client_status(self, obj):
        """Display client status in admin list"""
        return get_user_client_status(obj)

    get_client_status.short_description = "Client Status"
    get_client_status.admin_order_field = "category"

    def get_applicant_status(self, obj):
        """Display applicant status in admin list"""
        return get_user_applicant_status(obj)

    get_applicant_status.short_description = "Applicant Status"
    get_applicant_status.admin_order_field = "category"

    def get_lifecycle_stage(self, obj):
        """Display lifecycle stage in admin list"""
        return get_user_lifecycle_stage(obj)

    get_lifecycle_stage.short_description = "Lifecycle Stage"
    get_lifecycle_stage.admin_order_field = "last_login"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time")
    list_filter = ("user", "login_time", "logout_time")
    search_fields = ("user__username",)


class UserGroupsAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "is_active")
    list_editable = ("is_featured", "is_active")
    list_filter = ("is_featured", "is_active")


# Register the UserGroups model with the custom admin
admin.site.register(UserGroups, UserGroupsAdmin)
admin.site.register(CustomerUser, CustomerAdmin)
admin.site.register(LoginHistory, LoginHistoryAdmin)


# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Tracker)
admin.site.register(Credential)
admin.site.register(CredentialCategory)
admin.site.register(Team_Members)


@admin.register(TeamProfile)
class TeamProfileAdmin(admin.ModelAdmin):
    """
    Django Admin interface for TeamProfile - Team Assignment Management.
    
    Features:
    - View all team members with their categories and points
    - Filter by category, manual/auto assignment
    - Search by username, email
    - Bulk actions: promote, recalculate points
    - Inline editing of priority and notes
    """
    
    list_display = (
        'user_username',
        'user_fullname',
        'get_category_display',
        'priority',
        'total_points',
        'is_manually_assigned',
        'last_promoted_display',
    )
    
    list_filter = (
        'is_manually_assigned',
        ('user__groups', admin.RelatedOnlyFieldListFilter),  # Filter by group (category)
        'last_promoted',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'promotion_notes',
    )
    
    ordering = ('priority', '-total_points', 'user__date_joined')
    
    readonly_fields = (
        'get_category_display',
        'total_points_display',
        'created_at',
        'updated_at',
        'last_promoted',
    )
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'get_category_display')
        }),
        ('Assignment Details', {
            'fields': (
                'is_manually_assigned',
                'priority',
                'total_points_display',
            ),
            'description': 'Priority: Higher numbers display first. Points: Cached daily for performance.'
        }),
        ('Promotion Tracking', {
            'fields': (
                'last_promoted',
                'promotion_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'promote_to_junior_analyst',
        'promote_to_senior_analyst',
        'promote_to_lead_team',
        'recalculate_points_action',
        'mark_as_manual',
        'mark_as_points_based',
    ]
    
    # Custom display methods
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'
    
    def user_fullname(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_fullname.short_description = 'Full Name'
    user_fullname.admin_order_field = 'user__first_name'
    
    def get_category_display(self, obj):
        category = obj.category
        if category:
            assignment_type = '📌 Manual' if obj.is_manually_assigned else '📊 Auto'
            return f"{category} ({assignment_type})"
        return '❌ Not Assigned'
    get_category_display.short_description = 'Team Category'
    
    def total_points_display(self, obj):
        if obj.is_promotion_ready:
            return f"{obj.total_points:,} points 🎯 READY FOR PROMOTION!"
        return f"{obj.total_points:,} points"
    total_points_display.short_description = 'Total Points'
    
    def last_promoted_display(self, obj):
        if obj.last_promoted:
            from django.utils import timezone
            days_ago = (timezone.now() - obj.last_promoted).days
            return f"{obj.last_promoted.strftime('%Y-%m-%d')} ({days_ago} days ago)"
        return 'Never'
    last_promoted_display.short_description = 'Last Promoted'
    
    # Bulk actions
    def promote_to_junior_analyst(self, request, queryset):
        from main.services.team_service import TeamService
        from django.contrib import messages
        
        count = 0
        for team_profile in queryset:
            TeamService.assign_to_category(
                team_profile.user,
                'Junior Analysts',
                priority=50,
                is_manual=True,
                notes=f'Promoted by {request.user.username} via Django Admin'
            )
            count += 1
        
        self.message_user(
            request,
            f'Successfully promoted {count} member(s) to Junior Analysts',
            messages.SUCCESS
        )
    promote_to_junior_analyst.short_description = '🎯 Promote selected to Junior Analysts'
    
    def promote_to_senior_analyst(self, request, queryset):
        from main.services.team_service import TeamService
        from django.contrib import messages
        
        count = 0
        for team_profile in queryset:
            TeamService.assign_to_category(
                team_profile.user,
                'Senior Analysts',
                priority=70,
                is_manual=True,
                notes=f'Promoted by {request.user.username} via Django Admin'
            )
            count += 1
        
        self.message_user(
            request,
            f'Successfully promoted {count} member(s) to Senior Analysts',
            messages.SUCCESS
        )
    promote_to_senior_analyst.short_description = '⭐ Promote selected to Senior Analysts'
    
    def promote_to_lead_team(self, request, queryset):
        from main.services.team_service import TeamService
        from django.contrib import messages
        
        count = 0
        for team_profile in queryset:
            TeamService.assign_to_category(
                team_profile.user,
                'Lead Team',
                priority=80,
                is_manual=True,
                notes=f'Promoted by {request.user.username} via Django Admin'
            )
            count += 1
        
        self.message_user(
            request,
            f'Successfully promoted {count} member(s) to Lead Team',
            messages.SUCCESS
        )
    promote_to_lead_team.short_description = '🌟 Promote selected to Lead Team'
    
    def recalculate_points_action(self, request, queryset):
        from main.services.team_service import TeamService
        from django.contrib import messages
        from django.utils import timezone
        
        count = 0
        for team_profile in queryset:
            points = TeamService.calculate_total_points(team_profile.user)
            team_profile.total_points = points
            team_profile.save()
            count += 1
        
        self.message_user(
            request,
            f'Successfully recalculated points for {count} member(s)',
            messages.SUCCESS
        )
    recalculate_points_action.short_description = '🔄 Recalculate points for selected'
    
    def mark_as_manual(self, request, queryset):
        from django.contrib import messages
        
        count = queryset.update(is_manually_assigned=True)
        
        self.message_user(
            request,
            f'Marked {count} member(s) as manually assigned',
            messages.SUCCESS
        )
    mark_as_manual.short_description = '📌 Mark as Manual Assignment'
    
    def mark_as_points_based(self, request, queryset):
        from django.contrib import messages
        
        count = queryset.update(is_manually_assigned=False)
        
        self.message_user(
            request,
            f'Marked {count} member(s) as points-based',
            messages.SUCCESS
        )
    mark_as_points_based.short_description = '📊 Mark as Points-Based'
