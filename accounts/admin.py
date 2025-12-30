from django.contrib import admin
from .models import CustomerUser, Payment_History,LoginHistory

admin.site.register(CustomerUser)
admin.site.register(Payment_History)
admin.site.register(LoginHistory)
