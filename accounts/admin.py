from django.contrib import admin

from .models import CustomerUser,Membership,Faq


admin.site.register(CustomerUser)
admin.site.register(Membership)
admin.site.register(Faq)
