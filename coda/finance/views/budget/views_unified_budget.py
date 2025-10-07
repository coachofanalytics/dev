"""
Unified Budget Views for CODA Finance System

Phase 3: Consolidates multiple budget views into unified dashboard and planning views.

Replaces:
- automated_budget_estimation (estimation tab)
- enhanced_budget_dashboard (planning tab)
- budget_consolidation_dashboard (overview tab)
- budget_projection (analytics tab)
- weekly/monthly/yearly_budget_planning (single view with parameter)

Created: October 2025
Phase: 3 - View Consolidation
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
from accounts.models import Department
from finance.models import (
    Budget, BudgetCategory, BudgetSubCategory, 
    BudgetEstimateProjection, MultiYearBudgetPlan,
    BudgetRequest, DisbursementRequest, Transaction
)
from finance.services.unified_budget_estimation_service import UnifiedBudgetEstimationService
from finance.services.budget.consolidation import BudgetConsolidationService
from finance.services.data_quality_service import DataQualityService
from .utils.calculation_utils import CalculationUtils
from .utils.filter_utils import FilterUtils

User = get_user_model()
logger = logging.getLogger(__name__)


@login_required
def unified_budget_dashboard(request, company_slug="coda"):
    """
    Unified Budget Dashboard with tabs for all budget operations
    
    Tabs:
    - overview: Budget summary and quick stats
    - estimation: AI-powered automated estimation
    - planning: Multi-timeframe budget planning
    - approvals: Budget request approvals
    - analytics: Budget analytics and trends
    
    Consolidates:
    - automated_budget_estimation view
    - enhanced_budget_dashboard view
    - budget_consolidation_dashboard view
    - budget_projection view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("main:dashboard")
    
    # Get active tab from request (default: overview)
    active_tab = request.GET.get('tab', 'overview')
    
    # Get departments for filtering
    departments = Department.objects.all()
    selected_department = None
    
    if request.GET.get('department_id'):
        try:
            selected_department = Department.objects.get(id=request.GET.get('department_id'))
        except Department.DoesNotExist:
            pass
    
    # Initialize services
    estimation_service = UnifiedBudgetEstimationService()
    consolidation_service = BudgetConsolidationService()
    calculation_utils = CalculationUtils()
    filter_utils = FilterUtils()
    
    # Base context
    context = {
        'company': company,
        'departments': departments,
        'selected_department': selected_department,
        'active_tab': active_tab,
        'page_title': 'Unified Budget Dashboard',
    }
    
    # Get tab-specific data
    try:
        if active_tab == 'overview':
            context.update(_get_overview_tab_data(
                company, selected_department, estimation_service, consolidation_service
            ))
        
        elif active_tab == 'estimation':
            context.update(_get_estimation_tab_data(
                company, selected_department, estimation_service
            ))
        
        elif active_tab == 'planning':
            context.update(_get_planning_tab_data(
                company, selected_department, estimation_service
            ))
        
        elif active_tab == 'approvals':
            context.update(_get_approvals_tab_data(
                company, selected_department, request.user
            ))
        
        elif active_tab == 'analytics':
            context.update(_get_analytics_tab_data(
                company, selected_department, estimation_service
            ))
        
        else:
            # Default to overview if invalid tab
            context['active_tab'] = 'overview'
            context.update(_get_overview_tab_data(
                company, selected_department, estimation_service, consolidation_service
            ))
    
    except Exception as e:
        logger.error(f"Error loading tab '{active_tab}': {e}", exc_info=True)
        messages.error(request, f"Error loading dashboard data: {str(e)}")
        context['error'] = str(e)
    
    return render(request, 'finance/budgets/unified_dashboard.html', context)


def _get_overview_tab_data(company, department, estimation_service, consolidation_service):
    """
    Get data for Overview tab
    
    Shows:
    - Quick stats (total budgets, active budgets, etc.)
    - Budget summary by category
    - Department breakdown
    - Recent activity
    """
    try:
        # Get consolidated report
        consolidated_report = consolidation_service.get_unified_budget_report(
            company=company,
            department=department
        )
        
        # Get quick stats
        budget_filter = Q(company=company, is_active=True)
        if department:
            budget_filter &= Q(department=department)
        
        total_budgets = Budget.objects.filter(budget_filter).count()
        active_budgets = Budget.objects.filter(budget_filter, status='active').count()
        
        # FIX: Calculate item_total for each budget FIRST, then sum
        # Wrong: Sum(quantity) * Sum(unit_price) multiplies totals
        # Right: Sum(quantity * unit_price * cases) for each item
        total_amount = Budget.objects.filter(budget_filter).aggregate(
            total=Sum(
                F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                output_field=DecimalField()
            )
        )
        
        # Category summary
        category_summary = {}
        for category in BudgetCategory.objects.all():
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
        
        return {
            'overview_data': {
                'total_budgets': total_budgets,
                'active_budgets': active_budgets,
                'total_amount': total_amount,
                'category_summary': category_summary,
                'recent_budgets': recent_budgets,
                'consolidated_report': consolidated_report,
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting overview data: {e}", exc_info=True)
        return {'overview_data': {'error': str(e)}}


def _get_estimation_tab_data(company, department, estimation_service):
    """
    Get data for Estimation tab
    
    Shows:
    - Automated budget estimation
    - Spending patterns analysis
    - Next month estimate
    - Variance analysis
    - Recommendations
    """
    try:
        # Spending patterns (3 months)
        spending_analysis = estimation_service.analyze_spending_patterns(
            company=company,
            department=department,
            months=3
        )
        
        # Next month estimate
        next_month_estimate = estimation_service.estimate_next_month_budget(
            company=company,
            department=department,
            method='average'
        )
        
        # Get quarterly estimate for comparison
        quarterly_estimate = estimation_service.estimate_budget(
            company=company,
            department=department,
            timeframe='quarterly',
            periods=1,
            method='average'
        )
        
        # Get annual estimate
        annual_estimate = estimation_service.estimate_annual_budget(
            company=company,
            department=department
        )
        
        # Budget variance analysis
        variance_data = _calculate_variance_analysis(company, department, next_month_estimate)
        
        # Generate recommendations
        recommendations = _generate_budget_recommendations(
            spending_analysis, next_month_estimate, variance_data
        )
        
        return {
            'estimation_data': {
                'spending_analysis': spending_analysis,
                'next_month_estimate': next_month_estimate,
                'quarterly_estimate': quarterly_estimate,
                'annual_estimate': annual_estimate,
                'variance_analysis': variance_data,
                'recommendations': recommendations,
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting estimation data: {e}", exc_info=True)
        return {'estimation_data': {'error': str(e)}}


def _get_planning_tab_data(company, department, estimation_service):
    """
    Get data for Planning tab
    
    Shows:
    - Weekly planning
    - Monthly planning
    - Quarterly planning
    - Yearly planning
    - Multi-year plans (1, 2, 5 years)
    """
    try:
        # Get all timeframe estimates
        weekly_estimate = estimation_service.estimate_weekly_budget(
            company=company,
            department=department,
            weeks=4
        )
        
        monthly_estimate = estimation_service.estimate_monthly_budget(
            company=company,
            department=department,
            months=3
        )
        
        quarterly_estimate = estimation_service.estimate_budget(
            company=company,
            department=department,
            timeframe='quarterly',
            periods=4,  # 4 quarters = 1 year
            method='average'
        )
        
        yearly_estimate = estimation_service.estimate_yearly_budget(
            company=company,
            department=department,
            years=1
        )
        
        # Multi-year plans
        multi_year_plans = {
            '1_year': estimation_service.create_multi_year_plan(
                company=company,
                department=department,
                plan_years=1
            ),
            '2_year': estimation_service.create_multi_year_plan(
                company=company,
                department=department,
                plan_years=2
            ),
            '5_year': estimation_service.create_multi_year_plan(
                company=company,
                department=department,
                plan_years=5
            )
        }
        
        # Get existing multi-year plans
        existing_plans = MultiYearBudgetPlan.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        return {
            'planning_data': {
                'weekly_estimate': weekly_estimate,
                'monthly_estimate': monthly_estimate,
                'quarterly_estimate': quarterly_estimate,
                'yearly_estimate': yearly_estimate,
                'multi_year_plans': multi_year_plans,
                'existing_plans': existing_plans,
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting planning data: {e}", exc_info=True)
        return {'planning_data': {'error': str(e)}}


def _get_approvals_tab_data(company, department, user):
    """
    Get data for Approvals tab
    
    Shows:
    - Pending budget requests
    - Pending disbursement requests
    - Approval history
    - User's submitted requests
    """
    try:
        # Pending budget requests
        pending_requests = BudgetRequest.objects.filter(
            status__in=['submitted', 'under_review']
        )
        
        if department:
            pending_requests = pending_requests.filter(department=department)
        
        # User's requests
        user_requests = BudgetRequest.objects.filter(
            requester=user
        ).order_by('-created_at')[:10]
        
        # Pending disbursements
        pending_disbursements = DisbursementRequest.objects.filter(
            status__in=['pending', 'under_review']
        )
        
        if department:
            pending_disbursements = pending_disbursements.filter(department=department)
        
        # Budget estimate projections awaiting approval
        pending_projections = BudgetEstimateProjection.objects.filter(
            company=company,
            status='submitted'
        )
        
        if department:
            pending_projections = pending_projections.filter(department=department)
        
        # Approval statistics
        total_pending = pending_requests.count() + pending_disbursements.count()
        user_pending = user_requests.filter(status__in=['submitted', 'under_review']).count()
        
        return {
            'approvals_data': {
                'pending_requests': pending_requests,
                'pending_disbursements': pending_disbursements,
                'pending_projections': pending_projections,
                'user_requests': user_requests,
                'total_pending': total_pending,
                'user_pending': user_pending,
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting approvals data: {e}", exc_info=True)
        return {'approvals_data': {'error': str(e)}}


def _get_analytics_tab_data(company, department, estimation_service):
    """
    Get data for Analytics tab
    
    Shows:
    - Budget vs actual spending
    - Trend analysis
    - Category performance
    - Department comparison
    - Historical trends
    """
    try:
        # Budget vs actual analysis
        budget_filter = Q(company=company, is_active=True)
        if department:
            budget_filter &= Q(department=department)
        
        budgets = Budget.objects.filter(budget_filter)
        
        # Category performance
        category_performance = []
        for category in BudgetCategory.objects.all():
            cat_budgets = budgets.filter(category=category)
            if cat_budgets.exists():
                total_budgeted = sum(
                    b.total_amount for b in cat_budgets 
                    if hasattr(b, 'total_amount')
                )
                total_actual = sum(
                    b.actual_spent for b in cat_budgets 
                    if hasattr(b, 'actual_spent')
                )
                
                category_performance.append({
                    'category': category.name,
                    'budgeted': float(total_budgeted),
                    'actual': float(total_actual),
                    'variance': float(total_budgeted - total_actual),
                    'variance_percentage': float((total_budgeted - total_actual) / total_budgeted * 100) if total_budgeted > 0 else 0,
                })
        
        # Department comparison (if no department filter)
        department_comparison = []
        if not department:
            for dept in Department.objects.all():
                dept_budgets = budgets.filter(department=dept)
                if dept_budgets.exists():
                    dept_total = sum(
                        b.total_amount for b in dept_budgets 
                        if hasattr(b, 'total_amount')
                    )
                    department_comparison.append({
                        'department': dept.name,
                        'total': float(dept_total),
                        'count': dept_budgets.count(),
                    })
        
        # Trend analysis (last 6 months)
        monthly_trends = []
        for i in range(6, 0, -1):
            month_start = timezone.now() - timezone.timedelta(days=30 * i)
            month_end = month_start + timezone.timedelta(days=30)
            
            month_budgets = budgets.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            )
            
            monthly_trends.append({
                'month': month_start.strftime('%b %Y'),
                'count': month_budgets.count(),
                'total': float(sum(
                    b.total_amount for b in month_budgets 
                    if hasattr(b, 'total_amount')
                ))
            })
        
        return {
            'analytics_data': {
                'category_performance': category_performance,
                'department_comparison': department_comparison,
                'monthly_trends': monthly_trends,
                'total_budgets': budgets.count(),
                'total_amount': sum(
                    b.total_amount for b in budgets 
                    if hasattr(b, 'total_amount')
                ),
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}", exc_info=True)
        return {'analytics_data': {'error': str(e)}}


def _calculate_variance_analysis(company, department, next_month_estimate):
    """Calculate budget variance analysis"""
    try:
        budget_filter = Q(company=company, is_active=True)
        if department:
            budget_filter &= Q(department=department)
        
        budgets = Budget.objects.filter(budget_filter)
        
        total_budgeted = sum(
            b.total_amount for b in budgets 
            if hasattr(b, 'total_amount')
        )
        total_actual = sum(
            b.actual_spent for b in budgets 
            if hasattr(b, 'actual_spent')
        )
        
        variance = total_budgeted - total_actual
        variance_percentage = (variance / total_budgeted * 100) if total_budgeted > 0 else 0
        
        return {
            'total_budgeted': float(total_budgeted),
            'total_actual': float(total_actual),
            'variance': float(variance),
            'variance_percentage': float(variance_percentage),
            'status': 'over_budget' if variance < 0 else 'under_budget' if variance > 0 else 'on_budget'
        }
    
    except Exception as e:
        logger.error(f"Error calculating variance: {e}", exc_info=True)
        return {'error': str(e)}


def _generate_budget_recommendations(spending_analysis, next_month_estimate, variance_data):
    """Generate intelligent budget recommendations"""
    recommendations = []
    
    try:
        # Check spending patterns
        if spending_analysis.get('total_estimate', 0) > 0:
            recommendations.append({
                'type': 'info',
                'title': 'Historical Data Available',
                'message': f'Analysis based on {spending_analysis.get("transaction_count", 0)} transactions'
            })
        
        # Check variance
        if variance_data.get('status') == 'over_budget':
            recommendations.append({
                'type': 'warning',
                'title': 'Over Budget Alert',
                'message': f'Currently {abs(variance_data.get("variance_percentage", 0)):.1f}% over budget'
            })
        elif variance_data.get('status') == 'under_budget':
            recommendations.append({
                'type': 'success',
                'title': 'Under Budget',
                'message': f'Currently {variance_data.get("variance_percentage", 0):.1f}% under budget'
            })
        
        # Confidence-based recommendations
        confidence = next_month_estimate.get('confidence_score', 0)
        if confidence < 0.7:
            recommendations.append({
                'type': 'info',
                'title': 'Low Confidence Estimate',
                'message': 'Limited historical data. Consider manual review.'
            })
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        return []


@login_required
def unified_budget_planning(request, company_slug="coda"):
    """
    Unified Budget Planning View with timeframe parameter
    
    Consolidates:
    - weekly_budget_planning view
    - monthly_budget_planning view
    - yearly_budget_planning view
    - multi_year_planning view
    
    Uses timeframe parameter instead of separate views
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("main:dashboard")
    
    # Get timeframe from request (default: monthly)
    timeframe = request.GET.get('timeframe', 'monthly')
    periods = int(request.GET.get('periods', 1))
    method = request.GET.get('method', 'average')
    
    # Validate timeframe
    valid_timeframes = ['weekly', 'monthly', 'quarterly', 'yearly', 'multi_year']
    if timeframe not in valid_timeframes:
        timeframe = 'monthly'
    
    # Get departments for filtering
    departments = Department.objects.all()
    selected_department = None
    
    if request.GET.get('department_id'):
        try:
            selected_department = Department.objects.get(id=request.GET.get('department_id'))
        except Department.DoesNotExist:
            pass
    
    # Initialize service
    estimation_service = UnifiedBudgetEstimationService()
    
    try:
        # Get estimate for selected timeframe
        estimate = estimation_service.estimate_budget(
            company=company,
            department=selected_department,
            timeframe=timeframe,
            periods=periods,
            method=method
        )
        
        # Get comparison estimates (for context)
        comparison_estimates = {}
        for tf in valid_timeframes:
            if tf != timeframe:
                comparison_estimates[tf] = estimation_service.estimate_budget(
                    company=company,
                    department=selected_department,
                    timeframe=tf,
                    periods=1,
                    method='average'
                )
        
        # Get data quality score (if available)
        try:
            quality_service = DataQualityService()
            if hasattr(quality_service, 'analyze_data_quality'):
                data_quality = quality_service.analyze_data_quality(
                    company=company,
                    department=selected_department
                )
            else:
                data_quality = {'score': 0.85, 'status': 'good'}  # Default
        except Exception as e:
            logger.warning(f"Data quality service not available: {e}")
            data_quality = {'score': 0.85, 'status': 'good'}
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'timeframe': timeframe,
            'periods': periods,
            'method': method,
            'estimate': estimate,
            'comparison_estimates': comparison_estimates,
            'data_quality': data_quality,
            'valid_timeframes': valid_timeframes,
            'valid_methods': ['average', 'trend', 'ai'],
        }
        
        return render(request, 'finance/budgets/unified_planning.html', context)
    
    except Exception as e:
        logger.error(f"Error in unified planning: {e}", exc_info=True)
        messages.error(request, f"Error loading planning data: {str(e)}")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)

