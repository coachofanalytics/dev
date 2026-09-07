from django.contrib import admin

from .models import (
    # Assets,
    Readme,
    Location,
    Pricing,
    Plan,
    ClientAvailability,
    Search,
    Company,
    # ServiceAdmin,
    Testimonials,
    ServiceCategory,
    Volunteer,
    MembershipRegistration,
    Event,
)


# ========================= SERVICE CATEGORY =========================
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# ========================= COMPANY =========================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# # ========================= SERVICE ADMIN MODEL =========================
# @admin.register(ServiceAdmin)
# class ServiceAdminAdmin(admin.ModelAdmin):
#     list_display = ("id",)
#     search_fields = ()

from django.contrib import admin
from .models import Assets

# @admin.register(Assets)
# class AssetsAdmin(admin.ModelAdmin):
#     list_display = ("name", "category", "created_at", "updated_at")
#     search_fields = ("name", "category", "description")
#     list_filter = ("category", "created_at")# ========================= ASSETS =========================
# @admin.register(Assets)
# class AssetsAdmin(admin.ModelAdmin):
#     list_display = ("id", "name")
#     search_fields = ("name",)


# ========================= README =========================
@admin.register(Readme)
class ReadmeAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title",)


# ========================= LOCATION =========================
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id",)
    search_fields = ()


# ========================= PRICING =========================
@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = ("id",)


# ========================= PLAN =========================
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("id",)


# ========================= CLIENT AVAILABILITY =========================
@admin.register(ClientAvailability)
class ClientAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("id",)


# ========================= SEARCH =========================
@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ("id",)


# ========================= TESTIMONIALS =========================
@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ("id",)


# ========================= VOLUNTEER =========================
@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")


# ========================= MEMBERSHIP REGISTRATION =========================
@admin.register(MembershipRegistration)
class MembershipRegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email")
    search_fields = ("first_name", "last_name", "email")


# # ========================= CATEGORY =========================
# @admin.register(category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id",)


from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # These settings make the admin panel look much cleaner
    list_display = ('title', 'event_date', 'location', 'created_at')
    list_filter = ('event_date',)
    search_fields = ('title', 'description', 'location')