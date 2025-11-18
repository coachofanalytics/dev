"""
Compliance KPI Views for Management App

Phase 3: Advanced Analytics
API endpoints for compliance KPI tracking and real-time monitoring.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from management.services.compliance_kpi_service import ComplianceKPIService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def compliance_kpis_api(request):
    """
    API endpoint for real-time compliance KPIs.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        department_id: Optional department filter
        month: Target month (default: last month)
        year: Target year (default: current year)
    
    Returns:
        JSON response with compliance KPIs
    """
    try:
        department_id = request.GET.get('department_id')
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        # Convert to integers if provided
        department_id = int(department_id) if department_id else None
        month = int(month) if month else None
        year = int(year) if year else None
        
        # Initialize compliance KPI service
        kpi_service = ComplianceKPIService()
        
        # Get real-time KPIs
        kpis_result = kpi_service.get_realtime_compliance_kpis(
            department_id=department_id,
            target_month=month,
            target_year=year
        )
        
        if not kpis_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [kpis_result.get('message', 'Compliance KPI retrieval failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'period': kpis_result.get('period', {}),
                'overall_metrics': kpis_result.get('overall_metrics', {}),
                'employee_details': kpis_result.get('employee_details', []),
                'department_breakdown': kpis_result.get('department_breakdown', []),
                'trends': kpis_result.get('trends', {}),
                'alerts': kpis_result.get('alerts', [])
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'timestamp': kpis_result.get('timestamp')
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in compliance_kpis_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in compliance_kpis_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)


@login_required
@require_http_methods(["GET"])
def compliance_history_api(request):
    """
    API endpoint for historical compliance data.
    
    Phase 3: Advanced Analytics
    
    Query Parameters:
        months_back: Number of months to analyze (default: 12)
        department_id: Optional department filter
    
    Returns:
        JSON response with historical compliance data
    """
    try:
        months_back = int(request.GET.get('months_back', 12))
        department_id = request.GET.get('department_id')
        
        # Validate parameters
        if months_back < 1 or months_back > 24:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['months_back must be between 1 and 24']
            }, status=400)
        
        # Convert ID to integer if provided
        department_id = int(department_id) if department_id else None
        
        # Initialize compliance KPI service
        kpi_service = ComplianceKPIService()
        
        # Get compliance history
        history_result = kpi_service.get_compliance_history(
            months_back=months_back,
            department_id=department_id
        )
        
        if not history_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [history_result.get('message', 'Compliance history retrieval failed')]
            }, status=400)
        
        # Build response
        response_data = {
            'data': {
                'historical_data': history_result.get('historical_data', []),
                'trend': history_result.get('trend', {})
            },
            'meta': {
                'requested_at': timezone.now().isoformat(),
                'months_back': months_back,
                'department_id': department_id
            },
            'errors': []
        }
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid parameter in compliance_history_api: {e}")
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in compliance_history_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)

