"""
Trend Analysis Views for Management App

Phase 3: Advanced Analytics
API endpoints for trend analysis and pattern detection.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from management.services.trend_analysis_service import TrendAnalysisService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def trend_analysis_api(request):
    """
    API endpoint for historical trend analysis.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        months_back: Number of months to analyze (default: 12)
        department_id: Optional department filter
        category_id: Optional category filter
        employee_id: Optional employee filter
    
    Returns:
        JSON response with trend analysis data
    """
    try:
        months_back = int(request.GET.get('months_back', 12))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        employee_id = request.GET.get('employee_id')
        
        # Validate parameters
        if months_back < 1 or months_back > 24:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['months_back must be between 1 and 24']
            }, status=400)
        
        # Convert IDs to integers if provided
        department_id = int(department_id) if department_id else None
        category_id = int(category_id) if category_id else None
        employee_id = int(employee_id) if employee_id else None
        
        # Initialize trend analysis service
        trend_service = TrendAnalysisService()
        
        # Get trend analysis
        analysis_result = trend_service.analyze_historical_trends(
            months_back=months_back,
            department_id=department_id,
            category_id=category_id,
            employee_id=employee_id
        )
        
        if not analysis_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [analysis_result.get('message', 'Trend analysis failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'period': analysis_result.get('period', {}),
                'monthly_trends': analysis_result.get('monthly_trends', []),
                'category_trends': analysis_result.get('category_trends', []),
                'department_trends': analysis_result.get('department_trends', []),
                'seasonal_patterns': analysis_result.get('seasonal_patterns', {}),
                'anomalies': analysis_result.get('anomalies', []),
                'overall_trends': analysis_result.get('overall_trends', {})
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'parameters': analysis_result.get('metadata', {})
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in trend_analysis_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in trend_analysis_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)


@login_required
@require_http_methods(["GET"])
def employee_trend_analysis_api(request, employee_id: int):
    """
    API endpoint for employee-specific trend analysis.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        months_back: Number of months to analyze (default: 12)
    
    Returns:
        JSON response with employee trend analysis
    """
    try:
        months_back = int(request.GET.get('months_back', 12))
        
        # Validate parameters
        if months_back < 1 or months_back > 24:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['months_back must be between 1 and 24']
            }, status=400)
        
        # Initialize trend analysis service
        trend_service = TrendAnalysisService()
        
        # Get employee trend analysis
        analysis_result = trend_service.analyze_employee_trends(
            employee_id=employee_id,
            months_back=months_back
        )
        
        if not analysis_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [analysis_result.get('message', 'Employee trend analysis failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'employee_id': employee_id,
                'period': analysis_result.get('period', {}),
                'monthly_trends': analysis_result.get('monthly_trends', []),
                'overall_trends': analysis_result.get('overall_trends', {}),
                'anomalies': analysis_result.get('anomalies', [])
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'months_back': months_back
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in employee_trend_analysis_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in employee_trend_analysis_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)

