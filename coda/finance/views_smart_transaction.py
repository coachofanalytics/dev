"""
Smart Transaction Entry Views
Improved UX based on transaction data analysis learnings

Features:
- Auto-complete receiver names
- Category auto-suggestions
- Real-time validation
- Amount warnings
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum, Q
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from finance.models import Transaction, BudgetCategory
from finance.forms_improved import SmartTransactionForm


@login_required
def smart_transaction_entry(request):
    """
    Smart transaction entry form with auto-suggestions
    
    Uses patterns learned from data analysis to guide users
    toward entering high-quality, categorized data
    """
    
    if request.method == 'POST':
        form = SmartTransactionForm(request.POST, user=request.user)
        
        if form.is_valid():
            instance = form.save(commit=False)
            instance.sender = request.user
            instance.save()
            
            return redirect('finance:cashflows-list', type='operations')
        # If form has warnings (not errors), still show them
        elif hasattr(form, 'add_warning'):
            # Form is valid but has warnings
            pass
    else:
        form = SmartTransactionForm(user=request.user)
    
    # Get context data for smart suggestions
    context = _get_smart_form_context(request)
    context['form'] = form
    
    return render(request, 'finance/payments/smart_transaction_entry.html', context)


def _get_smart_form_context(request):
    """
    Get context data for smart form features
    
    Returns:
    - Last transaction by this user
    - Known receivers with their typical categories
    - Category averages for validation
    """
    
    # Get user's last transaction
    last_transaction = None
    if request.user.is_authenticated:
        last_transaction = Transaction.objects.filter(
            sender=request.user
        ).order_by('-transaction_date').first()
    
    # Get known receivers with their patterns
    known_receivers = _get_known_receivers()
    
    # Get average amounts by category
    category_averages = _get_category_averages()
    
    return {
        'last_transaction': last_transaction,
        'known_receivers': json.dumps(known_receivers),
        'category_averages': json.dumps(category_averages),
    }


def _get_known_receivers():
    """
    Get list of known receivers with their typical categories and amounts
    
    Based on historical transaction patterns
    Returns data for auto-complete functionality
    """
    
    # Get receivers with multiple transactions
    receiver_stats = Transaction.objects.values('receiver').annotate(
        count=Count('id'),
        avg_amount=Avg('amount'),
        total_amount=Sum('amount')
    ).filter(
        count__gte=2,  # Only receivers with 2+ transactions
        receiver__isnull=False
    ).order_by('-count')
    
    known_receivers = []
    
    for stat in receiver_stats[:100]:  # Top 100 receivers
        receiver = stat['receiver']
        
        # Get most common category for this receiver
        common_category = Transaction.objects.filter(
            receiver=receiver,
            category__isnull=False
        ).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        known_receivers.append({
            'name': receiver,
            'suggested_category': common_category['category__name'] if common_category else None,
            'avg_amount': float(stat['avg_amount']) if stat['avg_amount'] else 0,
            'transaction_count': stat['count'],
        })
    
    return known_receivers


def _get_category_averages():
    """
    Get average transaction amounts by category
    For real-time amount validation
    """
    
    averages = {}
    
    categories = BudgetCategory.objects.all()
    for category in categories:
        avg = Transaction.objects.filter(
            category=category
        ).aggregate(avg=Avg('amount'))['avg']
        
        if avg:
            averages[category.id] = float(avg)
    
    return averages


@require_http_methods(["GET"])
def api_suggest_category(request):
    """
    API endpoint to suggest category based on context
    
    Parameters:
    - receiver: Receiver name
    - department_id: Department ID
    - amount: Transaction amount
    
    Returns:
    - suggested_category: Category object data
    - confidence: high/medium/low
    - reason: Why this category was suggested
    """
    
    receiver = request.GET.get('receiver', '').lower()
    department_id = request.GET.get('department_id')
    amount = request.GET.get('amount')
    
    if amount:
        try:
            amount = Decimal(amount)
        except:
            amount = None
    
    # Use the same logic from SmartTransactionForm
    suggestion = None
    
    # Pattern 1: Known vendors
    vendor_categories = {
        'kplc': 'Utilities',
        'safaricom': 'IT and Software',
        'kenya power': 'Utilities',
        'nairobi water': 'Utilities',
    }
    
    for vendor, category_name in vendor_categories.items():
        if vendor in receiver:
            try:
                category = BudgetCategory.objects.get(name=category_name)
                return JsonResponse({
                    'suggested': True,
                    'category': {
                        'id': category.id,
                        'name': category.name
                    },
                    'confidence': 'high',
                    'reason': f'Known vendor: {vendor}'
                })
            except BudgetCategory.DoesNotExist:
                pass
    
    # Pattern 2: Department + Amount
    if department_id and amount:
        try:
            from accounts.models import Department
            dept = Department.objects.get(id=department_id)
            
            if dept.name == 'HR Department' and 1000 <= amount <= 50000:
                category = BudgetCategory.objects.get(name='Salaries and Wages')
                return JsonResponse({
                    'suggested': True,
                    'category': {
                        'id': category.id,
                        'name': category.name
                    },
                    'confidence': 'high',
                    'reason': 'HR Department + Salary range ($1K-$50K)'
                })
        except:
            pass
    
    # No strong suggestion
    return JsonResponse({
        'suggested': False,
        'message': 'No strong suggestion available'
    })


@require_http_methods(["GET"])
def api_validate_amount(request):
    """
    API endpoint to validate if amount is unusual for category
    
    Parameters:
    - category_id: Category ID
    - amount: Transaction amount
    
    Returns:
    - is_unusual: Boolean
    - average: Average amount for this category
    - message: Validation message
    """
    
    category_id = request.GET.get('category_id')
    amount = request.GET.get('amount')
    
    if not category_id or not amount:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        amount = Decimal(amount)
        category = BudgetCategory.objects.get(id=category_id)
        
        # Get average for this category
        avg_amount = Transaction.objects.filter(
            category=category
        ).aggregate(avg=Avg('amount'))['avg']
        
        if not avg_amount:
            return JsonResponse({
                'is_unusual': False,
                'message': 'No historical data for this category'
            })
        
        # Check if amount is more than 3x average
        is_unusual = amount > avg_amount * 3
        
        return JsonResponse({
            'is_unusual': is_unusual,
            'average': float(avg_amount),
            'category_name': category.name,
            'message': (
                f'This amount (${amount}) is unusually high for {category.name}. '
                f'Average is ${avg_amount:.2f}.'
            ) if is_unusual else 'Amount looks normal for this category'
        })
        
    except BudgetCategory.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_receiver_suggestions(request):
    """
    API endpoint for receiver auto-complete suggestions
    
    Parameters:
    - q: Query string (partial receiver name)
    
    Returns:
    - List of matching receivers with their patterns
    """
    
    query = request.GET.get('q', '').lower()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get receivers matching query
    matching_receivers = Transaction.objects.filter(
        receiver__icontains=query
    ).values('receiver').annotate(
        count=Count('id'),
        avg_amount=Avg('amount')
    ).order_by('-count')[:10]
    
    suggestions = []
    
    for match in matching_receivers:
        receiver = match['receiver']
        
        # Get most common category
        common_cat = Transaction.objects.filter(
            receiver=receiver,
            category__isnull=False
        ).values('category__id', 'category__name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        suggestions.append({
            'name': receiver,
            'suggested_category': common_cat['category__name'] if common_cat else None,
            'suggested_category_id': common_cat['category__id'] if common_cat else None,
            'avg_amount': float(match['avg_amount']) if match['avg_amount'] else 0,
            'transaction_count': match['count']
        })
    
    return JsonResponse({'suggestions': suggestions})

