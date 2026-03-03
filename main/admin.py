from django.contrib import admin
from .models import Assets, Readme, Location,Pricing,Plan,ClientAvailability,Search


# Simple registrations (no custom admin needed)
# admin.site.register(Service)
admin.site.register(Assets)
admin.site.register(Readme)
admin.site.register(Pricing)
# admin.site.register(Testimonials)
admin.site.register(Plan)
admin.site.register(ClientAvailability)
# admin.site.register(Search)


# Custom admin for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("zipcode", "city", "state", "country")
    search_fields = ("city", "state", "country")
    list_filter = ("country",)
    ordering = ("country", "city")

 

@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ("topic", "uploaded", "created_at")
    search_fields = ("topic", "question")
    list_filter = ("uploaded",)
