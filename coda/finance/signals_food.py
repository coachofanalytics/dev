"""
Food System Signal Handlers

Comprehensive signal-based automation for the food management system:
1. Automatic price change tracking
2. Purchase → Transaction → Budget sync
3. Consumption → Inventory updates
4. Restock → Budget request creation
5. Low stock alerts

All automation happens transparently via Django signals.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Import models
from finance.models import (
    Food,
    FoodPriceHistory,
    FoodInventory,
    FoodPurchaseTransaction,
    FoodConsumptionLog,
    FoodRestockRequest,
    Transaction,
    BudgetCategory,
    BudgetSubCategory,
    BudgetRequest,
)

# Import user tracking
from Middleware.track_user_middleware import get_current_user


# =============================================================================
# PRICE CHANGE TRACKING
# =============================================================================

@receiver(pre_save, sender=Food)
def capture_old_food_price(sender, instance, **kwargs):
    """
    Capture old price before saving (pre-save signal)
    
    This runs BEFORE the Food instance is saved, allowing us to
    capture the old value before it's overwritten.
    """
    if instance.pk:  # Only for updates, not new creates
        try:
            old_instance = Food.objects.get(pk=instance.pk)
            
            # Check if price changed
            if old_instance.current_unit_price != instance.current_unit_price:
                instance._old_price = old_instance.current_unit_price
                instance._price_changed = True
                logger.info(f"📊 Price change detected: {instance.name} "
                          f"{old_instance.current_unit_price} → {instance.current_unit_price}")
            else:
                instance._price_changed = False
                
        except Food.DoesNotExist:
            instance._price_changed = False
    else:
        instance._price_changed = False


@receiver(post_save, sender=Food)
def log_food_price_change(sender, instance, created, **kwargs):
    """
    Log price changes after Food is saved (post-save signal)
    
    Creates FoodPriceHistory record when price changes.
    Post-save ensures the change was successful before logging.
    """
    if not created and getattr(instance, '_price_changed', False):
        try:
            user = get_current_user()
            
            FoodPriceHistory.objects.create(
                food=instance,
                old_price=getattr(instance, '_old_price', None),
                new_price=instance.current_unit_price,
                supplier=instance.current_supplier,
                changed_by=user,
                change_reason=f"Price updated via {'admin' if user and user.is_staff else 'system'}"
            )
            
            logger.info(f"✅ Price change logged: {instance.name} - "
                       f"{instance._old_price} → {instance.current_unit_price}")
                       
        except Exception as e:
            logger.error(f"❌ Error logging price change for {instance.name}: {e}")


# =============================================================================
# PURCHASE → TRANSACTION → BUDGET INTEGRATION
# =============================================================================

@receiver(post_save, sender=FoodPurchaseTransaction)
def sync_food_purchase_to_transaction(sender, instance, created, **kwargs):
    """
    Create Transaction record when food is purchased
    
    Flow:
    FoodPurchaseTransaction → Transaction → Budget (via existing signal)
    
    This enables automatic budget tracking for all food purchases.
    """
    if created and not instance.transaction:
        try:
            with db_transaction.atomic():
                # Get or create Food & Accommodation category
                category, _ = BudgetCategory.objects.get_or_create(
                    name='Food & Accommodation',
                    defaults={'description': 'Food, beverages, and accommodation expenses'}
                )
                subcategory, _ = BudgetSubCategory.objects.get_or_create(
                    name='Food Supplies',
                    category=category
                )
                
                # Create Transaction (which will trigger budget sync via existing signal)
                txn = Transaction.objects.create(
                    category=category,
                    subcategory=subcategory,
                    type='Food_Accomodation',
                    receiver=instance.supplier.name if instance.supplier else 'Unknown Supplier',
                    description=f"Food Purchase: {instance.food_item.name} ({instance.quantity} {instance.food_item.unit_of_measurement})",
                    amount=instance.unit_price,
                    qty=instance.quantity,
                    currency=instance.currency,
                    payment_method=instance.payment_method,
                    department=instance.inventory.location if instance.inventory else None,
                    sender=instance.purchased_by,
                    transaction_date=instance.purchase_date,
                    receipt_link=instance.receipt_number,
                )
                
                # Link transaction to purchase
                instance.transaction = txn
                FoodPurchaseTransaction.objects.filter(pk=instance.pk).update(transaction=txn)
                
                logger.info(f"✅ Transaction {txn.id} created for food purchase: {instance.food_item.name}")
                logger.info(f"📊 Budget entry will be created automatically by Transaction signal")
                
        except Exception as e:
            logger.error(f"❌ Error creating transaction for food purchase {instance.id}: {e}")


@receiver(post_save, sender=FoodPurchaseTransaction)
def update_inventory_on_purchase(sender, instance, created, **kwargs):
    """
    Update inventory quantity when food is purchased
    
    Increases stock level and updates metadata.
    """
    if created and instance.inventory:
        try:
            inventory = instance.inventory
            inventory.quantity += instance.quantity
            inventory.last_restocked_date = instance.purchase_date
            inventory.last_restocked_quantity = instance.quantity
            inventory.last_updated_by = instance.purchased_by
            inventory.save(update_fields=[
                'quantity',
                'last_restocked_date',
                'last_restocked_quantity',
                'last_updated_by'
            ])
            
            # Update status
            inventory.update_status()
            
            logger.info(f"✅ Inventory updated: {instance.food_item.name} + {instance.quantity} = {inventory.quantity}")
            
        except Exception as e:
            logger.error(f"❌ Error updating inventory for purchase {instance.id}: {e}")


@receiver(post_save, sender=FoodPurchaseTransaction)
def update_food_current_price(sender, instance, created, **kwargs):
    """
    Update Food.current_unit_price if this is the latest purchase
    
    Keeps the master catalog price current based on recent purchases.
    """
    if created:
        try:
            # Check if this is the most recent purchase for this food item
            latest_purchase = FoodPurchaseTransaction.objects.filter(
                food_item=instance.food_item
            ).order_by('-purchase_date').first()
            
            if latest_purchase and latest_purchase.id == instance.id:
                # This is the latest purchase, update the food item
                Food.objects.filter(pk=instance.food_item.pk).update(
                    current_unit_price=instance.unit_price,
                    current_supplier=instance.supplier
                )
                
                logger.info(f"✅ Food price updated: {instance.food_item.name} → {instance.unit_price}")
                
        except Exception as e:
            logger.error(f"❌ Error updating food price for purchase {instance.id}: {e}")


# =============================================================================
# CONSUMPTION → INVENTORY UPDATES
# =============================================================================

@receiver(post_save, sender=FoodConsumptionLog)
def update_inventory_on_consumption(sender, instance, created, **kwargs):
    """
    Update inventory quantity and consumption rate when food is consumed
    
    Flow:
    1. Decrease inventory quantity
    2. Recalculate daily consumption rate
    3. Check if restock needed
    """
    if created:
        try:
            inventory = instance.inventory
            
            # Decrease inventory quantity
            inventory.quantity -= instance.quantity_consumed
            inventory.last_updated_by = instance.recorded_by
            inventory.save(update_fields=['quantity', 'last_updated_by'])
            
            # Update status
            inventory.update_status()
            
            logger.info(f"✅ Consumption logged: {inventory.food_item.name} - {instance.quantity_consumed} "
                       f"(Remaining: {inventory.quantity})")
            
            # Recalculate daily consumption rate
            update_consumption_rate(inventory)
            
            # Check if reorder needed
            if inventory.status in ['low_stock', 'out_of_stock']:
                check_and_create_restock_request(inventory)
            
        except Exception as e:
            logger.error(f"❌ Error processing consumption log {instance.id}: {e}")


def update_consumption_rate(inventory):
    """
    Calculate and update average daily consumption rate
    
    Uses last 30 days of consumption logs (normal usage only)
    """
    try:
        from datetime import timedelta
        from django.db.models import Avg
        
        cutoff_date = timezone.now().date() - timedelta(days=30)
        
        # Only include normal consumption (exclude waste, events)
        avg_consumption = FoodConsumptionLog.objects.filter(
            inventory=inventory,
            consumption_date__gte=cutoff_date,
            consumption_type='normal'
        ).aggregate(Avg('quantity_consumed'))['quantity_consumed__avg']
        
        if avg_consumption:
            inventory.daily_consumption_rate = avg_consumption
            inventory.save(update_fields=['daily_consumption_rate'])
            
            logger.info(f"📊 Consumption rate updated: {inventory.food_item.name} = "
                       f"{avg_consumption}/day")
                       
    except Exception as e:
        logger.error(f"❌ Error updating consumption rate for inventory {inventory.id}: {e}")


def check_and_create_restock_request(inventory):
    """
    Check if inventory needs restocking and create request if needed
    
    Only creates request if:
    1. Stock is at or below reorder level
    2. No pending/approved/ordered restock already exists
    """
    try:
        if inventory.quantity <= inventory.reorder_level:
            # Check for existing pending requests
            existing_request = FoodRestockRequest.objects.filter(
                inventory=inventory,
                status__in=['pending', 'approved', 'ordered']
            ).exists()
            
            if not existing_request:
                # Calculate estimated cost
                estimated_cost = inventory.reorder_quantity * inventory.food_item.current_unit_price
                
                # Create restock request
                restock_request = FoodRestockRequest.objects.create(
                    inventory=inventory,
                    requested_quantity=inventory.reorder_quantity,
                    estimated_cost=estimated_cost,
                    requested_by=inventory.last_updated_by or get_current_user(),
                    status='pending'
                )
                
                logger.warning(f"🔔 RESTOCK ALERT: {inventory.food_item.name} at {inventory.location.name} "
                             f"(Stock: {inventory.quantity}, Reorder Level: {inventory.reorder_level})")
                logger.info(f"✅ Restock request created: ID {restock_request.id}")
                
    except Exception as e:
        logger.error(f"❌ Error creating restock request for inventory {inventory.id}: {e}")


# =============================================================================
# RESTOCK → BUDGET REQUEST CREATION
# =============================================================================

@receiver(post_save, sender=FoodRestockRequest)
def create_budget_request_for_restock(sender, instance, created, **kwargs):
    """
    Create BudgetRequest when food restock is requested
    
    Flow:
    FoodRestockRequest → BudgetRequest → Approval Workflow
    
    This integrates food restocking with the budget approval system.
    """
    if created and not instance.budget_request:
        try:
            category, _ = BudgetCategory.objects.get_or_create(
                name='Food & Accommodation',
                defaults={'description': 'Food, beverages, and accommodation expenses'}
            )
            
            # Determine priority based on stock status
            if instance.inventory.status == 'out_of_stock':
                priority = 'high'
                urgency = 'urgent'
            elif instance.inventory.status == 'low_stock':
                priority = 'medium'
                urgency = 'normal'
            else:
                priority = 'low'
                urgency = 'normal'
            
            # Create budget request
            budget_request = BudgetRequest.objects.create(
                title=f"Food Restock: {instance.inventory.food_item.name} - {instance.inventory.location.name}",
                description=f"""Automatic restock request from inventory system

Item: {instance.inventory.food_item.name}
Location: {instance.inventory.location.name}
Current Stock: {instance.inventory.quantity} {instance.inventory.food_item.unit_of_measurement}
Reorder Level: {instance.inventory.reorder_level} {instance.inventory.food_item.unit_of_measurement}
Requested Quantity: {instance.requested_quantity} {instance.inventory.food_item.unit_of_measurement}
Unit Price: {instance.inventory.food_item.current_unit_price} {instance.inventory.food_item.currency}
Total Cost: {instance.estimated_cost} {instance.inventory.food_item.currency}

Days Until Stockout: {instance.inventory.days_until_stockout() or 'Unknown'}
Daily Consumption Rate: {instance.inventory.daily_consumption_rate or 'Not tracked'} {instance.inventory.food_item.unit_of_measurement}/day
""",
                department=instance.inventory.location,
                budget_category=category,
                requested_amount=instance.estimated_cost,
                currency=instance.inventory.food_item.currency,
                priority=priority,
                urgency=urgency,
                created_by=instance.requested_by,
                last_modified_by=instance.requested_by,
                notes=f"Auto-generated from Food Inventory System\nRestock Request ID: {instance.id}",
            )
            
            # Link budget request to restock request
            instance.budget_request = budget_request
            FoodRestockRequest.objects.filter(pk=instance.pk).update(budget_request=budget_request)
            
            logger.info(f"✅ Budget request {budget_request.id} created for restock {instance.id}")
            
            # Check if eligible for auto-approval
            check_auto_approval(budget_request, instance)
            
        except Exception as e:
            logger.error(f"❌ Error creating budget request for restock {instance.id}: {e}")


def check_auto_approval(budget_request, restock_request):
    """
    Check if restock request qualifies for auto-approval
    
    Auto-approve if:
    1. Amount is below threshold (e.g., $50)
    2. ApprovalPolicy says auto_approve=True
    """
    try:
        from finance.models import ApprovalPolicy
        
        # Find applicable approval policy
        policy = ApprovalPolicy.objects.filter(
            is_active=True,
            min_amount__lte=budget_request.requested_amount,
        ).filter(
            models.Q(max_amount__gte=budget_request.requested_amount) | 
            models.Q(max_amount__isnull=True)
        ).filter(
            applicable_categories=budget_request.budget_category
        ).first()
        
        if policy and policy.auto_approve:
            # Auto-approve both budget request and restock request
            budget_request.status = 'approved'
            budget_request.approved_by = None  # System approval
            budget_request.approved_at = timezone.now()
            budget_request.save(update_fields=['status', 'approved_by', 'approved_at'])
            
            restock_request.status = 'approved'
            restock_request.approved_by = None  # System approval
            restock_request.approved_at = timezone.now()
            restock_request.save(update_fields=['status', 'approved_by', 'approved_at'])
            
            logger.info(f"✅ AUTO-APPROVED: Restock request {restock_request.id} "
                       f"(Amount: {budget_request.requested_amount}, Policy: {policy.name})")
        else:
            logger.info(f"⏳ Manual approval required for restock {restock_request.id} "
                       f"(Amount: {budget_request.requested_amount})")
                       
    except Exception as e:
        logger.warning(f"⚠️  Could not check auto-approval for restock {restock_request.id}: {e}")


# =============================================================================
# RESTOCK STATUS SYNC
# =============================================================================

@receiver(post_save, sender=FoodRestockRequest)
def sync_restock_status_to_budget(sender, instance, created, **kwargs):
    """
    Sync restock request status changes to linked budget request
    
    When restock is approved/rejected, update the budget request too.
    """
    if not created and instance.budget_request:
        try:
            if instance.status == 'approved' and instance.budget_request.status != 'approved':
                instance.budget_request.status = 'approved'
                instance.budget_request.approved_by = instance.approved_by
                instance.budget_request.approved_at = instance.approved_at
                instance.budget_request.save(update_fields=['status', 'approved_by', 'approved_at'])
                
                logger.info(f"✅ Budget request {instance.budget_request.id} approved (linked to restock {instance.id})")
                
            elif instance.status == 'rejected' and instance.budget_request.status != 'rejected':
                instance.budget_request.status = 'rejected'
                instance.budget_request.rejected_by = instance.approved_by  # User who rejected
                instance.budget_request.rejection_reason = instance.rejection_reason
                instance.budget_request.save(update_fields=['status', 'rejected_by', 'rejection_reason'])
                
                logger.info(f"❌ Budget request {instance.budget_request.id} rejected (linked to restock {instance.id})")
                
        except Exception as e:
            logger.error(f"❌ Error syncing restock status to budget for {instance.id}: {e}")


# =============================================================================
# DAILY BACKGROUND TASKS (to be called by cron/celery)
# =============================================================================

def check_all_inventories_for_restock():
    """
    Background task: Check all inventories and trigger restock for low stock
    
    Run this daily via cron job or Celery beat.
    
    Usage in management command:
        python manage.py check_food_inventory_levels
    """
    low_stock_count = 0
    requests_created = 0
    
    try:
        # Find all low/out of stock inventories without pending restocks
        low_stock_inventories = FoodInventory.objects.filter(
            status__in=['low_stock', 'out_of_stock']
        ).exclude(
            restock_requests__status__in=['pending', 'approved', 'ordered']
        )
        
        low_stock_count = low_stock_inventories.count()
        
        for inventory in low_stock_inventories:
            check_and_create_restock_request(inventory)
            requests_created += 1
        
        logger.info(f"📊 Inventory check complete: {low_stock_count} low stock items, "
                   f"{requests_created} restock requests created")
        
        return {
            'low_stock_count': low_stock_count,
            'requests_created': requests_created
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking inventories: {e}")
        return {'error': str(e)}


# =============================================================================
# SIGNAL REGISTRATION STATUS
# =============================================================================

logger.info("✅ Food system signals loaded successfully")
logger.info("📊 Active signals:")
logger.info("   - Food price change tracking")
logger.info("   - Purchase → Transaction → Budget sync")
logger.info("   - Inventory updates on purchase/consumption")
logger.info("   - Automatic restock requests")
logger.info("   - Budget request creation for restocks")

