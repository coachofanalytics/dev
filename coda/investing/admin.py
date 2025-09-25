from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Ticker_Data)
admin.site.register(Portfolio)
admin.site.register(OverBoughtSold)
admin.site.register(credit_spread)
admin.site.register(ShortPut)
admin.site.register(covered_calls)
admin.site.register(Investments)
admin.site.register(Investment_rates)
admin.site.register(Investor_Information)
admin.site.register(InvestmentContent)
admin.site.register(InvestmentsStrategy)
admin.site.register(Cost_Basis)
admin.site.register(Daily_Trades)
admin.site.register(Returns_Balances)
admin.site.register(SavedResponses)
admin.site.register(Options_Returns)

# Investor Relations Models
admin.site.register(InvestmentPerformance)
admin.site.register(InvestmentReport)
admin.site.register(InvestmentMilestone)
admin.site.register(InvestmentUpgradeOffer)

# class InvestmentContentAdmin(admin.ModelAdmin):
#     list_display = ('title', 'slug', 'description')
