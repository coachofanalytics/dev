"""
Professional Services Views

This module contains views specifically for professional services operations.
Extracted from the massive professional_services/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the TrainingService and focus on HTTP request/response handling.
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
from .services import TrainingService


@login_required
def professional_services_home(request):
    """
    Display the professional services home page.
    
    Shows training programs, analytics, and user progress.
    """
    try:
        training_service = TrainingService()
        
        # Get training programs
        programs_response = training_service.get_training_programs(request.user)
        programs = programs_response.get('data', {}).get('training_programs', [])
        
        # Get user progress
        progress_response = training_service.get_user_training_progress(request.user)
        progress = progress_response.get('data', {})
        
        context = {
            'training_programs': programs,
            'user_progress': progress,
            'total_programs': len(programs),
            'completion_percentage': progress.get('completion_percentage', 0)
        }
        
        return render(request, 'professional_services/professional_home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading professional services page: {str(e)}")
        return render(request, 'professional_services/professional_home.html', {
            'training_programs': [],
            'user_progress': {},
            'total_programs': 0,
            'completion_percentage': 0
        })


@login_required
def training_programs(request):
    """
    Display list of training programs.
    """
    try:
        training_service = TrainingService()
        
        # Get training programs
        programs_response = training_service.get_training_programs(request.user)
        programs = programs_response.get('data', {}).get('training_programs', [])
        
        context = {
            'training_programs': programs,
            'total_count': len(programs)
        }
        
        return render(request, 'professional_services/training_programs.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading training programs: {str(e)}")
        return render(request, 'professional_services/training_programs.html', {
            'training_programs': [],
            'total_count': 0
        })


@login_required
def start_training(request, slug=None):
    """
    Start a training program.
    """
    try:
        training_service = TrainingService()
        
        if not slug:
            messages.error(request, "Training program not specified")
            return redirect('professional_services:professional_home')
        
        # Start training
        result = training_service.start_training(request.user, slug)
        
        if result['success']:
            training_session = result['data']
            messages.success(request, f"Training '{slug}' started successfully!")
            return redirect('professional_services:training_progress', training_id=training_session['id'])
        else:
            messages.error(request, f"Error starting training: {result['error']}")
            
    except Exception as e:
        messages.error(request, f"Error starting training: {str(e)}")
    
    return redirect('professional_services:professional_home')


@login_required
def training_progress(request, training_id=None):
    """
    Display user's training progress.
    """
    try:
        training_service = TrainingService()
        
        # Get training progress
        progress_response = training_service.get_user_training_progress(request.user, training_id)
        progress = progress_response.get('data', {})
        
        context = {
            'progress_data': progress,
            'training_id': training_id,
            'completion_percentage': progress.get('completion_percentage', 0),
            'current_training': progress.get('current_training', {})
        }
        
        return render(request, 'professional_services/training_progress.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading training progress: {str(e)}")
        return render(request, 'professional_services/training_progress.html', {
            'progress_data': {},
            'training_id': training_id,
            'completion_percentage': 0,
            'current_training': {}
        })


@login_required
@require_http_methods(["POST"])
def upload_training_material(request):
    """
    Handle training material uploads.
    """
    try:
        training_service = TrainingService()
        
        if 'file' not in request.FILES:
            messages.error(request, "No file was uploaded")
            return redirect('professional_services:training_programs')
        
        uploaded_file = request.FILES['file']
        training_id = request.POST.get('training_id')
        material_type = request.POST.get('material_type', 'document')
        
        if not training_id:
            messages.error(request, "Training ID is required")
            return redirect('professional_services:training_programs')
        
        # Upload training material
        result = training_service.upload_training_material(
            user=request.user,
            file_data=uploaded_file,
            training_id=int(training_id),
            material_type=material_type
        )
        
        if result['success']:
            upload_result = result['data']
            messages.success(
                request, 
                f"Material uploaded successfully: {upload_result['file_name']}"
            )
        else:
            messages.error(request, f"Error uploading material: {result['error']}")
            
    except Exception as e:
        messages.error(request, f"Error uploading material: {str(e)}")
    
    return redirect('professional_services:training_programs')


@login_required
def training_analytics(request, training_id=None):
    """
    Display training analytics.
    """
    try:
        training_service = TrainingService()
        
        # Get training analytics
        analytics_response = training_service.get_training_analytics(request.user, training_id)
        analytics = analytics_response.get('data', {})
        
        context = {
            'analytics_data': analytics,
            'training_id': training_id,
            'total_participants': analytics.get('total_participants', 0),
            'completion_rate': analytics.get('completion_rate', 0),
            'average_rating': analytics.get('user_feedback', {}).get('average_rating', 0)
        }
        
        return render(request, 'professional_services/training_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading training analytics: {str(e)}")
        return render(request, 'professional_services/training_analytics.html', {
            'analytics_data': {},
            'training_id': training_id,
            'total_participants': 0,
            'completion_rate': 0,
            'average_rating': 0
        })


@login_required
@require_http_methods(["POST"])
def generate_training_report(request):
    """
    Generate training report via AJAX.
    """
    try:
        training_service = TrainingService()
        
        report_type = request.POST.get('report_type', 'summary')
        date_range = None
        
        if request.POST.get('start_date') and request.POST.get('end_date'):
            date_range = {
                'start_date': datetime.fromisoformat(request.POST['start_date']),
                'end_date': datetime.fromisoformat(request.POST['end_date'])
            }
        
        # Generate training report
        result = training_service.generate_training_report(
            user=request.user,
            report_type=report_type,
            date_range=date_range
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'report_data': result['data']
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
def get_training_dashboard_data(request):
    """
    Get training dashboard data via AJAX.
    """
    try:
        training_service = TrainingService()
        
        # Get training programs
        programs_response = training_service.get_training_programs(request.user)
        programs = programs_response.get('data', {}).get('training_programs', [])
        
        # Get user progress
        progress_response = training_service.get_user_training_progress(request.user)
        progress = progress_response.get('data', {})
        
        dashboard_data = {
            'training_programs': programs,
            'user_progress': progress,
            'total_programs': len(programs),
            'completion_percentage': progress.get('completion_percentage', 0)
        }
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def course_overview(request, question_type=None):
    """
    Display course overview.
    """
    try:
        training_service = TrainingService()
        
        # Get training programs for course overview
        programs_response = training_service.get_training_programs(request.user)
        programs = programs_response.get('data', {}).get('training_programs', [])
        
        context = {
            'training_programs': programs,
            'question_type': question_type,
            'total_courses': len(programs)
        }
        
        return render(request, 'professional_services/course_overview.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading course overview: {str(e)}")
        return render(request, 'professional_services/course_overview.html', {
            'training_programs': [],
            'question_type': question_type,
            'total_courses': 0
        })





