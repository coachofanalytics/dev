from django.contrib import admin

from .models import UserProfile,Reporting,JobDetails
                   

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Reporting)
admin.site.register(JobDetails)



from django.contrib import admin
from .models import JobOpening

@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "location",
        "department",
        "employment_type",
        "posted_on",
        "is_active",
    )

    list_filter = (
        "employment_type",
        "department",
        "is_active",
    )

    search_fields = (
        "title",
        "location",
        "department",
    )



from django.contrib import admin
from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "job",
        "email",
        "status",
        "applied_on",
    )

    list_filter = (
        "status",
        "job",
    )

    search_fields = (
        "full_name",
        "email",
        "job__title",
    )

    readonly_fields = ("applied_on",)

