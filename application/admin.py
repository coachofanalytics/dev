from django.contrib import admin

from .models import UserProfile,Reporting,JobDetails
                   

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Reporting)
admin.site.register(JobDetails)



