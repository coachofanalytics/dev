"""
Smart Form API endpoints for auto-populating budget request fields
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from finance.services.smart_form_service import SmartFormService
from finance.models import Budget, BudgetCategory, Transaction
from django.utils import timezone
from datetime import timedelta

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def get_form_suggestions(request):
    """
    API endpoint to get smart form suggestions based on purpose and department
    """
    try:
        data = json.loads(request.body)
        purpose = data.get('purpose', '')
        department_name = data.get('department', '')
        amount = data.get('amount')
        
        service = SmartFormService()
        suggestions = service.suggest_fields(purpose, department_name, amount)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def get_department_defaults(request):
    """
    API endpoint to get smart defaults for a department
    """
    try:
        department_name = request.GET.get('department', '')
        service = SmartFormService()
        defaults = service.get_smart_defaults(department_name)
        
        return JsonResponse({
            'success': True,
            'defaults': defaults
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def item_lookup(request):
    """Lightweight lookup to find existing items and suggest fields.
    q: free-text query (item name or description)
    category_id (optional): narrow search to a category
    Returns: { suggestions: [ {source, confidence, item_name, category, subcategory, suggested_amount} ] }
    """
    try:
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category')
        if not query:
            return JsonResponse({'success': True, 'suggestions': []})

        suggestions = []

        # 1) Match existing Budget items
        budget_qs = Budget.objects.filter(item_name__icontains=query)
        if category_id:
            budget_qs = budget_qs.filter(category_id=category_id)
        budget_qs = budget_qs.select_related('category', 'subcategory')[:5]
        for b in budget_qs:
            # Use estimated_amount if present; otherwise compute from unit components
            if b.estimated_amount is not None:
                est = b.estimated_amount
            elif b.unit_price and b.quantity and (b.cases or 1):
                est = b.unit_price * b.quantity * (b.cases or 1)
            else:
                est = None
            suggestions.append({
                'source': 'budget',
                'confidence': 0.9,
                'item_name': b.item_name,
                'category': b.category.name if b.category else None,
                'subcategory': b.subcategory.name if b.subcategory else None,
                'suggested_amount': float(est) if est is not None else None,
            })

        # 2) Infer from Transactions (recent 12 months)
        now = timezone.now().date()
        year_ago = now - timedelta(days=365)
        tx_qs = Transaction.objects.filter(
            transaction_date__gte=year_ago,
        ).filter(
            Q(description__icontains=query) | Q(vendor_supplier__username__icontains=query) | Q(receiver__icontains=query)
        ).select_related('category')[:200]

        # Accumulate by subcategory text label (Transaction.subcategory is string)
        subcat_to_total = {}
        for t in tx_qs:
            label = (t.subcategory or '').strip() or None
            if not label:
                continue
            subcat_to_total[label] = subcat_to_total.get(label, 0) + float(t.amount or 0)

        # Convert to monthly average suggestion
        for label, total in list(subcat_to_total.items())[:5]:
            monthly = total / 12.0
            suggestions.append({
                'source': 'transactions',
                'confidence': 0.7,
                'item_name': query,
                'category': None,
                'subcategory': label,
                'suggested_amount': round(monthly, 2),
            })

        return JsonResponse({'success': True, 'suggestions': suggestions[:10]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
