"""
Enhanced Budget Views for CODA Finance System

Provides comprehensive budget management views including:
- Multi-timeframe budget estimation (weekly, monthly, yearly)
- Multi-year planning (1-year, 2-year, 5-year plans)
- Investment planning and funding analysis
- CODA development cost estimation
- Budget consolidation and reporting
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

from main.models import Company
from accounts.models import Department
from finance.models import Budget, CodaBudget, BudgetCategory, BudgetSubCategory
from finance.services.budget.estimation import BudgetEstimationService as EnhancedBudgetEstimationService
from finance.services.budget.consolidation import BudgetConsolidationService
from .utils.calculation_utils import CalculationUtils
from .utils.filter_utils import FilterUtils

User = get_user_model()


@login_required
def enhanced_budget_dashboard(request, company_slug="coda"):
    """
    Enhanced budget dashboard with multi-timeframe planning
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    # Initialize services
    estimation_service = EnhancedBudgetEstimationService()
    consolidation_service = BudgetConsolidationService()
    calculation_utils = CalculationUtils()
    filter_utils = FilterUtils()
    
    # Get departments for filtering
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        if department_id:
            selected_department = Department.objects.get(id=department_id)
    
    # Get budget estimates for different timeframes
    weekly_estimate = estimation_service.estimate_weekly_budget(
        company=company,
        department=selected_department,
        weeks=4
    )
    
    monthly_estimate = estimation_service.estimate_monthly_budget(
        company=company,
        department=selected_department,
        months=3
    )
    
    yearly_estimate = estimation_service.estimate_yearly_budget(
        company=company,
        department=selected_department,
        years=1
    )
    
    # Get multi-year plans
    multi_year_plans = {
        '1_year': estimation_service.create_multi_year_plan(
            company=company,
            department=selected_department,
            plan_years=1
        ),
        '2_year': estimation_service.create_multi_year_plan(
            company=company,
            department=selected_department,
            plan_years=2
        ),
        '5_year': estimation_service.create_multi_year_plan(
            company=company,
            department=selected_department,
            plan_years=5
        )
    }
    
    # Get consolidated report
    consolidated_report = consolidation_service.get_unified_budget_report(
        company=company,
        department=selected_department
    )
    
    # Get investment analysis
    investment_analysis = estimation_service.analyze_investment_opportunities(
        company=company,
        department=selected_department
    )
    
    context = {
        'company': company,
        'departments': departments,
        'selected_department': selected_department,
        'weekly_estimate': weekly_estimate,
        'monthly_estimate': monthly_estimate,
        'yearly_estimate': yearly_estimate,
        'multi_year_plans': multi_year_plans,
        'consolidated_report': consolidated_report,
        'investment_analysis': investment_analysis,
    }
    
    return render(request, "finance/budgets/enhanced_budget_dashboard.html", context)


@login_required
def weekly_budget_planning(request, company_slug="coda"):
    """
    Weekly budget planning view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        weeks = int(request.POST.get("weeks", 4))
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get weekly estimate
        weekly_estimate = estimation_service.estimate_weekly_budget(
            company=company,
            department=selected_department,
            weeks=weeks
        )
        
        # Get historical weekly data for comparison
        historical_data = estimation_service.get_historical_weekly_data(
            company=company,
            department=selected_department,
            weeks=weeks * 2  # Get more historical data for comparison
        )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'weekly_estimate': weekly_estimate,
            'historical_data': historical_data,
            'analysis_weeks': weeks,
        }
        
        return render(request, "finance/budgets/weekly_planning.html", context)
    
    context = {
        'company': company,
        'departments': departments,
    }
    
    return render(request, "finance/budgets/weekly_planning.html", context)


@login_required
def monthly_budget_planning(request, company_slug="coda"):
    """
    Monthly budget planning view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        months = int(request.POST.get("months", 3))
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get monthly estimate
        monthly_estimate = estimation_service.estimate_monthly_budget(
            company=company,
            department=selected_department,
            months=months
        )
        
        # Get historical monthly data for comparison
        historical_data = estimation_service.get_historical_monthly_data(
            company=company,
            department=selected_department,
            months=months * 2
        )
        
        # Get monthly trends
        trends = estimation_service.analyze_monthly_trends(
            company=company,
            department=selected_department,
            months=months
        )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'monthly_estimate': monthly_estimate,
            'historical_data': historical_data,
            'trends': trends,
            'analysis_months': months,
        }
        
        return render(request, "finance/budgets/monthly_planning.html", context)
    
    context = {
        'company': company,
        'departments': departments,
    }
    
    return render(request, "finance/budgets/monthly_planning.html", context)


@login_required
def yearly_budget_planning(request, company_slug="coda"):
    """
    Yearly budget planning view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        years = int(request.POST.get("years", 1))
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get yearly estimate
        yearly_estimate = estimation_service.estimate_yearly_budget(
            company=company,
            department=selected_department,
            years=years
        )
        
        # Get historical yearly data for comparison
        historical_data = estimation_service.get_historical_yearly_data(
            company=company,
            department=selected_department,
            years=years * 2
        )
        
        # Get yearly trends and growth analysis
        growth_analysis = estimation_service.analyze_yearly_growth(
            company=company,
            department=selected_department,
            years=years
        )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'yearly_estimate': yearly_estimate,
            'historical_data': historical_data,
            'growth_analysis': growth_analysis,
            'analysis_years': years,
        }
        
        return render(request, "finance/budgets/yearly_planning.html", context)
    
    context = {
        'company': company,
        'departments': departments,
    }
    
    return render(request, "finance/budgets/yearly_planning.html", context)


@login_required
def multi_year_planning(request, company_slug="coda"):
    """
    Multi-year budget planning view (1-year, 2-year, 5-year plans)
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    departments = Department.objects.all()
    selected_department = None
    plan_years = 5  # Default to 5-year plan
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        plan_years = int(request.POST.get("plan_years", 5))
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get multi-year plan
        multi_year_plan = estimation_service.create_multi_year_plan(
            company=company,
            department=selected_department,
            plan_years=plan_years
        )
        
        # Get investment analysis
        investment_analysis = estimation_service.analyze_investment_opportunities(
            company=company,
            department=selected_department
        )
        
        # Get funding recommendations
        funding_recommendations = estimation_service.get_funding_recommendations(
            company=company,
            department=selected_department,
            investment_amount=multi_year_plan.get('total_investment_required', 0)
        )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'multi_year_plan': multi_year_plan,
            'investment_analysis': investment_analysis,
            'funding_recommendations': funding_recommendations,
            'plan_years': plan_years,
        }
        
        return render(request, "finance/budgets/multi_year_planning.html", context)
    
    context = {
        'company': company,
        'departments': departments,
        'plan_years': plan_years,
    }
    
    return render(request, "finance/budgets/multi_year_planning.html", context)


@login_required
def coda_development_estimation(request, company_slug="coda"):
    """
    CODA development cost estimation view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    
    if request.method == "POST":
        app_models_count = int(request.POST.get("app_models_count", 0))
        custom_hourly_rate = request.POST.get("custom_hourly_rate")
        
        if custom_hourly_rate:
            custom_tasks = {
                "createview": {"hour": 10, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "updateview": {"hour": 5, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "listview": {"hour": 3, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "detailview": {"hour": 3, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "deleteview": {"hour": 2, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "template": {"hour": 5, "quantity": 3, "unit_price": float(custom_hourly_rate)},
                "form": {"hour": 4, "quantity": 1, "unit_price": float(custom_hourly_rate)},
                "api": {"hour": 10, "quantity": 3, "unit_price": float(custom_hourly_rate)},
            }
        else:
            custom_tasks = None
        
        # Get development cost estimation
        development_estimate = estimation_service.estimate_coda_development_cost(
            app_models_count=app_models_count,
            custom_tasks=custom_tasks
        )
        
        # Get project timeline estimation
        timeline_estimate = estimation_service.estimate_project_timeline(
            app_models_count=app_models_count,
            development_estimate=development_estimate
        )
        
        context = {
            'company': company,
            'development_estimate': development_estimate,
            'timeline_estimate': timeline_estimate,
            'app_models_count': app_models_count,
            'custom_hourly_rate': custom_hourly_rate,
        }
        
        return render(request, "finance/budgets/coda_development_estimation.html", context)
    
    context = {
        'company': company,
    }
    
    return render(request, "finance/budgets/coda_development_estimation.html", context)


@login_required
def investment_planning(request, company_slug="coda"):
    """
    Investment planning and funding analysis view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    estimation_service = EnhancedBudgetEstimationService()
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        investment_type = request.POST.get("investment_type", "all")
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get investment analysis
        investment_analysis = estimation_service.analyze_investment_opportunities(
            company=company,
            department=selected_department,
            investment_type=investment_type
        )
        
        # Get funding recommendations
        funding_recommendations = estimation_service.get_funding_recommendations(
            company=company,
            department=selected_department
        )
        
        # Get ROI analysis
        roi_analysis = estimation_service.analyze_roi_potential(
            company=company,
            department=selected_department
        )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'investment_analysis': investment_analysis,
            'funding_recommendations': funding_recommendations,
            'roi_analysis': roi_analysis,
            'investment_type': investment_type,
        }
        
        return render(request, "finance/budgets/investment_planning.html", context)
    
    context = {
        'company': company,
        'departments': departments,
    }
    
    return render(request, "finance/budgets/investment_planning.html", context)


@login_required
@require_http_methods(["POST"])
def create_budget_from_estimation(request, company_slug="coda"):
    """
    Create budget from estimation data
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=400)
    
    try:
        data = json.loads(request.body)
        
        # Create budget from estimation data
        budget = Budget.objects.create(
            company=company,
            department_id=data.get('department_id'),
            budget_lead=request.user,
            category_id=data.get('category_id'),
            subcategory_id=data.get('subcategory_id'),
            item=data.get('item_name'),
            description=data.get('description'),
            cases=data.get('cases', 1),
            qty=data.get('quantity', 1),
            unit_price=data.get('unit_price', 0),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            receipt_link=data.get('receipt_link'),
        )
        
        return JsonResponse({
            'success': True,
            'budget_id': budget.id,
            'message': 'Budget created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def budget_consolidation_report(request, company_slug="coda"):
    """
    Budget consolidation report view
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("some_error_view")
    
    consolidation_service = BudgetConsolidationService()
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        report_type = request.POST.get("report_type", "unified")
        
        if department_id:
            selected_department = Department.objects.get(id=department_id)
        
        # Get consolidation report
        if report_type == "unified":
            report = consolidation_service.get_unified_budget_report(
                company=company,
                department=selected_department
            )
        elif report_type == "comparative":
            report = consolidation_service.get_comparative_budget_report(
                company=company,
                department=selected_department
            )
        elif report_type == "variance":
            report = consolidation_service.get_budget_variance_report(
                company=company,
                department=selected_department
            )
        else:
            report = consolidation_service.get_unified_budget_report(
                company=company,
                department=selected_department
            )
        
        context = {
            'company': company,
            'departments': departments,
            'selected_department': selected_department,
            'report': report,
            'report_type': report_type,
        }
        
        return render(request, "finance/budgets/consolidation_report.html", context)
    
    context = {
        'company': company,
        'departments': departments,
    }
    
    return render(request, "finance/budgets/consolidation_report.html", context)
