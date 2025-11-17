from django.contrib import admin

from .models import AccountTeamMember, CustomerUser, Account

# Register your models here.
admin.site.register(CustomerUser)
# admin.site.register(Membership)
admin.site.register(Account)
admin.site.register(AccountTeamMember)