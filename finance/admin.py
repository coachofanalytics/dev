from django.contrib import admin

from .models import Food,OverBoughtSold
                   

# Register your models here.
admin.site.register(Food)
admin.site.register(OverBoughtSold)