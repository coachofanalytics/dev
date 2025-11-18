"""
Analytics Dashboard Views for Management App

Phase 3: Advanced Analytics
Dashboard views for displaying analytics data in a user-friendly format.
"""

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
try:
    from core.permissions import require_employee, require_manager
except ImportError:
    from accounts.permissions import require_employee, require_manager

from management.services.forecasting_service import ForecastingService
from management.services.trend_analysis_service import TrendAnalysisService
from management.services.compliance_kpi_service import ComplianceKPIService
from management.services.anomaly_detection_service import AnomalyDetectionService

logger = logging.getLogger(__name__)


@require_employee
def analytics_dashboard(request):
    """
    Analytics Dashboard - Main analytics hub for Phase 3 features.
    
    Displays all Phase 3 analytics in a unified dashboard.
    """
    try:
        user = request.user
        
        # Get parameters
        months_ahead = int(request.GET.get('months_ahead', 3))
        months_back = int(request.GET.get('months_back', 12))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        
        # Convert IDs to integers if provided
        department_id = int(department_id) if department_id else None
        category_id = int(category_id) if category_id else None
        
        # Initialize services
        forecasting_service = ForecastingService()
        trend_service = TrendAnalysisService()
        compliance_service = ComplianceKPIService()
        anomaly_service = AnomalyDetectionService()
        
        # Get analytics data
        context = {
            'user': user,
            'months_ahead': months_ahead,
            'months_back': months_back,
        }
        
        # Try to get forecasting data
        try:
            activity_forecast = forecasting_service.forecast_activity_trends(
                months_ahead=months_ahead,
                department_id=department_id,
                category_id=category_id
            )
            context['activity_forecast'] = activity_forecast
        except Exception as e:
            logger.warning(f"Could not load activity forecast: {e}")
            context['activity_forecast'] = None
        
        try:
            budget_forecast = forecasting_service.forecast_budget_needs(
                months_ahead=months_ahead,
                department_id=department_id
            )
            context['budget_forecast'] = budget_forecast
        except Exception as e:
            logger.warning(f"Could not load budget forecast: {e}")
            context['budget_forecast'] = None
        
        # Try to get trend analysis
        try:
            trend_analysis = trend_service.analyze_historical_trends(
                months_back=months_back,
                department_id=department_id,
                category_id=category_id,
                employee_id=user.id if not request.user.is_superuser else None
            )
            context['trend_analysis'] = trend_analysis
        except Exception as e:
            logger.warning(f"Could not load trend analysis: {e}")
            context['trend_analysis'] = None
        
        # Try to get compliance KPIs
        try:
            compliance_kpis = compliance_service.get_realtime_compliance_kpis(
                department_id=department_id
            )
            context['compliance_kpis'] = compliance_kpis
        except Exception as e:
            logger.warning(f"Could not load compliance KPIs: {e}")
            context['compliance_kpis'] = None
        
        # Try to get anomaly detection
        try:
            anomalies = anomaly_service.detect_anomalies(
                department_id=department_id
            )
            context['anomalies'] = anomalies
        except Exception as e:
            logger.warning(f"Could not load anomalies: {e}")
            context['anomalies'] = None
        
        return render(request, 'management/analytics/analytics_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading analytics dashboard: {e}", exc_info=True)
        return render(request, 'management/analytics/analytics_dashboard.html', {
            'error': str(e),
            'user': request.user
        })


@require_employee
@require_http_methods(["GET"])
def activity_forecast_dashboard(request):
    """Activity Forecast Dashboard - Forecast activity trends."""
    try:
        months_ahead = int(request.GET.get('months_ahead', 3))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        
        department_id = int(department_id) if department_id else None
        category_id = int(category_id) if category_id else None
        
        forecasting_service = ForecastingService()
        forecast = forecasting_service.forecast_activity_trends(
            months_ahead=months_ahead,
            department_id=department_id,
            category_id=category_id
        )
        
        return render(request, 'management/analytics/activity_forecast_dashboard.html', {
            'forecast': forecast,
            'user': request.user
        })
    except Exception as e:
        logger.error(f"Error loading activity forecast dashboard: {e}")
        return render(request, 'management/analytics/activity_forecast_dashboard.html', {
            'error': str(e),
            'user': request.user
        })


@require_employee
@require_http_methods(["GET"])
def trend_analysis_dashboard(request):
    """Trend Analysis Dashboard - Analyze historical trends and patterns."""
    try:
        months_back = int(request.GET.get('months_back', 12))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        employee_id = request.GET.get('employee_id')
        
        department_id = int(department_id) if department_id else None
        category_id = int(category_id) if category_id else None
        employee_id = int(employee_id) if employee_id else None
        
        trend_service = TrendAnalysisService()
        analysis = trend_service.analyze_historical_trends(
            months_back=months_back,
            department_id=department_id,
            category_id=category_id,
            employee_id=employee_id
        )
        
        return render(request, 'management/analytics/trend_analysis_dashboard.html', {
            'analysis': analysis,
            'user': request.user
        })
    except Exception as e:
        logger.error(f"Error loading trend analysis dashboard: {e}")
        return render(request, 'management/analytics/trend_analysis_dashboard.html', {
            'error': str(e),
            'user': request.user
        })


@require_manager
@require_http_methods(["GET"])
def compliance_dashboard(request):
    """Compliance Dashboard - Real-time compliance monitoring and KPIs."""
    try:
        department_id = request.GET.get('department_id')
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        department_id = int(department_id) if department_id else None
        month = int(month) if month else None
        year = int(year) if year else None
        
        compliance_service = ComplianceKPIService()
        kpis = compliance_service.get_realtime_compliance_kpis(
            department_id=department_id,
            target_month=month,
            target_year=year
        )
        
        history = compliance_service.get_compliance_history(
            months_back=12,
            department_id=department_id
        )
        
        return render(request, 'management/analytics/compliance_dashboard.html', {
            'kpis': kpis,
            'history': history,
            'user': request.user
        })
    except Exception as e:
        logger.error(f"Error loading compliance dashboard: {e}")
        return render(request, 'management/analytics/compliance_dashboard.html', {
            'error': str(e),
            'user': request.user
        })


@require_manager
@require_http_methods(["GET"])
def anomaly_detection_dashboard(request):
    """Anomaly Detection Dashboard - Automated anomaly detection and alerts."""
    try:
        department_id = request.GET.get('department_id')
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        department_id = int(department_id) if department_id else None
        month = int(month) if month else None
        year = int(year) if year else None
        
        anomaly_service = AnomalyDetectionService()
        anomalies = anomaly_service.detect_anomalies(
            department_id=department_id,
            target_month=month,
            target_year=year
        )
        
        return render(request, 'management/analytics/anomaly_detection_dashboard.html', {
            'anomalies': anomalies,
            'user': request.user
        })
    except Exception as e:
        logger.error(f"Error loading anomaly detection dashboard: {e}")
        return render(request, 'management/analytics/anomaly_detection_dashboard.html', {
            'error': str(e),
            'user': request.user
        })

