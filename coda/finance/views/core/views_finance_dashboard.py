"""
Finance Dashboard Views for CODA Finance System

Provides a comprehensive finance dashboard with:
- Investment information and analysis
- Budget overview and planning
- Transaction summaries
- Financial health metrics
- Multi-year planning integration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

from main.models import Company
from accounts.models import Department
from finance.models import (
    Budget, Transaction, Inflow, CodaBudget, 
    BudgetCategory, BudgetSubCategory, BudgetEstimationTemplate, 
    MultiYearBudgetPlan, BudgetRequest, DisbursementRequest
)
from finance.services.budget.estimation import BudgetEstimationService as EnhancedBudgetEstimationService
from finance.services.budget.consolidation import BudgetConsolidationService
from finance.utils.calculation_utils import CalculationUtils
from finance.utils.filter_utils import FilterUtils

User = get_user_model()


@login_required
def finance_dashboard(request, company_slug="coda"):
    """
    Comprehensive Finance Dashboard with Investment and Finance information
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("main:dashboard")
    
    # Initialize services
    estimation_service = EnhancedBudgetEstimationService()
    consolidation_service = BudgetConsolidationService()
    calculation_utils = CalculationUtils()
    filter_utils = FilterUtils()
    
    # Get departments
    departments = Department.objects.all()
    
    # Get current user's department
    user_department = None
    if hasattr(request.user, 'department'):
        user_department = request.user.department
    
    # Financial Overview Metrics
    financial_metrics = get_financial_metrics(company, user_department)
    
    # Budget Analysis
    budget_analysis = get_budget_analysis(company, user_department)
    
    # Investment Analysis
    investment_analysis = estimation_service.analyze_investment_opportunities(company, user_department)
    
    # Transaction Analysis
    transaction_analysis = get_transaction_analysis(company, user_department)
    
    # Multi-year Planning Overview
    multi_year_plans = MultiYearBudgetPlan.objects.filter(is_active=True).order_by('-created_at')[:3]
    
    # Recent Budget Requests
    recent_requests = BudgetRequest.objects.filter(
        department=user_department
    ).order_by('-created_at')[:5] if user_department else []
    
    # Recent Disbursements
    recent_disbursements = DisbursementRequest.objects.filter(
        department=user_department
    ).order_by('-created_at')[:5] if user_department else []
    
    # Budget Categories Performance
    category_performance = get_category_performance(company, user_department)
    
    # Financial Health Score
    health_score = calculate_financial_health_score(financial_metrics, budget_analysis, transaction_analysis)
    
    context = {
        'company': company,
        'departments': departments,
        'user_department': user_department,
        'financial_metrics': financial_metrics,
        'budget_analysis': budget_analysis,
        'investment_analysis': investment_analysis,
        'transaction_analysis': transaction_analysis,
        'multi_year_plans': multi_year_plans,
        'recent_requests': recent_requests,
        'recent_disbursements': recent_disbursements,
        'category_performance': category_performance,
        'health_score': health_score,
    }
    
    return render(request, "finance/unified_finance_dashboard.html", context)


def get_financial_metrics(company, department=None):
    """Get key financial metrics for the dashboard"""
    try:
        # Total Budget Amount
        budget_query = Budget.objects.filter(company=company)
        if department:
            budget_query = budget_query.filter(department=department)
        
        total_budget = budget_query.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Actual Spent
        actual_spent = budget_query.aggregate(
            total=Sum('actual_spent')
        )['total'] or Decimal('0.00')
        
        # Total Transactions
        transaction_query = Transaction.objects.filter(company=company)
        if department:
            transaction_query = transaction_query.filter(department=department)
        
        total_transactions = transaction_query.count()
        total_transaction_amount = transaction_query.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Budget Variance
        variance = actual_spent - total_budget
        variance_percentage = (variance / total_budget * 100) if total_budget > 0 else 0
        
        # Active Budgets
        active_budgets = budget_query.filter(status='active').count()
        
        # Over Budget Count
        from django.db import models
        over_budget_count = budget_query.filter(
            actual_spent__gt=models.F('total_amount')
        ).count()
        
        return {
            'total_budget': total_budget,
            'actual_spent': actual_spent,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'total_transactions': total_transactions,
            'total_transaction_amount': total_transaction_amount,
            'active_budgets': active_budgets,
            'over_budget_count': over_budget_count,
            'budget_utilization': (actual_spent / total_budget * 100) if total_budget > 0 else 0
        }
    except Exception as e:
        return {'error': str(e)}


def get_budget_analysis(company, department=None):
    """Get budget analysis for the dashboard"""
    try:
        budget_query = Budget.objects.filter(company=company)
        if department:
            budget_query = budget_query.filter(department=department)
        
        # Budget by Type
        budget_by_type = {}
        for budget_type, _ in Budget.BUDGET_TYPE_CHOICES:
            type_budgets = budget_query.filter(budget_type=budget_type)
            budget_by_type[budget_type] = {
                'count': type_budgets.count(),
                'total_amount': type_budgets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                'actual_spent': type_budgets.aggregate(total=Sum('actual_spent'))['total'] or Decimal('0.00')
            }
        
        # Budget by Timeframe
        budget_by_timeframe = {}
        for timeframe, _ in Budget.TIMEFRAME_CHOICES:
            timeframe_budgets = budget_query.filter(timeframe=timeframe)
            budget_by_timeframe[timeframe] = {
                'count': timeframe_budgets.count(),
                'total_amount': timeframe_budgets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            }
        
        # Investment Budgets
        investment_budgets = budget_query.filter(is_investment=True)
        total_investment = investment_budgets.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        return {
            'budget_by_type': budget_by_type,
            'budget_by_timeframe': budget_by_timeframe,
            'total_investment': total_investment,
            'investment_count': investment_budgets.count()
        }
    except Exception as e:
        return {'error': str(e)}


def get_transaction_analysis(company, department=None):
    """Get transaction analysis for the dashboard"""
    try:
        transaction_query = Transaction.objects.filter(company=company)
        if department:
            transaction_query = transaction_query.filter(department=department)
        
        # Last 30 days
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = transaction_query.filter(transaction_date__gte=thirty_days_ago)
        
        # Transaction trends
        monthly_totals = {}
        for i in range(6):  # Last 6 months
            month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)
            month_transactions = transaction_query.filter(
                transaction_date__gte=month_start,
                transaction_date__lt=month_end
            )
            month_total = month_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            monthly_totals[month_start.strftime('%Y-%m')] = month_total
        
        # Top Categories
        category_totals = transaction_query.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        return {
            'recent_transactions_count': recent_transactions.count(),
            'recent_transactions_amount': recent_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'monthly_totals': monthly_totals,
            'top_categories': list(category_totals),
            'average_transaction': transaction_query.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
        }
    except Exception as e:
        return {'error': str(e)}


def get_category_performance(company, department=None):
    """Get budget category performance analysis"""
    try:
        budget_query = Budget.objects.filter(company=company)
        if department:
            budget_query = budget_query.filter(department=department)
        
        categories = BudgetCategory.objects.all()
        category_data = []
        
        for category in categories:
            category_budgets = budget_query.filter(category=category)
            total_budget = category_budgets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            actual_spent = category_budgets.aggregate(total=Sum('actual_spent'))['total'] or Decimal('0.00')
            variance = actual_spent - total_budget
            variance_percentage = (variance / total_budget * 100) if total_budget > 0 else 0
            
            category_data.append({
                'category': category,
                'total_budget': total_budget,
                'actual_spent': actual_spent,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'budget_count': category_budgets.count(),
                'utilization': (actual_spent / total_budget * 100) if total_budget > 0 else 0
            })
        
        return sorted(category_data, key=lambda x: x['total_budget'], reverse=True)
    except Exception as e:
        return []


def calculate_financial_health_score(metrics, budget_analysis, transaction_analysis):
    """Calculate overall financial health score (0-100)"""
    try:
        score = 100
        
        # Budget variance penalty
        if metrics.get('variance_percentage', 0) > 10:
            score -= 20
        elif metrics.get('variance_percentage', 0) > 5:
            score -= 10
        
        # Over budget penalty
        if metrics.get('over_budget_count', 0) > 0:
            score -= metrics['over_budget_count'] * 5
        
        # Budget utilization bonus/penalty
        utilization = metrics.get('budget_utilization', 0)
        if utilization > 90:
            score -= 15  # Over-utilization
        elif utilization < 50:
            score -= 10  # Under-utilization
        elif 70 <= utilization <= 90:
            score += 10  # Good utilization
        
        # Transaction consistency bonus
        if transaction_analysis.get('recent_transactions_count', 0) > 10:
            score += 5
        
        return max(0, min(100, score))
    except Exception as e:
        return 50  # Default neutral score


@login_required
def finance_dashboard_api(request, company_slug="coda"):
    """
    API endpoint for finance dashboard data
    """
    try:
        company = Company.objects.get(slug=company_slug)
        
        # Get department filter
        department_id = request.GET.get('department_id')
        department = None
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        
        # Get financial metrics
        financial_metrics = get_financial_metrics(company, department)
        budget_analysis = get_budget_analysis(company, department)
        transaction_analysis = get_transaction_analysis(company, department)
        
        return JsonResponse({
            'success': True,
            'financial_metrics': financial_metrics,
            'budget_analysis': budget_analysis,
            'transaction_analysis': transaction_analysis,
            'department': department.name if department else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
