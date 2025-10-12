"""
User-friendly forms and views for budget requests
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q

from finance.models import BudgetRequest, BudgetCategory, ApprovalPolicy
from finance.forms.budget import BudgetRequestForm
from finance.services.automation_service import BudgetRequestService, ApprovalEngineService
from accounts.models import Department


@login_required
def budget_request_form(request):
    """User-friendly budget request form"""
    if request.method == 'POST':
        form = BudgetRequestForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    budget_request = form.save(commit=False)
                    budget_request.requester = request.user
                    budget_request.created_by = request.user
                    budget_request.last_modified_by = request.user
                    budget_request.save()
                    
                    # Auto-submit for approval if user chooses
                    if request.POST.get('submit_for_approval') == 'on':
                        service = BudgetRequestService()
                        budget_request = service.submit_for_approval(
                            budget_request.id, 
                            request.user, 
                            request
                        )
                        messages.success(
                            request, 
                            f'Budget request #{budget_request.id} created and submitted for approval!'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Budget request #{budget_request.id} created and saved as draft.'
                        )
                    
                    return redirect('finance:budget_request_detail', pk=budget_request.id)
            except Exception as e:
                messages.error(request, f'Error creating budget request: {str(e)}')
    else:
        form = BudgetRequestForm()
    
    # Get available departments and categories
    departments = Department.objects.filter(is_active=True)
    categories = BudgetCategory.objects.all()
    
    context = {
        'form': form,
        'departments': departments,
        'categories': categories,
        'page_title': 'Create Budget Request',
        'submit_text': 'Create Request'
    }
    
    return render(request, 'finance/budget_request_form.html', context)


@login_required
def budget_request_detail(request, pk):
    """View budget request details"""
    budget_request = get_object_or_404(BudgetRequest, pk=pk)
    
    # Check if user can view this request
    if not request.user.is_staff and budget_request.requester != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('finance:budget_requests_list')
    
    context = {
        'budget_request': budget_request,
        'page_title': f'Budget Request #{budget_request.id}',
        'can_edit': (
            request.user.is_staff or 
            (budget_request.requester == request.user and budget_request.status == 'draft')
        ),
        'can_approve': (
            request.user.is_staff and 
            budget_request.status in ['submitted', 'under_review'] and
            budget_request.current_approver == request.user
        )
    }
    
    return render(request, 'finance/budget_request_detail.html', context)


@login_required
def budget_requests_list(request):
    """List user's budget requests"""
    # Filter requests based on user role
    if request.user.is_staff:
        requests = BudgetRequest.objects.all().select_related(
            'requester', 'department', 'budget_category', 'current_approver'
        )
    else:
        requests = BudgetRequest.objects.filter(requester=request.user).select_related(
            'requester', 'department', 'budget_category', 'current_approver'
        )
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    department_filter = request.GET.get('department')
    if department_filter:
        requests = requests.filter(department_id=department_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        requests = requests.filter(
            Q(purpose__icontains=search_query) |
            Q(cost_center__icontains=search_query) |
            Q(requester__first_name__icontains=search_query) |
            Q(requester__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(requests.order_by('-request_date'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = Department.objects.filter(is_active=True)
    status_choices = BudgetRequest.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'status_choices': status_choices,
        'current_filters': {
            'status': status_filter,
            'department': department_filter,
            'search': search_query
        },
        'page_title': 'My Budget Requests' if not request.user.is_staff else 'All Budget Requests'
    }
    
    return render(request, 'finance/budget_requests_list.html', context)


@login_required
def budget_request_edit(request, pk):
    """Edit budget request"""
    budget_request = get_object_or_404(BudgetRequest, pk=pk)
    
    # Check permissions
    if not request.user.is_staff and budget_request.requester != request.user:
        messages.error(request, 'You do not have permission to edit this request.')
        return redirect('finance:budget_requests_list')
    
    if budget_request.status not in ['draft']:
        messages.error(request, 'Only draft requests can be edited.')
        return redirect('finance:budget_request_detail', pk=pk)
    
    if request.method == 'POST':
        form = BudgetRequestForm(request.POST, instance=budget_request)
        if form.is_valid():
            try:
                with transaction.atomic():
                    budget_request = form.save(commit=False)
                    budget_request.last_modified_by = request.user
                    budget_request.save()
                    
                    # Auto-submit for approval if user chooses
                    if request.POST.get('submit_for_approval') == 'on':
                        service = BudgetRequestService()
                        budget_request = service.submit_for_approval(
                            budget_request.id, 
                            request.user, 
                            request
                        )
                        messages.success(
                            request, 
                            f'Budget request #{budget_request.id} updated and submitted for approval!'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Budget request #{budget_request.id} updated successfully.'
                        )
                    
                    return redirect('finance:budget_request_detail', pk=budget_request.id)
            except Exception as e:
                messages.error(request, f'Error updating budget request: {str(e)}')
    else:
        form = BudgetRequestForm(instance=budget_request, user=request.user)
    
    # Get available departments and categories
    departments = Department.objects.filter(is_active=True)
    categories = BudgetCategory.objects.all()
    
    context = {
        'form': form,
        'budget_request': budget_request,
        'departments': departments,
        'categories': categories,
        'page_title': f'Edit Budget Request #{budget_request.id}',
        'submit_text': 'Update Request'
    }
    
    return render(request, 'finance/budget_request_form.html', context)


@login_required
@require_http_methods(["POST"])
def submit_for_approval(request, pk):
    """Submit budget request for approval"""
    budget_request = get_object_or_404(BudgetRequest, pk=pk)
    
    # Check permissions
    if not request.user.is_staff and budget_request.requester != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if budget_request.status != 'draft':
        return JsonResponse({'success': False, 'error': 'Only draft requests can be submitted'}, status=400)
    
    try:
        service = BudgetRequestService()
        budget_request = service.submit_for_approval(pk, request.user, request)
        
        return JsonResponse({
            'success': True,
            'message': 'Request submitted for approval successfully',
            'status': budget_request.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def approve_request(request, pk):
    """Approve budget request"""
    budget_request = get_object_or_404(BudgetRequest, pk=pk)
    
    # Check permissions
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if budget_request.current_approver != request.user:
        return JsonResponse({'success': False, 'error': 'You are not the current approver'}, status=400)
    
    try:
        service = ApprovalEngineService()
        comments = request.POST.get('comments', 'Approved via web interface')
        
        budget_request = service.process_approval(
            pk, 
            request.user, 
            'approved',
            comments,
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Request approved successfully',
            'status': budget_request.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def reject_request(request, pk):
    """Reject budget request"""
    budget_request = get_object_or_404(BudgetRequest, pk=pk)
    
    # Check permissions
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if budget_request.current_approver != request.user:
        return JsonResponse({'success': False, 'error': 'You are not the current approver'}, status=400)
    
    try:
        service = ApprovalEngineService()
        reason = request.POST.get('reason', 'Rejected via web interface')
        
        budget_request = service.process_approval(
            pk, 
            request.user, 
            'rejected',
            reason,
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Request rejected successfully',
            'status': budget_request.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

