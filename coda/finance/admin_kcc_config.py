from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

class KCCLoanConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for KCC loan configuration"""
    
    list_display = [
        'performance_tier_display', 
        'loan_type_display', 
        'amount_range', 
        'interest_range', 
        'term_range', 
        'is_active', 
        'updated_at'
    ]
    
    list_filter = [
        'performance_tier', 
        'loan_type', 
        'is_active', 
        'created_at', 
        'updated_at'
    ]
    
    search_fields = ['performance_tier', 'loan_type']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('performance_tier', 'loan_type', 'is_active')
        }),
        ('Loan Amounts', {
            'fields': ('min_amount', 'max_amount'),
            'description': 'Set the minimum and maximum loan amounts for this tier'
        }),
        ('Interest Rates', {
            'fields': ('min_interest_rate', 'max_interest_rate'),
            'description': 'Set the interest rate range (e.g., 10.00 for 10%)'
        }),
        ('Loan Terms', {
            'fields': ('min_term_weeks', 'max_term_weeks'),
            'description': 'Set the loan term range in weeks'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def performance_tier_display(self, obj):
        """Display performance tier with color coding"""
        colors = {
            'new': '#FF6B6B',      # Red for new
            'bronze': '#CD7F32',    # Bronze
            'silver': '#C0C0C0',   # Silver
            'gold': '#FFD700',     # Gold
            'platinum': '#E5E4E2',  # Platinum
        }
        color = colors.get(obj.performance_tier, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_performance_tier_display()
        )
    performance_tier_display.short_description = 'Performance Tier'
    
    def loan_type_display(self, obj):
        """Display loan type with formatting"""
        return obj.get_loan_type_display().replace('_', ' ').title()
    loan_type_display.short_description = 'Loan Type'
    
    def amount_range(self, obj):
        """Display amount range"""
        return f"${obj.min_amount:,.2f} - ${obj.max_amount:,.2f}"
    amount_range.short_description = 'Amount Range'
    
    def interest_range(self, obj):
        """Display interest rate range"""
        return f"{obj.min_interest_rate}% - {obj.max_interest_rate}%"
    interest_range.short_description = 'Interest Rate'
    
    def term_range(self, obj):
        """Display term range"""
        return f"{obj.min_term_weeks} - {obj.max_term_weeks} weeks"
    term_range.short_description = 'Term Range'
    
    def get_queryset(self, request):
        """Order by performance tier priority"""
        return super().get_queryset(request).order_by(
            models.Case(
                models.When(performance_tier='new', then=models.Value(1)),
                models.When(performance_tier='bronze', then=models.Value(2)),
                models.When(performance_tier='silver', then=models.Value(3)),
                models.When(performance_tier='gold', then=models.Value(4)),
                models.When(performance_tier='platinum', then=models.Value(5)),
                default=models.Value(6),
                output_field=models.IntegerField(),
            )
        )
    
    actions = ['activate_configurations', 'deactivate_configurations']
    
    def activate_configurations(self, request, queryset):
        """Activate selected configurations"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"Successfully activated {updated} configuration(s)."
        )
    activate_configurations.short_description = "Activate selected configurations"
    
    def deactivate_configurations(self, request, queryset):
        """Deactivate selected configurations"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"Successfully deactivated {updated} configuration(s)."
        )
    deactivate_configurations.short_description = "Deactivate selected configurations"

# Register the admin interface
admin.site.register(KCCLoanConfiguration, KCCLoanConfigurationAdmin) 