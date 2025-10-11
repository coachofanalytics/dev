"""
Budget drill-down views - detailed views for budget categories and items.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import logging

from main.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetItemLibrary, Transaction

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetDrillDownView(BaseFinanceView):
    """Base class for budget drill-down views."""
    
    def __init__(self):
        super().__init__()
    
    def _get_budget_comparison_data(self, company, category, comparison_type, period_count):
        """Get budget comparison data for different periods."""
        try:
            from datetime import datetime, timedelta
            from dateutil.relativedelta import relativedelta
            
            comparison_data = []
            current_date = timezone.now().date()
            
            for i in range(period_count):
                if comparison_type == 'monthly':
                    period_start = current_date - relativedelta(months=i+1)
                    period_end = current_date - relativedelta(months=i)
                    period_name = period_start.strftime('%B %Y')
                elif comparison_type == 'quarterly':
                    quarter_start = (current_date.month - 1) // 3 * 3 + 1
                    period_start = current_date.replace(month=quarter_start, day=1) - relativedelta(months=3*i+3)
                    period_end = current_date.replace(month=quarter_start, day=1) - relativedelta(months=3*i)
                    period_name = "Q{} {}".format(((period_start.month - 1) // 3) + 1, period_start.year)
                else:  # yearly
                    period_start = current_date.replace(month=1, day=1) - relativedelta(years=i+1)
                    period_end = current_date.replace(month=1, day=1) - relativedelta(years=i)
                    period_name = str(period_start.year)
                
                # Get budgets for this period
                budgets = Budget.objects.filter(
                    company=company,
                    category=category,
                    start_date__gte=period_start,
                    end_date__lte=period_end
                )
                
                # Calculate totals
                total_estimated = sum(budget.estimated_amount for budget in budgets)
                total_actual = sum(budget.actual_spent for budget in budgets)
                total_variance = total_actual - total_estimated
                
                comparison_data.append({
                    'period_name': period_name,
                    'period_start': period_start,
                    'period_end': period_end,
                    'total_estimated': total_estimated,
                    'total_actual': total_actual,
                    'total_variance': total_variance,
                    'variance_percentage': (total_variance / total_estimated * 100) if total_estimated > 0 else 0,
                    'budget_count': budgets.count(),
                })
            
            return comparison_data
        
        except Exception as e:
            self.log_error("Error getting budget comparison data", e)
            return []
    
    def _handle_budget_item_edit_post(self, request, company, budget):
        """Handle POST request for budget item editing."""
        try:
            # Update budget fields
            budget.item_name = request.POST.get('item_name', budget.item_name)
            budget.description = request.POST.get('description', budget.description)
            budget.estimated_amount = Decimal(request.POST.get('estimated_amount', budget.estimated_amount))
            budget.quantity = Decimal(request.POST.get('quantity', budget.quantity))
            budget.unit_price = Decimal(request.POST.get('unit_price', budget.unit_price))
            budget.cases = int(request.POST.get('cases', budget.cases))
            budget.notes = request.POST.get('notes', budget.notes)
            
            # Update dates if provided
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            if start_date:
                budget.start_date = start_date
            if end_date:
                budget.end_date = end_date
            
            budget.save()
            
            messages.success(request, "Budget item '{}' updated successfully.".format(budget.item_name))
            return redirect('finance:budget-item-edit', 
                           company_slug=company.slug, item_id=budget.id)
        
        except Exception as e:
            self.handle_error(request, e, "Error updating budget item")
            return redirect('finance:budget-item-edit', 
                           company_slug=company.slug, item_id=budget.id)


@login_required_finance
@company_required
def budget_category_detail(request, company_slug, category_id, company=None):
    """
    Detailed view of a budget category with subcategories and items.
    """
    view = BudgetDrillDownView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get category
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Get user department for filtering transactions
        user_department = view.get_user_department(request, company)
        
        # Get subcategories with budget data
        subcategories = BudgetSubCategory.objects.filter(
            category=category
        ).prefetch_related('items', 'sub_category_type')
        
        # Get budget data for each subcategory
        subcategory_data = []
        for subcategory in subcategories:
            budgets = Budget.objects.filter(
                company=company,
                subcategory=subcategory
            ).select_related('budget_lead')
            
            # Calculate totals (handle None values)
            total_estimated = sum(budget.estimated_amount or 0 for budget in budgets)
            total_actual = sum(budget.actual_spent or 0 for budget in budgets)
            total_variance = total_actual - total_estimated
            
            # Get recent transactions - filter by subcategory name
            transaction_filter = {'subcategory': subcategory.name}
            if user_department:
                transaction_filter['department'] = user_department
            
            recent_transactions = Transaction.objects.filter(
                **transaction_filter
            ).order_by('-transaction_date')[:5]
            
            subcategory_data.append({
                'subcategory': subcategory,
                'budgets': budgets,
                'total_estimated': total_estimated,
                'total_actual': total_actual,
                'total_variance': total_variance,
                'variance_percentage': (total_variance / total_estimated * 100) if total_estimated > 0 else 0,
                'recent_transactions': recent_transactions,
                'budget_count': budgets.count(),
            })
        
        # Get category-level statistics
        category_budgets = Budget.objects.filter(
            company=company,
            category=category
        )
        
        category_stats = {
            'total_budgets': category_budgets.count(),
            'total_estimated': sum(budget.estimated_amount or 0 for budget in category_budgets),
            'total_actual': sum(budget.actual_spent or 0 for budget in category_budgets),
            'average_amount': sum(budget.estimated_amount or 0 for budget in category_budgets) / category_budgets.count() if category_budgets.count() > 0 else 0,
        }
        
        context = {
            'company': company,
            'category': category,
            'subcategory_data': subcategory_data,
            'category_stats': category_stats,
        }
        
        return render(request, 'finance/budgets/budget_category_detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget category details")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def budget_comparison_view(request, company_slug, category_id, company=None):
    """
    Compare budget performance across different time periods or departments.
    """
    view = BudgetDrillDownView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get category
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Get comparison parameters
        comparison_type = request.GET.get('type', 'monthly')  # monthly, quarterly, yearly
        period_count = int(request.GET.get('periods', 6))
        
        # Get budget data for comparison
        comparison_data = view._get_budget_comparison_data(
            company, category, comparison_type, period_count
        )
        
        context = {
            'company': company,
            'category': category,
            'comparison_type': comparison_type,
            'period_count': period_count,
            'comparison_data': comparison_data,
        }
        
        return render(request, 'finance/budgets/budget_comparison.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget comparison")
        return redirect('finance:budget-category-detail', 
                       company_slug=company_slug, category_id=category_id)


@login_required_finance
@company_required
def budget_item_edit(request, company_slug, item_id, company=None):
    """
    Edit a specific budget item.
    """
    view = BudgetDrillDownView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget item
        budget = get_object_or_404(
            Budget,
            id=item_id,
            company=company
        )
        
        # Handle form submission
        if request.method == 'POST':
            return view._handle_budget_item_edit_post(request, company, budget)
        
        # Get user department for filtering transactions
        user_department = view.get_user_department(request, company)
        
        # Get related data - filter by department since Transaction doesn't have company field
        transaction_filter = {
            'budget_category': budget.category,
            'budget_subcategory': budget.subcategory
        }
        if user_department:
            transaction_filter['department'] = user_department
            
        recent_transactions = Transaction.objects.filter(
            **transaction_filter
        ).order_by('-transaction_date')[:10]
        
        context = {
            'company': company,
            'budget': budget,
            'recent_transactions': recent_transactions,
        }
        
        return render(request, 'finance/budgets/budget_item_edit.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget item edit")
        return redirect('finance:budget-category-detail', 
                       company_slug=company_slug, category_id=budget.category.id)




@require_http_methods(["GET"])
@login_required_finance
def budget_category_api(request, company_slug, category_id):
    """
    API endpoint for budget category data.
    """
    view = BudgetDrillDownView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        # Get category
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Get budget data
        budgets = Budget.objects.filter(
            company=company,
            category=category
        ).select_related('subcategory', 'budget_lead')
        
        # Calculate totals
        total_estimated = sum(budget.estimated_amount for budget in budgets)
        total_actual = sum(budget.actual_spent for budget in budgets)
        total_variance = total_actual - total_estimated
        
        data = {
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
            },
            'statistics': {
                'total_budgets': budgets.count(),
                'total_estimated': float(total_estimated),
                'total_actual': float(total_actual),
                'total_variance': float(total_variance),
                'variance_percentage': float((total_variance / total_estimated * 100) if total_estimated > 0 else 0),
            },
            'budgets': [
                {
                    'id': budget.id,
                    'item_name': budget.item_name,
                    'subcategory': budget.subcategory.name,
                    'estimated_amount': float(budget.estimated_amount),
                    'actual_spent': float(budget.actual_spent),
                    'variance': float(budget.variance),
                    'status': budget.status,
                }
                for budget in budgets
            ]
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in budget category API", e)
        return error_json_response("Internal server error", 500)
