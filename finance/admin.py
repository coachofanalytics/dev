from django.contrib import admin

from .models import Food,OverBoughtSold,PaymentInformation,Default_Payment_Fees,PayslipConfig
                   

# Register your models here.
admin.site.register(Food)
admin.site.register(OverBoughtSold)
admin.site.register(PaymentInformation)
admin.site.register(Default_Payment_Fees)
admin.site.register(PayslipConfig)