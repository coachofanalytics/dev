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
    list_display = ['gateway_name', 'is_active', 'is_test_mode', 'masked_config_preview', 'updated_at']
    list_filter = ['is_active', 'is_test_mode', 'gateway_name']
    readonly_fields = ['created_at', 'updated_at', 'config_preview_masked']

    def has_change_permission(self, request, obj=None):
        """Restrict config changes to superusers only for security"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Restrict config deletion to superusers only for security"""
        return request.user.is_superuser

    def masked_config_preview(self, obj):
        """
        Show only config keys in list view, not values.
        This prevents accidental exposure of API keys in the admin list.
        """
        from django.utils.html import format_html
        config = obj.config_data
        if not config:
            return "-"

        # Show only keys, not values
        keys = ', '.join(config.keys()) if config else 'No keys'
        num_keys = len(config)
        return format_html(
            '<span title="Contains {} configuration keys">{} key(s): {}</span>',
            num_keys, num_keys, keys[:50] + ('...' if len(keys) > 50 else '')
        )
    masked_config_preview.short_description = 'Config Keys'

    def config_preview_masked(self, obj):
        """
        Show masked values in detail view for verification.
        Only shows last 4 characters of each value.
        """
        from django.utils.html import format_html
        import json

        config = obj.config_data
        if not config:
            return "No configuration data"

        # Mask all but last 4 characters of each value
        masked = {}
        for key, value in config.items():
            if isinstance(value, str) and len(value) > 4:
                masked[key] = f"{'*' * (len(value) - 4)}{value[-4:]}"
            else:
                masked[key] = "****"

        return format_html('<pre>{}</pre>', json.dumps(masked, indent=2))
    config_preview_masked.short_description = 'Configuration Preview (Masked)'

    def save_model(self, request, obj, form, change):
        """Save model and log the change for audit purposes"""
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)

        # Log sensitive config change for security audit
        from payments.models import WalletActivityLog
        from django.utils import timezone

        WalletActivityLog.objects.create(
            user=request.user,
            action_type='settings_change',
            description=f'Updated payment gateway config: {obj.gateway_name}',
            ip_address=self._get_client_ip(request),
            metadata={
                'gateway': obj.gateway_name,
                'is_test_mode': obj.is_test_mode,
                'is_active': obj.is_active,
                'changed_at': timezone.now().isoformat()
            }
        )

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
