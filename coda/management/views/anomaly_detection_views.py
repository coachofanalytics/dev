"""
Anomaly Detection Views for Management App

Phase 3: Advanced Analytics
API endpoints for anomaly detection and automated alerts.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from management.services.anomaly_detection_service import AnomalyDetectionService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def anomaly_detection_api(request):
    """
    API endpoint for anomaly detection.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        month: Target month (default: last month)
        year: Target year (default: current year)
        department_id: Optional department filter
    
    Returns:
        JSON response with detected anomalies
    """
    try:
        month = request.GET.get('month')
        year = request.GET.get('year')
        department_id = request.GET.get('department_id')
        
        # Convert to integers if provided
        month = int(month) if month else None
        year = int(year) if year else None
        department_id = int(department_id) if department_id else None
        
        # Initialize anomaly detection service
        anomaly_service = AnomalyDetectionService()
        
        # Detect anomalies
        anomalies_result = anomaly_service.detect_anomalies(
            target_month=month,
            target_year=year,
            department_id=department_id
        )
        
        if not anomalies_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [anomalies_result.get('message', 'Anomaly detection failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'period': anomalies_result.get('period', {}),
                'summary': anomalies_result.get('summary', {}),
                'anomalies': anomalies_result.get('anomalies', {})
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'timestamp': anomalies_result.get('timestamp')
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in anomaly_detection_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in anomaly_detection_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)

