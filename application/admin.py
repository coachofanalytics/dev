from django.contrib import admin

from .models import (Applicant_Profile, Application, Employee, FirstUpload,
                     Policy, Rated, Reporting)

# Register your models here.
admin.site.register(Applicant_Profile)
admin.site.register(Application)
admin.site.register(Rated)
admin.site.register(Employee)
admin.site.register(FirstUpload)
admin.site.register(Policy)
admin.site.register(Reporting)
