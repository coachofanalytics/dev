from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomerUser, Department, Credential, TaskGroup, TeamMember, CredentialCategory,Sprintplanning,CapacityBuilding





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


class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time')
    list_filter = ('user', 'login_time', 'logout_time')
    search_fields = ('user__username',)



# Now register the new UserAdmin...
admin.site.register(CustomerUser, CustomerAdmin)
# admin.site.register(CustomerUser)

# Register your models here.
# admin.site.register(LoginHistory)
admin.site.register(Department
                    )
admin.site.register(Credential)
admin.site.register(TaskGroup)
admin.site.register(TeamMember)
admin.site.register(CredentialCategory)
admin.site.register(Sprintplanning)
admin.site.register(CapacityBuilding)
