from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Service)
# admin.site.register(ServiceCategory)
admin.site.register(Assets)
admin.site.register(Volunteer)
admin.site.register(ClientAvailability)
