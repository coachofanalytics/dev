from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Service)
admin.site.register(Location)
admin.site.register(Assets)
admin.site.register(Readme)
admin.site.register(ServiceCategory)
admin.site.register(Testimonials)
admin.site.register(Volunteer)