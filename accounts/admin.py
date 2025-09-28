from django.contrib import admin

from .models import CustomerUser, MemberRegistration,Membership, MembershipPlan

#
admin.site.register(CustomerUser)
admin.site.register(Membership)
admin.site.register(MembershipPlan)
admin.site.register(MemberRegistration)
