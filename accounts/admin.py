from django.contrib import admin

from .models import CustomerUser,Membership

#
admin.site.register(CustomerUser)
admin.site.register(Membership) 
