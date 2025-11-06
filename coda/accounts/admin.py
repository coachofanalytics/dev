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


# Custom filters for better user management
class CategoryFilter(admin.SimpleListFilter):
    """Enhanced category filter with clear labels"""
    title = 'User Category'
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        # Get actual categories from database
        from accounts.choices import UserCategory
        categories = CustomerUser.objects.values_list('category', flat=True).distinct().order_by('category')
        category_map = {
            UserCategory.APPLICANT: '1 - Applicant (Applied to work for CODA)',
            UserCategory.STUDENT: '2 - Student (Taking courses/training)',
            UserCategory.CONSULTANT: '3 - Consultant (External professional)',
            UserCategory.INVESTOR: '4 - Investor (Financial/KCC member)',
            UserCategory.EXPLORER: '5 - Explorer (Visitor/Researcher)',
        }
        return [(cat, category_map.get(cat, f'{cat} - Unknown')) for cat in categories if cat]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


class SubCategoryFilter(admin.SimpleListFilter):
    """Enhanced subcategory filter"""
    title = 'User Sub-Category'
    parameter_name = 'sub_category'
    
    def lookups(self, request, model_admin):
        subcategories = CustomerUser.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        # Sub-categories depend on parent category, but we'll show general labels
        subcategory_map = {
            # Applicant sub-categories
            1: '1 - Full-time / Data Analytics',
            2: '2 - Contract / Programming',
            3: '3 - Internship / Other',
            # Consultant/Investor/Explorer sub-categories
            4: '4 - Individual/Partnership',
        }
        return [(subcat, subcategory_map.get(subcat, f'{subcat} - Subcategory {subcat}')) for subcat in subcategories if subcat]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sub_category=self.value())
        return queryset


class TeamAssignmentFilter(admin.SimpleListFilter):
    """Filter by team assignment status"""
    title = 'Team Assignment'
    parameter_name = 'team_assignment'
    
    def lookups(self, request, model_admin):
        return (
            ('assigned', 'Has Team Assignment'),
            ('not_assigned', 'Not Assigned to Team'),
            ('bog', 'BOG-Leadership'),
            ('elite', 'Elite Team'),
            ('lead', 'Lead Team'),
            ('support', 'Support Team'),
            ('analysts', 'Analysts (Senior/Junior)'),
            ('trainees', 'Trainees'),
            ('available', 'Available for Hire'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'assigned':
            return queryset.filter(groups__isnull=False).distinct()
        if self.value() == 'not_assigned':
            return queryset.filter(groups__isnull=True)
        if self.value() == 'bog':
            return queryset.filter(groups__name='BOG-Leadership')
        if self.value() == 'elite':
            return queryset.filter(groups__name='Elite Team')
        if self.value() == 'lead':
            return queryset.filter(groups__name='Lead Team')
        if self.value() == 'support':
            return queryset.filter(groups__name='Support Team')
        if self.value() == 'analysts':
            return queryset.filter(groups__name__in=['Senior Analysts', 'Junior Analysts'])
        if self.value() == 'trainees':
            return queryset.filter(groups__name__in=['Senior Trainee', 'Junior Trainee', 'Elementary'])
        if self.value() == 'available':
            return queryset.filter(groups__name='Available for Hire')
        return queryset


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
        "get_category_display",
        "get_subcategory_display",
        "get_team_assignments",
        "get_employment_status",
        "is_active",
        "is_staff",
        "date_joined",
    )
    
    list_display_links = ("username", "email")
    
    list_editable = ("is_active",)

    list_filter = (
        CategoryFilter,
        SubCategoryFilter,
        TeamAssignmentFilter,
        "is_active",
        "is_staff",
        "is_admin",
        "is_superuser",
        "date_joined",
        "last_login",
        ("groups", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "username",
        "first_name", 
        "last_name",
        "email",
        "phone",
        "address",
        "city",
    )
    
    # Pagination settings
    list_per_page = 50  # Show 50 users per page
    list_max_show_all = 500  # Max users to show on "show all" page
    
    # Default ordering
    ordering = ('-date_joined',)  # Newest users first
    
    # Enable date hierarchy for easy browsing by join date
    date_hierarchy = 'date_joined'
    
    # Custom display methods
    def get_category_display(self, obj):
        from accounts.choices import UserCategory
        category_map = {
            UserCategory.APPLICANT: '📝 Applicant',
            UserCategory.STUDENT: '🎓 Student',
            UserCategory.CONSULTANT: '💡 Consultant',
            UserCategory.INVESTOR: '💰 Investor',
            UserCategory.EXPLORER: '🔍 Explorer',
        }
        return category_map.get(obj.category, f'{obj.category} - Unknown')
    get_category_display.short_description = 'Category'
    get_category_display.admin_order_field = 'category'
    
    def get_subcategory_display(self, obj):
        if not obj.sub_category:
            return '—'
        
        from accounts.choices import get_subcategory_display_name
        display = get_subcategory_display_name(obj.category, obj.sub_category)
        
        # Fallback if not found
        if display == "Unknown":
            return f'{obj.sub_category}'
        
        return display
    get_subcategory_display.short_description = 'Sub-Category'
    get_subcategory_display.admin_order_field = 'sub_category'
    
    def get_team_assignments(self, obj):
        """Show all team assignments"""
        groups = obj.groups.all()
        if not groups:
            return '—'
        return ', '.join([g.name for g in groups])
    get_team_assignments.short_description = 'Team Assignments'
    
    # Custom actions for bulk operations
    actions = [
        'activate_users',
        'deactivate_users',
        'mark_as_staff',
        'unmark_as_staff',
        'export_to_csv',
        'add_to_bog_leadership',
        'add_to_support_team',
        'add_to_available_for_hire',
    ]
    
    def activate_users(self, request, queryset):
        """Bulk activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated successfully.')
    activate_users.short_description = "✅ Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated successfully.')
    deactivate_users.short_description = "❌ Deactivate selected users"
    
    def mark_as_staff(self, request, queryset):
        """Mark users as staff"""
        count = queryset.update(is_staff=True)
        self.message_user(request, f'{count} user(s) marked as staff.')
    mark_as_staff.short_description = "👔 Mark as staff"
    
    def unmark_as_staff(self, request, queryset):
        """Remove staff status"""
        count = queryset.update(is_staff=False)
        self.message_user(request, f'{count} user(s) unmarked as staff.')
    unmark_as_staff.short_description = "👕 Remove staff status"
    
    def export_to_csv(self, request, queryset):
        """Export selected users to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Category', 'Sub-Category', 'Teams', 'Active', 'Staff'])
        
        for user in queryset:
            teams = ', '.join([g.name for g in user.groups.all()])
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.category,
                user.sub_category,
                teams,
                user.is_active,
                user.is_staff,
            ])
        
        self.message_user(request, f'{queryset.count()} user(s) exported to CSV.')
        return response
    export_to_csv.short_description = "📊 Export to CSV"
    
    def add_to_bog_leadership(self, request, queryset):
        """Add users to BOG-Leadership team"""
        from django.contrib.auth.models import Group
        from main.services.team_service import TeamService
        from accounts.models import TeamProfile
        
        group = Group.objects.get(name='BOG-Leadership')
        count = 0
        for user in queryset:
            if user.category == 2:  # Only employees
                TeamService.assign_to_category(user, 'BOG-Leadership', priority=50, is_manual=True)
                count += 1
        
        self.message_user(request, f'{count} employee(s) added to BOG-Leadership.')
    add_to_bog_leadership.short_description = "🏢 Add to BOG-Leadership"
    
    def add_to_support_team(self, request, queryset):
        """Add users to Support Team"""
        from main.services.team_service import TeamService
        
        count = 0
        for user in queryset:
            if user.category == 2:  # Only employees
                TeamService.assign_to_category(user, 'Support Team', priority=50, is_manual=True)
                count += 1
        
        self.message_user(request, f'{count} employee(s) added to Support Team.')
    add_to_support_team.short_description = "🤝 Add to Support Team"
    
    def add_to_available_for_hire(self, request, queryset):
        """Mark users as available for hire"""
        from django.contrib.auth.models import Group
        
        group, _ = Group.objects.get_or_create(name='Available for Hire')
        count = 0
        for user in queryset:
            user.groups.add(group)
            count += 1
        
        self.message_user(request, f'{count} user(s) marked as available for hire.')
    add_to_available_for_hire.short_description = "💼 Mark as Available for Hire"

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
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups"),
                "description": "Note: is_staff is auto-synced with Category 2 (Employee/Staff)."
            },
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


# ============================================================================
# UserProfile Admin - Enhanced with filtering, search, and bulk actions
# ============================================================================

class PerformanceTierFilter(admin.SimpleListFilter):
    """Filter by performance tier"""
    title = 'Performance Tier'
    parameter_name = 'performance_tier'
    
    def lookups(self, request, model_admin):
        return (
            ('new', '🆕 New'),
            ('bronze', '🥉 Bronze'),
            ('silver', '🥈 Silver'),
            ('gold', '🥇 Gold'),
            ('platinum', '💎 Platinum'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(performance_tier=self.value())
        return queryset


class EducationLevelFilter(admin.SimpleListFilter):
    """Filter by education level"""
    title = 'Education Level'
    parameter_name = 'education'
    
    def lookups(self, request, model_admin):
        return (
            (1, '🎓 High School'),
            (2, '📚 Some College'),
            (3, '🎓 Bachelor\'s Degree'),
            (4, '🎓 Master\'s Degree'),
            (5, '🎓 Doctorate'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(education=self.value())
        return queryset


class KCCMemberFilter(admin.SimpleListFilter):
    """Filter by KCC membership"""
    title = 'KCC Membership'
    parameter_name = 'kcc_member'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', '✅ KCC Member'),
            ('no', '❌ Not KCC Member'),
            ('expired', '⏰ Expired'),
        )
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        if self.value() == 'yes':
            return queryset.filter(is_karen_country_club_member=True)
        if self.value() == 'no':
            return queryset.filter(is_karen_country_club_member=False)
        if self.value() == 'expired':
            return queryset.filter(
                is_karen_country_club_member=True,
                kcc_membership_expiry__lt=timezone.now().date()
            )
        return queryset


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Enhanced UserProfile admin with advanced filtering and management.
    """
    
    list_display = (
        'user_username',
        'user_fullname',
        'get_user_category',
        'position',
        'education_display',
        'performance_tier_display',
        'kcc_member_display',
        'laptop_status',
        'is_active',
    )
    
    list_display_links = ('user_username', 'user_fullname')
    
    list_editable = ('is_active', 'laptop_status')
    
    list_filter = (
        'is_active',
        EducationLevelFilter,
        PerformanceTierFilter,
        KCCMemberFilter,
        'staff_level',
        'laptop_status',
        ('user__groups', admin.RelatedOnlyFieldListFilter),
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'position',
        'company',
        'description',
        'national_id_no',
        'kcc_membership_number',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'employment_months',
        'img_url',
        'img_category',
    )
    
    fieldsets = (
        ('User Link', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('position', 'company', 'description', 'linkedin')
        }),
        ('Education & Skills', {
            'fields': ('education', 'skills')
        }),
        ('Profile Images', {
            'fields': ('image', 'image2', 'img_url'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('upload_a', 'upload_b', 'upload_c'),
            'classes': ('collapse',)
        }),
        ('Identification', {
            'fields': ('national_id_no', 'id_file', 'account_number', 'country'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_name',
                'emergency_address',
                'emergency_citizenship',
                'emergency_national_id_no',
                'emergency_phone',
                'emergency_email',
            ),
            'classes': ('collapse',)
        }),
        ('KCC Membership', {
            'fields': (
                'is_karen_country_club_member',
                'kcc_membership_number',
                'kcc_membership_date',
                'kcc_membership_expiry',
            )
        }),
        ('Performance & Status', {
            'fields': (
                'performance_tier',
                'staff_level',
                'monthly_income',
                'employment_start_date',
                'employment_months',
                'credit_score',
            )
        }),
        ('User Preferences', {
            'fields': ('preferred_contact_method', 'notification_preferences'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('section', 'laptop_status', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 50
    list_max_show_all = 500
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Custom display methods
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'
    
    def user_fullname(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_fullname.short_description = 'Full Name'
    user_fullname.admin_order_field = 'user__first_name'
    
    def get_user_category(self, obj):
        """Show user's category with icon"""
        from accounts.choices import UserCategory
        category_map = {
            UserCategory.APPLICANT: '📝 Applicant',
            UserCategory.STUDENT: '🎓 Student',
            UserCategory.CONSULTANT: '💡 Consultant',
            UserCategory.INVESTOR: '💰 Investor',
            UserCategory.EXPLORER: '🔍 Explorer',
        }
        return category_map.get(obj.user.category, f'❓ Unknown ({obj.user.category})')
    get_user_category.short_description = 'User Category'
    get_user_category.admin_order_field = 'user__category'
    
    def education_display(self, obj):
        """Show education with emoji"""
        education_map = {
            1: '🎓 High School',
            2: '📚 Some College',
            3: '🎓 Bachelor\'s',
            4: '🎓 Master\'s',
            5: '🎓 Doctorate',
        }
        return education_map.get(obj.education, '—')
    education_display.short_description = 'Education'
    education_display.admin_order_field = 'education'
    
    def performance_tier_display(self, obj):
        """Show performance tier with emoji"""
        tier_map = {
            'new': '🆕 New',
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver',
            'gold': '🥇 Gold',
            'platinum': '💎 Platinum',
        }
        return tier_map.get(obj.performance_tier, '—')
    performance_tier_display.short_description = 'Performance'
    performance_tier_display.admin_order_field = 'performance_tier'
    
    def kcc_member_display(self, obj):
        """Show KCC membership status"""
        if not obj.is_karen_country_club_member:
            return '—'
        
        from django.utils import timezone
        if obj.kcc_membership_expiry:
            if obj.kcc_membership_expiry < timezone.now().date():
                return '⏰ Expired'
            return f'✅ Active (#{obj.kcc_membership_number})'
        return '✅ Member'
    kcc_member_display.short_description = 'KCC Status'
    
    # Bulk actions
    actions = [
        'activate_profiles',
        'deactivate_profiles',
        'mark_laptop_received',
        'mark_laptop_not_received',
        'upgrade_to_bronze',
        'upgrade_to_silver',
        'upgrade_to_gold',
        'export_profiles_to_csv',
    ]
    
    def activate_profiles(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} profile(s) activated.')
    activate_profiles.short_description = "✅ Activate profiles"
    
    def deactivate_profiles(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} profile(s) deactivated.')
    deactivate_profiles.short_description = "❌ Deactivate profiles"
    
    def mark_laptop_received(self, request, queryset):
        count = queryset.update(laptop_status=True)
        self.message_user(request, f'{count} profile(s) marked as having laptop.')
    mark_laptop_received.short_description = "💻 Mark laptop received"
    
    def mark_laptop_not_received(self, request, queryset):
        count = queryset.update(laptop_status=False)
        self.message_user(request, f'{count} profile(s) marked as needing laptop.')
    mark_laptop_not_received.short_description = "❌ Mark no laptop"
    
    def upgrade_to_bronze(self, request, queryset):
        count = queryset.update(performance_tier='bronze')
        self.message_user(request, f'{count} profile(s) upgraded to Bronze.')
    upgrade_to_bronze.short_description = "🥉 Upgrade to Bronze"
    
    def upgrade_to_silver(self, request, queryset):
        count = queryset.update(performance_tier='silver')
        self.message_user(request, f'{count} profile(s) upgraded to Silver.')
    upgrade_to_silver.short_description = "🥈 Upgrade to Silver"
    
    def upgrade_to_gold(self, request, queryset):
        count = queryset.update(performance_tier='gold')
        self.message_user(request, f'{count} profile(s) upgraded to Gold.')
    upgrade_to_gold.short_description = "🥇 Upgrade to Gold"
    
    def export_profiles_to_csv(self, request, queryset):
        """Export profiles to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_profiles_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Full Name', 'Email', 'Position', 'Company',
            'Education', 'Performance Tier', 'KCC Member', 'Laptop',
            'Monthly Income', 'Active'
        ])
        
        for profile in queryset.select_related('user'):
            writer.writerow([
                profile.user.username,
                profile.user.get_full_name(),
                profile.user.email,
                profile.position or '',
                profile.company or '',
                profile.get_education_display(),
                profile.performance_tier,
                'Yes' if profile.is_karen_country_club_member else 'No',
                'Yes' if profile.laptop_status else 'No',
                profile.monthly_income or 0,
                'Yes' if profile.is_active else 'No',
            ])
        
        self.message_user(request, f'{queryset.count()} profile(s) exported.')
        return response
    export_profiles_to_csv.short_description = "📊 Export to CSV"


# Register models
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
