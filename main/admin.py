from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Assets)
admin.site.register(Feedback)
admin.site.register(Description)
admin.site.register(Page)
admin.site.register(Team)
admin.site.register(Content)
admin.site.register(Service)
admin.site.register(SubService)
admin.site.register(News)
admin.site.register(Gallery_image)
admin.site.register(ContactUs)
#<<<<<<< 25.10_DC48_UAT_UO
admin.site.register(SafetyAlertSubscription)
admin.site.register(EmergencyHotlines)
admin.site.register(StaffContact)
admin.site.register(EmergencyHelpActivations)

#=======
admin.site.register(Donation_organisation)
admin.site.register(ContactMessage)
admin.site.register(Donation_organization)
admin.site.register(Scholarship)
#>>>>>>> 25.10_DC48_UAT_ND

