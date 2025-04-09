from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .models import CustomerUser, Membership


#
class CustomerAdmin(UserAdmin):
    list_display = ("id", "email", "first_name", "last_name")

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "id",
                    "email",
                    "first_name",
                    "last_name",
                    "date_joined",
                    "category",
                    "is_admin",
                    "is_member",
                    "email_verified",
                    "verification_token",
                )
            },
        ),
    )
    search_fields = ("last_name", "email")
    list_filter = ("is_member", "last_name", "email")

    # filter_horizontal = ()


admin.site.register(CustomerUser, CustomerAdmin)
admin.site.register(Membership)
