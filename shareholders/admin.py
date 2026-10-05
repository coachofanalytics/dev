from django.contrib import admin
from .models import Shareholder, Contribution

@admin.register(Shareholder)
class ShareholderAdmin(admin.ModelAdmin):
    # Removed 'total_shares' and 'voting_power' because they aren't in the model yet
    list_display = ('user',) 

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('shareholder', 'contribution_type', 'amount', 'is_approved')
    list_filter = ('is_approved',)