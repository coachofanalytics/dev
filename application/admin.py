from django.contrib import admin

from .models import UserProfile,Reporting
                   

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Reporting)


