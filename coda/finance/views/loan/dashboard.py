"""
Loan dashboard views - loan overview and management.
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

from shared_core.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import LoanApplication, LoanProduct, Budget, BudgetCategory

logger = logging.getLogger(__name__)
User = get_user_model()


class LoanDashboardView(BaseFinanceView):
    """Base class for loan dashboard views."""
    
    def __init__(self):
        super().__init__()


@login_required_finance
@company_required
def loan_dashboard(request, company_slug, company=None):
    """
    Loan dashboard showing loan overview and statistics.
    """
    view = LoanDashboardView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get loan statistics
        loan_stats = view._get_loan_statistics(company, user_department)
        
        # Get recent loan applications
        recent_applications = LoanApplication.objects.filter(
            borrower=request.user
        ).select_related('loan_product').order_by('-created_at')[:10]
        
        # Get available loan products
        available_products = LoanProduct.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Get loan performance data
        performance_data = view._get_loan_performance_data(company, user_department)
        
        context = {
            'company': company,
            'user_department': user_department,
            'loan_stats': loan_stats,
            'recent_applications': recent_applications,
            'available_products': available_products,
            'performance_data': performance_data,
        }
        
        return render(request, 'finance/loans/dashboard.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading loan dashboard")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


def _get_loan_statistics(self, company, department):
    """Get loan statistics for the dashboard."""
    try:
        # Base query for loans
        loan_query = LoanApplication.objects.filter(borrower__profile__department__company=company)
        
        if department:
            loan_query = loan_query.filter(borrower__profile__department=department)
        
        # Calculate statistics
        total_loans = loan_query.count()
        total_amount = loan_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        avg_amount = loan_query.aggregate(Avg('amount'))['amount__avg'] or Decimal('0.00')
        
        # Status breakdown
        status_breakdown = loan_query.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Recent activity
        recent_loans = loan_query.order_by('-created_at')[:5]
        
        return {
            'total_loans': total_loans,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_breakdown': list(status_breakdown),
            'recent_loans': recent_loans,
        }
    
    except Exception as e:
        self.log_error("Error getting loan statistics", e)
        return {
            'total_loans': 0,
            'total_amount': Decimal('0.00'),
            'avg_amount': Decimal('0.00'),
            'status_breakdown': [],
            'recent_loans': [],
        }


def _get_loan_performance_data(self, company, department):
    """Get loan performance data for charts."""
    try:
        # Get loan performance by month
        from django.db.models.functions import TruncMonth
        
        performance_query = LoanApplication.objects.filter(
            borrower__profile__department__company=company
        )
        
        if department:
            performance_query = performance_query.filter(borrower__profile__department=department)
        
        monthly_performance = performance_query.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month')
        
        return {
            'monthly_performance': list(monthly_performance),
        }
    
    except Exception as e:
        self.log_error("Error getting loan performance data", e)
        return {
            'monthly_performance': [],
        }


# Add methods to the class
LoanDashboardView._get_loan_statistics = _get_loan_statistics
LoanDashboardView._get_loan_performance_data = _get_loan_performance_data


@require_http_methods(["GET"])
@login_required_finance
def loan_dashboard_api(request, company_slug):
    """
    API endpoint for loan dashboard data.
    """
    view = LoanDashboardView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        user_department = view.get_user_department(request, company)
        
        # Get loan statistics
        loan_stats = view._get_loan_statistics(company, user_department)
        performance_data = view._get_loan_performance_data(company, user_department)
        
        data = {
            'loan_stats': loan_stats,
            'performance_data': performance_data,
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in loan dashboard API", e)
        return error_json_response("Internal server error", 500)



