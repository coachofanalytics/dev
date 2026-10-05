from django.contrib import admin
from .models import (
    Company,
    ServiceCategory,
    Assets,
    Readme,
    Location,
    MembershipRegistration,
    Pricing,
    Plan,
    ClientAvailability,
    Search
)

# ========================= LOCATION =========================
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("zipcode", "city", "state", "country")
    search_fields = ("city", "state", "country")
    list_filter = ("country",)
    ordering = ("country", "city")

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
from django.contrib import admin
from .models import Assets

@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    # Using only valid fields from your model
    list_display = ('name', 'category', 'description')
    
    # Optional: If you want to filter by category
    list_filter = ('category',)
# ========================= README =========================
@admin.register(Readme)
class ReadmeAdmin(admin.ModelAdmin):
    pass

# ========================= MEMBERSHIP =========================
@admin.register(MembershipRegistration)
class MembershipRegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "is_active")
    search_fields = ("first_name", "last_name", "email")
    list_filter = ("is_active",)

# ========================= SEARCH =========================
@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ("topic", "uploaded", "created_at")
    search_fields = ("topic", "question")
    list_filter = ("uploaded",)

# ========================= SIMPLE REGISTRATIONS =========================
# Register models here that don't need a custom Admin class
admin.site.register(Pricing)
admin.site.register(Plan)
admin.site.register(ClientAvailability)