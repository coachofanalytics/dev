"""
API endpoints for cascading form data
Provides filtered data for Category → Subcategory → Item dropdowns
"""
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import BudgetCategory, BudgetSubCategory, Transaction, Budget, CodaBudget


def api_get_subcategories(request):
    """
    Get subcategories filtered by category
    
    Usage: /api/subcategories/?category_id=5
    """
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'error': 'category_id required'}, status=400)
    
    try:
        subcategories = BudgetSubCategory.objects.filter(
            category_id=category_id
        ).values('id', 'name').order_by('name')
        
        return JsonResponse({
            'subcategories': list(subcategories),
            'count': len(subcategories)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_get_items(request):
    """
    Get common items filtered by category and/or subcategory
    
    Based on historical transaction data to suggest existing items
    and prevent data entry errors
    
    Usage: /api/items/?category_id=5&subcategory_id=10
    """
    category_id = request.GET.get('category_id')
    subcategory_id = request.GET.get('subcategory_id')
    department_id = request.GET.get('department_id')
    
    # Build filter
    filters = Q()
    if category_id:
        filters &= Q(category_id=category_id)
    if subcategory_id:
        filters &= Q(subcategory_id=subcategory_id)
    if department_id:
        filters &= Q(department_id=department_id)
    
    # Get items from Transaction history
    transaction_items = Transaction.objects.filter(
        filters
    ).exclude(
        type__isnull=True
    ).exclude(
        type=''
    ).values('type').annotate(
        count=Count('id')
    ).order_by('-count')[:50]  # Top 50 most common
    
    # Get items from Budget
    budget_items = Budget.objects.filter(
        filters
    ).exclude(
        item_name__isnull=True
    ).exclude(
        item_name=''
    ).values('item_name').annotate(
        count=Count('id')
    ).order_by('-count')[:50]
    
    # Get items from CodaBudget
    codabudget_items = CodaBudget.objects.filter(
        filters
    ).exclude(
        item__isnull=True
    ).exclude(
        item=''
    ).values('item').annotate(
        count=Count('id')
    ).order_by('-count')[:50]
    
    # Combine and deduplicate
    items_dict = {}
    
    # Add transaction items
    for item in transaction_items:
        name = item['type'].strip()
        if name:
            items_dict[name] = items_dict.get(name, 0) + item['count']
    
    # Add budget items
    for item in budget_items:
        name = item['item_name'].strip()
        if name:
            items_dict[name] = items_dict.get(name, 0) + item['count']
    
    # Add codabudget items
    for item in codabudget_items:
        name = item['item'].strip()
        if name:
            items_dict[name] = items_dict.get(name, 0) + item['count']
    
    # Sort by frequency
    sorted_items = sorted(
        items_dict.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Format response
    items_list = [
        {'name': name, 'frequency': count} 
        for name, count in sorted_items[:30]  # Top 30
    ]
    
    return JsonResponse({
        'items': items_list,
        'count': len(items_list),
        'filters': {
            'category_id': category_id,
            'subcategory_id': subcategory_id,
            'department_id': department_id,
        }
    })


def api_suggest_defaults(request):
    """
    Suggest default values based on receiver, department, and amount
    
    Uses historical patterns to pre-fill category, subcategory, item
    
    Usage: /api/suggest-defaults/?receiver=KPLC&department_id=1&amount=5000
    """
    receiver = request.GET.get('receiver', '').strip()
    department_id = request.GET.get('department_id')
    amount = request.GET.get('amount')
    
    if not receiver and not department_id:
        return JsonResponse({'error': 'receiver or department_id required'}, status=400)
    
    # Find most common category/subcategory/item for this receiver+department
    filters = Q()
    if receiver:
        filters &= Q(receiver__icontains=receiver)
    if department_id:
        filters &= Q(department_id=department_id)
    if amount:
        try:
            amount_val = float(amount)
            # Look for similar amounts (±20%)
            filters &= Q(
                amount__gte=amount_val * 0.8,
                amount__lte=amount_val * 1.2
            )
        except ValueError:
            pass
    
    # Get most common combination
    similar_transactions = Transaction.objects.filter(
        filters
    ).exclude(
        category__isnull=True
    ).values(
        'category_id',
        'category__name',
        'subcategory_id',
        'subcategory__name',
        'type',
        'department__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    if similar_transactions:
        return JsonResponse({
            'suggested': {
                'category_id': similar_transactions['category_id'],
                'category_name': similar_transactions['category__name'],
                'subcategory_id': similar_transactions['subcategory_id'],
                'subcategory_name': similar_transactions['subcategory__name'],
                'item': similar_transactions['type'],
                'department': similar_transactions['department__name'],
                'confidence': 'high' if similar_transactions['count'] > 3 else 'medium',
                'match_count': similar_transactions['count']
            }
        })
    else:
        return JsonResponse({
            'suggested': None,
            'message': 'No similar transactions found'
        })

