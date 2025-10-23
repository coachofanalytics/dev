"""
Food Management Services

Business logic layer for food inventory management, consumption tracking,
and budget integration.

Services:
- FoodInventoryService: Inventory management operations
- FoodConsumptionService: Consumption logging and tracking
- FoodBudgetIntegrationService: Budget system integration
"""

from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Avg, Q
from decimal import Decimal
from datetime import timedelta
import logging

from finance.models import (
    Food,
    FoodInventory,
    FoodPurchaseTransaction,
    FoodConsumptionLog,
    FoodRestockRequest,
    Transaction,
    BudgetCategory,
    BudgetSubCategory,
    BudgetRequest,
)
from finance.services.base_service import BaseFinanceService

logger = logging.getLogger(__name__)


# =============================================================================
# INVENTORY MANAGEMENT SERVICE
# =============================================================================

class FoodInventoryService(BaseFinanceService):
    """
    Service for managing food inventory operations
    """
    
    def get_inventory_for_location(self, location, include_zero_stock=False):
        """
        Get all inventory items for a specific location
        
        Args:
            location: Department instance
            include_zero_stock: Whether to include out-of-stock items
            
        Returns:
            QuerySet of FoodInventory objects
        """
        inventories = FoodInventory.objects.filter(location=location)
        
        if not include_zero_stock:
            inventories = inventories.exclude(status='out_of_stock')
        
        return inventories.select_related('food_item', 'location')
    
    def get_low_stock_items(self, location=None):
        """
        Get all items with low or no stock
        
        Args:
            location: Optional Department to filter by
            
        Returns:
            QuerySet of FoodInventory objects
        """
        inventories = FoodInventory.objects.filter(
            status__in=['low_stock', 'out_of_stock']
        )
        
        if location:
            inventories = inventories.filter(location=location)
        
        return inventories.select_related('food_item', 'location').order_by('quantity')
    
    def get_inventory_summary(self, location=None):
        """
        Get summary statistics for inventory
        
        Returns:
            Dict with counts and statistics
        """
        inventories = FoodInventory.objects.all()
        
        if location:
            inventories = inventories.filter(location=location)
        
        return {
            'total_items': inventories.count(),
            'in_stock': inventories.filter(status='in_stock').count(),
            'low_stock': inventories.filter(status='low_stock').count(),
            'out_of_stock': inventories.filter(status='out_of_stock').count(),
            'reorder_pending': inventories.filter(status='reorder_pending').count(),
            'pending_restocks': FoodRestockRequest.objects.filter(
                inventory__in=inventories,
                status='pending'
            ).count(),
        }
    
    @transaction.atomic
    def create_initial_inventory(self, food_item, location, initial_quantity, reorder_level, reorder_quantity, user):
        """
        Create initial inventory record for a food item at a location
        
        Args:
            food_item: Food instance
            location: Department instance
            initial_quantity: Initial stock quantity
            reorder_level: Threshold for reorder
            reorder_quantity: Amount to reorder
            user: User creating the inventory
            
        Returns:
            FoodInventory instance
        """
        try:
            inventory, created = FoodInventory.objects.get_or_create(
                food_item=food_item,
                location=location,
                defaults={
                    'quantity': initial_quantity,
                    'reorder_level': reorder_level,
                    'reorder_quantity': reorder_quantity,
                    'last_updated_by': user,
                }
            )
            
            if not created:
                # Update existing inventory
                inventory.quantity = initial_quantity
                inventory.reorder_level = reorder_level
                inventory.reorder_quantity = reorder_quantity
                inventory.last_updated_by = user
                inventory.save()
            
            inventory.update_status()
            
            logger.info(f"✅ Inventory initialized: {food_item.name} @ {location.name} = {initial_quantity}")
            
            return inventory
            
        except Exception as e:
            logger.error(f"❌ Error creating inventory: {e}")
            raise


# =============================================================================
# CONSUMPTION TRACKING SERVICE
# =============================================================================

class FoodConsumptionService(BaseFinanceService):
    """
    Service for logging and analyzing food consumption
    """
    
    @transaction.atomic
    def log_daily_consumption(self, inventory_id, quantity_consumed, user, notes='', consumption_type='normal'):
        """
        Log daily consumption and update inventory
        
        Args:
            inventory_id: ID of FoodInventory
            quantity_consumed: Amount consumed
            user: User logging the consumption
            notes: Optional notes
            consumption_type: Type of consumption (normal/event/waste/donation)
            
        Returns:
            FoodConsumptionLog instance
            
        Raises:
            ValueError: If quantity exceeds available stock
        """
        try:
            inventory = FoodInventory.objects.select_for_update().get(id=inventory_id)
            
            # Validate quantity
            if quantity_consumed > inventory.quantity:
                raise ValueError(
                    f"Cannot consume {quantity_consumed} {inventory.food_item.unit_of_measurement} - "
                    f"only {inventory.quantity} available"
                )
            
            if quantity_consumed <= 0:
                raise ValueError("Consumption quantity must be positive")
            
            # Create consumption log (signals will handle inventory update)
            log = FoodConsumptionLog.objects.create(
                inventory=inventory,
                quantity_consumed=quantity_consumed,
                consumption_date=timezone.now().date(),
                consumption_type=consumption_type,
                recorded_by=user,
                notes=notes,
                is_automatic=False
            )
            
            logger.info(f"✅ Consumption logged: {quantity_consumed} {inventory.food_item.unit_of_measurement} "
                       f"of {inventory.food_item.name}")
            
            return log
            
        except FoodInventory.DoesNotExist:
            logger.error(f"❌ Inventory {inventory_id} not found")
            raise ValueError(f"Inventory {inventory_id} not found")
        except Exception as e:
            logger.error(f"❌ Error logging consumption: {e}")
            raise
    
    def get_consumption_history(self, inventory, days=30):
        """
        Get consumption history for an inventory
        
        Args:
            inventory: FoodInventory instance
            days: Number of days to look back
            
        Returns:
            QuerySet of FoodConsumptionLog objects
        """
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        return FoodConsumptionLog.objects.filter(
            inventory=inventory,
            consumption_date__gte=cutoff_date
        ).order_by('-consumption_date')
    
    def get_consumption_analytics(self, inventory, days=30):
        """
        Get consumption analytics for an inventory
        
        Returns:
            Dict with analytics data
        """
        logs = self.get_consumption_history(inventory, days)
        
        if not logs.exists():
            return {
                'total_consumed': 0,
                'avg_daily': 0,
                'days_tracked': 0,
                'waste_percentage': 0,
            }
        
        total_consumed = logs.aggregate(Sum('quantity_consumed'))['quantity_consumed__sum'] or 0
        waste_consumed = logs.filter(consumption_type='waste').aggregate(
            Sum('quantity_consumed')
        )['quantity_consumed__sum'] or 0
        days_tracked = logs.values('consumption_date').distinct().count()
        
        avg_daily = total_consumed / days_tracked if days_tracked > 0 else 0
        waste_percentage = (waste_consumed / total_consumed * 100) if total_consumed > 0 else 0
        
        return {
            'total_consumed': total_consumed,
            'avg_daily': avg_daily,
            'days_tracked': days_tracked,
            'waste_percentage': waste_percentage,
            'normal_usage': logs.filter(consumption_type='normal').count(),
            'special_events': logs.filter(consumption_type='event').count(),
            'waste_incidents': logs.filter(consumption_type='waste').count(),
            'donations': logs.filter(consumption_type='donation').count(),
        }


# =============================================================================
# BUDGET INTEGRATION SERVICE
# =============================================================================

class FoodBudgetIntegrationService(BaseFinanceService):
    """
    Service for integrating food system with budget system
    
    Handles:
    - Purchase to budget sync
    - Restock request to budget request creation
    - Approval workflow integration
    """
    
    def get_food_spending_summary(self, department=None, start_date=None, end_date=None):
        """
        Get summary of food spending
        
        Args:
            department: Optional department filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict with spending summary
        """
        purchases = FoodPurchaseTransaction.objects.all()
        
        if department:
            purchases = purchases.filter(inventory__location=department)
        
        if start_date:
            purchases = purchases.filter(purchase_date__gte=start_date)
        
        if end_date:
            purchases = purchases.filter(purchase_date__lte=end_date)
        
        total_spent = purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_purchases = purchases.count()
        
        # Group by food item
        by_item = {}
        for purchase in purchases.select_related('food_item'):
            item_name = purchase.food_item.name
            if item_name not in by_item:
                by_item[item_name] = {
                    'total_spent': 0,
                    'quantity_purchased': 0,
                    'purchase_count': 0
                }
            by_item[item_name]['total_spent'] += purchase.total_amount
            by_item[item_name]['quantity_purchased'] += purchase.quantity
            by_item[item_name]['purchase_count'] += 1
        
        return {
            'total_spent': total_spent,
            'total_purchases': total_purchases,
            'by_item': by_item,
            'department': department.name if department else 'All',
        }
    
    def get_budget_vs_actual(self, department, category_name='Food & Accommodation', year=None):
        """
        Compare budgeted vs actual food spending
        
        Args:
            department: Department instance
            category_name: Budget category name
            year: Optional year (defaults to current year)
            
        Returns:
            Dict with budget vs actual data
        """
        from finance.models import Budget
        
        if not year:
            year = timezone.now().year
        
        try:
            category = BudgetCategory.objects.get(name=category_name)
            
            # Get budgeted amount
            budgets = Budget.objects.filter(
                department=department,
                category=category,
                start_date__year=year
            )
            budgeted_amount = budgets.aggregate(
                total=Sum(models.F('unit_price') * models.F('quantity'))
            )['total'] or 0
            
            # Get actual spending
            actual_spending = self.get_food_spending_summary(
                department=department,
                start_date=timezone.datetime(year, 1, 1),
                end_date=timezone.datetime(year, 12, 31, 23, 59, 59)
            )['total_spent']
            
            variance = budgeted_amount - actual_spending
            variance_percentage = (variance / budgeted_amount * 100) if budgeted_amount > 0 else 0
            
            return {
                'budgeted': budgeted_amount,
                'actual': actual_spending,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'status': 'under' if variance > 0 else 'over',
            }
            
        except BudgetCategory.DoesNotExist:
            logger.error(f"❌ Budget category '{category_name}' not found")
            return None
    
    def get_pending_approvals_summary(self):
        """
        Get summary of pending food-related budget requests
        
        Returns:
            Dict with pending approvals data
        """
        pending_restocks = FoodRestockRequest.objects.filter(
            status='pending'
        ).select_related('inventory__food_item', 'inventory__location', 'budget_request')
        
        summary = {
            'total_pending': pending_restocks.count(),
            'total_amount': sum(r.estimated_cost for r in pending_restocks),
            'by_location': {},
            'urgent_count': 0,
        }
        
        for restock in pending_restocks:
            location_name = restock.inventory.location.name
            if location_name not in summary['by_location']:
                summary['by_location'][location_name] = {
                    'count': 0,
                    'amount': 0,
                    'items': []
                }
            
            summary['by_location'][location_name]['count'] += 1
            summary['by_location'][location_name]['amount'] += restock.estimated_cost
            summary['by_location'][location_name]['items'].append({
                'food_item': restock.inventory.food_item.name,
                'quantity': restock.requested_quantity,
                'cost': restock.estimated_cost,
            })
            
            if restock.inventory.status == 'out_of_stock':
                summary['urgent_count'] += 1
        
        return summary


# =============================================================================
# CONSUMPTION SERVICE
# =============================================================================

class FoodConsumptionService(BaseFinanceService):
    """
    Extended service specifically for consumption operations
    """
    
    @transaction.atomic
    def log_consumption(self, inventory, quantity, user, notes='', consumption_type='normal'):
        """
        Log food consumption with validation
        
        Wrapper around model creation with additional business logic.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if quantity > inventory.quantity:
            raise ValueError(
                f"Insufficient stock: {inventory.quantity} available, {quantity} requested"
            )
        
        log = FoodConsumptionLog.objects.create(
            inventory=inventory,
            quantity_consumed=quantity,
            consumption_date=timezone.now().date(),
            consumption_type=consumption_type,
            recorded_by=user,
            notes=notes,
            is_automatic=False
        )
        
        logger.info(f"✅ Logged {consumption_type} consumption: {quantity} of {inventory.food_item.name}")
        
        return log
    
    def bulk_log_daily_consumption(self, consumption_data, user):
        """
        Log multiple consumption entries at once (end-of-day logging)
        
        Args:
            consumption_data: List of dicts with {inventory_id, quantity, notes}
            user: User logging the data
            
        Returns:
            Dict with results
        """
        results = {
            'success': [],
            'errors': [],
        }
        
        for data in consumption_data:
            try:
                inventory = FoodInventory.objects.get(id=data['inventory_id'])
                log = self.log_consumption(
                    inventory=inventory,
                    quantity=data['quantity'],
                    user=user,
                    notes=data.get('notes', ''),
                    consumption_type=data.get('type', 'normal')
                )
                results['success'].append({
                    'inventory_id': data['inventory_id'],
                    'log_id': log.id,
                })
            except Exception as e:
                results['errors'].append({
                    'inventory_id': data.get('inventory_id'),
                    'error': str(e),
                })
        
        logger.info(f"📊 Bulk consumption logged: {len(results['success'])} success, "
                   f"{len(results['errors'])} errors")
        
        return results


# =============================================================================
# PURCHASE SERVICE
# =============================================================================

class FoodPurchaseService(BaseFinanceService):
    """
    Service for recording food purchases
    """
    
    @transaction.atomic
    def record_purchase(self, food_item, quantity, unit_price, supplier, inventory=None, 
                       payment_method='Mpesa', receipt_number='', user=None, notes=''):
        """
        Record a food purchase
        
        This will automatically:
        1. Create FoodPurchaseTransaction
        2. Create Transaction (via signals)
        3. Create Budget entry (via existing signals)
        4. Update inventory (via signals)
        5. Update food current price (via signals)
        
        Args:
            food_item: Food instance
            quantity: Quantity purchased
            unit_price: Price per unit
            supplier: Supplier instance
            inventory: Optional FoodInventory to restock
            payment_method: Payment method used
            receipt_number: Receipt/invoice number
            user: User making the purchase
            notes: Additional notes
            
        Returns:
            FoodPurchaseTransaction instance
        """
        try:
            purchase = FoodPurchaseTransaction.objects.create(
                food_item=food_item,
                inventory=inventory,
                quantity=quantity,
                unit_price=unit_price,
                currency=food_item.currency,
                supplier=supplier,
                purchase_date=timezone.now(),
                payment_method=payment_method,
                receipt_number=receipt_number,
                purchased_by=user,
                notes=notes
            )
            
            logger.info(f"✅ Purchase recorded: {quantity} {food_item.unit_of_measurement} of {food_item.name} "
                       f"for {purchase.total_amount} {food_item.currency}")
            
            # Signals will handle:
            # - Transaction creation
            # - Budget entry creation
            # - Inventory update
            # - Food price update
            
            return purchase
            
        except Exception as e:
            logger.error(f"❌ Error recording purchase: {e}")
            raise
    
    def fulfill_restock_request(self, restock_request, actual_quantity, actual_unit_price, 
                                supplier, payment_method='Mpesa', receipt_number='', user=None):
        """
        Fulfill a restock request by recording the actual purchase
        
        Args:
            restock_request: FoodRestockRequest instance
            actual_quantity: Actual quantity received
            actual_unit_price: Actual price paid
            supplier: Supplier used
            payment_method: Payment method
            receipt_number: Receipt number
            user: User fulfilling the request
            
        Returns:
            FoodPurchaseTransaction instance
        """
        try:
            # Record the purchase
            purchase = self.record_purchase(
                food_item=restock_request.inventory.food_item,
                quantity=actual_quantity,
                unit_price=actual_unit_price,
                supplier=supplier,
                inventory=restock_request.inventory,
                payment_method=payment_method,
                receipt_number=receipt_number,
                user=user,
                notes=f"Restock request #{restock_request.id} fulfilled"
            )
            
            # Update restock request status
            restock_request.status = 'received'
            restock_request.save(update_fields=['status'])
            
            logger.info(f"✅ Restock request {restock_request.id} fulfilled with purchase {purchase.id}")
            
            return purchase
            
        except Exception as e:
            logger.error(f"❌ Error fulfilling restock request {restock_request.id}: {e}")
            raise


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_food_inventory_service():
    """Get instance of FoodInventoryService"""
    return FoodInventoryService()


def get_food_consumption_service():
    """Get instance of FoodConsumptionService"""
    return FoodConsumptionService()


def get_food_purchase_service():
    """Get instance of FoodPurchaseService"""
    return FoodPurchaseService()


