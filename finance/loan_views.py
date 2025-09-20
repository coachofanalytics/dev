"""
Loan Views

This module contains views specifically for loan operations.
Extracted from the massive finance/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the LoanService and focus on HTTP request/response handling.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from accounts.models import CustomerUser
from .models import LoanApplication, LoanProduct
from .services import LoanService
from .forms import LoanApplicationForm


class LoanViewsMixin(LoginRequiredMixin):
    """Mixin for loan views with common functionality."""
    
    def dispatch(self, request, *args, **kwargs):
        """Add loan service to request for easy access."""
        self.loan_service = LoanService()
        return super().dispatch(request, *args, **kwargs)


@login_required
def loan_application_home(request):
    """
    Display the loan application home page.
    
    Shows available loan products and user's application history.
    """
    try:
        loan_service = LoanService()
        
        # Get available loan products
        loan_products = LoanProduct.objects.filter(is_active=True)
        
        # Get user's loan applications
        user_applications = loan_service.get_user_loan_applications(request.user)
        
        context = {
            'loan_products': loan_products,
            'user_applications': user_applications.get('data', {}).get('applications', []),
            'has_pending_applications': any(
                app['status'] == 'pending' 
                for app in user_applications.get('data', {}).get('applications', [])
            )
        }
        
        return render(request, 'finance/loan_application_home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading loan page: {str(e)}")
        return render(request, 'finance/loan_application_home.html', {
            'loan_products': [],
            'user_applications': [],
            'has_pending_applications': False
        })


@login_required
def apply_for_loan(request, plan_id=None):
    """
    Handle loan application submission.
    
    Args:
        plan_id: Optional loan product ID to pre-select
    """
    if request.method == 'POST':
        try:
            loan_service = LoanService()
            
            # Extract form data
            loan_data = {
                'loan_amount': request.POST.get('loan_amount'),
                'loan_product_id': request.POST.get('loan_product_id'),
                'purpose': request.POST.get('purpose'),
                'employment_status': request.POST.get('employment_status'),
                'monthly_income': request.POST.get('monthly_income', 0)
            }
            
            # Create loan application
            result = loan_service.create_loan_application(request.user, loan_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('finance:loan_application_home')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error submitting application: {str(e)}")
    
    # GET request - show form
    loan_products = LoanProduct.objects.filter(is_active=True)
    selected_product = None
    
    if plan_id:
        try:
            selected_product = LoanProduct.objects.get(id=plan_id, is_active=True)
        except LoanProduct.DoesNotExist:
            messages.warning(request, "Selected loan product not found")
    
    context = {
        'loan_products': loan_products,
        'selected_product': selected_product,
        'form': LoanApplicationForm()
    }
    
    return render(request, 'finance/apply_for_loan.html', context)


@login_required
def admin_loan_applications(request):
    """
    Admin view to manage loan applications.
    
    Shows all pending applications for admin review.
    """
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('main:layout')
    
    try:
        # Get pending applications
        pending_applications = LoanApplication.objects.filter(
            status='pending'
        ).select_related('user', 'loan_product').order_by('-application_date')
        
        context = {
            'applications': pending_applications,
            'total_pending': pending_applications.count()
        }
        
        return render(request, 'finance/admin_loan_applications.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        return render(request, 'finance/admin_loan_applications.html', {
            'applications': [],
            'total_pending': 0
        })


@login_required
@require_http_methods(["POST"])
def approve_loan_application(request, pk):
    """
    Approve a loan application.
    
    Args:
        pk: Primary key of the loan application
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        loan_service = LoanService()
        
        # Extract approval data
        approval_data = {
            'notes': request.POST.get('notes', '')
        }
        
        result = loan_service.approve_loan_application(pk, request.user, approval_data)
        
        if result['success']:
            messages.success(request, result['message'])
            return JsonResponse({'success': True, 'message': result['message']})
        else:
            return JsonResponse({'success': False, 'error': result['error']})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def reject_loan_application(request, pk):
    """
    Reject a loan application.
    
    Args:
        pk: Primary key of the loan application
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        loan_service = LoanService()
        
        # Extract rejection data
        rejection_data = {
            'reason': request.POST.get('reason'),
            'notes': request.POST.get('notes', '')
        }
        
        if not rejection_data['reason']:
            return JsonResponse({'success': False, 'error': 'Rejection reason is required'})
        
        result = loan_service.reject_loan_application(pk, request.user, rejection_data)
        
        if result['success']:
            messages.success(request, result['message'])
            return JsonResponse({'success': True, 'message': result['message']})
        else:
            return JsonResponse({'success': False, 'error': result['error']})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def loan_application_confirmation(request):
    """
    Show loan application confirmation page.
    
    Displays confirmation details after successful application submission.
    """
    # Get the most recent application for this user
    try:
        latest_application = LoanApplication.objects.filter(
            user=request.user
        ).order_by('-application_date').first()
        
        if not latest_application:
            messages.warning(request, "No recent application found")
            return redirect('finance:loan_application_home')
        
        context = {
            'application': latest_application
        }
        
        return render(request, 'finance/loan_application_confirmation.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading confirmation: {str(e)}")
        return redirect('finance:loan_application_home')


@login_required
def loan_analytics(request):
    """
    Display loan analytics dashboard.
    
    Shows loan performance metrics and statistics.
    """
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('main:layout')
    
    try:
        # Get loan statistics
        total_applications = LoanApplication.objects.count()
        pending_applications = LoanApplication.objects.filter(status='pending').count()
        approved_applications = LoanApplication.objects.filter(status='approved').count()
        rejected_applications = LoanApplication.objects.filter(status='rejected').count()
        
        # Calculate approval rate
        processed_applications = approved_applications + rejected_applications
        approval_rate = (approved_applications / processed_applications * 100) if processed_applications > 0 else 0
        
        context = {
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
            'rejected_applications': rejected_applications,
            'approval_rate': round(approval_rate, 2)
        }
        
        return render(request, 'finance/loan_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'finance/loan_analytics.html', {
            'total_applications': 0,
            'pending_applications': 0,
            'approved_applications': 0,
            'rejected_applications': 0,
            'approval_rate': 0
        })

