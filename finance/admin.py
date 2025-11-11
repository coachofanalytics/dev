from django.contrib import admin

# Register your models here.
from .models import OverBoughtSold


# Register your models here.

from .models import FinanceRecord


@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ("category", "amount", "description", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("category", "description")


admin.site.register(OverBoughtSold)
