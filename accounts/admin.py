from django.contrib import admin

from .models import AccountTeamMember, Account,UserGroups

# Register your models here.
# admin.site.register(CustomerUser)
# admin.site.register(Membership)
admin.site.register(Account)
admin.site.register(AccountTeamMember)
admin.site.register(UserGroups)