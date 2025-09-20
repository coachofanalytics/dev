"""
Main Views

This module contains views specifically for main/core operations.
Extracted from the massive main/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the CoreService and focus on HTTP request/response handling.
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.models import CustomerUser
from .services import CoreService


def handler400(request, exception):
    """Handle 400 Bad Request errors."""
    return render(request, 'main/errors/400.html', status=400)


def handler403(request, exception):
    """Handle 403 Forbidden errors."""
    return render(request, 'main/errors/403.html', status=403)


def handler404(request, exception):
    """Handle 404 Not Found errors."""
    return render(request, 'main/errors/404.html', status=404)


def handler500(request):
    """Handle 500 Internal Server errors."""
    return render(request, 'main/errors/500.html', status=500)


def data_policy(request):
    """
    Display data policy page.
    """
    try:
        core_service = CoreService()
        
        # Get data policy content
        policy_data = {
            'title': 'Data Policy',
            'content': 'Our data policy and privacy information.',
            'last_updated': '2024-01-01'
        }
        
        context = {
            'policy_data': policy_data
        }
        
        return render(request, 'main/data_policy.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading data policy: {str(e)}")
        return render(request, 'main/data_policy.html', {
            'policy_data': {}
        })


def layout(request):
    """
    Display main layout page.
    """
    try:
        core_service = CoreService()
        
        # Get layout data
        layout_response = core_service.get_layout_data(request.user)
        layout_data = layout_response.get('data', {})
        
        context = {
            'layout_data': layout_data,
            'navigation': layout_data.get('navigation', {}),
            'sidebar': layout_data.get('sidebar', {}),
            'footer': layout_data.get('footer', {})
        }
        
        return render(request, 'main/layout.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading layout: {str(e)}")
        return render(request, 'main/layout.html', {
            'layout_data': {},
            'navigation': {},
            'sidebar': {},
            'footer': {}
        })


def home(request):
    """
    Display home page.
    """
    try:
        core_service = CoreService()
        
        # Get home data
        home_response = core_service.get_home_data(request.user)
        home_data = home_response.get('data', {})
        
        context = {
            'home_data': home_data,
            'testimonials': home_data.get('testimonials', []),
            'services': home_data.get('services', []),
            'announcements': home_data.get('announcements', [])
        }
        
        return render(request, 'main/home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading home page: {str(e)}")
        return render(request, 'main/home.html', {
            'home_data': {},
            'testimonials': [],
            'services': [],
            'announcements': []
        })


def search(request):
    """
    Handle search requests.
    """
    try:
        core_service = CoreService()
        
        query = request.GET.get('q', '')
        content_type = request.GET.get('type', 'all')
        
        if not query:
            messages.warning(request, "Please enter a search query")
            return render(request, 'main/search.html', {
                'search_results': {},
                'query': '',
                'content_type': content_type
            })
        
        # Perform search
        search_response = core_service.search_content(request.user, query, content_type)
        search_results = search_response.get('data', {})
        
        context = {
            'search_results': search_results,
            'query': query,
            'content_type': content_type,
            'total_count': search_results.get('total_count', 0)
        }
        
        return render(request, 'main/search.html', context)
        
    except Exception as e:
        messages.error(request, f"Error performing search: {str(e)}")
        return render(request, 'main/search.html', {
            'search_results': {},
            'query': '',
            'content_type': 'all',
            'total_count': 0
        })


def services(request):
    """
    Display services page.
    """
    try:
        core_service = CoreService()
        
        # Get services
        services_response = core_service.get_services(request.user)
        services_data = services_response.get('data', {}).get('services', [])
        
        context = {
            'services': services_data,
            'total_count': len(services_data)
        }
        
        return render(request, 'main/services.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading services: {str(e)}")
        return render(request, 'main/services.html', {
            'services': [],
            'total_count': 0
        })


@login_required
def create_service(request):
    """
    Handle service creation.
    """
    if request.method == 'POST':
        try:
            core_service = CoreService()
            
            # Extract form data
            service_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description')
            }
            
            # Create service
            result = core_service.create_service(request.user, service_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('main:services')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating service: {str(e)}")
    
    # GET request - show form
    return render(request, 'main/create_service.html')


@login_required
def delete_service(request, service_id):
    """
    Handle service deletion.
    """
    try:
        core_service = CoreService()
        
        # Delete service
        result = core_service.delete_service(request.user, service_id)
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
            
    except Exception as e:
        messages.error(request, f"Error deleting service: {str(e)}")
    
    return redirect('main:services')


def service_plans(request):
    """
    Display service plans page.
    """
    try:
        core_service = CoreService()
        
        service_id = request.GET.get('service_id')
        
        # Get service plans
        plans_response = core_service.get_service_plans(request.user, service_id)
        plans_data = plans_response.get('data', {}).get('service_plans', [])
        
        context = {
            'service_plans': plans_data,
            'service_id': service_id,
            'total_count': len(plans_data)
        }
        
        return render(request, 'main/service_plans.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading service plans: {str(e)}")
        return render(request, 'main/service_plans.html', {
            'service_plans': [],
            'service_id': None,
            'total_count': 0
        })


def job_market(request):
    """
    Display job market page.
    """
    try:
        core_service = CoreService()
        
        # Get job market data
        market_response = core_service.get_job_market_data(request.user)
        market_data = market_response.get('data', {})
        
        context = {
            'job_market_data': market_data,
            'total_jobs': market_data.get('total_jobs', 0),
            'featured_jobs': market_data.get('featured_jobs', [])
        }
        
        return render(request, 'main/job_market.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading job market: {str(e)}")
        return render(request, 'main/job_market.html', {
            'job_market_data': {},
            'total_jobs': 0,
            'featured_jobs': []
        })


@login_required
def core_analytics(request):
    """
    Display core analytics page.
    """
    try:
        core_service = CoreService()
        
        # Get core analytics
        analytics_response = core_service.get_core_analytics(request.user)
        analytics_data = analytics_response.get('data', {})
        
        context = {
            'analytics_data': analytics_data,
            'total_services': analytics_data.get('total_services', 0),
            'total_users': analytics_data.get('total_users', 0),
            'system_health': analytics_data.get('system_health', 'unknown')
        }
        
        return render(request, 'main/analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'main/analytics.html', {
            'analytics_data': {},
            'total_services': 0,
            'total_users': 0,
            'system_health': 'error'
        })


@require_http_methods(["GET"])
def get_home_data(request):
    """
    Get home data via AJAX.
    """
    try:
        core_service = CoreService()
        
        # Get home data
        result = core_service.get_home_data(request.user)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']
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


@require_http_methods(["GET"])
def get_layout_data(request):
    """
    Get layout data via AJAX.
    """
    try:
        core_service = CoreService()
        
        page_type = request.GET.get('page_type', 'default')
        
        # Get layout data
        result = core_service.get_layout_data(request.user, page_type)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']
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





