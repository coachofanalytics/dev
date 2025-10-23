"""
Food Management Views

Views for inventory management, consumption logging, and purchase recording.
Integrates with existing budget system via signals.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from finance.models import (
    Food, FoodInventory, FoodPurchaseTransaction,
    FoodConsumptionLog, FoodRestockRequest, Supplier
)
from finance.forms_food import (
    DailyConsumptionLogForm, BulkConsumptionLogForm,
    FoodPurchaseForm, RestockRequestForm,
    FoodInventoryForm, FoodItemForm, QuickConsumptionForm
)
from finance.services.food_service import (
    get_food_inventory_service,
    get_food_consumption_service,
    get_food_purchase_service,
)

logger = logging.getLogger(__name__)


# =============================================================================
# INVENTORY DASHBOARD
# =============================================================================

@login_required
def food_inventory_dashboard(request):
    """
    Main dashboard for food inventory management
    
    Shows:
    - Current stock levels
    - Low stock alerts
    - Recent consumption
    - Pending restock requests
    """
    inventory_service = get_food_inventory_service()
    
    # Get user's department if available
    user_department = getattr(request.user, 'department', None)
    
    # Get inventory summary
    summary = inventory_service.get_inventory_summary(location=user_department)
    
    # Get low stock items
    low_stock_items = inventory_service.get_low_stock_items(location=user_department)
    
    # Get recent consumption (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_consumption = FoodConsumptionLog.objects.filter(
        consumption_date__gte=seven_days_ago.date()
    ).select_related('inventory__food_item', 'recorded_by').order_by('-consumption_date')
    
    if user_department:
        recent_consumption = recent_consumption.filter(inventory__location=user_department)
    
    # Get pending restock requests
    pending_restocks = FoodRestockRequest.objects.filter(
        status='pending'
    ).select_related('inventory__food_item', 'inventory__location', 'requested_by')
    
    if user_department:
        pending_restocks = pending_restocks.filter(inventory__location=user_department)
    
    # Get all inventory for the location
    inventories = FoodInventory.objects.filter(
        Q(location=user_department) if user_department else Q()
    ).select_related('food_item', 'location').order_by('food_item__name')
    
    context = {
        'summary': summary,
        'low_stock_items': low_stock_items[:10],  # Top 10
        'recent_consumption': recent_consumption[:20],  # Last 20
        'pending_restocks': pending_restocks,
        'inventories': inventories,
        'user_department': user_department,
    }
    
    return render(request, 'finance/food/dashboard.html', context)


# =============================================================================
# CONSUMPTION LOGGING
# =============================================================================

@login_required
def log_daily_consumption(request):
    """
    View for logging daily food consumption
    
    Staff use this to record what was consumed each day.
    Signals will automatically update inventory and trigger restocks.
    """
    user_department = getattr(request.user, 'department', None)
    
    if request.method == 'POST':
        form = DailyConsumptionLogForm(request.POST, location=user_department)
        
        if form.is_valid():
            try:
                consumption_service = get_food_consumption_service()
                
                log = consumption_service.log_daily_consumption(
                    inventory_id=form.cleaned_data['inventory'].id,
                    quantity_consumed=form.cleaned_data['quantity_consumed'],
                    user=request.user,
                    notes=form.cleaned_data['notes'],
                    consumption_type=form.cleaned_data['consumption_type']
                )
                
                messages.success(
                    request,
                    f"✅ Logged consumption: {log.quantity_consumed} "
                    f"{log.inventory.food_item.unit_of_measurement} of "
                    f"{log.inventory.food_item.name}"
                )
                
                # Check if restock was triggered
                inventory = log.inventory
                inventory.refresh_from_db()
                if inventory.status in ['low_stock', 'out_of_stock']:
                    messages.warning(
                        request,
                        f"⚠️ {inventory.food_item.name} is now {inventory.get_status_display()}. "
                        f"A restock request will be created automatically."
                    )
                
                return redirect('finance:food_inventory_dashboard')
                
            except Exception as e:
                logger.error(f"Error logging consumption: {e}")
                messages.error(request, f"❌ Error: {str(e)}")
    else:
        form = DailyConsumptionLogForm(location=user_department)
    
    context = {
        'form': form,
        'user_department': user_department,
    }
    
    return render(request, 'finance/food/log_consumption.html', context)


@login_required
@require_POST
def quick_log_consumption(request):
    """
    AJAX endpoint for quick consumption logging
    
    Returns JSON response for single-page app updates
    """
    form = QuickConsumptionForm(request.POST)
    
    if form.is_valid():
        try:
            consumption_service = get_food_consumption_service()
            inventory = FoodInventory.objects.get(id=form.cleaned_data['inventory_id'])
            
            log = consumption_service.log_consumption(
                inventory=inventory,
                quantity=form.cleaned_data['quantity'],
                user=request.user,
                notes=form.cleaned_data.get('notes', '')
            )
            
            # Refresh inventory to get updated values
            inventory.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'message': f'Logged {log.quantity_consumed} {inventory.food_item.unit_of_measurement}',
                'new_quantity': str(inventory.quantity),
                'status': inventory.status,
                'status_display': inventory.get_status_display(),
            })
            
        except Exception as e:
            logger.error(f"Error in quick log: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


# =============================================================================
# PURCHASE RECORDING
# =============================================================================

@login_required
def record_food_purchase(request):
    """
    View for recording food purchases
    
    Creates purchase record which automatically:
    - Creates Transaction
    - Updates Budget
    - Updates Inventory
    - Updates Food price
    """
    if request.method == 'POST':
        form = FoodPurchaseForm(request.POST)
        
        if form.is_valid():
            try:
                purchase = form.save(commit=False)
                purchase.purchased_by = request.user
                purchase.save()
                
                messages.success(
                    request,
                    f"✅ Purchase recorded: {purchase.quantity} {purchase.food_item.unit_of_measurement} "
                    f"of {purchase.food_item.name} for {purchase.total_amount} {purchase.currency}"
                )
                messages.info(
                    request,
                    "📊 Budget entry and inventory update will be created automatically"
                )
                
                return redirect('finance:food_inventory_dashboard')
                
            except Exception as e:
                logger.error(f"Error recording purchase: {e}")
                messages.error(request, f"❌ Error: {str(e)}")
    else:
        form = FoodPurchaseForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'finance/food/record_purchase.html', context)


@login_required
def fulfill_restock_request(request, request_id):
    """
    View for fulfilling a restock request
    
    Allows staff to record the actual purchase details when fulfilling a restock.
    """
    restock_request = get_object_or_404(FoodRestockRequest, id=request_id)
    
    if request.method == 'POST':
        form = FoodPurchaseForm(request.POST)
        
        if form.is_valid():
            try:
                purchase_service = get_food_purchase_service()
                
                purchase = purchase_service.fulfill_restock_request(
                    restock_request=restock_request,
                    actual_quantity=form.cleaned_data['quantity'],
                    actual_unit_price=form.cleaned_data['unit_price'],
                    supplier=form.cleaned_data['supplier'],
                    payment_method=form.cleaned_data['payment_method'],
                    receipt_number=form.cleaned_data['receipt_number'],
                    user=request.user
                )
                
                messages.success(
                    request,
                    f"✅ Restock request #{request_id} fulfilled with purchase #{purchase.id}"
                )
                
                return redirect('finance:food_inventory_dashboard')
                
            except Exception as e:
                logger.error(f"Error fulfilling restock: {e}")
                messages.error(request, f"❌ Error: {str(e)}")
    else:
        # Pre-fill form with restock request details
        initial_data = {
            'food_item': restock_request.inventory.food_item,
            'inventory': restock_request.inventory,
            'quantity': restock_request.requested_quantity,
            'unit_price': restock_request.inventory.food_item.current_unit_price,
            'currency': restock_request.inventory.food_item.currency,
            'supplier': restock_request.inventory.food_item.current_supplier,
        }
        form = FoodPurchaseForm(initial=initial_data)
    
    context = {
        'form': form,
        'restock_request': restock_request,
    }
    
    return render(request, 'finance/food/fulfill_restock.html', context)


# =============================================================================
# RESTOCK REQUEST MANAGEMENT
# =============================================================================

@login_required
def create_restock_request(request):
    """
    View for manually creating restock requests
    
    Usually auto-created, but staff can create manually if needed.
    """
    if request.method == 'POST':
        form = RestockRequestForm(request.POST)
        
        if form.is_valid():
            try:
                restock = form.save(commit=False)
                restock.requested_by = request.user
                restock.status = 'pending'
                
                # Calculate estimated cost
                inventory = restock.inventory
                restock.estimated_cost = (
                    restock.requested_quantity * inventory.food_item.current_unit_price
                )
                
                restock.save()
                
                messages.success(
                    request,
                    f"✅ Restock request created for {inventory.food_item.name}"
                )
                messages.info(
                    request,
                    "📊 Budget request will be created automatically"
                )
                
                return redirect('finance:food_inventory_dashboard')
                
            except Exception as e:
                logger.error(f"Error creating restock request: {e}")
                messages.error(request, f"❌ Error: {str(e)}")
    else:
        form = RestockRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'finance/food/create_restock_request.html', context)


@login_required
def restock_request_list(request):
    """
    View list of restock requests with filtering
    """
    status_filter = request.GET.get('status', 'all')
    
    requests = FoodRestockRequest.objects.select_related(
        'inventory__food_item', 'inventory__location',
        'requested_by', 'approved_by', 'budget_request'
    ).order_by('-created_at')
    
    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    
    # Filter by user's department if not staff
    if not request.user.is_staff:
        user_department = getattr(request.user, 'department', None)
        if user_department:
            requests = requests.filter(inventory__location=user_department)
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
    }
    
    return render(request, 'finance/food/restock_requests.html', context)


# =============================================================================
# INVENTORY DETAIL & ANALYTICS
# =============================================================================

@login_required
def inventory_detail(request, inventory_id):
    """
    Detailed view of a single inventory item
    
    Shows:
    - Current stock
    - Consumption history
    - Purchase history
    - Restock requests
    - Analytics
    """
    inventory = get_object_or_404(
        FoodInventory.objects.select_related('food_item', 'location'),
        id=inventory_id
    )
    
    # Get consumption history
    consumption_service = get_food_consumption_service()
    consumption_logs = consumption_service.get_consumption_history(inventory, days=30)
    analytics = consumption_service.get_consumption_analytics(inventory, days=30)
    
    # Get purchase history
    purchase_history = FoodPurchaseTransaction.objects.filter(
        inventory=inventory
    ).select_related('supplier', 'purchased_by').order_by('-purchase_date')[:10]
    
    # Get restock requests
    restock_requests = FoodRestockRequest.objects.filter(
        inventory=inventory
    ).select_related('requested_by', 'approved_by').order_by('-created_at')[:10]
    
    context = {
        'inventory': inventory,
        'consumption_logs': consumption_logs[:30],  # Last 30 logs
        'analytics': analytics,
        'purchase_history': purchase_history,
        'restock_requests': restock_requests,
    }
    
    return render(request, 'finance/food/inventory_detail.html', context)


# =============================================================================
# API ENDPOINTS (AJAX)
# =============================================================================

@login_required
def api_get_inventory_by_location(request):
    """
    AJAX endpoint to get inventories for a location
    
    Used for cascading dropdowns
    """
    location_id = request.GET.get('location_id')
    
    if not location_id:
        return JsonResponse({'error': 'Missing location_id'}, status=400)
    
    inventories = FoodInventory.objects.filter(
        location_id=location_id,
        status__in=['in_stock', 'low_stock']
    ).select_related('food_item').values(
        'id', 'food_item__name', 'quantity', 
        'food_item__unit_of_measurement', 'status'
    )
    
    return JsonResponse({
        'inventories': list(inventories)
    })


@login_required
def api_get_inventory_details(request, inventory_id):
    """
    AJAX endpoint to get inventory details
    
    Returns current stock, unit, status for display
    """
    try:
        inventory = FoodInventory.objects.select_related('food_item').get(id=inventory_id)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': inventory.id,
                'food_item': inventory.food_item.name,
                'quantity': str(inventory.quantity),
                'unit': inventory.food_item.unit_of_measurement,
                'status': inventory.status,
                'status_display': inventory.get_status_display(),
                'reorder_level': str(inventory.reorder_level),
                'daily_consumption_rate': str(inventory.daily_consumption_rate) if inventory.daily_consumption_rate else None,
                'days_until_stockout': inventory.days_until_stockout(),
            }
        })
    except FoodInventory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Inventory not found'
        }, status=404)


@login_required
def api_consumption_chart_data(request, inventory_id):
    """
    AJAX endpoint to get chart data for consumption over time
    
    Returns data suitable for Chart.js
    """
    try:
        inventory = FoodInventory.objects.get(id=inventory_id)
        days = int(request.GET.get('days', 30))
        
        consumption_service = get_food_consumption_service()
        logs = consumption_service.get_consumption_history(inventory, days=days)
        
        # Aggregate by date
        from django.db.models import Sum
        daily_data = logs.values('consumption_date').annotate(
            total=Sum('quantity_consumed')
        ).order_by('consumption_date')
        
        labels = [log['consumption_date'].strftime('%Y-%m-%d') for log in daily_data]
        values = [float(log['total']) for log in daily_data]
        
        return JsonResponse({
            'success': True,
            'data': {
                'labels': labels,
                'values': values,
                'unit': inventory.food_item.unit_of_measurement,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# REPORTS
# =============================================================================

@login_required
def food_spending_report(request):
    """
    Report on food spending vs budget
    
    Shows spending by department, category, and time period
    """
    from finance.services.food_service import FoodBudgetIntegrationService
    
    budget_service = FoodBudgetIntegrationService()
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get user's department
    user_department = getattr(request.user, 'department', None)
    
    # Get spending summary
    spending_summary = budget_service.get_food_spending_summary(
        department=user_department,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get budget vs actual (if department specified)
    budget_comparison = None
    if user_department:
        budget_comparison = budget_service.get_budget_vs_actual(
            department=user_department,
            year=timezone.now().year
        )
    
    # Get pending approvals
    pending_approvals = budget_service.get_pending_approvals_summary()
    
    context = {
        'spending_summary': spending_summary,
        'budget_comparison': budget_comparison,
        'pending_approvals': pending_approvals,
        'start_date': start_date,
        'end_date': end_date,
        'user_department': user_department,
    }
    
    return render(request, 'finance/food/spending_report.html', context)

