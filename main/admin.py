from django.contrib import admin
from .models import Assets, Readme, Location,Pricing,Testimonials,Plan


# Simple registrations (no custom admin needed)
# admin.site.register(Service)
admin.site.register(Assets)
admin.site.register(Readme)
admin.site.register(Pricing)
admin.site.register(Testimonials)
admin.site.register(Plan)


# Custom admin for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("zipcode", "city", "state", "country")
    search_fields = ("city", "state", "country")
    list_filter = ("country",)
    ordering = ("country", "city")
