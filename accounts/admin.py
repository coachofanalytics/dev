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
