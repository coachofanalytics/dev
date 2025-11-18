"""
Anomaly Detection Service for Management App

Phase 3: Advanced Analytics
Service for detecting anomalies in activity data and generating automated alerts.

Provides:
- Activity anomaly detection
- Performance anomaly detection
- Automated alert generation
- Anomaly severity classification
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, Avg, Count, Max, Min, F
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import TaskHistory, Task
from accounts.models import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class AnomalyDetectionService:
    """
    Service for detecting anomalies in activity data.
    
    Phase 3: Advanced Analytics
    Provides automated anomaly detection for:
    - Activity volume anomalies
    - Performance anomalies
    - Compliance anomalies
    - Evidence coverage anomalies
    """
    
    def __init__(self):
        self.logger = logger
    
    def detect_anomalies(
        self,
        target_month: Optional[int] = None,
        target_year: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in activity data.
        
        Args:
            target_month: Target month (default: last month)
            target_year: Target year (default: current year)
            department_id: Optional department filter
        
        Returns:
            Dict with detected anomalies
        """
        try:
            # Default to last month
            if target_month is None or target_year is None:
                last_month = date.today() - relativedelta(months=1)
                target_month = target_month or last_month.month
                target_year = target_year or last_month.year
            
            self.logger.info(
                f"Detecting anomalies for {target_month}/{target_year} "
                f"(department={department_id})"
            )
            
            # Build query
            query = Q(
                daf_date__month=target_month,
                daf_date__year=target_year,
                employee__is_active=True,
                employee__is_staff=True
            )
            
            if department_id:
                query &= Q(employee__department_id=department_id)
            
            query &= ~Q(employee__username__in=['coda_info', 'luke', 'angel'])
            
            # Detect different types of anomalies
            activity_anomalies = self._detect_activity_anomalies(query, target_month, target_year)
            performance_anomalies = self._detect_performance_anomalies(query, target_month, target_year)
            compliance_anomalies = self._detect_compliance_anomalies(query, target_month, target_year)
            evidence_anomalies = self._detect_evidence_anomalies(query, target_month, target_year)
            
            # Combine all anomalies
            all_anomalies = (
                activity_anomalies +
                performance_anomalies +
                compliance_anomalies +
                evidence_anomalies
            )
            
            # Classify by severity
            critical_anomalies = [a for a in all_anomalies if a.get('severity') == 'critical']
            high_anomalies = [a for a in all_anomalies if a.get('severity') == 'high']
            medium_anomalies = [a for a in all_anomalies if a.get('severity') == 'medium']
            low_anomalies = [a for a in all_anomalies if a.get('severity') == 'low']
            
            return {
                'success': True,
                'period': {
                    'month': target_month,
                    'year': target_year,
                    'period_label': f"{target_month}/{target_year}"
                },
                'summary': {
                    'total_anomalies': len(all_anomalies),
                    'critical_count': len(critical_anomalies),
                    'high_count': len(high_anomalies),
                    'medium_count': len(medium_anomalies),
                    'low_count': len(low_anomalies)
                },
                'anomalies': {
                    'critical': critical_anomalies,
                    'high': high_anomalies,
                    'medium': medium_anomalies,
                    'low': low_anomalies,
                    'all': sorted(all_anomalies, key=lambda x: (
                        {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('severity', 'low'), 3),
                        x.get('timestamp', '')
                    ))
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Anomaly detection error: {str(e)}',
                'summary': {},
                'anomalies': {}
            }
    
    def _detect_activity_anomalies(
        self,
        query: Q,
        target_month: int,
        target_year: int
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in activity volume."""
        anomalies = []
        
        try:
            # Get current month data
            current_tasks = TaskHistory.objects.filter(query)
            current_totals = current_tasks.aggregate(
                total_points=Sum('point'),
                total_tasks=Count('id'),
                unique_employees=Count('employee', distinct=True)
            )
            
            # Get historical data (last 6 months excluding current)
            historical_months = []
            for i in range(1, 7):
                hist_date = date(target_year, target_month, 1) - relativedelta(months=i)
                hist_query = Q(
                    daf_date__month=hist_date.month,
                    daf_date__year=hist_date.year,
                    employee__is_active=True,
                    employee__is_staff=True
                )
                hist_query &= ~Q(employee__username__in=['coda_info', 'luke', 'angel'])
                
                hist_tasks = TaskHistory.objects.filter(hist_query)
                hist_totals = hist_tasks.aggregate(
                    total_points=Sum('point'),
                    total_tasks=Count('id')
                )
                
                if hist_totals['total_tasks']:
                    historical_months.append({
                        'month': hist_date.strftime('%Y-%m'),
                        'total_points': float(hist_totals['total_points'] or 0),
                        'total_tasks': hist_totals['total_tasks'] or 0
                    })
            
            if not historical_months:
                return []
            
            # Calculate statistics
            historical_points = [m['total_points'] for m in historical_months]
            historical_tasks = [m['total_tasks'] for m in historical_months]
            
            avg_points = sum(historical_points) / len(historical_points)
            avg_tasks = sum(historical_tasks) / len(historical_tasks)
            
            std_dev_points = (sum((x - avg_points) ** 2 for x in historical_points) / len(historical_points)) ** 0.5
            std_dev_tasks = (sum((x - avg_tasks) ** 2 for x in historical_tasks) / len(historical_tasks)) ** 0.5
            
            current_points = float(current_totals['total_points'] or 0)
            current_tasks_count = current_totals['total_tasks'] or 0
            
            # Detect outliers (beyond 2 standard deviations)
            threshold = 2.0
            
            if std_dev_points > 0:
                points_z_score = abs((current_points - avg_points) / std_dev_points)
                if points_z_score > threshold:
                    severity = 'critical' if points_z_score > 3 else 'high' if points_z_score > 2.5 else 'medium'
                    anomalies.append({
                        'type': 'activity_volume',
                        'severity': severity,
                        'metric': 'total_points',
                        'current_value': current_points,
                        'historical_average': round(avg_points, 2),
                        'z_score': round(points_z_score, 2),
                        'description': f'Activity points ({current_points:.0f}) significantly different from average ({avg_points:.0f})',
                        'recommendation': 'Review activity patterns and investigate cause',
                        'timestamp': timezone.now().isoformat()
                    })
            
            if std_dev_tasks > 0:
                tasks_z_score = abs((current_tasks_count - avg_tasks) / std_dev_tasks)
                if tasks_z_score > threshold:
                    severity = 'critical' if tasks_z_score > 3 else 'high' if tasks_z_score > 2.5 else 'medium'
                    anomalies.append({
                        'type': 'activity_volume',
                        'severity': severity,
                        'metric': 'total_tasks',
                        'current_value': current_tasks_count,
                        'historical_average': round(avg_tasks, 2),
                        'z_score': round(tasks_z_score, 2),
                        'description': f'Task count ({current_tasks_count}) significantly different from average ({avg_tasks:.0f})',
                        'recommendation': 'Review task assignment patterns',
                        'timestamp': timezone.now().isoformat()
                    })
            
        except Exception as e:
            self.logger.warning(f"Error detecting activity anomalies: {e}")
        
        return anomalies
    
    def _detect_performance_anomalies(
        self,
        query: Q,
        target_month: int,
        target_year: int
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in performance metrics."""
        anomalies = []
        
        try:
            # Get employee-level performance
            employees_data = TaskHistory.objects.filter(query).values('employee').annotate(
                emp_points=Sum('point'),
                emp_max_points=Sum('mxpoint'),
                task_count=Count('id')
            ).filter(emp_max_points__gt=0)
            
            completion_rates = []
            for emp_data in employees_data:
                emp_points = emp_data['emp_points'] or 0
                emp_max_points = emp_data['emp_max_points'] or 0
                if emp_max_points > 0:
                    completion_rate = (emp_points / emp_max_points * 100)
                    completion_rates.append(completion_rate)
            
            if not completion_rates:
                return []
            
            # Calculate statistics
            avg_completion = sum(completion_rates) / len(completion_rates)
            std_dev = (sum((x - avg_completion) ** 2 for x in completion_rates) / len(completion_rates)) ** 0.5
            
            # Detect employees with unusually low or high performance
            threshold = 2.0
            
            for emp_data in employees_data:
                emp_points = emp_data['emp_points'] or 0
                emp_max_points = emp_data['emp_max_points'] or 0
                if emp_max_points > 0:
                    completion_rate = (emp_points / emp_max_points * 100)
                    
                    if std_dev > 0:
                        z_score = abs((completion_rate - avg_completion) / std_dev)
                        
                        if z_score > threshold:
                            if completion_rate < avg_completion:
                                severity = 'critical' if completion_rate < 20 else 'high' if completion_rate < 30 else 'medium'
                                try:
                                    employee = CustomerUser.objects.get(id=emp_data['employee'])
                                    anomalies.append({
                                        'type': 'performance',
                                        'severity': severity,
                                        'metric': 'completion_rate',
                                        'employee_id': emp_data['employee'],
                                        'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                                        'current_value': round(completion_rate, 2),
                                        'average': round(avg_completion, 2),
                                        'z_score': round(z_score, 2),
                                        'description': f'Employee {employee.username} has unusually low completion rate ({completion_rate:.1f}%)',
                                        'recommendation': 'Review employee performance and provide support',
                                        'timestamp': timezone.now().isoformat()
                                    })
                                except CustomerUser.DoesNotExist:
                                    pass
            
        except Exception as e:
            self.logger.warning(f"Error detecting performance anomalies: {e}")
        
        return anomalies
    
    def _detect_compliance_anomalies(
        self,
        query: Q,
        target_month: int,
        target_year: int
    ) -> List[Dict[str, Any]]:
        """Detect compliance-related anomalies."""
        anomalies = []
        
        try:
            from management.services.compliance_kpi_service import ComplianceKPIService
            
            kpi_service = ComplianceKPIService()
            kpis = kpi_service.get_realtime_compliance_kpis(
                target_month=target_month,
                target_year=target_year
            )
            
            if not kpis.get('success'):
                return []
            
            overall_metrics = kpis.get('overall_metrics', {})
            compliance_rate = overall_metrics.get('overall_compliance_rate', 0)
            
            # Alert if compliance is below threshold
            if compliance_rate < 70:
                anomalies.append({
                    'type': 'compliance',
                    'severity': 'critical',
                    'metric': 'overall_compliance_rate',
                    'current_value': compliance_rate,
                    'threshold': 70,
                    'description': f'Overall compliance rate ({compliance_rate:.1f}%) is critically low',
                    'recommendation': 'Immediate action required to improve compliance',
                    'timestamp': timezone.now().isoformat()
                })
            elif compliance_rate < 80:
                anomalies.append({
                    'type': 'compliance',
                    'severity': 'high',
                    'metric': 'overall_compliance_rate',
                    'current_value': compliance_rate,
                    'threshold': 80,
                    'description': f'Overall compliance rate ({compliance_rate:.1f}%) is below target',
                    'recommendation': 'Review compliance trends and provide support',
                    'timestamp': timezone.now().isoformat()
                })
            
        except Exception as e:
            self.logger.warning(f"Error detecting compliance anomalies: {e}")
        
        return anomalies
    
    def _detect_evidence_anomalies(
        self,
        query: Q,
        target_month: int,
        target_year: int
    ) -> List[Dict[str, Any]]:
        """Detect evidence coverage anomalies."""
        anomalies = []
        
        try:
            # Get tasks with and without evidence
            tasks = TaskHistory.objects.filter(query)
            total_tasks = tasks.count()
            
            if total_tasks == 0:
                return []
            
            # Match TaskHistory to TaskLinks via Task
            from management.models import TaskLinks
            
            matching_tasks = Task.objects.filter(
                activity_name__in=tasks.values_list('activity_name', flat=True),
                employee__in=tasks.values_list('employee', flat=True)
            )
            
            task_links = TaskLinks.objects.filter(
                task__in=matching_tasks,
                is_active=True
            )
            
            tasks_with_evidence = task_links.values_list('task__id', flat=True).distinct().count()
            evidence_coverage = (tasks_with_evidence / total_tasks * 100) if total_tasks > 0 else 0.0
            
            # Alert if evidence coverage is low
            if evidence_coverage < 50:
                anomalies.append({
                    'type': 'evidence',
                    'severity': 'critical',
                    'metric': 'evidence_coverage',
                    'current_value': round(evidence_coverage, 2),
                    'threshold': 50,
                    'description': f'Evidence coverage ({evidence_coverage:.1f}%) is critically low',
                    'recommendation': 'Review evidence collection process and improve coverage',
                    'timestamp': timezone.now().isoformat()
                })
            elif evidence_coverage < 70:
                anomalies.append({
                    'type': 'evidence',
                    'severity': 'high',
                    'metric': 'evidence_coverage',
                    'current_value': round(evidence_coverage, 2),
                    'threshold': 70,
                    'description': f'Evidence coverage ({evidence_coverage:.1f}%) is below target',
                    'recommendation': 'Improve evidence collection and linking',
                    'timestamp': timezone.now().isoformat()
                })
            
        except Exception as e:
            self.logger.warning(f"Error detecting evidence anomalies: {e}")
        
        return anomalies

