from django.contrib import admin
from .models import FinancialServiceRequest, Transaction, Budget

admin.site.register(FinancialServiceRequest)
admin.site.register(Transaction)
admin.site.register(Budget)
