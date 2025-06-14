from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomerUser
from django.apps import AppConfig
from django.contrib import admin
from .models import Assets

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'  # or use full path like 'dev.accounts' if it's inside 'dev'


# admin.site.register(CustomerUser)
class CustomerAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    list_display = ("email", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "gender",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "is_admin",
                    # "is_staff",
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
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "gender",
                    "category",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "is_admin",
                    "resume_file",
                )
            },
        ),
    )
    search_fields = ("email",)
    filter_horizontal = ()


# Now register the new UserAdmin...
admin.site.register(CustomerUser, CustomerAdmin)
admin.site.register(Assets,)
# admin.site.register(Tracker)
# admin.site.register(CAHistory)
# Register your models here.
from django.contrib import admin
from .models import Credential

@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ("name", "added_by", "user_type", "slug")
    search_fields = ("name", "description", "link_name")
    prepopulated_fields = {"slug": ("name",)}  # Optional: auto-fill slug from name
