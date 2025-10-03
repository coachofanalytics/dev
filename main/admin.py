from django.contrib import admin
from django.contrib import admin
from django.contrib import admin
from .models import ServiceCategory
from django.contrib import admin
from .models import WCAGStandardWebsite

# from .models import 
from .models import *

# Register your models here.
admin.site.register(Service)
# admin.site.register(ServiceCategory)
admin.site.register(Assets)
admin.site.register(Volunteer)
# admin.site.register(service_coda)
admin.site.register(Testimonials)
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    ...
    # your_app/admin.py


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name', 'slug'),
    prepopulated_fields = {'slug': ('name',)}  # Optional: auto-generate slug from name



admin.site.register(WCAGStandardWebsite)
