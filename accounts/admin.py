from django.contrib import admin

from .models import CustomerUser,Membership,MembershipPlan,MemberRegistration

#
admin.site.register(CustomerUser)
admin.site.register(Membership)
admin.site.register(MembershipPlan)
admin.site.register(MemberRegistration)