from django.contrib import admin
from .models import *

class DescriptionAdmin(admin.ModelAdmin):
    list_display = ("page", "name", "content")

    search_fields = ("page", "name")
    list_filter = ("name",)
    ordering = ("name",)
    filter_horizontal = ()

# Register your models here.
# admin.site.register(Assets)
#admin.site.register(Feedback)
admin.site.register(Description, DescriptionAdmin)
# admin.site.register(Page)
#admin.site.register(Team)
#admin.site.register(Content)
#admin.site.register(Service)
#admin.site.register(SubService)
#admin.site.register(News)
#admin.site.register(Gallery)
#admin.site.register(ContactUs)
#admin.site.register(Faq)
admin.site.register(Volunteer)
admin.site.register(Donation)

