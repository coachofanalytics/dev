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

@admin.register(FeeTierConfiguration)
class FeeTierConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'tier_name',
        'tier_code',
        'minimum_capital',
        'monthly_fee',
        'per_session_fee',
        'profit_share_percentage',
        'display_order',
        'is_active'
    ]
    list_filter = ['is_active', 'tier_code']
    list_editable = ['display_order', 'is_active']
    search_fields = ['tier_name', 'tier_code']
    ordering = ['display_order', 'minimum_capital']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tier_code', 'tier_name', 'display_order', 'is_active')
        }),
        ('Capital Requirements', {
            'fields': ('minimum_capital',)
        }),
        ('Fee Structure', {
            'fields': ('monthly_fee', 'per_session_fee', 'profit_share_percentage', 'max_sessions_per_month')
        }),
        ('Features & Description', {
            'fields': ('short_description', 'features', 'compatible_risk_levels'),
            'description': 'Enter features as JSON list (e.g., ["AI-powered analysis", "Automated execution"])'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make tier_code readonly after creation to prevent breaking references
        if obj:  # Editing existing object
            return ['tier_code']
        return []

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
        ('Notification Preferences (WhatsApp/Telegram)', {
            'fields': (
                'whatsapp_enabled', 'whatsapp_phone',
                'telegram_enabled', 'telegram_chat_id'
            ),
            'description': 'Enable real-time alerts for position updates via WhatsApp and Telegram'
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


# ============================================================================
# PHASE 6: CLIENT ONBOARDING & COMPLIANCE ADMIN
# ============================================================================

@admin.register(InvestorRiskProfile)
class InvestorRiskProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'risk_category',
        'risk_score',
        'assessed_date',
        'expires_date',
        'is_current',
        'is_expired_display'
    ]
    list_filter = ['risk_category', 'is_current', 'assessed_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['assessed_date', 'last_updated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('user',)
        }),
        ('Risk Assessment', {
            'fields': ('risk_score', 'risk_category', 'questionnaire_data')
        }),
        ('Recommended Tiers', {
            'fields': ('recommended_tiers_display',),
            'classes': ('collapse',)
        }),
        ('Validity', {
            'fields': ('is_current', 'expires_date', 'assessed_date', 'last_updated')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.short_description = 'Expired?'
    is_expired_display.boolean = True
    
    def recommended_tiers_display(self, obj):
        return ', '.join(obj.recommended_tiers)
    recommended_tiers_display.short_description = 'Recommended Tiers'


@admin.register(ManagedTradingApplication)
class ManagedTradingApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applied_date',
        'user',
        'initial_capital',
        'fee_tier',
        'status',
        'risk_tier_match_display',
        'capital_tier_match_display',
        'contracts_signed_display',
        'reviewed_by'
    ]
    list_filter = ['status', 'fee_tier', 'applied_date', 'all_contracts_signed']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'applied_date', 'created_at', 'updated_at',
        'risk_tier_match_display', 'capital_tier_match_display',
        'is_qualified_display'
    ]
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('user', 'risk_profile')
        }),
        ('Investment Details', {
            'fields': ('initial_capital', 'fee_tier', 'preferred_manager', 'funding_method')
        }),
        ('Qualification Status', {
            'fields': (
                'risk_tier_match_display',
                'capital_tier_match_display',
                'is_qualified_display'
            ),
            'classes': ('collapse',)
        }),
        ('Application Status', {
            'fields': ('status', 'applied_date')
        }),
        ('Contract Status', {
            'fields': ('contracts_generated', 'all_contracts_signed')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_date', 'approval_notes', 'rejection_reason')
        }),
        ('Created Account', {
            'fields': ('managed_account',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def risk_tier_match_display(self, obj):
        return obj.risk_tier_match
    risk_tier_match_display.short_description = 'Risk/Tier Match?'
    risk_tier_match_display.boolean = True
    
    def capital_tier_match_display(self, obj):
        return obj.capital_tier_match
    capital_tier_match_display.short_description = 'Capital Sufficient?'
    capital_tier_match_display.boolean = True
    
    def contracts_signed_display(self, obj):
        return obj.all_contracts_signed
    contracts_signed_display.short_description = 'Contracts Signed?'
    contracts_signed_display.boolean = True
    
    def is_qualified_display(self, obj):
        return obj.is_qualified_for_auto_approval
    is_qualified_display.short_description = 'Auto-Approval Qualified?'
    is_qualified_display.boolean = True


@admin.register(ManagedTradingContract)
class ManagedTradingContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_type',
        'application',
        'managed_account',
        'is_signed',
        'signed_date',
        'pdf_generated'
    ]
    list_filter = ['contract_type', 'is_signed', 'pdf_generated', 'signed_date']
    search_fields = [
        'application__user__username',
        'application__user__first_name',
        'application__user__last_name',
        'title'
    ]
    readonly_fields = ['signed_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contract Information', {
            'fields': ('contract_type', 'title', 'application', 'managed_account')
        }),
        ('Contract Content', {
            'fields': ('contract_text',)
        }),
        ('Signature', {
            'fields': ('is_signed', 'signature_data', 'signed_date', 'signature_ip')
        }),
        ('PDF', {
            'fields': ('pdf_generated', 'pdf_url'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# PHASE 7: BATCH APPROVAL SYSTEM ADMIN
# ============================================================================

@admin.register(PositionBatch)
class PositionBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number',
        'managed_account',
        'created_date',
        'approval_deadline',
        'status',
        'total_positions',
        'total_capital_required',
        'hours_remaining',
        'is_expired_display'
    ]
    list_filter = ['status', 'created_date', 'approval_deadline']
    search_fields = ['batch_number', 'managed_account__account_number']
    readonly_fields = [
        'created_date', 'approved_date', 'created_at', 'updated_at',
        'hours_remaining', 'time_remaining_display', 'is_expired_display'
    ]
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_number', 'managed_account', 'status')
        }),
        ('Timing', {
            'fields': (
                'created_date', 'approval_deadline',
                'hours_remaining', 'time_remaining_display', 'is_expired_display'
            )
        }),
        ('Batch Summary', {
            'fields': ('total_positions', 'total_capital_required')
        }),
        ('Client Approval', {
            'fields': ('approved_date', 'approval_signature', 'approval_ip')
        }),
        ('Notifications', {
            'fields': ('reminder_sent', 'timeout_notification_sent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def time_remaining_display(self, obj):
        if obj.status != 'pending':
            return 'N/A'
        hours = obj.hours_remaining
        if hours <= 0:
            return 'EXPIRED'
        return f"{hours} hours"
    time_remaining_display.short_description = 'Time Remaining'
    
    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.short_description = 'Expired?'
    is_expired_display.boolean = True


# ============================================================================
# POSITION AUTOMATION: SUGGESTED POSITIONS ADMIN
# ============================================================================

@admin.register(SuggestedPosition)
class SuggestedPositionAdmin(admin.ModelAdmin):
    list_display = [
        'symbol',
        'ai_score_display',  # NEW: Show AI score prominently
        'strategy',
        'source',
        'probability_of_profit',
        'premium_collected',
        'dte',
        'review_status',
        'reviewed_by',
        'fetched_at'
    ]
    list_filter = ['review_status', 'ai_rating', 'source', 'strategy', 'fetched_at']  # Added ai_rating filter
    search_fields = ['symbol', 'ai_reasoning', 'ai_recommendation', 'staff_notes']
    readonly_fields = [
        'fetched_at', 'reviewed_at', 'created_at', 'updated_at',
        'risk_reward_ratio', 'meets_criteria', 
        'ai_score', 'ai_rating', 'ai_breakdown', 'ai_recommendation', 'ai_confidence_level'  # NEW: AI fields readonly
    ]
    list_editable = []
    ordering = ['-ai_score', '-probability_of_profit', '-fetched_at']  # Sort by AI score first!
    
    fieldsets = (
        ('Position Details', {
            'fields': ('symbol', 'strategy', 'positions', 'expiration_date', 'dte')
        }),
        ('Source Information', {
            'fields': ('source', 'fetched_at', 'api_response_data')
        }),
        ('Financial Metrics', {
            'fields': (
                'premium_collected', 'capital_required',
                'max_profit', 'max_loss', 'breakeven',
                'risk_reward_ratio'
            )
        }),
        ('High Probability Indicators', {
            'fields': ('probability_of_profit', 'meets_criteria'),
            'description': 'Criteria: 70%+ probability, $100+ premium, 30-60 DTE'
        }),
        ('Greeks', {
            'fields': ('position_delta', 'position_theta', 'position_gamma', 'position_vega'),
            'classes': ('collapse',)
        }),
        ('AI Position Scoring (6-Factor Algorithm)', {
            'fields': (
                'ai_score', 'ai_rating', 'ai_confidence_level',
                'ai_recommendation', 'ai_breakdown'
            ),
            'description': 'AI scores 0-100 using historical win rate, IV rank, greeks, risk/reward, earnings, liquidity'
        }),
        ('AI Analysis (Legacy)', {
            'fields': ('ai_confidence', 'ai_reasoning'),
            'classes': ('collapse',)
        }),
        ('Staff Review', {
            'fields': (
                'review_status', 'reviewed_by', 'reviewed_at',
                'staff_notes', 'target_account'
            )
        }),
        ('Conversion', {
            'fields': ('created_position',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """Bulk approve selected suggestions"""
        from django.utils import timezone
        updated = queryset.filter(review_status='pending').update(
            review_status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"Approved {updated} position(s)")
    approve_selected.short_description = "✅ Approve selected suggestions"
    
    def reject_selected(self, request, queryset):
        """Bulk reject selected suggestions"""
        from django.utils import timezone
        updated = queryset.filter(review_status='pending').update(
            review_status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            staff_notes="Bulk rejected"
        )
        self.message_user(request, f"Rejected {updated} position(s)")
    reject_selected.short_description = "❌ Reject selected suggestions"
    
    def ai_score_display(self, obj):
        """Display AI score with stars and color coding"""
        if not obj.ai_score:
            return "N/A"
        
        score = obj.ai_score
        stars = ""
        if score >= 95:
            stars = "⭐⭐⭐⭐⭐"
            color = "#28a745"  # Green
        elif score >= 85:
            stars = "⭐⭐⭐⭐"
            color = "#17a2b8"  # Blue
        elif score >= 70:
            stars = "⭐⭐⭐"
            color = "#ffc107"  # Yellow
        elif score >= 50:
            stars = "⭐⭐"
            color = "#fd7e14"  # Orange
        else:
            stars = "⭐"
            color = "#dc3545"  # Red
        
        from django.utils.html import format_html
        return format_html(
            '<strong style="color: {}; font-size: 1.1em;">{}</strong><br><span>{}</span>',
            color,
            f"{score:.0f}/100",
            stars
        )
    
    ai_score_display.short_description = "🤖 AI Score"
    ai_score_display.admin_order_field = 'ai_score'


@admin.register(OptionPlayRawData)
class OptionPlayRawDataAdmin(admin.ModelAdmin):
    """
    Admin interface for manually uploaded OptionPlay CSV data
    
    Fallback when Playwright scraper fails:
    1. Download CSV from OptionPlay.com
    2. Upload via "Import CSV" button
    3. Convert to SuggestedPositions
    """
    list_display = [
        'symbol', 'strategy_type', 'sell_strike', 'buy_strike', 'premium',
        'expiry', 'days_to_expiry', 'iv_rank', 'is_processed', 'uploaded_by', 'upload_date'
    ]
    list_filter = ['strategy_type', 'is_processed', 'upload_date', 'expiry']
    search_fields = ['symbol', 'earnings_date']
    readonly_fields = ['upload_date', 'processed_date', 'created_suggestion', 'calculated_dte']
    ordering = ['-upload_date', 'symbol']
    
    fieldsets = (
        ('Position Details', {
            'fields': ('symbol', 'strategy_type', 'spread_strategy', 'option_type')
        }),
        ('Strikes & Pricing', {
            'fields': ('stock_price', 'sell_strike', 'buy_strike', 'premium', 'width')
        }),
        ('Expiration', {
            'fields': ('expiry', 'days_to_expiry', 'calculated_dte')
        }),
        ('Metrics', {
            'fields': ('iv_rank', 'prem_width_ratio', 'raw_return', 'annualized_return', 'distance_to_strike'),
            'classes': ('collapse',)
        }),
        ('Earnings', {
            'fields': ('earnings_date', 'earnings_flag'),
            'classes': ('collapse',)
        }),
        ('Upload Info', {
            'fields': ('uploaded_by', 'upload_date', 'upload_notes')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_date', 'created_suggestion', 'processing_error')
        }),
        ('Raw Data', {
            'fields': ('csv_row_data',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['convert_to_suggestions', 'delete_processed']
    
    def convert_to_suggestions(self, request, queryset):
        """Convert selected raw data to SuggestedPositions"""
        from investing.services.optionplay_converter import OptionPlayConverterService
        
        # Only convert unprocessed
        to_convert = queryset.filter(is_processed=False)
        
        if not to_convert.exists():
            self.message_user(request, "⚠️ No unprocessed data selected", level='warning')
            return
        
        converter = OptionPlayConverterService()
        suggestions, errors = converter.bulk_convert(to_convert)
        
        self.message_user(
            request,
            f"✅ Converted {len(suggestions)} positions to SuggestedPosition. Errors: {len(errors)}"
        )
        
        if errors:
            self.message_user(request, f"⚠️ Errors: {', '.join(errors[:5])}", level='warning')
    
    convert_to_suggestions.short_description = "🔄 Convert to SuggestedPositions"
    
    def delete_processed(self, request, queryset):
        """Delete processed raw data (cleanup)"""
        processed = queryset.filter(is_processed=True)
        count = processed.count()
        processed.delete()
        self.message_user(request, f"🗑️ Deleted {count} processed records")
    
    delete_processed.short_description = "🗑️ Delete processed records"


@admin.register(OptionsPositionHistory)
class OptionsPositionHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for historical position outcomes
    
    Purpose:
    - Review past trades (wins/losses)
    - Analyze ML features
    - Train AI scoring model
    """
    list_display = [
        'position_symbol', 'position_strategy', 'was_profitable', 
        'actual_return_percentage', 'annualized_return', 'days_held', 
        'performance_category', 'created_at'
    ]
    list_filter = [
        'was_profitable', 'performance_category', 'exit_reason', 
        'entry_market_trend', 'created_at'
    ]
    search_fields = [
        'position__symbol', 'position__account__user__username', 
        'exit_notes', 'ai_post_analysis'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'risk_reward_realized', 'holding_efficiency'
    ]
    
    fieldsets = (
        ('Position Link', {
            'fields': ('position',)
        }),
        ('Outcome', {
            'fields': (
                'was_profitable', 'actual_return_amount', 
                'actual_return_percentage', 'annualized_return', 
                'days_held', 'performance_category'
            )
        }),
        ('Exit Details', {
            'fields': ('exit_reason', 'exit_notes', 'exit_stock_price', 'max_profit_captured')
        }),
        ('Entry Conditions (ML Features)', {
            'fields': (
                'entry_iv_rank', 'entry_market_trend', 'entry_vix', 
                'entry_stock_price', 'days_to_earnings'
            ),
            'classes': ('collapse',)
        }),
        ('AI Analysis', {
            'fields': ('ai_confidence_at_entry', 'ai_post_analysis'),
            'classes': ('collapse',)
        }),
        ('Calculated Metrics', {
            'fields': ('risk_reward_realized', 'holding_efficiency', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def position_symbol(self, obj):
        return obj.position.symbol
    position_symbol.short_description = 'Symbol'
    position_symbol.admin_order_field = 'position__symbol'
    
    def position_strategy(self, obj):
        return obj.position.strategy
    position_strategy.short_description = 'Strategy'
    position_strategy.admin_order_field = 'position__strategy'