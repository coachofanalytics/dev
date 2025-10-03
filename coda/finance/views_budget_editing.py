"""
Budget Editing Views - Phase 2 Implementation
Integrates with existing BudgetRequest and ApprovalPolicy system
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from decimal import Decimal
import json

from .models import (
    BudgetCategory, BudgetSubCategory, BudgetItemLibrary, 
    BudgetRequest, ApprovalPolicy, Budget, Company, Department
)
from .services.automation_service import BudgetRequestService, ApprovalEngineService
from .forms_improved import SmartTransactionForm


@login_required
def budget_category_edit(request, company_slug, category_id):
    """
    Edit budget estimates for a specific category
    Shows line items and allows editing with approval workflow
    """
    company = get_object_or_404(Company, slug=company_slug)
    category = get_object_or_404(BudgetCategory, id=category_id)
    
    # Get user's department
    user_department = getattr(request.user, 'department', None)
    
    # Get existing budget items for this category
    existing_budgets = Budget.objects.filter(
        company=company,
        category=category,
        department=user_department
    ).select_related('subcategory')
    
    # Get available subcategories and items from library
    subcategories = BudgetSubCategory.objects.filter(category=category)
    items_library = BudgetItemLibrary.objects.filter(
        category=category,
        is_active=True
    ).select_related('subcategory').order_by('subcategory__name', 'item_name')
    
    # Group items by subcategory
    items_by_subcategory = {}
    for item in items_library:
        subcat_name = item.subcategory.name
        if subcat_name not in items_by_subcategory:
            items_by_subcategory[subcat_name] = []
        items_by_subcategory[subcat_name].append(item)
    
    # Calculate totals
    total_estimated = existing_budgets.aggregate(
        total=Sum('estimated_amount')
    )['total'] or Decimal('0.00')
    
    total_actual = existing_budgets.aggregate(
        total=Sum('actual_spent')
    )['total'] or Decimal('0.00')
    
    context = {
        'company': company,
        'category': category,
        'subcategories': subcategories,
        'items_by_subcategory': items_by_subcategory,
        'existing_budgets': existing_budgets,
        'total_estimated': total_estimated,
        'total_actual': total_actual,
        'user_department': user_department,
    }
    
    return render(request, 'finance/budgets/budget_category_edit.html', context)


@login_required
def save_budget_estimates(request, company_slug, category_id):
    """
    Save budget estimates and create BudgetRequest for approval
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        with transaction.atomic():
            company = get_object_or_404(Company, slug=company_slug)
            category = get_object_or_404(BudgetCategory, id=category_id)
            user_department = getattr(request.user, 'department', None)
            
            # Parse the budget data
            budget_data = json.loads(request.body)
            line_items = budget_data.get('line_items', [])
            justification = budget_data.get('justification', '')
            
            if not line_items:
                return JsonResponse({'error': 'No budget items provided'}, status=400)
            
            # Calculate total amount
            total_amount = sum(
                Decimal(str(item.get('amount', 0))) 
                for item in line_items 
                if item.get('amount')
            )
            
            # Create BudgetRequest
            budget_request = BudgetRequest.objects.create(
                company=company,
                department=user_department,
                budget_category=category,
                amount=total_amount,
                description=f"Budget estimates for {category.name}",
                justification=justification,
                request_date=timezone.now().date(),
                required_date=timezone.now().date() + timezone.timedelta(days=30),
                priority='medium',
                status='draft',
                created_by=request.user,
                last_modified_by=request.user,
                # Store line items in attachments field as JSON
                attachments=[{
                    'type': 'budget_line_items',
                    'data': line_items,
                    'created_at': timezone.now().isoformat()
                }]
            )
            
            # Auto-submit for approval if amount is significant
            if total_amount > Decimal('1000.00'):
                budget_service = BudgetRequestService()
                budget_service.submit_for_approval(budget_request.id, request.user, request)
                messages.success(
                    request, 
                    f'Budget estimates submitted for approval. Total: ${total_amount:,.2f}'
                )
            else:
                messages.success(
                    request, 
                    f'Budget estimates saved as draft. Total: ${total_amount:,.2f}'
                )
            
            return JsonResponse({
                'success': True,
                'request_id': budget_request.id,
                'status': budget_request.status,
                'total_amount': float(total_amount),
                'message': 'Budget estimates saved successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error saving budget estimates: {str(e)}'
        }, status=500)


@login_required
def budget_requests_list(request, company_slug):
    """
    List all budget requests for the company
    """
    company = get_object_or_404(Company, slug=company_slug)
    user_department = getattr(request.user, 'department', None)
    
    # Get budget requests
    requests = BudgetRequest.objects.filter(
        company=company,
        department=user_department
    ).select_related(
        'budget_category', 'created_by', 'current_approver'
    ).order_by('-request_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': requests.count(),
        'draft': requests.filter(status='draft').count(),
        'submitted': requests.filter(status='submitted').count(),
        'under_review': requests.filter(status='under_review').count(),
        'approved': requests.filter(status='approved').count(),
        'rejected': requests.filter(status='rejected').count(),
    }
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
    }
    
    return render(request, 'finance/budgets/budget_requests_list.html', context)


@login_required
def budget_request_detail(request, company_slug, request_id):
    """
    View detailed budget request with line items
    """
    company = get_object_or_404(Company, slug=company_slug)
    budget_request = get_object_or_404(
        BudgetRequest, 
        id=request_id, 
        company=company
    )
    
    # Get line items from attachments
    line_items = []
    for attachment in budget_request.attachments:
        if attachment.get('type') == 'budget_line_items':
            line_items = attachment.get('data', [])
            break
    
    # Check if user can approve
    can_approve = (
        request.user == budget_request.current_approver and 
        budget_request.status == 'under_review'
    )
    
    context = {
        'company': company,
        'budget_request': budget_request,
        'line_items': line_items,
        'can_approve': can_approve,
    }
    
    return render(request, 'finance/budgets/budget_request_detail.html', context)


@login_required
def approve_budget_request(request, company_slug, request_id):
    """
    Approve a budget request and create Budget records
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        with transaction.atomic():
            company = get_object_or_404(Company, slug=company_slug)
            budget_request = get_object_or_404(
                BudgetRequest, 
                id=request_id, 
                company=company
            )
            
            # Check if user can approve
            if request.user != budget_request.current_approver:
                return JsonResponse({'error': 'Not authorized to approve'}, status=403)
            
            if budget_request.status != 'under_review':
                return JsonResponse({'error': 'Request not in review status'}, status=400)
            
            # Get line items
            line_items = []
            for attachment in budget_request.attachments:
                if attachment.get('type') == 'budget_line_items':
                    line_items = attachment.get('data', [])
                    break
            
            # Create Budget records for each line item
            created_budgets = []
            for item in line_items:
                if not item.get('amount'):
                    continue
                
                subcategory = get_object_or_404(
                    BudgetSubCategory, 
                    id=item.get('subcategory_id')
                )
                
                budget = Budget.objects.create(
                    company=company,
                    department=budget_request.department,
                    category=budget_request.budget_category,
                    subcategory=subcategory,
                    item_name=item.get('item_name', ''),
                    estimated_amount=Decimal(str(item.get('amount', 0))),
                    actual_spent=Decimal('0.00'),
                    currency='USD',
                    fiscal_year=timezone.now().year,
                    status='active',
                    requires_approval=False,  # Already approved through BudgetRequest
                    approved_by=request.user,
                    approved_at=timezone.now(),
                )
                created_budgets.append(budget)
            
            # Update budget request status
            budget_request.status = 'approved'
            budget_request.approved_by = request.user
            budget_request.approved_at = timezone.now()
            budget_request.save()
            
            messages.success(
                request, 
                f'Budget request approved. Created {len(created_budgets)} budget records.'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Budget request approved successfully',
                'budgets_created': len(created_budgets)
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error approving budget request: {str(e)}'
        }, status=500)


@login_required
def reject_budget_request(request, company_slug, request_id):
    """
    Reject a budget request
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        with transaction.atomic():
            company = get_object_or_404(Company, slug=company_slug)
            budget_request = get_object_or_404(
                BudgetRequest, 
                id=request_id, 
                company=company
            )
            
            # Check if user can reject
            if request.user != budget_request.current_approver:
                return JsonResponse({'error': 'Not authorized to reject'}, status=403)
            
            if budget_request.status != 'under_review':
                return JsonResponse({'error': 'Request not in review status'}, status=400)
            
            # Get rejection reason
            data = json.loads(request.body)
            rejection_reason = data.get('rejection_reason', '')
            
            if not rejection_reason:
                return JsonResponse({'error': 'Rejection reason required'}, status=400)
            
            # Update budget request
            budget_request.status = 'rejected'
            budget_request.rejection_reason = rejection_reason
            budget_request.save()
            
            messages.warning(
                request, 
                'Budget request rejected.'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Budget request rejected successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error rejecting budget request: {str(e)}'
        }, status=500)


@login_required
def budget_approval_dashboard(request, company_slug):
    """
    Dashboard for budget approvals - shows pending requests
    """
    company = get_object_or_404(Company, slug=company_slug)
    
    # Get requests pending user's approval
    pending_approvals = BudgetRequest.objects.filter(
        company=company,
        current_approver=request.user,
        status='under_review'
    ).select_related(
        'budget_category', 'created_by', 'department'
    ).order_by('-request_date')
    
    # Get user's submitted requests
    my_requests = BudgetRequest.objects.filter(
        company=company,
        created_by=request.user
    ).select_related(
        'budget_category', 'current_approver'
    ).order_by('-request_date')[:10]
    
    # Get recent approvals
    recent_approvals = BudgetRequest.objects.filter(
        company=company,
        status__in=['approved', 'rejected']
    ).select_related(
        'budget_category', 'created_by', 'approved_by'
    ).order_by('-approved_at')[:10]
    
    context = {
        'company': company,
        'pending_approvals': pending_approvals,
        'my_requests': my_requests,
        'recent_approvals': recent_approvals,
    }
    
    return render(request, 'finance/budgets/budget_approval_dashboard.html', context)
