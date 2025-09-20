"""
Investment Views

This module contains views specifically for investment operations.
Extracted from the massive investing/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the InvestmentService and focus on HTTP request/response handling.
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
from .models import Investment_rates, Investor_Information
from .services import InvestmentService
from .forms import InvestmentForm, InvestmentRateForm


class InvestmentViewsMixin(LoginRequiredMixin):
    """Mixin for investment views with common functionality."""
    
    def dispatch(self, request, *args, **kwargs):
        """Add investment service to request for easy access."""
        self.investment_service = InvestmentService()
        return super().dispatch(request, *args, **kwargs)


@login_required
def investment_home(request):
    """
    Display the investment home page.
    
    Shows available investment options and user's investment summary.
    """
    try:
        investment_service = InvestmentService()
        
        # Get user's investment summary
        summary_response = investment_service.get_investment_summary(request.user)
        summary = summary_response.get('data', {}).get('summary', {})
        
        # Get user's investments
        investments_response = investment_service.get_user_investments(request.user)
        investments = investments_response.get('data', {}).get('investments', [])
        
        # Get investment rates
        rates_response = investment_service.get_investment_rates()
        rates = rates_response.get('data', {}).get('rates', [])
        
        context = {
            'summary': summary,
            'investments': investments,
            'rates': rates,
            'total_investments': summary.get('total_investments', 0),
            'total_amount': summary.get('total_amount', 0)
        }
        
        return render(request, 'investing/investment_home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading investment page: {str(e)}")
        return render(request, 'investing/investment_home.html', {
            'summary': {},
            'investments': [],
            'rates': [],
            'total_investments': 0,
            'total_amount': 0
        })


@login_required
def create_investment(request, plan_id=None):
    """
    Handle investment creation.
    
    Args:
        plan_id: Optional investment plan ID to pre-select
    """
    if request.method == 'POST':
        try:
            investment_service = InvestmentService()
            
            # Extract form data
            investment_data = {
                'amount': request.POST.get('amount'),
                'investment_plan_id': request.POST.get('investment_plan_id'),
                'investment_type': request.POST.get('investment_type'),
                'notes': request.POST.get('notes', '')
            }
            
            # Create investment
            result = investment_service.create_investment(request.user, investment_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('investing:investment_home')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating investment: {str(e)}")
    
    # GET request - show form
    context = {
        'form': InvestmentForm(),
        'plan_id': plan_id
    }
    
    return render(request, 'investing/create_investment.html', context)


@login_required
def user_investments(request, username=None):
    """
    Display user's investments.
    
    Args:
        username: Optional username filter
    """
    try:
        investment_service = InvestmentService()
        
        # Get investments
        if username:
            try:
                user = CustomerUser.objects.get(username=username)
                investments_response = investment_service.get_user_investments(user)
            except CustomerUser.DoesNotExist:
                messages.error(request, "User not found")
                return redirect('investing:investment_home')
        else:
            investments_response = investment_service.get_user_investments(request.user)
        
        investments = investments_response.get('data', {}).get('investments', [])
        
        context = {
            'investments': investments,
            'username': username or request.user.username,
            'total_count': len(investments)
        }
        
        return render(request, 'investing/user_investments.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading investments: {str(e)}")
        return render(request, 'investing/user_investments.html', {
            'investments': [],
            'username': username or request.user.username,
            'total_count': 0
        })


@login_required
def investment_plan_list(request, path="options"):
    """
    Display investment plan options.
    
    Args:
        path: Type of plans to show
    """
    try:
        investment_service = InvestmentService()
        
        # Get investment rates
        rates_response = investment_service.get_investment_rates()
        rates = rates_response.get('data', {}).get('rates', [])
        
        context = {
            'rates': rates,
            'path': path,
            'total_plans': len(rates)
        }
        
        return render(request, 'investing/investment_plan_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading investment plans: {str(e)}")
        return render(request, 'investing/investment_plan_list.html', {
            'rates': [],
            'path': path,
            'total_plans': 0
        })


@login_required
def investment_plan_detail(request, pk):
    """
    Display detailed view of an investment plan.
    
    Args:
        pk: Primary key of the investment plan
    """
    try:
        investment_service = InvestmentService()
        
        # Get specific rate
        rates_response = investment_service.get_investment_rates()
        rates = rates_response.get('data', {}).get('rates', [])
        
        rate = next((r for r in rates if r['id'] == pk), None)
        
        if not rate:
            messages.error(request, "Investment plan not found")
            return redirect('investing:investment_plan_list')
        
        context = {
            'rate': rate,
            'form': InvestmentForm()
        }
        
        return render(request, 'investing/investment_plan_detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading investment plan: {str(e)}")
        return redirect('investing:investment_plan_list')


@login_required
def calculate_returns(request, investment_id):
    """
    Calculate returns for an investment.
    
    Args:
        investment_id: ID of the investment
    """
    try:
        investment_service = InvestmentService()
        
        # Calculate returns
        result = investment_service.calculate_investment_returns(investment_id, request.user)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'calculations': result['data']['calculations']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def update_investment_status(request, investment_id):
    """
    Update investment status.
    
    Args:
        investment_id: ID of the investment
    """
    try:
        investment_service = InvestmentService()
        
        # Extract new status
        new_status = request.POST.get('status')
        
        if not new_status:
            return JsonResponse({'success': False, 'error': 'Status is required'})
        
        result = investment_service.update_investment_status(investment_id, request.user, new_status)
        
        if result['success']:
            messages.success(request, result['message'])
            return JsonResponse({'success': True, 'message': result['message']})
        else:
            return JsonResponse({'success': False, 'error': result['error']})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def create_investment_rate(request):
    """
    Handle investment rate creation (admin only).
    """
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('investing:investment_home')
    
    if request.method == 'POST':
        try:
            investment_service = InvestmentService()
            
            # Extract form data
            rate_data = {
                'rate_name': request.POST.get('rate_name'),
                'rate_value': request.POST.get('rate_value'),
                'rate_type': request.POST.get('rate_type'),
                'description': request.POST.get('description', '')
            }
            
            # Create investment rate
            result = investment_service.create_investment_rate(request.user, rate_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('investing:investment_home')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating investment rate: {str(e)}")
    
    # GET request - show form
    context = {
        'form': InvestmentRateForm()
    }
    
    return render(request, 'investing/create_investment_rate.html', context)





