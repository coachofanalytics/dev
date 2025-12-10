from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomerUser, LoginHistory,Tracker


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomerUser
        fields = ("username", "email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomerUser
        fields = "__all__"


class CustomerAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomerUser

    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_client", "is_applicant")

    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Information",
            {
                "fields": (
                    "gender",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "zipcode",
                    "country",
                    "category",
                    "sub_category",
                    "is_admin",
                    "is_client",
                    "is_applicant",
                    "is_employee_contract_signed",
                    "resume_file",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional Information",
            {
                "fields": (
                    "username",      # REQUIRED for login
                    "email",
                    "first_name",
                    "last_name",
                    "gender",
                    "category",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "zipcode",
                    "country",
                    "is_admin",
                    "resume_file",
                )
            },
        ),
    )

    search_fields = ("username", "email")
    ordering = ("username",)


class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time")
    list_filter = ("user", "login_time", "logout_time")
    search_fields = ("user__username",)


admin.site.register(CustomerUser, CustomerAdmin)
admin.site.register(LoginHistory, LoginHistoryAdmin)
admin.site.register(Tracker)
