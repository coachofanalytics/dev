from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomerUser


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
# admin.site.register(CustomerUser)
# @admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description", "is_featured", "is_active")
    search_fields = ("name", "slug", "description")
from django.contrib import admin
from .models import Credential, CredentialCategory

@admin.register(CredentialCategory)
class CredentialCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'name', 
        'department', 
        'added_by', 
        'is_active', 
        'is_featured', 
        'entry_date'
    )
    search_fields = ('name', 'department', 'description', 'link_name')
    list_filter = ('is_active', 'is_featured', 'department', 'entry_date')
    ordering = ('-entry_date',)
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug from name
    filter_horizontal = ('category',)  # Nice ManyToMany widget in admin
    readonly_fields = ('entry_date',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'department', 'description', 'category')
        }),
        ('Links & Access', {
            'fields': ('link_name', 'link', 'password')
        }),
        ('Status & Meta', {
            'fields': ('user_types', 'added_by', 'is_active', 'is_featured', 'entry_date')
        }),
    )

