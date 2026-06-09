from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .models import CustomerUser, Membership, Region, Chapter, Profile


#
class CustomerAdmin(UserAdmin):

    model = CustomerUser

    list_display = ("email", "first_name", "last_name", "date_joined")

  
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "country",
                    "state",
                    "city",
                    "date_joined",
                    "category",
                    "is_active",
                    "is_admin",
                    "is_member",
                    "email_verified",
                    # "verification_token",
                )
            },
        ),
    )

    search_fields = ("last_name", "email")
    list_filter = ("is_member", "last_name", "email")

    # filter_horizontal = ()

class RegionAdmin(UserAdmin):
    list_display = ("id", "name")

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "id",
                    "name",
                )
            },
        ),
    )
    search_fields = ("name",)
    list_filter = ()
    ordering = ["id"]
    filter_horizontal = ()


class ChapterAdmin(UserAdmin):
    list_display = ("id", "region", "name")

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "id",
                    "name",
                    "region"
                )
            },
        ),
    )
    search_fields = ("name","region")
    list_filter = ("region",)
    ordering = ["id"]
    filter_horizontal = ()


admin.site.register(CustomerUser, CustomerAdmin)
admin.site.register(Membership)
admin.site.register(Region)
admin.site.register(Chapter)
admin.site.register(Profile)
