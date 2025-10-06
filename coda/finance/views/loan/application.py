"""
Loan application views - loan application management and processing.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import logging

from main.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import LoanApplication, LoanProduct, Budget, BudgetCategory
from ...services.loan_service import LoanService

logger = logging.getLogger(__name__)
User = get_user_model()


class LoanApplicationView(BaseFinanceView):
    """Base class for loan application views."""
    
    def __init__(self):
        super().__init__()
        self.loan_service = LoanService()


@login_required_finance
@company_required
def loan_application_list(request, company_slug, company=None):
    """
    List all loan applications for the user.
    """
    view = LoanApplicationView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get user's loan applications
        loan_applications = LoanApplication.objects.filter(
            borrower=request.user
        ).select_related('loan_product').order_by('-created_at')
        
        # Get application statistics
        app_stats = {
            'total_applications': loan_applications.count(),
            'pending_applications': loan_applications.filter(status='pending').count(),
            'approved_applications': loan_applications.filter(status='approved').count(),
            'rejected_applications': loan_applications.filter(status='rejected').count(),
        }
        
        context = {
            'company': company,
            'user_department': user_department,
            'loan_applications': loan_applications,
            'app_stats': app_stats,
        }
        
        return render(request, 'finance/loans/application_list.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading loan applications")
        return redirect('finance:loan-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def loan_application_detail(request, company_slug, application_id, company=None):
    """
    Detailed view of a loan application.
    """
    view = LoanApplicationView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get loan application
        loan_application = get_object_or_404(
            LoanApplication,
            id=application_id,
            borrower=request.user
        )
        
        # Get related budget information
        related_budgets = Budget.objects.filter(
            company=company,
            category__name__icontains='loan'
        ).select_related('category', 'subcategory')
        
        context = {
            'company': company,
            'loan_application': loan_application,
            'related_budgets': related_budgets,
        }
        
        return render(request, 'finance/loans/application_detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading loan application detail")
        return redirect('finance:loan-application-list', company_slug=company_slug)


@login_required_finance
@company_required
def create_loan_application(request, company_slug, company=None):
    """
    Create a new loan application.
    """
    view = LoanApplicationView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        if request.method == 'POST':
            return view._handle_loan_application_post(request, company, user_department)
        
        # Get available loan products
        available_products = LoanProduct.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Get user's eligibility
        eligibility = view.loan_service.check_eligibility(request.user, company)
        
        context = {
            'company': company,
            'user_department': user_department,
            'available_products': available_products,
            'eligibility': eligibility,
        }
        
        return render(request, 'finance/loans/create_application.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error creating loan application")
        return redirect('finance:loan-dashboard', company_slug=company_slug)


def _handle_loan_application_post(self, request, company, user_department):
    """Handle POST request for loan application creation."""
    try:
        # Get form data
        loan_product_id = request.POST.get('loan_product_id')
        amount = request.POST.get('amount')
        purpose = request.POST.get('purpose')
        repayment_period = request.POST.get('repayment_period')
        
        # Validate required fields
        if not all([loan_product_id, amount, purpose, repayment_period]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('finance:create-loan-application', company_slug=company.slug)
        
        # Get loan product
        loan_product = get_object_or_404(LoanProduct, id=loan_product_id, is_active=True)
        
        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid amount.")
            return redirect('finance:create-loan-application', company_slug=company.slug)
        
        # Check eligibility
        eligibility = self.loan_service.check_eligibility(request.user, company)
        if not eligibility.get('eligible', False):
            messages.error(request, "You are not eligible for a loan at this time.")
            return redirect('finance:create-loan-application', company_slug=company.slug)
        
        # Create loan application
        loan_application = LoanApplication.objects.create(
            borrower=request.user,
            loan_product=loan_product,
            amount=amount,
            purpose=purpose,
            repayment_period=int(repayment_period),
            status='pending',
            application_date=timezone.now()
        )
        
        messages.success(request, "Loan application submitted successfully. Application ID: {}".format(loan_application.id))
        return redirect('finance:loan-application-detail', 
                       company_slug=company.slug, application_id=loan_application.id)
    
    except Exception as e:
        self.handle_error(request, e, "Error processing loan application")
        return redirect('finance:create-loan-application', company_slug=company.slug)


# Add method to the class
LoanApplicationView._handle_loan_application_post = _handle_loan_application_post


@require_http_methods(["POST"])
@login_required_finance
@company_required
def cancel_loan_application(request, company_slug, application_id, company=None):
    """
    Cancel a loan application.
    """
    view = LoanApplicationView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get loan application
        loan_application = get_object_or_404(
            LoanApplication,
            id=application_id,
            borrower=request.user
        )
        
        # Check if application can be cancelled
        if loan_application.status not in ['pending', 'under_review']:
            return error_json_response("Application cannot be cancelled in current status", 400)
        
        # Cancel the application
        loan_application.status = 'cancelled'
        loan_application.cancelled_at = timezone.now()
        loan_application.cancelled_by = request.user
        loan_application.save()
        
        return json_response({
            'success': True,
            'message': 'Loan application cancelled successfully',
            'application_id': loan_application.id,
            'status': loan_application.status
        })
    
    except Exception as e:
        view.log_error("Error cancelling loan application", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["GET"])
@login_required_finance
def loan_application_api(request, company_slug):
    """
    API endpoint for loan application data.
    """
    view = LoanApplicationView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        # Get user's loan applications
        loan_applications = LoanApplication.objects.filter(
            borrower=request.user
        ).values('id', 'amount', 'purpose', 'status', 'created_at', 'loan_product__name')
        
        # Get application statistics
        app_stats = {
            'total_applications': LoanApplication.objects.filter(borrower=request.user).count(),
            'pending_applications': LoanApplication.objects.filter(borrower=request.user, status='pending').count(),
            'approved_applications': LoanApplication.objects.filter(borrower=request.user, status='approved').count(),
            'rejected_applications': LoanApplication.objects.filter(borrower=request.user, status='rejected').count(),
        }
        
        data = {
            'loan_applications': list(loan_applications),
            'app_stats': app_stats,
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in loan application API", e)
        return error_json_response("Internal server error", 500)



