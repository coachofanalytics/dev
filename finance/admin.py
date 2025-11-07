from django.contrib import admin

from .models import Food,OverBoughtSold,payment_infomation
                   

# Register your models here.
admin.site.register(Food)
admin.site.register(OverBoughtSold)
admin.site.register(payment_infomation)