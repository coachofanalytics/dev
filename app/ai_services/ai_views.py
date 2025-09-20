"""
AI Services Views

This module contains views specifically for AI operations.
Extracted from the massive ai_services/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the AIAnalyticsService and focus on HTTP request/response handling.
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from datetime import datetime, timedelta

from accounts.models import CustomerUser
from .services import AIAnalyticsService


@login_required
def ai_analytics_home(request):
    """
    Display the AI analytics home page.
    
    Shows AI dashboard with data processing status, recent uploads, and analytics.
    """
    try:
        ai_service = AIAnalyticsService()
        
        # Get dashboard data
        dashboard_response = ai_service.get_analytics_dashboard_data(request.user)
        dashboard = dashboard_response.get('data', {}).get('dashboard', {})
        
        context = {
            'dashboard': dashboard,
            'total_processed': dashboard.get('total_data_processed', 0),
            'recent_uploads': dashboard.get('recent_uploads', []),
            'processing_queue': dashboard.get('processing_queue', 0),
            'system_health': dashboard.get('system_health', 'unknown')
        }
        
        return render(request, 'ai_services/ai_home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading AI analytics page: {str(e)}")
        return render(request, 'ai_services/ai_home.html', {
            'dashboard': {},
            'total_processed': 0,
            'recent_uploads': [],
            'processing_queue': 0,
            'system_health': 'error'
        })


@login_required
@require_http_methods(["POST"])
def upload_data(request):
    """
    Handle data file uploads for AI processing.
    """
    try:
        ai_service = AIAnalyticsService()
        
        if 'file' not in request.FILES:
            messages.error(request, "No file was uploaded")
            return redirect('ai_services:ai_home')
        
        uploaded_file = request.FILES['file']
        data_type = request.POST.get('data_type', 'csv')
        
        # Process the uploaded data
        result = ai_service.process_uploaded_data(
            user=request.user,
            file_data=uploaded_file,
            data_type=data_type
        )
        
        if result['success']:
            processing_result = result['data']
            messages.success(
                request, 
                f"Data uploaded successfully. Processed {processing_result['rows_processed']} rows."
            )
        else:
            messages.error(request, f"Error processing data: {result['error']}")
            
    except Exception as e:
        messages.error(request, f"Error uploading data: {str(e)}")
    
    return redirect('ai_services:ai_home')


@login_required
def meeting_analytics(request):
    """
    Display meeting analytics page.
    """
    try:
        ai_service = AIAnalyticsService()
        
        # Get date range from request or default to last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        if request.GET.get('start_date'):
            start_date = datetime.fromisoformat(request.GET['start_date'])
        if request.GET.get('end_date'):
            end_date = datetime.fromisoformat(request.GET['end_date'])
        
        # Analyze meeting data
        analysis_response = ai_service.analyze_meeting_data(
            user=request.user,
            start_date=start_date,
            end_date=end_date
        )
        
        if analysis_response['success']:
            analysis_data = analysis_response['data']
        else:
            messages.error(request, f"Error analyzing meeting data: {analysis_response['error']}")
            analysis_data = {}
        
        context = {
            'analysis_data': analysis_data,
            'start_date': start_date.date(),
            'end_date': end_date.date(),
            'total_meetings': analysis_data.get('total_meetings', 0),
            'average_duration': analysis_data.get('average_duration', 0)
        }
        
        return render(request, 'ai_services/meeting_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading meeting analytics: {str(e)}")
        return render(request, 'ai_services/meeting_analytics.html', {
            'analysis_data': {},
            'start_date': datetime.now().date(),
            'end_date': datetime.now().date(),
            'total_meetings': 0,
            'average_duration': 0
        })


@login_required
@require_http_methods(["POST"])
def process_whatsapp_data(request):
    """
    Process WhatsApp group data.
    """
    try:
        ai_service = AIAnalyticsService()
        
        # Get group data from request
        group_data_json = request.POST.get('group_data', '[]')
        group_data = json.loads(group_data_json)
        
        # Process WhatsApp groups
        result = ai_service.process_whatsapp_groups(
            user=request.user,
            group_data=group_data
        )
        
        if result['success']:
            processing_result = result['data']
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'data': processing_result
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
def stock_analytics(request):
    """
    Display stock analytics page.
    """
    try:
        ai_service = AIAnalyticsService()
        
        # For now, use empty stock data - in real implementation, 
        # this would fetch from database or external API
        stock_data = []
        
        # Analyze stock data
        analysis_response = ai_service.analyze_stock_data(
            user=request.user,
            stock_data=stock_data
        )
        
        if analysis_response['success']:
            analysis_data = analysis_response['data']
        else:
            messages.error(request, f"Error analyzing stock data: {analysis_response['error']}")
            analysis_data = {}
        
        context = {
            'analysis_data': analysis_data,
            'total_trades': analysis_data.get('total_trades', 0),
            'profit_loss': analysis_data.get('profit_loss', 0),
            'best_stocks': analysis_data.get('best_performing_stocks', []),
            'worst_stocks': analysis_data.get('worst_performing_stocks', [])
        }
        
        return render(request, 'ai_services/stock_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading stock analytics: {str(e)}")
        return render(request, 'ai_services/stock_analytics.html', {
            'analysis_data': {},
            'total_trades': 0,
            'profit_loss': 0,
            'best_stocks': [],
            'worst_stocks': []
        })


@login_required
@require_http_methods(["POST"])
def generate_insights(request):
    """
    Generate AI insights via AJAX.
    """
    try:
        ai_service = AIAnalyticsService()
        
        data_type = request.POST.get('data_type')
        analysis_params = json.loads(request.POST.get('analysis_params', '{}'))
        
        # Generate AI insights
        result = ai_service.generate_ai_insights(
            user=request.user,
            data_type=data_type,
            analysis_parameters=analysis_params
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'insights': result['data']
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
def process_big_data(request):
    """
    Process big data via AJAX.
    """
    try:
        ai_service = AIAnalyticsService()
        
        data_source = request.POST.get('data_source')
        processing_options = json.loads(request.POST.get('processing_options', '{}'))
        
        # Process big data
        result = ai_service.process_big_data(
            user=request.user,
            data_source=data_source,
            processing_options=processing_options
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'processing_result': result['data']
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
def get_dashboard_data(request):
    """
    Get AI analytics dashboard data via AJAX.
    """
    try:
        ai_service = AIAnalyticsService()
        
        # Get dashboard data
        result = ai_service.get_analytics_dashboard_data(request.user)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']['dashboard']
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