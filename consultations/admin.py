from django.contrib import admin
from .models import consultations
from .models import*

# Register your models here.
admin.site.register(consultations)
from django.contrib import admin
from .models import Signup
@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("firstname", "lastname", "email", "phone")
    search_fields = ("firstname", "lastname", "email", "phone")
from django.contrib import admin
from .models import VisaApplication


@admin.register(VisaApplication)
class VisaApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "email",
        "visa_type",
        "destination_country",
        "created_at"
    )

    list_filter = ("visa_type", "destination_country")

    search_fields = ("first_name", "last_name", "email", "passport_number")


