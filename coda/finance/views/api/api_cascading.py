"""
API endpoints for cascading form data
Provides filtered data for Category → Subcategory → Item dropdowns
"""
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
from finance.models import BudgetCategory, BudgetSubCategory, BudgetItemLibrary, Transaction, Budget, CodaBudget
from main.models import Company
from decimal import Decimal


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
    Get items from BudgetItemLibrary filtered by category and/or subcategory
    
    Now uses predefined item library (500+ items) instead of historical data
    Falls back to transaction history if no library items found
    
    Usage: /api/items/?category_id=5&subcategory_id=10
    """
    category_id = request.GET.get('category_id')
    subcategory_id = request.GET.get('subcategory_id')
    
    if not subcategory_id and not category_id:
        return JsonResponse({'error': 'category_id or subcategory_id required'}, status=400)
    
    try:
        # PRIMARY: Get items from BudgetItemLibrary
        filters = Q(is_active=True)
        
        if subcategory_id:
            filters &= Q(subcategory_id=subcategory_id)
        elif category_id:
            filters &= Q(category_id=category_id)
        
        library_items = BudgetItemLibrary.objects.filter(
            filters
        ).values(
            'id', 
            'item_name', 
            'typical_amount', 
            'unit_type', 
            'usage_count',
            'description'
        ).order_by('-usage_count', 'item_name')[:100]
        
        if library_items:
            # Return library items (preferred)
            items_list = [
                {
                    'id': item['id'],
                    'name': item['item_name'],
                    'typical_amount': float(item['typical_amount']) if item['typical_amount'] else None,
                    'unit_type': item['unit_type'],
                    'usage_count': item['usage_count'],
                    'description': item['description'],
                    'source': 'library'
                }
                for item in library_items
            ]
            
            return JsonResponse({
                'items': items_list,
                'count': len(items_list),
                'source': 'Budget Item Library',
                'filters': {
                    'category_id': category_id,
                    'subcategory_id': subcategory_id,
                }
            })
        
        # FALLBACK: Use historical transaction data if no library items
        filters = Q()
        if category_id:
            filters &= Q(category_id=category_id)
        if subcategory_id:
            filters &= Q(subcategory_id=subcategory_id)
        
        # Get items from Transaction history
        transaction_items = Transaction.objects.filter(
            filters
        ).exclude(
            type__isnull=True
        ).exclude(
            type=''
        ).values('type').annotate(
            count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-count')[:30]
        
        items_list = [
            {
                'name': item['type'],
                'typical_amount': float(item['avg_amount']) if item['avg_amount'] else None,
                'usage_count': item['count'],
                'source': 'historical'
            }
            for item in transaction_items
        ]
        
        return JsonResponse({
            'items': items_list,
            'count': len(items_list),
            'source': 'Historical Transactions (Fallback)',
            'message': 'No library items found. Showing historical data. Consider populating item library.',
            'filters': {
                'category_id': category_id,
                'subcategory_id': subcategory_id,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


@csrf_exempt
@require_http_methods(["POST"])
def generate_budget_projections_api(request):
    """
    API endpoint to generate budget projections
    
    POST /api/generate-budget-projections/
    Body: {
        "company_slug": "coda",
        "projection_months": 12,
        "save": true
    }
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        company_slug = data.get('company_slug', 'coda')
        projection_months = data.get('projection_months', 12)
        save = data.get('save', True)
        
        # Get company
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Company {company_slug} not found'
            }, status=404)
        
        # Import the management command
        from finance.management.commands.generate_budget_projections import Command as GenerateBudgetCommand
        from io import StringIO
        from django.core.management import call_command
        
        # Create command instance
        cmd = GenerateBudgetCommand()
        
        # Capture output
        output = StringIO()
        
        # Call the management command
        try:
            call_command(
                'generate_budget_projections',
                company=company_slug,
                projection_months=projection_months,
                save=save,
                stdout=output
            )
            
            # Parse output to get results
            output_text = output.getvalue()
            
            # Get actual data from the database after generation
            from finance.models import Budget, BudgetCategory
            from django.db.models import Sum, Count, F, DecimalField
            from django.db.models.functions import Coalesce
            
            # Calculate actual totals from generated budgets
            budget_totals = Budget.objects.filter(
                company=company,
                is_active=True
            ).aggregate(
                total_annual=Sum(
                    F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                    output_field=DecimalField()
                ),
                count=Count('id')
            )
            
            # Get category breakdown
            category_breakdown = {}
            for category in BudgetCategory.objects.all():
                cat_total = Budget.objects.filter(
                    company=company,
                    category=category,
                    is_active=True
                ).aggregate(
                    total=Sum(
                        F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                        output_field=DecimalField()
                    )
                )['total'] or 0
                
                if cat_total > 0:
                    category_breakdown[category.name] = float(cat_total)
            
            total_annual = float(budget_totals['total_annual'] or 0)
            monthly_average = total_annual / 12 if total_annual > 0 else 0
            
            result = {
                'success': True,
                'message': 'Budget projections generated successfully',
                'total_annual': total_annual,
                'monthly_average': monthly_average,
                'categories_count': len(category_breakdown),
                'breakdown': category_breakdown,
                'projections_created': budget_totals['count']
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': f'Command execution failed: {str(e)}'
            }
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Budget projections generated successfully',
                'total_annual': result['total_annual'],
                'monthly_average': result['monthly_average'],
                'categories_count': result['categories_count'],
                'projections_created': result['projections_created']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def inline_set_subcategory_budget(request):
    """Create or update a simple monthly Budget item for a subcategory (inline edit)."""
    try:
        data = json.loads(request.body)
        company_slug = data.get('company_slug')
        category_id = data.get('category_id')
        subcategory_id = data.get('subcategory_id')
        amount_kes = Decimal(str(data.get('amount_kes', 0)))

        company = Company.objects.get(slug=company_slug)
        category = BudgetCategory.objects.get(id=category_id)
        subcategory = BudgetSubCategory.objects.get(id=subcategory_id) if subcategory_id else None

        # Upsert a simple monthly item
        item_name = f"{subcategory.name if subcategory else 'General'} - Inline"
        budget, _ = Budget.objects.update_or_create(
            company=company,
            category=category,
            subcategory=subcategory,
            item_name=item_name,
            defaults={
                'unit_price': amount_kes,
                'quantity': Decimal('1'),
                'cases': 1,
                'timeframe': 'monthly',
                'status': 'draft',
                'is_active': False,
            }
        )

        return JsonResponse({'success': True, 'budget_id': budget.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def bulk_apply_strategy(request):
    """Apply a planning strategy across all subcategories for a company (or a single category).
    Body: { company_slug, category_id (optional), strategy: 'last_month'|'avg_3m'|'avg_12m' }
    """
    try:
        data = json.loads(request.body)
        company_slug = data.get('company_slug')
        category_id = data.get('category_id')
        strategy = data.get('strategy', 'avg_3m')

        company = Company.objects.get(slug=company_slug)
        cat_qs = BudgetCategory.objects.all()
        # Coerce category_id to integer if provided and valid
        if category_id is not None:
            try:
                cat_qs = cat_qs.filter(id=int(category_id))
            except (TypeError, ValueError):
                # If a non-numeric came in (e.g., a name), fall back to name lookup
                cat_qs = BudgetCategory.objects.filter(name=str(category_id))

        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        one_month_ago = today - timedelta(days=30)
        three_months_ago = today - timedelta(days=90)
        twelve_months_ago = today - timedelta(days=365)

        created_or_updated = 0
        for category in cat_qs:
            subcats = BudgetSubCategory.objects.filter(category=category)
            for sc in subcats:
                try:
                    base_qs = Transaction.objects.filter(subcategory=sc.name)
                    if strategy == 'last_month':
                        total = sum(t.amount or 0 for t in base_qs.filter(transaction_date__gte=one_month_ago))
                        monthly = total
                    elif strategy == 'avg_12m':
                        total = sum(t.amount or 0 for t in base_qs.filter(transaction_date__gte=twelve_months_ago))
                        monthly = (total / 12) if total else 0
                    else:  # avg_3m default
                        total = sum(t.amount or 0 for t in base_qs.filter(transaction_date__gte=three_months_ago))
                        monthly = (total / 3) if total else 0

                    if monthly and monthly > 0:
                        # Ensure we're passing proper instances
                        if not isinstance(category, BudgetCategory):
                            raise ValueError(f"category is not a BudgetCategory instance: {type(category)} = {category}")
                        if not isinstance(sc, BudgetSubCategory):
                            raise ValueError(f"subcategory is not a BudgetSubCategory instance: {type(sc)} = {sc}")
                        
                        budget, _ = Budget.objects.update_or_create(
                            company=company,
                            category=category,
                            subcategory=sc,
                            item_name=f"{sc.name} - Planning",
                            defaults={
                                'unit_price': Decimal(str(monthly)),
                                'quantity': Decimal('1'),
                                'cases': 1,
                                'timeframe': 'monthly',
                                'status': 'draft',
                                'is_active': False,
                                'estimation_method': 'planning_strategy',
                            }
                        )
                        created_or_updated += 1
                except Exception as e:
                    # Log but don't fail entire bulk operation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"bulk_apply_strategy error for {category.name if hasattr(category, 'name') else category}/{sc.name if hasattr(sc, 'name') else sc}: {type(e).__name__}: {e}")
                    continue

        return JsonResponse({'success': True, 'items_applied': created_or_updated})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'{type(e).__name__}: {e}'}, status=400)

