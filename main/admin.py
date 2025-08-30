from django.contrib import admin
from django.contrib import admin
from .models import ClientAvailability
from .models import *

# Register your models here.
admin.site.register(Service)
# admin.site.register(ServiceCategory)
admin.site.register(Assets)
admin.site.register(Volunteer)
admin.site.register(service_coda)
admin.site.register(Testimonials)
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    ...
from django.contrib import admin
from .models import ClientAvailability

@admin.register(ClientAvailability)
class ClientAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'day', 'start_time', 'end_time', 'time_standards', 'topic')
    list_filter = ('day', 'time_standards')
    search_fields = ('client', 'topic', 'day')
