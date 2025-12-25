from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import OverBoughtSold, PaymentInformation, FinanceRecord

class StatusFilter(SimpleListFilter):
    title = 'status'  # The title of the filter in the admin panel
    parameter_name = 'status'  # The query parameter used in the URL

    def lookups(self, request, model_admin):
        return (
            ('Overbought', 'Overbought'),
            ('Oversold', 'Oversold'),
            ('Neutral', 'Neutral'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Overbought':
            return queryset.filter(RSI__gt=70)
        if self.value() == 'Oversold':
            return queryset.filter(RSI__lt=30)
        if self.value() == 'Neutral':
            return queryset.filter(RSI__gte=30, RSI__lte=70)
        return queryset

# Register the OverBoughtSold model and add the custom filter
@admin.register(OverBoughtSold)
class OverBoughtSoldAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'last', 'volume', 'RSI', 'rank', 'status', 'created_at')
    list_filter = (StatusFilter,)  # Use the custom filter
    search_fields = ('symbol', 'rank')

@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ("category", "amount", "description", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("category", "description")

@admin.register(PaymentInformation)
class PaymentInformationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'total_fees', 'remaining_balance', 'payment_method', 'created_at')
    search_fields = ('customer__username', 'customer__email')  # Search by customer username or email
    list_filter = ('payment_method', 'is_active', 'is_tested')  # Filter options
