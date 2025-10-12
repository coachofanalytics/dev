"""
Budget editing views - budget editing and approval workflows.
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
from finance.views.core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from finance.models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, ApprovalPolicy
from finance.forms import forms as legacy_forms

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetEditingView(BaseFinanceView):
    """Base class for budget editing views."""
    
    def __init__(self):
        super().__init__()


@login_required_finance
@company_required
def budget_category_edit(request, company_slug, category_id, company=None):
    """
    Edit budget estimates for a specific category.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get category
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Get budgets for this category
        budgets = Budget.objects.filter(
            category=category
        ).select_related('subcategory', 'budget_lead')
        
        # Get subcategories for this category
        subcategories = BudgetSubCategory.objects.filter(category=category)
        
        # Handle form submission
        if request.method == 'POST':
            return view._handle_budget_edit_post(request, company, category, budgets)
        
        context = {
            'company': company,
            'category': category,
            'budgets': budgets,
            'subcategories': subcategories,
            'form': BudgetEditForm(),
        }
        
        return render(request, 'finance/budgets/budget_category_edit.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget edit page")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


def _handle_budget_edit_post(self, request, company, category, budgets):
    """Handle POST request for budget editing."""
    try:
        # Process budget updates
        updated_budgets = []
        
        for budget in budgets:
            budget_id = str(budget.id)
            estimated_amount = request.POST.get('estimated_amount_{}'.format(budget_id))
            
            if estimated_amount:
                try:
                    budget.estimated_amount = Decimal(estimated_amount)
                    budget.save(update_fields=['estimated_amount'])
                    updated_budgets.append(budget)
                except (ValueError, TypeError):
                    self.log_error("Invalid amount for budget {}: {}".format(budget.id, estimated_amount))
        
        # Create budget request if required
        if updated_budgets and request.POST.get('submit_for_approval'):
            budget_request = self._create_budget_request(
                request, company, category, updated_budgets
            )
            
            if budget_request:
                messages.success(
                    request, 
                    "Budget changes submitted for approval. Request ID: {}".format(budget_request.id)
                )
                return redirect('finance:budget-requests-list', company_slug=company_slug)
        
        messages.success(request, "Updated {} budget items.".format(len(updated_budgets)))
        return redirect('finance:budget-category-edit', company_slug=company_slug, category_id=category.id)
    
    except Exception as e:
        self.handle_error(request, e, "Error updating budgets")
        return redirect('finance:budget-category-edit', company_slug=company_slug, category_id=category.id)


def _create_budget_request(self, request, company, category, updated_budgets):
    """Create a budget request for approval."""
    try:
        # Calculate total amount
        total_amount = sum(budget.estimated_amount for budget in updated_budgets)
        
        # Create budget request
        budget_request = BudgetRequest.objects.create(
            purpose="Budget Update - {}".format(category.name),
            budget_category=category,
            amount=total_amount,
            requester=request.user,
            department=request.user.userprofile.department if hasattr(request.user, 'userprofile') and request.user.userprofile.department else None,
            required_date=timezone.now().date(),
            priority='medium'
        )
        
        # Submit for approval (set status to submitted)
        budget_request.status = 'submitted'
        budget_request.save(update_fields=['status'])
        
        return budget_request
    
    except Exception as e:
        self.log_error("Error creating budget request", e)
        return None


# Add methods to the class
BudgetEditingView._handle_budget_edit_post = _handle_budget_edit_post
BudgetEditingView._create_budget_request = _create_budget_request


@login_required_finance
@company_required
def save_budget_estimates(request, company_slug, category_id, company=None):
    """
    Save budget estimates via AJAX.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        if request.method != 'POST':
            return error_json_response("Method not allowed", 405)
        
        # Get category
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Process budget updates
        data = json.loads(request.body)
        updated_count = 0
        
        for budget_data in data.get('budgets', []):
            try:
                budget = Budget.objects.get(
                    id=budget_data['id'],
                    category=category
                )
                budget.estimated_amount = Decimal(budget_data['estimated_amount'])
                budget.save(update_fields=['estimated_amount'])
                updated_count += 1
            except (Budget.DoesNotExist, ValueError, KeyError) as e:
                view.log_error("Error updating budget {}".format(budget_data.get('id')), e)
        
        return json_response({
            'success': True,
            'message': 'Updated {} budget items'.format(updated_count),
            'updated_count': updated_count
        })
    
    except Exception as e:
        view.log_error("Error saving budget estimates", e)
        return error_json_response("Internal server error", 500)


@login_required_finance
@company_required
def budget_requests_list(request, company_slug, company=None):
    """
    List all budget requests for a company.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget requests
        budget_requests = BudgetRequest.objects.all().select_related(
            'budget_category', 'requester', 'approved_by'
        ).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            budget_requests = budget_requests.filter(status=status_filter)
        
        context = {
            'company': company,
            'budget_requests': budget_requests,
            'status_filter': status_filter,
        }
        
        return render(request, 'finance/budgets/budget_requests_list.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget requests")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def budget_request_detail(request, company_slug, request_id, company=None):
    """
    View details of a specific budget request.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
        )
        
        context = {
            'company': company,
            'budget_request': budget_request,
        }
        
        return render(request, 'finance/budgets/budget_request_detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget request details")
        return redirect('finance:budget-requests-list', company_slug=company_slug)


@login_required_finance
@company_required
def approve_budget_request(request, company_slug, request_id, company=None):
    """
    Approve a budget request.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
        )
        
        # Check if user can approve
        if not view._can_approve_request(request.user, budget_request):
            messages.error(request, "You don't have permission to approve this request.")
            return redirect('finance:budget-request-detail', company_slug=company_slug, request_id=request_id)
        
        # Approve the request
        budget_request.status = 'approved'
        budget_request.last_modified_by = request.user
        budget_request.save(update_fields=['status', 'last_modified_by'])
        
        messages.success(request, "Budget request '{}' has been approved.".format(budget_request.purpose))
        return redirect('finance:budget-request-detail', company_slug=company_slug, request_id=request_id)
    
    except Exception as e:
        view.handle_error(request, e, "Error approving budget request")
        return redirect('finance:budget-requests-list', company_slug=company_slug)


@login_required_finance
@company_required
def reject_budget_request(request, company_slug, request_id, company=None):
    """
    Reject a budget request.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
        )
        
        # Check if user can approve
        if not view._can_approve_request(request.user, budget_request):
            messages.error(request, "You don't have permission to reject this request.")
            return redirect('finance:budget-request-detail', company_slug=company_slug, request_id=request_id)
        
        # Get rejection reason
        reason = request.POST.get('rejection_reason', 'No reason provided')
        
        # Reject the request
        budget_request.status = 'rejected'
        budget_request.rejection_reason = reason
        budget_request.last_modified_by = request.user
        budget_request.save(update_fields=['status', 'rejection_reason', 'last_modified_by'])
        
        messages.success(request, "Budget request '{}' has been rejected.".format(budget_request.purpose))
        return redirect('finance:budget-request-detail', company_slug=company_slug, request_id=request_id)
    
    except Exception as e:
        view.handle_error(request, e, "Error rejecting budget request")
        return redirect('finance:budget-requests-list', company_slug=company_slug)


@login_required_finance
@company_required
def budget_approval_dashboard(request, company_slug, company=None):
    """
    Dashboard for budget approvals.
    """
    view = BudgetEditingView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get pending requests (BudgetRequest doesn't have company field)
        pending_requests = BudgetRequest.objects.filter(
            status__in=['submitted', 'under_review']
        ).select_related(
            'budget_category', 'department', 'requester'
        ).order_by('-created_at')
        
        # Get recent approvals
        recent_approvals = BudgetRequest.objects.filter(
            status='approved'
        ).select_related(
            'budget_category', 'department', 'requester'
        ).order_by('-updated_at')[:10]
        
        # Calculate approval statistics
        approval_stats = {
            'pending_count': pending_requests.count(),
            'approved_count': BudgetRequest.objects.filter(status='approved').count(),
            'rejected_count': BudgetRequest.objects.filter(status='rejected').count(),
            'total_requests': BudgetRequest.objects.count(),
        }
        
        context = {
            'company': company,
            'pending_requests': pending_requests,
            'recent_approvals': recent_approvals,
            'approval_stats': approval_stats,
        }
        
        return render(request, 'finance/budgets/approval_dashboard.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget approval dashboard")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


def _can_approve_request(self, user, budget_request):
    """Check if user can approve the budget request."""
    # Check if user is in approval policy
    if budget_request.approval_policy:
        return budget_request.approval_policy.approvers.filter(id=user.id).exists()
    
    # Default: allow if user is staff
    return user.is_staff


# Add method to the class
BudgetEditingView._can_approve_request = _can_approve_request
