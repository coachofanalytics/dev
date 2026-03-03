from django.contrib import admin

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