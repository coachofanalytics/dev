"""
Food System Admin Interface

Admin registration for enhanced food management models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    Food, FoodPriceHistory, FoodInventory,
    FoodPurchaseTransaction, FoodConsumptionLog, 
    FoodRestockRequest, Supplier
)


# =============================================================================
# FOOD CATALOG ADMIN
# =============================================================================

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    """Admin interface for food items catalog"""
    
    list_display = ['name', 'category', 'current_unit_price', 'currency', 
                   'current_supplier', 'current_stock_display', 'is_active']
    list_filter = ['category', 'is_active', 'currency']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('current_unit_price', 'currency', 'unit_of_measurement')
        }),
        ('Supplier', {
            'fields': ('current_supplier',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_stock_display(self, obj):
        stock = obj.current_stock
        if stock > 0:
            return format_html('<span style="color: green;">{} {}</span>', 
                             stock, obj.unit_of_measurement)
        return format_html('<span style="color: red;">Out of Stock</span>')
    current_stock_display.short_description = 'Total Stock'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# PRICE HISTORY ADMIN
# =============================================================================

@admin.register(FoodPriceHistory)
class FoodPriceHistoryAdmin(admin.ModelAdmin):
    """Admin interface for food price history (audit trail)"""
    
    list_display = ['food', 'old_price', 'new_price', 'change_percentage_display', 
                   'supplier', 'changed_by', 'change_date']
    list_filter = ['change_date', 'food__category']
    search_fields = ['food__name', 'change_reason']
    readonly_fields = ['food', 'old_price', 'new_price', 'change_percentage', 
                      'supplier', 'changed_by', 'change_date', 'change_reason']
    date_hierarchy = 'change_date'
    
    def has_add_permission(self, request):
        return False  # Price history is auto-generated
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit trail
    
    def change_percentage_display(self, obj):
        if obj.change_percentage:
            color = 'red' if obj.change_percentage > 0 else 'green'
            return format_html('<span style="color: {};">{:+.2f}%</span>', 
                             color, obj.change_percentage)
        return '-'
    change_percentage_display.short_description = 'Change %'


# =============================================================================
# INVENTORY ADMIN
# =============================================================================

class FoodConsumptionLogInline(admin.TabularInline):
    """Inline for consumption logs"""
    model = FoodConsumptionLog
    extra = 0
    fields = ['consumption_date', 'quantity_consumed', 'consumption_type', 'recorded_by', 'notes']
    readonly_fields = ['consumption_date', 'recorded_by', 'created_at']
    can_delete = False


class FoodRestockRequestInline(admin.TabularInline):
    """Inline for restock requests"""
    model = FoodRestockRequest
    extra = 0
    fields = ['requested_quantity', 'estimated_cost', 'status', 'created_at']
    readonly_fields = ['created_at', 'budget_request']
    can_delete = False


@admin.register(FoodInventory)
class FoodInventoryAdmin(admin.ModelAdmin):
    """Admin interface for food inventory"""
    
    list_display = ['food_item', 'location', 'quantity', 'unit_display', 'status_display', 
                   'daily_consumption_rate', 'days_until_stockout_display', 'reorder_level']
    list_filter = ['status', 'location', 'food_item__category']
    search_fields = ['food_item__name', 'location__name']
    readonly_fields = ['status', 'last_restocked_date', 'last_restocked_quantity', 
                      'last_updated_by', 'created_at', 'updated_at']
    inlines = [FoodConsumptionLogInline, FoodRestockRequestInline]
    
    fieldsets = (
        ('Item & Location', {
            'fields': ('food_item', 'location')
        }),
        ('Current Stock', {
            'fields': ('quantity', 'status')
        }),
        ('Reorder Settings', {
            'fields': ('reorder_level', 'reorder_quantity')
        }),
        ('Analytics', {
            'fields': ('daily_consumption_rate',)
        }),
        ('Last Restock', {
            'fields': ('last_restocked_date', 'last_restocked_quantity'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('last_updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def unit_display(self, obj):
        return obj.food_item.unit_of_measurement
    unit_display.short_description = 'Unit'
    
    def status_display(self, obj):
        colors = {
            'in_stock': 'green',
            'low_stock': 'orange',
            'out_of_stock': 'red',
            'reorder_pending': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                         color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def days_until_stockout_display(self, obj):
        days = obj.days_until_stockout()
        if days is not None:
            if days < 3:
                color = 'red'
            elif days < 7:
                color = 'orange'
            else:
                color = 'green'
            return format_html('<span style="color: {};">{:.0f} days</span>', color, days)
        return '-'
    days_until_stockout_display.short_description = 'Days Until Stockout'


# =============================================================================
# PURCHASE ADMIN
# =============================================================================

@admin.register(FoodPurchaseTransaction)
class FoodPurchaseTransactionAdmin(admin.ModelAdmin):
    """Admin interface for food purchases"""
    
    list_display = ['food_item', 'quantity', 'unit_price', 'total_amount', 
                   'supplier', 'purchase_date', 'payment_method', 'transaction_link']
    list_filter = ['purchase_date', 'payment_method', 'food_item__category']
    search_fields = ['food_item__name', 'supplier__name', 'receipt_number']
    readonly_fields = ['total_amount', 'transaction', 'created_at', 'updated_at']
    date_hierarchy = 'purchase_date'
    
    fieldsets = (
        ('Purchase Details', {
            'fields': ('food_item', 'inventory', 'quantity', 'unit_price', 'total_amount', 'currency')
        }),
        ('Supplier & Payment', {
            'fields': ('supplier', 'payment_method', 'receipt_number', 'purchase_date')
        }),
        ('Integration', {
            'fields': ('transaction',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('purchased_by', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def transaction_link(self, obj):
        if obj.transaction:
            url = reverse('admin:finance_transaction_change', args=[obj.transaction.id])
            return format_html('<a href="{}">Transaction #{}</a>', url, obj.transaction.id)
        return '-'
    transaction_link.short_description = 'Linked Transaction'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.purchased_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# CONSUMPTION LOG ADMIN
# =============================================================================

@admin.register(FoodConsumptionLog)
class FoodConsumptionLogAdmin(admin.ModelAdmin):
    """Admin interface for consumption logs"""
    
    list_display = ['inventory', 'quantity_consumed', 'consumption_type', 
                   'consumption_date', 'recorded_by', 'is_automatic']
    list_filter = ['consumption_type', 'consumption_date', 'is_automatic', 
                  'inventory__location']
    search_fields = ['inventory__food_item__name', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'consumption_date'
    
    fieldsets = (
        ('Consumption Details', {
            'fields': ('inventory', 'quantity_consumed', 'consumption_date', 'consumption_type')
        }),
        ('Context', {
            'fields': ('recorded_by', 'notes', 'is_automatic')
        }),
        ('Audit', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# RESTOCK REQUEST ADMIN
# =============================================================================

@admin.register(FoodRestockRequest)
class FoodRestockRequestAdmin(admin.ModelAdmin):
    """Admin interface for restock requests"""
    
    list_display = ['inventory', 'requested_quantity', 'estimated_cost', 'status_display', 
                   'requested_by', 'budget_request_link', 'created_at']
    list_filter = ['status', 'inventory__location', 'created_at']
    search_fields = ['inventory__food_item__name', 'inventory__location__name']
    readonly_fields = ['estimated_cost', 'budget_request', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_requests', 'reject_requests']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('inventory', 'requested_quantity', 'estimated_cost')
        }),
        ('Status', {
            'fields': ('status', 'requested_by')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Budget Integration', {
            'fields': ('budget_request',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'ordered': 'blue',
            'received': 'green',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                         color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def budget_request_link(self, obj):
        if obj.budget_request:
            url = reverse('admin:finance_budgetrequest_change', args=[obj.budget_request.id])
            return format_html('<a href="{}">BR #{}</a>', url, obj.budget_request.id)
        return '-'
    budget_request_link.short_description = 'Budget Request'
    
    def approve_requests(self, request, queryset):
        """Bulk approve selected restock requests"""
        updated = 0
        for restock in queryset.filter(status='pending'):
            restock.status = 'approved'
            restock.approved_by = request.user
            restock.approved_at = timezone.now()
            restock.save()
            updated += 1
        
        self.message_user(request, f'{updated} restock requests approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Bulk reject selected restock requests"""
        updated = 0
        for restock in queryset.filter(status='pending'):
            restock.status = 'rejected'
            restock.approved_by = request.user
            restock.rejection_reason = 'Bulk rejection via admin'
            restock.save()
            updated += 1
        
        self.message_user(request, f'{updated} restock requests rejected.')
    reject_requests.short_description = 'Reject selected requests'


# =============================================================================
# SUPPLIER ADMIN
# =============================================================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin interface for suppliers"""
    
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    
    fieldsets = (
        ('Supplier Information', {
            'fields': ('name', 'contact_person')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Tax Information', {
            'fields': ('tax_id',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

