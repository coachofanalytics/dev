from django.contrib import admin
# dt_string = "12/11/2018 09:15:32"
# Register your models here.
from .models import *

class Payment_HistoryAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "payment_fees",
        "down_payment",
        "student_bonus",
        "fee_balance",
        "plan",
        "contract_submitted_date",
    )

admin.site.register(Transaction)
admin.site.register(Payment_History, Payment_HistoryAdmin)

admin.site.register(Payment_Information)
admin.site.register(Default_Payment_Fees)
admin.site.register(CodaBudget)
admin.site.register(Budget)
admin.site.register(BudgetCategory)
admin.site.register(BudgetSubCategory)
