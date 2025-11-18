"""
Forecasting Views for Management App

Phase 3: Advanced Analytics
API endpoints for forecasting activity trends and budget needs.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from management.services.forecasting_service import ForecastingService
from accounts.models import Department
from management.models import TaskCategory

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def activity_forecast_api(request):
    """
    API endpoint for forecasting activity trends.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        months_ahead: Number of months to forecast (default: 3)
        department_id: Optional department filter
        category_id: Optional category filter
        historical_months: Historical data to analyze (default: 12)
    
    Returns:
        JSON response with forecast data
    """
    try:
        months_ahead = int(request.GET.get('months_ahead', 3))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        historical_months = int(request.GET.get('historical_months', 12))
        
        # Validate parameters
        if months_ahead < 1 or months_ahead > 12:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['months_ahead must be between 1 and 12']
            }, status=400)
        
        if historical_months < 3 or historical_months > 24:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['historical_months must be between 3 and 24']
            }, status=400)
        
        # Convert IDs to integers if provided
        department_id = int(department_id) if department_id else None
        category_id = int(category_id) if category_id else None
        
        # Initialize forecasting service
        forecasting_service = ForecastingService()
        
        # Get forecast
        forecast_result = forecasting_service.forecast_activity_trends(
            months_ahead=months_ahead,
            department_id=department_id,
            category_id=category_id,
            historical_months=historical_months
        )
        
        if not forecast_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [forecast_result.get('message', 'Forecast failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'forecast_period': forecast_result.get('forecast_period'),
                'historical_data': forecast_result.get('historical_data', []),
                'forecasted_data': forecast_result.get('forecasted_data', []),
                'trends': forecast_result.get('trends', {}),
                'confidence': forecast_result.get('confidence', 0.0),
                'insights': forecast_result.get('insights', [])
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'parameters': forecast_result.get('metadata', {})
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in activity_forecast_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in activity_forecast_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)


@login_required
@require_http_methods(["GET"])
def budget_forecast_api(request):
    """
    API endpoint for forecasting budget needs.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        months_ahead: Number of months to forecast (default: 3)
        department_id: Optional department filter
        historical_months: Historical data to analyze (default: 12)
    
    Returns:
        JSON response with budget forecast
    """
    try:
        months_ahead = int(request.GET.get('months_ahead', 3))
        department_id = request.GET.get('department_id')
        historical_months = int(request.GET.get('historical_months', 12))
        
        # Validate parameters
        if months_ahead < 1 or months_ahead > 12:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['months_ahead must be between 1 and 12']
            }, status=400)
        
        if historical_months < 3 or historical_months > 24:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['historical_months must be between 3 and 24']
            }, status=400)
        
        # Convert ID to integer if provided
        department_id = int(department_id) if department_id else None
        
        # Initialize forecasting service
        forecasting_service = ForecastingService()
        
        # Get budget forecast
        forecast_result = forecasting_service.forecast_budget_needs(
            months_ahead=months_ahead,
            department_id=department_id,
            historical_months=historical_months
        )
        
        if not forecast_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [forecast_result.get('message', 'Budget forecast failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'forecast_period': forecast_result.get('forecast_period'),
                'total_forecasted_earnings': forecast_result.get('total_forecasted_earnings', 0),
                'monthly_forecasts': forecast_result.get('monthly_forecasts', []),
                'trends': forecast_result.get('trends', {}),
                'confidence': forecast_result.get('confidence', 0.0),
                'insights': forecast_result.get('insights', [])
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'months_ahead': months_ahead,
                'department_id': department_id
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in budget_forecast_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in budget_forecast_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)

