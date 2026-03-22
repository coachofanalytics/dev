from django.contrib import admin
from .models import Assets, Readme, Location,Pricing,Plan,ClientAvailability,Search,Company,PricingSubPlan

<<<<<<< HEAD
from .models import (
    Company,
    Service,
    ServiceCategory,
    Assets,
    Readme,
    Volunteer,
    Location,
    MembershipRegistration,
)


# ========================= LOCATION =========================
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "state", "country", "zipcode")
    search_fields = ("city", "state", "country")
    list_filter = ("country",)
    ordering = ("city",)


# ========================= SERVICE CATEGORY =========================
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "service", "is_active", "is_featured")
    list_filter = ("is_active", "is_featured")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-id",)


# ========================= COMPANY =========================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# ========================= SERVICE =========================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "company", "is_active", "is_featured")
    list_filter = ("is_active", "company", "is_featured")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("title",)


# ========================= ASSETS =========================
@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "is_active")
    search_fields = ("name", "category")
    list_filter = ("category", "is_active")


# ========================= README =========================
@admin.register(Readme)
class ReadmeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


# ========================= VOLUNTEER =========================
@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at")
    search_fields = ("name", "email")


# ========================= MEMBERSHIP =========================
@admin.register(MembershipRegistration)
class MembershipRegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "is_active")
    search_fields = ("first_name", "last_name", "email")
    list_filter = ("is_active",)
=======

# Simple registrations (no custom admin needed)
# admin.site.register(Service)
admin.site.register(Assets)
admin.site.register(Readme)
admin.site.register(Pricing)
# admin.site.register(Testimonials)
admin.site.register(Plan)
admin.site.register(ClientAvailability)
# admin.site.register(Search)
admin.site.register(Company)
admin.site.register(PricingSubPlan)


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
>>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
