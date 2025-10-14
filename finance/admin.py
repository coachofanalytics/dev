from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Transaction
from django.db.models import Sum

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'category', 'amount', 'date')
    search_fields = ('category', 'transaction_type')

    # Add the custom dashboard summary to the admin page
    def changelist_view(self, request, extra_context=None):
        # Summarize the total inflow, outflow, and net balance
        inflow_total = Transaction.objects.filter(transaction_type='Inflow').aggregate(Sum('amount'))['amount__sum'] or 0
        outflow_total = Transaction.objects.filter(transaction_type='Outflow').aggregate(Sum('amount'))['amount__sum'] or 0
        net_balance = inflow_total - outflow_total

        # Add the summary data to the extra context
        extra_context = extra_context or {}
        extra_context['inflow_total'] = inflow_total
        extra_context['outflow_total'] = outflow_total
        extra_context['net_balance'] = net_balance

        # Return the base changelist view with the new context
        return super().changelist_view(request, extra_context=extra_context)

    # Display these summary values in the header of the changelist
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

