from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import OverBoughtSold


# Register your models here.

from django.contrib import admin
from .models import FinanceRecord

@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'description', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('category', 'description')

admin.site.register(OverBoughtSold)
