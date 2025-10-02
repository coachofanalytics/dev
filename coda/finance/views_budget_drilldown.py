"""
Budget Drill-Down Views for User Perspective

Allows users to:
1. Click on category in budget overview
2. See detailed breakdown
3. Edit individual budget items
4. View transaction history
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse

from main.models import Company
from accounts.models import Department  
from finance.models import Budget, BudgetCategory, BudgetSubCategory, Transaction


@login_required
def budget_category_detail(request, company_slug, category_id):
    """
    Detailed view of a specific budget category
    Shows all budget items in this category and allows editing
    """
    company = get_object_or_404(Company, slug=company_slug)
    category = get_object_or_404(BudgetCategory, id=category_id)
    
    # Get all budget items in this category
    budget_items = Budget.objects.filter(
        company=company,
        category=category,
        is_active=True
    ).select_related(
        'department', 'subcategory', 'budget_lead'
    ).order_by('department', 'subcategory')
    
    # Calculate totals
    total_amount = budget_items.aggregate(
        total=Sum(
            F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
            output_field=DecimalField()
        )
    )['total'] or 0
    
    # Get transaction history for this category
    transactions = Transaction.objects.filter(
        category=category
    ).select_related(
        'department', 'subcategory'
    ).order_by('-transaction_date')[:20]  # Last 20
    
    # Calculate transaction totals
    transaction_total = transactions.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get breakdown by subcategory
    by_subcategory = budget_items.values(
        'subcategory__name'
    ).annotate(
        count=Count('id'),
        total=Sum(
            F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
            output_field=DecimalField()
        )
    ).order_by('-total')
    
    context = {
        'company': company,
        'category': category,
        'budget_items': budget_items,
        'total_amount': total_amount,
        'item_count': budget_items.count(),
        'transactions': transactions,
        'transaction_total': transaction_total,
        'by_subcategory': by_subcategory,
        'can_edit': request.user.is_staff,  # or custom permission
    }
    
    return render(request, 'finance/budgets/category_detail.html', context)


@login_required
def budget_item_edit(request, item_id):
    """
    Quick edit for a budget item
    """
    budget_item = get_object_or_404(Budget, id=item_id)
    
    if request.method == 'POST':
        # Update fields
        budget_item.quantity = request.POST.get('quantity', budget_item.quantity)
        budget_item.unit_price = request.POST.get('unit_price', budget_item.unit_price)
        budget_item.cases = request.POST.get('cases', budget_item.cases)
        budget_item.description = request.POST.get('description', budget_item.description)
        budget_item.save()
        
        messages.success(request, f'Updated: {budget_item.item_name}')
        
        # Return JSON if AJAX
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'total_amount': float(budget_item.total_amount)
            })
        
        return redirect('finance:budget-category-detail', 
                       company_slug=budget_item.company.slug,
                       category_id=budget_item.category.id)
    
    context = {
        'budget_item': budget_item,
    }
    
    return render(request, 'finance/budgets/item_edit.html', context)


@login_required
def budget_comparison_view(request, company_slug, category_id):
    """
    Compare budget vs actual spending for a category
    Shows variance and trends
    """
    company = get_object_or_404(Company, slug=company_slug)
    category = get_object_or_404(BudgetCategory, id=category_id)
    
    # Get budgeted amount
    budgeted = Budget.objects.filter(
        company=company,
        category=category,
        is_active=True
    ).aggregate(
        total=Sum(
            F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
            output_field=DecimalField()
        )
    )['total'] or 0
    
    # Get actual spending
    actual = Transaction.objects.filter(
        category=category
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Calculate variance
    variance = actual - budgeted
    variance_pct = (variance / budgeted * 100) if budgeted > 0 else 0
    
    # Get monthly breakdown
    from django.db.models.functions import TruncMonth
    
    monthly_actual = Transaction.objects.filter(
        category=category
    ).annotate(
        month=TruncMonth('transaction_date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')
    
    context = {
        'company': company,
        'category': category,
        'budgeted': budgeted,
        'actual': actual,
        'variance': variance,
        'variance_pct': variance_pct,
        'status': 'over_budget' if variance > 0 else 'under_budget',
        'monthly_actual': monthly_actual,
    }
    
    return render(request, 'finance/budgets/category_comparison.html', context)


