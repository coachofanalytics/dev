from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Ticker_Data)
admin.site.register(Portfolio)
admin.site.register(OverBoughtSold)
admin.site.register(credit_spread)
admin.site.register(ShortPut)
admin.site.register(covered_calls)
admin.site.register(Investments)
admin.site.register(Investment_rates)
admin.site.register(Investor_Information)
admin.site.register(InvestmentContent)
admin.site.register(InvestmentsStrategy)
admin.site.register(Cost_Basis)
admin.site.register(Daily_Trades)
admin.site.register(Returns_Balances)
admin.site.register(SavedResponses)
admin.site.register(Options_Returns)

# Investor Relations Models
admin.site.register(InvestmentPerformance)
admin.site.register(InvestmentReport)
admin.site.register(InvestmentMilestone)
admin.site.register(InvestmentUpgradeOffer)

# class InvestmentContentAdmin(admin.ModelAdmin):
#     list_display = ('title', 'slug', 'description')


# ============================================================================
# MANAGED OPTIONS TRADING ADMIN
# ============================================================================

@admin.register(ManagedTradingAccount)
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_number',
        'client',
        'account_manager',
        'current_balance',
        'total_profit_loss',
        'win_rate_display',
        'roi_display',
        'status',
        'fee_tier',
        'created_at'
    ]
    list_filter = ['status', 'fee_tier', 'trading_enabled', 'account_manager', 'created_at']
    search_fields = ['account_number', 'client__username', 'client__email', 'client__first_name', 'client__last_name']
    readonly_fields = ['account_number', 'created_at', 'updated_at', 'win_rate_display', 'roi_display', 'available_buying_power_display', 'risk_exposure_display']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'client', 'account_name', 'account_manager', 'status')
        }),
        ('Financial Details', {
            'fields': (
                'initial_capital', 'current_balance', 
                'cash_available', 'cash_reserved', 'high_water_mark',
                'available_buying_power_display'
            )
        }),
        ('Fee Structure', {
            'fields': (
                'fee_tier',
                'management_fee_percentage', 
                'performance_fee_percentage', 
                'performance_threshold'
            )
        }),
        ('Consultative Tier Settings', {
            'fields': (
                'session_fee', 'sessions_per_month', 'monthly_platform_fee',
                'sessions_completed_this_month', 'total_sessions_completed',
                'next_session_date'
            ),
            'classes': ('collapse',)
        }),
        ('Risk Parameters', {
            'fields': (
                'max_position_risk', 'max_total_risk', 
                'max_daily_loss', 'max_weekly_loss', 'max_monthly_loss',
                'max_positions', 'risk_exposure_display'
            )
        }),
        ('Trading Settings', {
            'fields': ('trading_enabled', 'auto_trading_enabled', 'activation_date', 'closure_date')
        }),
        ('Performance Tracking', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades',
                'win_rate_display', 'roi_display',
                'total_profit_loss', 'total_fees_paid',
                'last_fee_calculation_date'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def win_rate_display(self, obj):
        return f"{obj.win_rate:.2f}%"
    win_rate_display.short_description = 'Win Rate'
    
    def roi_display(self, obj):
        return f"{obj.return_on_investment:.2f}%"
    roi_display.short_description = 'ROI'
    
    def available_buying_power_display(self, obj):
        return f"${obj.available_buying_power:,.2f}"
    available_buying_power_display.short_description = 'Available Buying Power'
    
    def risk_exposure_display(self, obj):
        return f"{obj.current_risk_exposure:.2f}%"
    risk_exposure_display.short_description = 'Risk Exposure'


@admin.register(OptionsPosition)
class OptionsPositionAdmin(admin.ModelAdmin):
    list_display = [
        'symbol',
        'strategy',
        'managed_account',
        'entry_date',
        'expiration_date',
        'days_to_expiration_display',
        'premium_collected',
        'unrealized_pnl',
        'realized_pnl',
        'profit_percentage_display',
        'status'
    ]
    list_filter = ['strategy', 'status', 'entry_date', 'expiration_date', 'managed_account']
    search_fields = ['symbol', 'managed_account__account_number', 'notes']
    readonly_fields = [
        'entry_date', 'created_at', 'updated_at',
        'days_in_trade_display', 'days_to_expiration_display',
        'profit_percentage_display', 'is_profitable_display'
    ]
    
    fieldsets = (
        ('Position Details', {
            'fields': ('managed_account', 'symbol', 'strategy', 'positions', 'status')
        }),
        ('Financial Details', {
            'fields': (
                'capital_required', 'premium_collected',
                'max_profit', 'max_loss',
                'current_value', 'unrealized_pnl', 'realized_pnl',
                'profit_percentage_display', 'is_profitable_display'
            )
        }),
        ('Greeks', {
            'fields': ('position_delta', 'position_theta', 'position_gamma', 'position_vega'),
            'classes': ('collapse',)
        }),
        ('Dates & Duration', {
            'fields': (
                'entry_date', 'expiration_date', 'exit_date',
                'days_in_trade_display', 'days_to_expiration_display'
            )
        }),
        ('Exit Details', {
            'fields': ('exit_reason', 'exit_price'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_in_trade_display(self, obj):
        return f"{obj.days_in_trade} days"
    days_in_trade_display.short_description = 'Days in Trade'
    
    def days_to_expiration_display(self, obj):
        dte = obj.days_to_expiration
        if dte < 0:
            return f"Expired {abs(dte)} days ago"
        return f"{dte} days"
    days_to_expiration_display.short_description = 'DTE'
    
    def profit_percentage_display(self, obj):
        return f"{obj.profit_percentage:.2f}%"
    profit_percentage_display.short_description = 'Profit %'
    
    def is_profitable_display(self, obj):
        return "✓" if obj.is_profitable else "✗"
    is_profitable_display.short_description = 'Profitable'
    is_profitable_display.boolean = True


@admin.register(TradingRule)
class TradingRuleAdmin(admin.ModelAdmin):
    list_display = [
        'rule_name',
        'rule_type',
        'managed_account',
        'is_active',
        'priority',
        'created_at'
    ]
    list_filter = ['rule_type', 'is_active', 'priority', 'managed_account']
    search_fields = ['rule_name', 'managed_account__account_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('managed_account', 'rule_name', 'rule_type', 'is_active', 'priority')
        }),
        ('Rule Configuration', {
            'fields': ('rule_config',),
            'description': 'JSON configuration for rule parameters and thresholds'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TradingActivity)
class TradingActivityAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'activity_type',
        'managed_account',
        'position',
        'performed_by',
        'description_short'
    ]
    list_filter = ['activity_type', 'timestamp', 'managed_account', 'performed_by']
    search_fields = ['description', 'managed_account__account_number']
    readonly_fields = ['timestamp', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('managed_account', 'position', 'activity_type', 'description')
        }),
        ('Data & Context', {
            'fields': ('data_snapshot', 'performed_by', 'timestamp'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:75] + '...' if len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        # Activities should be created programmatically, not manually
        return False


@admin.register(TradingSession)
class TradingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_date',
        'managed_account',
        'session_type',
        'session_duration_minutes',
        'fee_charged',
        'is_billed',
        'created_at'
    ]
    list_filter = ['session_type', 'is_billed', 'session_date', 'managed_account']
    search_fields = ['managed_account__account_number', 'topics_discussed', 'session_notes']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['positions_reviewed']
    
    fieldsets = (
        ('Session Information', {
            'fields': (
                'managed_account', 'session_date', 'session_duration_minutes',
                'session_type'
            )
        }),
        ('Session Content', {
            'fields': ('topics_discussed', 'positions_reviewed', 'action_items')
        }),
        ('Session Notes', {
            'fields': ('session_notes', 'client_feedback'),
            'classes': ('collapse',)
        }),
        ('Billing', {
            'fields': ('fee_charged', 'is_billed', 'billing_date')
        }),
        ('Recording', {
            'fields': ('recording_url',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )