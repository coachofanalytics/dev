from django.contrib import admin
from .models import CustomerUser, Payment_History,LoginHistory,Tracker

admin.site.register(CustomerUser)
admin.site.register(Payment_History)
admin.site.register(LoginHistory)
admin.site.register(Tracker)


