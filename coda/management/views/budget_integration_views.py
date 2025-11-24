"""
Management Budget Integration API Views

Phase 2: Budget Integration
API endpoints for Finance app to consume validated activity data.

Following the documented API contract:
- GET /management/api/budget/activity-totals?month=10&year=2025
- GET /management/api/budget/evidence-validation?month=10&year=2025
- Returns: { data: {...}, meta: {...}, errors: [] }
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count, F, Avg
from django.db import transaction

from management.models import TaskHistory, TaskLinks, Task, TaskCategory
from management.services.taskhistory_analyzer import TaskHistoryAnalyzer
from shared_core.users import CustomerUser, Department

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def budget_activity_totals_api(request):
    """
    API endpoint for validated activity totals for budget estimation.
    
    Phase 2 Requirement: Provide validated activity totals to Finance
    
    Query Parameters:
        month: Target month (1-12) - default: last month
        year: Target year (YYYY) - default: current year
        department_id: Optional department filter
        category_id: Optional category filter
        include_evidence: Include evidence counts (default: true)
        include_validation: Include validation status (default: true)
    
    Returns:
        JSON response with validated activity totals:
        {
            "data": {
                "period": "10/2025",
                "totals": {
                    "total_minutes": int,
                    "total_points": Decimal,
                    "total_max_points": Decimal,
                    "total_earnings": Decimal,
                    "completion_rate": float,
                    "task_count": int,
                    "unique_employees": int
                },
                "by_department": [...],
                "by_category": [...],
                "evidence_summary": {...},
                "validation_status": {...}
            },
            "meta": {
                "month": int,
                "year": int,
                "generated_at": "ISO datetime",
                "department_filter": int|null,
                "category_filter": int|null
            },
            "errors": []
        }
    """
    try:
        # Get query parameters
        current_date = date.today()
        last_month = current_date - relativedelta(months=1)
        
        month = int(request.GET.get('month', last_month.month))
        year = int(request.GET.get('year', last_month.year))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        include_evidence = request.GET.get('include_evidence', 'true').lower() == 'true'
        include_validation = request.GET.get('include_validation', 'true').lower() == 'true'
        
        # Validate month/year
        if month < 1 or month > 12:
            return JsonResponse({
                'data': {},
                'meta': {},
                'errors': ['Invalid month. Must be 1-12']
            }, status=400)
        
        # Build base queryset
        queryset = TaskHistory.objects.filter(
            daf_date__month=month,
            daf_date__year=year,
            employee__is_active=True,
            employee__is_staff=True
        ).exclude(
            employee__username__in=['coda_info', 'luke', 'angel']
        ).select_related('employee', 'category', 'employee__department')
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(employee__department__id=department_id)
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        
        # Calculate totals
        totals = queryset.aggregate(
            total_minutes=Sum('duration'),
            total_points=Sum('point'),
            total_max_points=Sum('mxpoint'),
            total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning')),
            task_count=Count('id'),
            unique_employees=Count('employee', distinct=True)
        )
        
        # Calculate completion rate
        total_points = totals['total_points'] or Decimal('0')
        total_max_points = totals['total_max_points'] or Decimal('0')
        completion_rate = float(total_points / total_max_points) if total_max_points > 0 else 0.0
        
        # Group by department
        by_department = queryset.values(
            'employee__department__id',
            'employee__department__name'
        ).annotate(
            total_minutes=Sum('duration'),
            total_points=Sum('point'),
            total_max_points=Sum('mxpoint'),
            total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning')),
            task_count=Count('id'),
            unique_employees=Count('employee', distinct=True)
        ).order_by('employee__department__name')
        
        # Format department data
        department_data = []
        for dept in by_department:
            dept_points = dept['total_points'] or Decimal('0')
            dept_max_points = dept['total_max_points'] or Decimal('0')
            dept_completion = float(dept_points / dept_max_points) if dept_max_points > 0 else 0.0
            
            department_data.append({
                'department_id': dept['employee__department__id'],
                'department_name': dept['employee__department__name'],
                'total_minutes': dept['total_minutes'] or 0,
                'total_points': float(dept_points),
                'total_max_points': float(dept_max_points),
                'total_earnings': float(dept['total_earnings'] or 0),
                'completion_rate': round(dept_completion, 2),
                'task_count': dept['task_count'],
                'unique_employees': dept['unique_employees']
            })
        
        # Group by category
        by_category = queryset.values(
            'category__id',
            'category__title'
        ).annotate(
            total_minutes=Sum('duration'),
            total_points=Sum('point'),
            total_max_points=Sum('mxpoint'),
            total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning')),
            task_count=Count('id'),
            unique_employees=Count('employee', distinct=True)
        ).order_by('category__title')
        
        # Format category data
        category_data = []
        for cat in by_category:
            cat_points = cat['total_points'] or Decimal('0')
            cat_max_points = cat['total_max_points'] or Decimal('0')
            cat_completion = float(cat_points / cat_max_points) if cat_max_points > 0 else 0.0
            
            category_data.append({
                'category_id': cat['category__id'],
                'category_title': cat['category__title'],
                'total_minutes': cat['total_minutes'] or 0,
                'total_points': float(cat_points),
                'total_max_points': float(cat_max_points),
                'total_earnings': float(cat['total_earnings'] or 0),
                'completion_rate': round(cat_completion, 2),
                'task_count': cat['task_count'],
                'unique_employees': cat['unique_employees']
            })
        
        # Evidence summary (if requested)
        evidence_summary = {}
        if include_evidence:
            # Count tasks with evidence (TaskLinks)
            # Note: TaskLinks references Task, not TaskHistory
            # Match TaskHistory to Task by activity_name and employee, then find TaskLinks
            task_history_pairs = queryset.values_list('activity_name', 'employee').distinct()
            
            # Find Tasks that match TaskHistory records
            matching_tasks = Task.objects.filter(
                activity_name__in=queryset.values_list('activity_name', flat=True),
                employee__in=queryset.values_list('employee', flat=True)
            )
            
            # Find TaskLinks for matching Tasks
            task_ids_with_evidence = TaskLinks.objects.filter(
                task__in=matching_tasks,
                is_active=True
            ).values_list('task__id', flat=True).distinct()
            
            # Count TaskHistory records that have corresponding Task with evidence
            tasks_with_evidence = queryset.filter(
                activity_name__in=Task.objects.filter(
                    id__in=task_ids_with_evidence
                ).values_list('activity_name', flat=True),
                employee__in=Task.objects.filter(
                    id__in=task_ids_with_evidence
                ).values_list('employee', flat=True)
            ).distinct().count()
            
            total_tasks = totals['task_count'] or 0
            evidence_coverage = (tasks_with_evidence / total_tasks * 100) if total_tasks > 0 else 0.0
            
            evidence_summary = {
                'tasks_with_evidence': tasks_with_evidence,
                'total_tasks': total_tasks,
                'evidence_coverage_percent': round(evidence_coverage, 2),
                'tasks_without_evidence': total_tasks - tasks_with_evidence
            }
        
        # Validation status (if requested)
        validation_status = {}
        if include_validation:
            # Calculate validation metrics
            total_tasks = totals['task_count'] or 0
            # Use same evidence counting logic as evidence_summary
            if include_evidence and evidence_summary:
                tasks_with_evidence_count = evidence_summary.get('tasks_with_evidence', 0)
            else:
                tasks_with_evidence_count = 0
            
            # Compliance check (33% threshold)
            compliant_employees = queryset.values('employee').annotate(
                emp_points=Sum('point'),
                emp_max_points=Sum('mxpoint')
            ).filter(
                emp_max_points__gt=0
            ).annotate(
                compliance_rate=F('emp_points') / F('emp_max_points') * 100
            ).filter(
                compliance_rate__gte=33
            ).count()
            
            total_employees = totals['unique_employees'] or 0
            compliance_rate = (compliant_employees / total_employees * 100) if total_employees > 0 else 0.0
            
            validation_status = {
                'is_validated': completion_rate >= 0.33,  # 33% minimum compliance
                'completion_rate': round(completion_rate, 2),
                'compliance_threshold': 33,
                'compliant_employees': compliant_employees,
                'total_employees': total_employees,
                'compliance_rate': round(compliance_rate, 2),
                'evidence_coverage': evidence_summary.get('evidence_coverage_percent', 0) if include_evidence else None,
                'validation_timestamp': timezone.now().isoformat()
            }
        
        # Build response
        response_data = {
            'period': f"{month}/{year}",
            'totals': {
                'total_minutes': totals['total_minutes'] or 0,
                'total_points': float(total_points),
                'total_max_points': float(total_max_points),
                'total_earnings': float(totals['total_earnings'] or 0),
                'completion_rate': round(completion_rate, 2),
                'task_count': totals['task_count'],
                'unique_employees': totals['unique_employees']
            },
            'by_department': department_data,
            'by_category': category_data
        }
        
        if include_evidence:
            response_data['evidence_summary'] = evidence_summary
        
        if include_validation:
            response_data['validation_status'] = validation_status
        
        return JsonResponse({
            'data': response_data,
            'meta': {
                'month': month,
                'year': year,
                'generated_at': timezone.now().isoformat(),
                'department_filter': int(department_id) if department_id else None,
                'category_filter': int(category_id) if category_id else None,
                'include_evidence': include_evidence,
                'include_validation': include_validation
            },
            'errors': []
        })
        
    except Exception as e:
        logger.error(f"Error in budget_activity_totals_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)


@login_required
@require_http_methods(["GET"])
def budget_evidence_validation_api(request):
    """
    API endpoint for evidence validation and completeness tracking.
    
    Phase 2 Requirement: Track evidence presence, anomalies, and approval trails
    
    Query Parameters:
        month: Target month (1-12) - default: last month
        year: Target year (YYYY) - default: current year
        department_id: Optional department filter
        category_id: Optional category filter
        min_confidence: Minimum confidence score for auto-linked evidence (default: 0.8)
    
    Returns:
        JSON response with evidence validation data:
        {
            "data": {
                "period": "10/2025",
                "evidence_statistics": {
                    "total_tasks": int,
                    "tasks_with_evidence": int,
                    "tasks_without_evidence": int,
                    "evidence_coverage_percent": float,
                    "auto_linked_count": int,
                    "manual_linked_count": int,
                    "pending_review_count": int
                },
                "evidence_by_type": {
                    "meeting_links": int,
                    "document_links": int,
                    "other_links": int
                },
                "anomalies": [...],
                "approval_trails": [...]
            },
            "meta": {...},
            "errors": []
        }
    """
    try:
        # Get query parameters
        current_date = date.today()
        last_month = current_date - relativedelta(months=1)
        
        month = int(request.GET.get('month', last_month.month))
        year = int(request.GET.get('year', last_month.year))
        department_id = request.GET.get('department_id')
        category_id = request.GET.get('category_id')
        min_confidence = float(request.GET.get('min_confidence', 0.8))
        
        # Build base queryset
        queryset = TaskHistory.objects.filter(
            daf_date__month=month,
            daf_date__year=year,
            employee__is_active=True,
            employee__is_staff=True
        ).exclude(
            employee__username__in=['coda_info', 'luke', 'angel']
        ).select_related('employee', 'category', 'employee__department')
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(employee__department__id=department_id)
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        
        # Get evidence statistics
        total_tasks = queryset.count()
        
        # Note: TaskLinks references Task, not TaskHistory
        # Match TaskHistory to Task by activity_name and employee, then find TaskLinks
        matching_tasks = Task.objects.filter(
            activity_name__in=queryset.values_list('activity_name', flat=True),
            employee__in=queryset.values_list('employee', flat=True)
        )
        
        # Find TaskLinks for matching Tasks
        task_links = TaskLinks.objects.filter(
            task__in=matching_tasks,
            is_active=True
        ).select_related('task')
        
        # Count TaskHistory records that have corresponding Task with evidence
        task_ids_with_evidence = task_links.values_list('task__id', flat=True).distinct()
        tasks_with_evidence = queryset.filter(
            activity_name__in=Task.objects.filter(
                id__in=task_ids_with_evidence
            ).values_list('activity_name', flat=True),
            employee__in=Task.objects.filter(
                id__in=task_ids_with_evidence
            ).values_list('employee', flat=True)
        ).distinct().count()
        
        tasks_without_evidence = total_tasks - tasks_with_evidence
        evidence_coverage = (tasks_with_evidence / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Count by link type
        auto_linked = task_links.filter(link_type='auto', confidence_score__gte=min_confidence).count()
        manual_linked = task_links.filter(link_type='manual').count()
        pending_review = task_links.filter(
            link_type='auto',
            confidence_score__lt=min_confidence,
            is_approved=False,
            is_rejected=False
        ).count()
        
        # Evidence by type (simplified - can be enhanced)
        meeting_links = task_links.filter(link_name__icontains='meeting').count()
        document_links = task_links.filter(link__icontains='drive').count()
        other_links = task_links.count() - meeting_links - document_links
        
        # Anomalies detection
        anomalies = []
        
        # Anomaly 1: Tasks with high points but no evidence
        high_point_no_evidence = queryset.filter(
            point__gte=F('mxpoint') * 0.5,  # 50% or more points
            tasklinks__isnull=True
        ).values('id', 'activity_name', 'employee__username', 'point', 'mxpoint')[:10]
        
        for anomaly in high_point_no_evidence:
            anomalies.append({
                'type': 'high_points_no_evidence',
                'task_id': anomaly['id'],
                'activity_name': anomaly['activity_name'],
                'employee': anomaly['employee__username'],
                'points': float(anomaly['point']),
                'max_points': float(anomaly['mxpoint']),
                'severity': 'medium'
            })
        
        # Anomaly 2: Tasks with low confidence auto-links
        low_confidence_links = task_links.filter(
            link_type='auto',
            confidence_score__lt=min_confidence,
            is_approved=False,
            is_rejected=False
        ).select_related('task').values(
            'id', 'task__activity_name', 'task__employee__username', 'confidence_score', 'link_name'
        )[:10]
        
        for link in low_confidence_links:
            anomalies.append({
                'type': 'low_confidence_auto_link',
                'link_id': link['id'],
                'activity_name': link['task__activity_name'],
                'employee': link['task__employee__username'],
                'confidence_score': float(link['confidence_score'] or 0),
                'link_name': link['link_name'],
                'severity': 'low'
            })
        
        # Approval trails (simplified - can be enhanced with dedicated model)
        approval_trails = []
        reviewed_links = task_links.filter(
            Q(is_approved=True) | Q(is_rejected=True)
        ).select_related('task', 'reviewed_by').order_by('-reviewed_at')[:20]
        
        for link in reviewed_links:
            approval_trails.append({
                'link_id': link.id,
                'task_id': link.task.id if link.task else None,
                'activity_name': link.task.activity_name if link.task else 'N/A',
                'employee': link.task.employee.username if link.task and link.task.employee else 'N/A',
                'action': 'approved' if link.is_approved else 'rejected',
                'reviewed_by': link.reviewed_by.username if link.reviewed_by else 'System',
                'reviewed_at': link.reviewed_at.isoformat() if link.reviewed_at else None,
                'confidence_score': float(link.confidence_score) if link.confidence_score else None
            })
        
        return JsonResponse({
            'data': {
                'period': f"{month}/{year}",
                'evidence_statistics': {
                    'total_tasks': total_tasks,
                    'tasks_with_evidence': tasks_with_evidence,
                    'tasks_without_evidence': tasks_without_evidence,
                    'evidence_coverage_percent': round(evidence_coverage, 2),
                    'auto_linked_count': auto_linked,
                    'manual_linked_count': manual_linked,
                    'pending_review_count': pending_review
                },
                'evidence_by_type': {
                    'meeting_links': meeting_links,
                    'document_links': document_links,
                    'other_links': other_links
                },
                'anomalies': anomalies,
                'approval_trails': approval_trails
            },
            'meta': {
                'month': month,
                'year': year,
                'generated_at': timezone.now().isoformat(),
                'department_filter': int(department_id) if department_id else None,
                'category_filter': int(category_id) if category_id else None,
                'min_confidence': min_confidence
            },
            'errors': []
        })
        
    except Exception as e:
        logger.error(f"Error in budget_evidence_validation_api: {e}", exc_info=True)
        return JsonResponse({
            'data': {},
            'meta': {},
            'errors': [f'An unexpected error occurred: {str(e)}']
        }, status=500)

