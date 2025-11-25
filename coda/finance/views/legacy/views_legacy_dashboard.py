"""
Enhanced Legacy Finance Dashboard Views

Provides an enhanced version of the legacy finance dashboard that incorporates
all the original links while adding modern features from our consolidated template system.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal

from shared_core.models import Company
from shared_core.users import Department
from finance.models import Budget, Transaction, Inflow, BudgetRequest, DisbursementRequest
from finance.services.budget.estimation import BudgetEstimationService


@login_required
def enhanced_legacy_dashboard(request, company_slug="coda"):
    """
    Enhanced Legacy Finance Dashboard
    
    Combines the original legacy dashboard layout with modern features
    from our consolidated template system.
    """
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Company not found")
        return redirect("main:dashboard")
    
    # Get user's department
    user_department = None
    if hasattr(request.user, 'department'):
        user_department = request.user.department
    
    # Calculate quick stats for the dashboard
    stats = _calculate_quick_stats(company, user_department)
    
    # Get recent activity
    recent_activity = _get_recent_activity(company, user_department)
    
    # Get financial health indicators
    financial_health = _get_financial_health_indicators(company, user_department)
    
    context = {
        'company': company,
        'user_department': user_department,
        'total_budget': stats['total_budget'],
        'total_inflow': stats['total_inflow'],
        'total_outflow': stats['total_outflow'],
        'active_budgets': stats['active_budgets'],
        'recent_activity': recent_activity,
        'financial_health': financial_health,
        'page_title': 'Finance Department Dashboard',
    }
    
    return render(request, "finance/enhanced_legacy_dashboard.html", context)


def _calculate_quick_stats(company, department=None):
    """Calculate quick statistics for the dashboard"""
    # Base queries
    budget_query = Budget.objects.filter(company=company)
    inflow_query = Inflow.objects.filter(company=company)
    
    # Transaction query - filter by department since Transaction doesn't have company field
    if department:
        transaction_query = Transaction.objects.filter(department=department)
        budget_query = budget_query.filter(department=department)
        inflow_query = inflow_query.filter(department=department)
    else:
        # If no specific department, get all transactions
        transaction_query = Transaction.objects.all()
    
    # Calculate totals
    # For Budget model, we need to calculate total_amount using the property
    total_budget = Decimal('0.00')
    for budget in budget_query:
        total_budget += budget.total_amount
    
    total_inflow = inflow_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_outflow = transaction_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    active_budgets = budget_query.filter(status='active').count()
    
    return {
        'total_budget': total_budget,
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'active_budgets': active_budgets,
    }


def _get_recent_activity(company, department=None):
    """Get recent activity for the dashboard"""
    recent_activity = {
        'budget_requests': [],
        'disbursements': [],
        'transactions': [],
    }
    
    # Recent budget requests
    if department:
        recent_activity['budget_requests'] = list(
            BudgetRequest.objects.filter(department=department)
            .order_by('-created_at')[:5]
            .values('id', 'amount', 'purpose', 'status', 'created_at')
        )
        
        recent_activity['disbursements'] = list(
            DisbursementRequest.objects.filter(department=department)
            .order_by('-created_at')[:5]
            .values('id', 'amount', 'purpose', 'status', 'created_at')
        )
    
    # Recent transactions
    if department:
        transaction_query = Transaction.objects.filter(department=department)
    else:
        transaction_query = Transaction.objects.all()
    
    recent_activity['transactions'] = list(
        transaction_query.order_by('-transaction_date')[:10]
        .values('id', 'receiver', 'amount', 'transaction_date', 'category__name')
    )
    
    return recent_activity


def _get_financial_health_indicators(company, department=None):
    """Get financial health indicators"""
    # Calculate basic financial health metrics
    stats = _calculate_quick_stats(company, department)
    
    # Calculate net cash flow
    net_cash_flow = stats['total_inflow'] - stats['total_outflow']
    
    # Calculate budget utilization
    budget_utilization = 0
    if stats['total_budget'] > 0:
        actual_spent = Budget.objects.filter(
            company=company,
            department=department
        ).aggregate(Sum('actual_spent'))['actual_spent__sum'] or Decimal('0.00')
        budget_utilization = (actual_spent / stats['total_budget']) * 100
    
    # Determine health status
    health_status = "Good"
    if net_cash_flow < 0:
        health_status = "Poor"
    elif budget_utilization > 90:
        health_status = "Warning"
    elif budget_utilization > 75:
        health_status = "Fair"
    
    return {
        'net_cash_flow': net_cash_flow,
        'budget_utilization': budget_utilization,
        'health_status': health_status,
        'total_budget': stats['total_budget'],
        'total_inflow': stats['total_inflow'],
        'total_outflow': stats['total_outflow'],
    }


@login_required
def legacy_dashboard_redirect(request):
    """
    Redirect to the enhanced legacy dashboard
    """
    return redirect('finance:enhanced-legacy-dashboard', company_slug='coda')
