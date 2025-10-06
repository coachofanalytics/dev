"""
Budget approval views - budget approval workflows and management.
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
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, ApprovalPolicy

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetApprovalView(BaseFinanceView):
    """Base class for budget approval views."""
    
    def __init__(self):
        super().__init__()


@login_required_finance
@company_required
def budget_approval_dashboard(request, company_slug, company=None):
    """
    Budget approval dashboard showing pending and processed approvals.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get pending approvals
        pending_requests = BudgetRequest.objects.filter(
            company=company,
            status='pending'
        ).select_related('requested_by', 'category', 'subcategory')
        
        # Get recent approvals
        recent_approvals = BudgetRequest.objects.filter(
            company=company,
            status__in=['approved', 'rejected']
        ).select_related('requested_by', 'category', 'subcategory').order_by('-updated_at')[:10]
        
        # Get approval statistics
        approval_stats = {
            'pending_count': pending_requests.count(),
            'approved_count': BudgetRequest.objects.filter(company=company, status='approved').count(),
            'rejected_count': BudgetRequest.objects.filter(company=company, status='rejected').count(),
            'total_requests': BudgetRequest.objects.filter(company=company).count(),
        }
        
        context = {
            'company': company,
            'user_department': user_department,
            'pending_requests': pending_requests,
            'recent_approvals': recent_approvals,
            'approval_stats': approval_stats,
        }
        
        return render(request, 'finance/budgets/approval_dashboard.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget approval dashboard")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def budget_approval_detail(request, company_slug, request_id, company=None):
    """
    Detailed view of a budget approval request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Get related budgets
        related_budgets = Budget.objects.filter(
            company=company,
            category=budget_request.category
        ).select_related('subcategory', 'budget_lead')
        
        context = {
            'company': company,
            'budget_request': budget_request,
            'related_budgets': related_budgets,
        }
        
        return render(request, 'finance/budgets/approval_detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget approval detail")
        return redirect('finance:budget-approval-dashboard', company_slug=company_slug)


@require_http_methods(["POST"])
@login_required_finance
@company_required
def approve_budget_request(request, company_slug, request_id, company=None):
    """
    Approve a budget request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Check if user has permission to approve
        if not view._can_approve_budget(request.user, budget_request):
            return error_json_response("Insufficient permissions to approve this request", 403)
        
        # Approve the request
        budget_request.approve(request.user)
        
        return json_response({
            'success': True,
            'message': 'Budget request approved successfully',
            'request_id': budget_request.id,
            'status': budget_request.status
        })
    
    except Exception as e:
        view.log_error("Error approving budget request", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["POST"])
@login_required_finance
@company_required
def reject_budget_request(request, company_slug, request_id, company=None):
    """
    Reject a budget request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Check if user has permission to reject
        if not view._can_approve_budget(request.user, budget_request):
            return error_json_response("Insufficient permissions to reject this request", 403)
        
        # Get rejection reason
        rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
        
        # Reject the request
        budget_request.reject(request.user, rejection_reason)
        
        return json_response({
            'success': True,
            'message': 'Budget request rejected successfully',
            'request_id': budget_request.id,
            'status': budget_request.status
        })
    
    except Exception as e:
        view.log_error("Error rejecting budget request", e)
        return error_json_response("Internal server error", 500)


def _can_approve_budget(self, user, budget_request):
    """Check if user can approve this budget request."""
    try:
        # Check if user is in the same department or is a manager
        if hasattr(user, 'profile') and user.profile.department:
            user_department = user.profile.department
            if budget_request.department == user_department:
                return True
        
        # Check if user is a manager or admin
        if user.is_staff or user.is_superuser:
            return True
        
        # Check approval policies
        approval_policies = ApprovalPolicy.objects.filter(
            company=budget_request.company,
            category=budget_request.category
        )
        
        for policy in approval_policies:
            if policy.can_approve(user, budget_request.amount):
                return True
        
        return False
    
    except Exception as e:
        self.log_error("Error checking approval permissions", e)
        return False


# Add method to the class
BudgetApprovalView._can_approve_budget = _can_approve_budget


@require_http_methods(["GET"])
@login_required_finance
def budget_approval_api(request, company_slug):
    """
    API endpoint for budget approval data.
    """
    view = BudgetApprovalView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        # Get approval data
        pending_requests = BudgetRequest.objects.filter(
            company=company,
            status='pending'
        ).values('id', 'title', 'amount', 'category__name', 'requested_by__username', 'created_at')
        
        approval_stats = {
            'pending_count': BudgetRequest.objects.filter(company=company, status='pending').count(),
            'approved_count': BudgetRequest.objects.filter(company=company, status='approved').count(),
            'rejected_count': BudgetRequest.objects.filter(company=company, status='rejected').count(),
        }
        
        data = {
            'pending_requests': list(pending_requests),
            'approval_stats': approval_stats,
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in budget approval API", e)
        return error_json_response("Internal server error", 500)



