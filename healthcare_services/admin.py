from django.contrib import admin
from .models import DoctorSpecialty


@admin.register(DoctorSpecialty)
class DoctorSpecialtyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_default")
    search_fields = ("name",)
    list_filter = ("is_default",)