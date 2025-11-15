from django.contrib import admin
from django.utils.html import format_html
from .models import Wallet, SubscriptionPlan, UserSubscription, Invoice, Transaction, PaymentGatewayConfig


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'is_active', 'created_at']
    list_filter = ['is_active', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['balance', 'created_at', 'updated_at']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'category', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'payment_method', 'auto_renew']
    search_fields = ['user__username', 'plan__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'user', 'amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status', 'created_at']
    search_fields = ['invoice_number', 'user__username']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'payment_gateway', 'status', 'created_at']
    list_filter = ['transaction_type', 'payment_gateway', 'status']
    search_fields = ['transaction_id', 'user__username', 'gateway_transaction_id']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ['gateway_name', 'is_active', 'is_test_mode', 'updated_at']
    list_filter = ['is_active', 'is_test_mode', 'gateway_name']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)
