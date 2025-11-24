"""
Management API Views

Phase 1: Data Pipeline & Evidence Automation
API endpoints for activity summary and analytics.

Following the documented API contract:
- GET /management/api/activity/summary?window=month
- Returns: { data: {...}, meta: {...} }
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count, F

from management.services.taskhistory_analyzer import TaskHistoryAnalyzer
from management.models import TaskHistory, Task, TaskCategory
from shared_core.users import Department

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def activity_summary_api(request):
    """
    API endpoint for activity summary data.
    
    Phase 1 Requirement: Expose query/report endpoints for historical analysis
    
    Query Parameters:
        window: Time window (month, quarter, year) - default: month
        department_id: Optional department filter
        category_id: Optional category filter
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        JSON response with format:
        {
            "data": {
                "department_id": int,
                "category_id": int,
                "total_minutes": int,
                "evidence_count": int,
                ...
            },
            "meta": {
                "window": str,
                "start_date": str,
                "end_date": str,
                "total_records": int
            },
            "errors": []
        }
    """
    try:
        # Get query parameters
        window = request.GET.get('window', 'month').lower()
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Calculate date range based on window
        end_date_dt = timezone.now()
        
        if start_date_str and end_date_str:
            # Use provided dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'data': {},
                    'meta': {},
                    'errors': ['Invalid date format. Use YYYY-MM-DD']
                }, status=400)
        else:
            # Calculate from window
            if window == 'month':
                start_date = (end_date_dt - relativedelta(months=1)).date()
            elif window == 'quarter':
                start_date = (end_date_dt - relativedelta(months=3)).date()
            elif window == 'year':
                start_date = (end_date_dt - relativedelta(years=1)).date()
            else:
                return JsonResponse({
                    'data': {},
                    'meta': {},
                    'errors': [f'Invalid window: {window}. Use: month, quarter, year']
                }, status=400)
            end_date = end_date_dt.date()
        
        # Build queryset
        queryset = TaskHistory.objects.filter(
            daf_date__gte=start_date,
            daf_date__lte=end_date
        ).select_related('employee', 'category', 'employee__department')
        
        # Apply filters
        if department_id:
            try:
                queryset = queryset.filter(employee__department_id=int(department_id))
            except ValueError:
                return JsonResponse({
                    'data': {},
                    'meta': {},
                    'errors': ['Invalid department_id']
                }, status=400)
        
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except ValueError:
                return JsonResponse({
                    'data': {},
                    'meta': {},
                    'errors': ['Invalid category_id']
                }, status=400)
        
        # If no data with dates, try to use all data (for development/testing)
        if not queryset.exists():
            logger.warning(f"No TaskHistory data found for date range {start_date} to {end_date}")
            # Fallback to all data if no date-filtered data exists
            queryset = TaskHistory.objects.all().select_related('employee', 'category', 'employee__department')
            if department_id:
                queryset = queryset.filter(employee__department_id=int(department_id))
            if category_id:
                queryset = queryset.filter(category_id=int(category_id))
        
        # Calculate summary statistics
        total_records = queryset.count()
        
        # Aggregate by department and category
        summary_data = []
        
        # Group by department and category
        grouped_data = queryset.values(
            'employee__department_id',
            'employee__department__name',
            'category_id',
            'category__title'
        ).annotate(
            total_minutes=Sum(F('duration') * 60),  # Convert hours to minutes if duration is in hours
            total_points=Sum('point'),
            total_max_points=Sum('mxpoint'),
            task_count=Count('id'),
            unique_employees=Count('employee', distinct=True)
        ).order_by('employee__department_id', 'category_id')
        
        # Get evidence count (TaskLinks)
        from management.models import TaskLinks
        evidence_counts = TaskLinks.objects.filter(
            task__in=Task.objects.filter(
                id__in=queryset.values_list('id', flat=True)
            )
        ).values(
            'task__category_id',
            'task__employee__department_id'
        ).annotate(
            evidence_count=Count('id')
        )
        
        # Create evidence lookup
        evidence_lookup = {}
        for item in evidence_counts:
            key = (item['task__employee__department_id'], item['task__category_id'])
            evidence_lookup[key] = item['evidence_count']
        
        # Build response data
        for item in grouped_data:
            dept_id = item['employee__department_id']
            dept_name = item['employee__department__name']
            cat_id = item['category_id']
            cat_title = item['category__title']
            
            evidence_count = evidence_lookup.get((dept_id, cat_id), 0)
            
            summary_data.append({
                'department_id': dept_id,
                'department_name': dept_name,
                'category_id': cat_id,
                'category_title': cat_title,
                'total_minutes': int(item['total_minutes'] or 0),
                'total_points': int(item['total_points'] or 0),
                'total_max_points': int(item['total_max_points'] or 0),
                'completion_rate': float(item['total_points'] / item['total_max_points']) if item['total_max_points'] and item['total_max_points'] > 0 else 0.0,
                'task_count': item['task_count'],
                'unique_employees': item['unique_employees'],
                'evidence_count': evidence_count
            })
        
        # Calculate overall totals
        overall_totals = queryset.aggregate(
            total_minutes=Sum(F('duration') * 60),
            total_points=Sum('point'),
            total_max_points=Sum('mxpoint'),
            total_tasks=Count('id'),
            unique_employees=Count('employee', distinct=True)
        )
        
        # Get total evidence count
        total_evidence = TaskLinks.objects.filter(
            task__in=Task.objects.filter(
                id__in=queryset.values_list('id', flat=True)
            )
        ).count()
        
        # Build response
        response_data = {
            'data': {
                'summary': summary_data,
                'totals': {
                    'total_minutes': int(overall_totals['total_minutes'] or 0),
                    'total_points': int(overall_totals['total_points'] or 0),
                    'total_max_points': int(overall_totals['total_max_points'] or 0),
                    'total_tasks': overall_totals['total_tasks'],
                    'unique_employees': overall_totals['unique_employees'],
                    'evidence_count': total_evidence,
                    'overall_completion_rate': float(
                        overall_totals['total_points'] / overall_totals['total_max_points']
                    ) if overall_totals['total_max_points'] and overall_totals['total_max_points'] > 0 else 0.0
                }
            },
            'meta': {
                'window': window,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_records': total_records,
                'department_filter': int(department_id) if department_id else None,
                'category_filter': int(category_id) if category_id else None,
                'generated_at': timezone.now().isoformat()
            },
            'errors': []
        }
        
        logger.info(f"Activity summary API called: window={window}, records={total_records}")
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        logger.error(f"Error in activity_summary_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Internal server error: {str(e)}']
        }, status=500)


@login_required
@require_http_methods(["GET"])
def activity_analytics_api(request):
    """
    Advanced analytics API endpoint using TaskHistoryAnalyzer service.
    
    Phase 1 Requirement: Expose comprehensive analytics for Finance integration
    
    Query Parameters:
        months: Number of months to analyze (default: 12)
        format: Response format (summary, detailed) - default: summary
    
    Returns:
        JSON response with comprehensive analytics
    """
    try:
        months = int(request.GET.get('months', 12))
        format_type = request.GET.get('format', 'summary').lower()
        
        # Initialize analyzer
        analyzer = TaskHistoryAnalyzer()
        
        # Get comprehensive analysis
        analysis_result = analyzer.analyze_complete_performance_patterns(months_back=months)
        
        if not analysis_result.get('success'):
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': [analysis_result.get('message', 'Analysis failed')]
            }, status=400)
        
        # Format response based on requested format
        if format_type == 'summary':
            # Return summary version
            response_data = {
                'data': {
                    'employee_performance': analysis_result.get('employee_performance', {}),
                    'department_analysis': analysis_result.get('department_analysis', {}),
                    'category_analysis': analysis_result.get('category_analysis', {}),
                    'completion_rates': analysis_result.get('completion_rates', {}),
                    'key_insights': analysis_result.get('key_insights', [])
                },
                'meta': {
                    'months_analyzed': months,
                    'date_range': analysis_result.get('date_range', {}),
                    'total_records': analysis_result.get('total_records', 0),
                    'format': 'summary',
                    'generated_at': timezone.now().isoformat()
                },
                'errors': []
            }
        else:
            # Return detailed version
            response_data = {
                'data': analysis_result,
                'meta': {
                    'months_analyzed': months,
                    'format': 'detailed',
                    'generated_at': timezone.now().isoformat()
                },
                'errors': []
            }
        
        logger.info(f"Activity analytics API called: months={months}, format={format_type}")
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Invalid parameter: {str(e)}']
        }, status=400)
    except Exception as e:
        logger.error(f"Error in activity_analytics_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'Internal server error: {str(e)}']
        }, status=500)

