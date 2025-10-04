"""
Budget dashboard views - unified budget dashboard and planning views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import logging

from main.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetEstimateProjection
from ...services.budget.estimation import BudgetEstimationService
from ...services.budget.consolidation import BudgetConsolidationService

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetDashboardView(BaseFinanceView):
    """Base class for budget dashboard views."""
    
    def __init__(self):
        super().__init__()
        self.estimation_service = BudgetEstimationService()
        self.consolidation_service = BudgetConsolidationService()


@login_required_finance
@company_required
def unified_budget_dashboard(request, company_slug, company=None):
    """
    Unified budget dashboard with multiple tabs.
    
    Tabs:
    - Overview: Budget summary and category breakdown
    - Planning: Budget planning and estimation
    - Analytics: Budget analytics and projections
    - Estimation: AI-powered budget estimation
    """
    view = BudgetDashboardView()
    
    try:
        # Get company and user department
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get active tab from request
        active_tab = request.GET.get('tab', 'overview')
        
        # Initialize context
        context = {
            'company': company,
            'departments': company.departments.all() if hasattr(company, 'departments') else [],
            'selected_department': user_department,
            'active_tab': active_tab,
        }
        
        # Load tab-specific data
        if active_tab == 'overview':
            context.update(view._get_overview_tab_data(
                company, user_department, view.estimation_service, view.consolidation_service
            ))
        elif active_tab == 'planning':
            context.update(view._get_planning_tab_data(
                company, user_department, view.estimation_service
            ))
        elif active_tab == 'analytics':
            context.update(view._get_analytics_tab_data(
                company, user_department, view.consolidation_service
            ))
        elif active_tab == 'estimation':
            context.update(view._get_estimation_tab_data(
                company, user_department, view.estimation_service
            ))
        else:
            context['active_tab'] = 'overview'
            context.update(view._get_overview_tab_data(
                company, user_department, view.estimation_service, view.consolidation_service
            ))
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget dashboard")
        context['error'] = str(e)
    
    return render(request, 'finance/budgets/unified_dashboard.html', context)


def _get_overview_tab_data(self, company, department, estimation_service, consolidation_service):
    """Get data for Overview tab."""
    try:
        # Build budget filter
        budget_filter = Q(company=company)
        if department:
            budget_filter &= Q(department=department)
        
        # Get budget summary by category
        category_summary = {}
        categories = BudgetCategory.objects.all()
        
        for category in categories:
            cat_budgets = Budget.objects.filter(
                budget_filter, category=category
            )
            if cat_budgets.exists():
                category_summary[category.name] = {
                    'count': cat_budgets.count(),
                    'total': sum(
                        b.total_amount for b in cat_budgets 
                        if hasattr(b, 'total_amount')
                    ),
                    'category_id': category.id
                }
        
        # Recent budgets
        recent_budgets = Budget.objects.filter(budget_filter).order_by('-created_at')[:10]
        
        # Budget statistics
        total_budgets = Budget.objects.filter(budget_filter).count()
        total_estimated = Budget.objects.filter(budget_filter).aggregate(
            total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        total_actual = Budget.objects.filter(budget_filter).aggregate(
            total=Sum('actual_spent')
        )['total'] or Decimal('0.00')
        
        total_variance = total_actual - total_estimated
        
        return {
            'overview_data': {
                'category_summary': category_summary,
                'recent_budgets': recent_budgets,
                'statistics': {
                    'total_budgets': total_budgets,
                    'total_estimated': total_estimated,
                    'total_actual': total_actual,
                    'total_variance': total_variance,
                    'variance_percentage': (total_variance / total_estimated * 100) if total_estimated > 0 else 0,
                }
            }
        }
    
    except Exception as e:
        self.log_error("Error getting overview data", e)
        return {'overview_data': {'error': str(e)}}


def _get_planning_tab_data(self, company, department, estimation_service):
    """Get data for Planning tab."""
    try:
        # Get budget categories for planning
        categories = BudgetCategory.objects.all()
        
        # Get recent projections
        recent_projections = BudgetEstimateProjection.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        return {
            'planning_data': {
                'categories': categories,
                'recent_projections': recent_projections,
            }
        }
    
    except Exception as e:
        self.log_error("Error getting planning data", e)
        return {'planning_data': {'error': str(e)}}


def _get_analytics_tab_data(self, company, department, consolidation_service):
    """Get data for Analytics tab."""
    try:
        # Get budget analytics
        analytics_data = consolidation_service.get_budget_analytics(company, department)
        
        return {
            'analytics_data': analytics_data
        }
    
    except Exception as e:
        self.log_error("Error getting analytics data", e)
        return {'analytics_data': {'error': str(e)}}


def _get_estimation_tab_data(self, company, department, estimation_service):
    """Get data for Estimation tab."""
    try:
        # Get estimation options
        estimation_options = estimation_service.get_estimation_options(company)
        
        return {
            'estimation_data': {
                'options': estimation_options,
            }
        }
    
    except Exception as e:
        self.log_error("Error getting estimation data", e)
        return {'estimation_data': {'error': str(e)}}


# Add methods to the class
BudgetDashboardView._get_overview_tab_data = _get_overview_tab_data
BudgetDashboardView._get_planning_tab_data = _get_planning_tab_data
BudgetDashboardView._get_analytics_tab_data = _get_analytics_tab_data
BudgetDashboardView._get_estimation_tab_data = _get_estimation_tab_data


@login_required_finance
@company_required
def budget_planning_view(request, company_slug, company=None):
    """
    Budget planning view for creating and managing budget plans.
    """
    view = BudgetDashboardView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get planning data
        planning_data = view._get_planning_tab_data(
            company, user_department, view.estimation_service
        )
        
        context = {
            'company': company,
            'departments': company.departments.all() if hasattr(company, 'departments') else [],
            'selected_department': user_department,
            **planning_data
        }
        
        return render(request, 'finance/budgets/unified_planning.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget planning")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@require_http_methods(["GET"])
@login_required_finance
def budget_dashboard_api(request, company_slug):
    """
    API endpoint for budget dashboard data.
    """
    view = BudgetDashboardView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        user_department = view.get_user_department(request, company)
        
        # Get overview data
        overview_data = view._get_overview_tab_data(
            company, user_department, view.estimation_service, view.consolidation_service
        )
        
        return json_response(overview_data)
    
    except Exception as e:
        view.log_error("Error in budget dashboard API", e)
        return error_json_response("Internal server error", 500)
