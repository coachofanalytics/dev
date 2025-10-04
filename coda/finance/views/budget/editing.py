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
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, ApprovalPolicy
from ...forms import legacy_forms

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
            company=company,
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
            estimated_amount = request.POST.get(f'estimated_amount_{budget_id}')
            
            if estimated_amount:
                try:
                    budget.estimated_amount = Decimal(estimated_amount)
                    budget.save(update_fields=['estimated_amount'])
                    updated_budgets.append(budget)
                except (ValueError, TypeError):
                    self.log_error(f"Invalid amount for budget {budget.id}: {estimated_amount}")
        
        # Create budget request if required
        if updated_budgets and request.POST.get('submit_for_approval'):
            budget_request = self._create_budget_request(
                request, company, category, updated_budgets
            )
            
            if budget_request:
                messages.success(
                    request, 
                    f"Budget changes submitted for approval. Request ID: {budget_request.id}"
                )
                return redirect('finance:budget-requests-list', company_slug=company.slug)
        
        messages.success(request, f"Updated {len(updated_budgets)} budget items.")
        return redirect('finance:budget-category-edit', 
                       company_slug=company.slug, category_id=category.id)
    
    except Exception as e:
        self.handle_error(request, e, "Error updating budgets")
        return redirect('finance:budget-category-edit', 
                       company_slug=company.slug, category_id=category.id)


def _create_budget_request(self, request, company, category, updated_budgets):
    """Create a budget request for approval."""
    try:
        # Calculate total amount
        total_amount = sum(budget.estimated_amount for budget in updated_budgets)
        
        # Create budget request
        budget_request = BudgetRequest.objects.create(
            company=company,
            title=f"Budget Update - {category.name}",
            description=f"Updated budget estimates for {category.name} category",
            category=category,
            subcategory=updated_budgets[0].subcategory,  # Use first budget's subcategory
            requested_amount=total_amount,
            requested_by=request.user,
            justification=request.POST.get('justification', ''),
            business_case=request.POST.get('business_case', ''),
        )
        
        # Submit for approval
        budget_request.submit_for_approval()
        
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
                    company=company,
                    category=category
                )
                budget.estimated_amount = Decimal(budget_data['estimated_amount'])
                budget.save(update_fields=['estimated_amount'])
                updated_count += 1
            except (Budget.DoesNotExist, ValueError, KeyError) as e:
                view.log_error(f"Error updating budget {budget_data.get('id')}", e)
        
        return json_response({
            'success': True,
            'message': f'Updated {updated_count} budget items',
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
        budget_requests = BudgetRequest.objects.filter(
            company=company
        ).select_related(
            'category', 'subcategory', 'requested_by', 'approved_by'
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
            company=company
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
            company=company
        )
        
        # Check if user can approve
        if not view._can_approve_request(request.user, budget_request):
            messages.error(request, "You don't have permission to approve this request.")
            return redirect('finance:budget-request-detail', 
                           company_slug=company.slug, request_id=request_id)
        
        # Approve the request
        budget_request.approve(request.user)
        
        messages.success(request, f"Budget request '{budget_request.title}' has been approved.")
        return redirect('finance:budget-request-detail', 
                       company_slug=company.slug, request_id=request_id)
    
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
            company=company
        )
        
        # Check if user can approve
        if not view._can_approve_request(request.user, budget_request):
            messages.error(request, "You don't have permission to reject this request.")
            return redirect('finance:budget-request-detail', 
                           company_slug=company.slug, request_id=request_id)
        
        # Get rejection reason
        reason = request.POST.get('rejection_reason', 'No reason provided')
        
        # Reject the request
        budget_request.reject(request.user, reason)
        
        messages.success(request, f"Budget request '{budget_request.title}' has been rejected.")
        return redirect('finance:budget-request-detail', 
                       company_slug=company.slug, request_id=request_id)
    
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
        
        # Get pending requests
        pending_requests = BudgetRequest.objects.filter(
            company=company,
            status__in=['Submitted', 'Under Review']
        ).select_related(
            'category', 'subcategory', 'requested_by'
        ).order_by('-created_at')
        
        # Get recent approvals
        recent_approvals = BudgetRequest.objects.filter(
            company=company,
            status='Approved'
        ).select_related(
            'category', 'subcategory', 'requested_by', 'approved_by'
        ).order_by('-approved_at')[:10]
        
        context = {
            'company': company,
            'pending_requests': pending_requests,
            'recent_approvals': recent_approvals,
        }
        
        return render(request, 'finance/budgets/budget_approval_dashboard.html', context)
    
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
