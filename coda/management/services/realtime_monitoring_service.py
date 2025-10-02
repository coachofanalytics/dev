"""
Real-Time Performance Monitoring Service

This service provides live monitoring, alerts, and real-time insights
for employee performance, task completion, and system health.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F
from django.core.cache import cache

from management.models import TaskHistory
from accounts.models import CustomerUser
from management.services.simple_ai_service import SimpleAIService
from management.services.data_validation_service import DataValidationService


class RealTimeMonitoringService:
    """Service for real-time performance monitoring and alerts."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_service = SimpleAIService()
        self.validation_service = DataValidationService()
        
        # Alert thresholds
        self.thresholds = {
            'completion_rate_low': 0.5,
            'completion_rate_critical': 0.3,
            'workload_high': 0.8,
            'workload_critical': 0.95,
            'data_quality_warning': 90.0,
            'data_quality_critical': 80.0
        }
    
    def get_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive real-time dashboard data."""
        try:
            self.logger.info("Generating real-time dashboard data")
            
            # Get current system status
            system_status = self._get_system_status()
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics()
            
            # Get active alerts
            active_alerts = self._get_active_alerts()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            # Get data quality status
            data_quality = self._get_data_quality_status()
            
            return {
                'success': True,
                'timestamp': timezone.now(),
                'system_status': system_status,
                'performance_metrics': performance_metrics,
                'active_alerts': active_alerts,
                'recent_activity': recent_activity,
                'data_quality': data_quality,
                'dashboard_health': self._calculate_dashboard_health(system_status, active_alerts)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating real-time dashboard data: {e}")
            return {
                'success': False,
                'message': f'Dashboard data generation failed: {str(e)}',
                'timestamp': timezone.now()
            }
    
    def check_performance_alerts(self) -> Dict[str, Any]:
        """Check for performance-related alerts."""
        try:
            alerts = []
            
            # Check employee performance alerts
            employee_alerts = self._check_employee_performance_alerts()
            alerts.extend(employee_alerts)
            
            # Check workload alerts
            workload_alerts = self._check_workload_alerts()
            alerts.extend(workload_alerts)
            
            # Check system health alerts
            system_alerts = self._check_system_health_alerts()
            alerts.extend(system_alerts)
            
            # Check data quality alerts
            data_quality_alerts = self._check_data_quality_alerts()
            alerts.extend(data_quality_alerts)
            
            # Prioritize alerts
            prioritized_alerts = self._prioritize_alerts(alerts)
            
            return {
                'success': True,
                'timestamp': timezone.now(),
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
                'high_alerts': len([a for a in alerts if a['severity'] == 'high']),
                'alerts': prioritized_alerts,
                'alert_summary': self._generate_alert_summary(alerts)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")
            return {
                'success': False,
                'message': f'Alert checking failed: {str(e)}',
                'alerts': []
            }
    
    def get_employee_realtime_status(self, employee_id: int) -> Dict[str, Any]:
        """Get real-time status for a specific employee."""
        try:
            self.logger.info(f"Getting real-time status for employee {employee_id}")
            
            # Get employee
            try:
                employee = CustomerUser.objects.get(id=employee_id)
            except CustomerUser.DoesNotExist:
                return {
                    'success': False,
                    'message': f'Employee {employee_id} not found'
                }
            
            # Get current workload
            current_workload = self._get_employee_current_workload(employee_id)
            
            # Get recent performance
            recent_performance = self._get_employee_recent_performance(employee_id)
            
            # Get active tasks
            active_tasks = self._get_employee_active_tasks(employee_id)
            
            # Get performance prediction
            performance_prediction = self.ai_service.predict_employee_performance(employee_id)
            
            # Check for alerts
            employee_alerts = self._check_employee_specific_alerts(employee_id, current_workload, recent_performance)
            
            return {
                'success': True,
                'employee_id': employee_id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'current_workload': current_workload,
                'recent_performance': recent_performance,
                'active_tasks': active_tasks,
                'performance_prediction': performance_prediction,
                'alerts': employee_alerts,
                'status': self._determine_employee_status(current_workload, recent_performance, employee_alerts),
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting employee real-time status: {e}")
            return {
                'success': False,
                'message': f'Employee status retrieval failed: {str(e)}'
            }
    
    def get_department_realtime_status(self, department_name: str) -> Dict[str, Any]:
        """Get real-time status for a department."""
        try:
            self.logger.info(f"Getting real-time status for department {department_name}")
            
            # Get department employees
            category_mapping = {'IT': 1, 'HR': 2, 'Finance': 3, 'Marketing': 4, 'Operations': 5, 'Other': 999}
            category = category_mapping.get(department_name)
            
            if category is None:
                return {
                    'success': False,
                    'message': f'Unknown department: {department_name}'
                }
            
            employees = CustomerUser.objects.filter(category=category)
            employee_ids = [emp.id for emp in employees]
            
            if not employee_ids:
                return {
                    'success': False,
                    'message': f'No employees found in department {department_name}'
                }
            
            # Get department metrics
            department_metrics = self._get_department_metrics(employee_ids)
            
            # Get department alerts
            department_alerts = self._check_department_alerts(employee_ids, department_metrics)
            
            # Get workload distribution
            workload_distribution = self._get_department_workload_distribution(employee_ids)
            
            return {
                'success': True,
                'department_name': department_name,
                'employee_count': len(employees),
                'department_metrics': department_metrics,
                'workload_distribution': workload_distribution,
                'alerts': department_alerts,
                'status': self._determine_department_status(department_metrics, department_alerts),
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting department real-time status: {e}")
            return {
                'success': False,
                'message': f'Department status retrieval failed: {str(e)}'
            }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            # Get basic counts
            total_employees = CustomerUser.objects.filter(is_active=True).count()
            total_tasks_today = TaskHistory.objects.filter(
                daf_date=timezone.now().date()
            ).count()
            
            # Get recent task completion
            recent_tasks = TaskHistory.objects.filter(
                daf_date__gte=timezone.now().date() - timedelta(days=7)
            )
            
            if recent_tasks.exists():
                completed_tasks = recent_tasks.filter(mxpoint__gt=0)
                if completed_tasks.exists():
                    completion_rates = []
                    for task in completed_tasks:
                        if task.mxpoint > 0:
                            completion_rates.append(float(task.point) / float(task.mxpoint))
                    
                    avg_completion_rate = sum(completion_rates) / len(completion_rates)
                else:
                    avg_completion_rate = 0.0
            else:
                avg_completion_rate = 0.0
            
            return {
                'status': 'healthy' if avg_completion_rate > 0.5 else 'warning',
                'total_employees': total_employees,
                'active_employees': total_employees,
                'tasks_today': total_tasks_today,
                'avg_completion_rate': avg_completion_rate,
                'system_load': 'normal',
                'uptime': '99.9%'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            # Get last 24 hours data
            yesterday = timezone.now().date() - timedelta(days=1)
            today = timezone.now().date()
            
            recent_tasks = TaskHistory.objects.filter(
                daf_date__gte=yesterday,
                daf_date__lte=today
            )
            
            if recent_tasks.exists():
                # Calculate completion metrics
                completed_tasks = recent_tasks.filter(mxpoint__gt=0)
                if completed_tasks.exists():
                    completion_rates = []
                    for task in completed_tasks:
                        if task.mxpoint > 0:
                            completion_rates.append(float(task.point) / float(task.mxpoint))
                    
                    avg_completion = sum(completion_rates) / len(completion_rates)
                    high_performers = len([r for r in completion_rates if r > 0.8])
                    low_performers = len([r for r in completion_rates if r < 0.5])
                else:
                    avg_completion = 0.0
                    high_performers = 0
                    low_performers = 0
                
                # Calculate earnings
                total_earnings = sum(float(task.mxearning) for task in recent_tasks)
                
                return {
                    'avg_completion_rate': avg_completion,
                    'total_tasks': recent_tasks.count(),
                    'completed_tasks': completed_tasks.count(),
                    'high_performers': high_performers,
                    'low_performers': low_performers,
                    'total_earnings': total_earnings,
                    'avg_earnings_per_task': total_earnings / recent_tasks.count() if recent_tasks.count() > 0 else 0
                }
            else:
                return {
                    'avg_completion_rate': 0.0,
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'high_performers': 0,
                    'low_performers': 0,
                    'total_earnings': 0.0,
                    'avg_earnings_per_task': 0.0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {
                'avg_completion_rate': 0.0,
                'total_tasks': 0,
                'error': str(e)
            }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        try:
            alerts = []
            
            # Check performance alerts
            performance_alerts = self._check_employee_performance_alerts()
            alerts.extend(performance_alerts)
            
            # Check workload alerts
            workload_alerts = self._check_workload_alerts()
            alerts.extend(workload_alerts)
            
            # Check data quality alerts
            data_quality_alerts = self._check_data_quality_alerts()
            alerts.extend(data_quality_alerts)
            
            # Sort by severity and timestamp
            alerts.sort(key=lambda x: (x['severity'] == 'critical', x['timestamp']), reverse=True)
            
            return alerts[:10]  # Return top 10 alerts
            
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity."""
        try:
            # Get recent task completions
            recent_tasks = TaskHistory.objects.filter(
                daf_date=timezone.now().date()
            ).select_related('employee', 'category')[:10]
            
            activities = []
            for task in recent_tasks:
                activities.append({
                    'type': 'task_completion',
                    'description': f"{task.employee.first_name} completed a task in {task.category.title if task.category else 'Unknown'}",
                    'timestamp': timezone.now(),
                    'employee_name': f"{task.employee.first_name} {task.employee.last_name}",
                    'category': task.category.title if task.category else 'Unknown'
                })
            
            return activities
            
        except Exception as e:
            self.logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_data_quality_status(self) -> Dict[str, Any]:
        """Get current data quality status."""
        try:
            # Use cached validation results if available
            cache_key = 'data_quality_status'
            cached_result = cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Run validation if not cached
            validation_results = self.validation_service.validate_task_history_data()
            
            result = {
                'quality_score': validation_results['overall_score'],
                'total_issues': len(validation_results['issues']),
                'total_warnings': len(validation_results['warnings']),
                'critical_issues': len([i for i in validation_results['issues'] if i['severity'] == 'critical']),
                'status': 'good' if validation_results['overall_score'] > 90 else 'warning' if validation_results['overall_score'] > 80 else 'critical'
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, result, 300)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting data quality status: {e}")
            return {
                'quality_score': 0.0,
                'status': 'error',
                'message': str(e)
            }
    
    def _check_employee_performance_alerts(self) -> List[Dict[str, Any]]:
        """Check for employee performance alerts."""
        alerts = []
        
        try:
            # Get employees with recent poor performance
            recent_tasks = TaskHistory.objects.filter(
                daf_date__gte=timezone.now().date() - timedelta(days=7),
                mxpoint__gt=0
            )
            
            employee_performance = {}
            for task in recent_tasks:
                emp_id = task.employee.id
                completion_rate = float(task.point) / float(task.mxpoint)
                
                if emp_id not in employee_performance:
                    employee_performance[emp_id] = {
                        'employee_name': f"{task.employee.first_name} {task.employee.last_name}",
                        'completion_rates': []
                    }
                
                employee_performance[emp_id]['completion_rates'].append(completion_rate)
            
            # Check for poor performers
            for emp_id, data in employee_performance.items():
                if data['completion_rates']:
                    avg_rate = sum(data['completion_rates']) / len(data['completion_rates'])
                    
                    if avg_rate < self.thresholds['completion_rate_critical']:
                        alerts.append({
                            'type': 'performance',
                            'severity': 'critical',
                            'title': f'Critical Performance Alert: {data["employee_name"]}',
                            'description': f'Employee completion rate is {avg_rate:.1%}, below critical threshold',
                            'employee_id': emp_id,
                            'metric': 'completion_rate',
                            'value': avg_rate,
                            'threshold': self.thresholds['completion_rate_critical'],
                            'timestamp': timezone.now()
                        })
                    elif avg_rate < self.thresholds['completion_rate_low']:
                        alerts.append({
                            'type': 'performance',
                            'severity': 'high',
                            'title': f'Performance Warning: {data["employee_name"]}',
                            'description': f'Employee completion rate is {avg_rate:.1%}, below warning threshold',
                            'employee_id': emp_id,
                            'metric': 'completion_rate',
                            'value': avg_rate,
                            'threshold': self.thresholds['completion_rate_low'],
                            'timestamp': timezone.now()
                        })
            
        except Exception as e:
            self.logger.error(f"Error checking employee performance alerts: {e}")
        
        return alerts
    
    def _check_workload_alerts(self) -> List[Dict[str, Any]]:
        """Check for workload-related alerts."""
        alerts = []
        
        try:
            # Check for overloaded employees
            employee_workloads = {}
            recent_tasks = TaskHistory.objects.filter(
                daf_date__gte=timezone.now().date() - timedelta(days=7)
            )
            
            for task in recent_tasks:
                emp_id = task.employee.id
                employee_workloads[emp_id] = employee_workloads.get(emp_id, 0) + 1
            
            # Check for overloaded employees
            for emp_id, task_count in employee_workloads.items():
                if task_count > 15:  # More than 15 tasks in a week
                    employee = CustomerUser.objects.get(id=emp_id)
                    alerts.append({
                        'type': 'workload',
                        'severity': 'high',
                        'title': f'High Workload Alert: {employee.first_name} {employee.last_name}',
                        'description': f'Employee has {task_count} tasks in the last 7 days',
                        'employee_id': emp_id,
                        'metric': 'task_count',
                        'value': task_count,
                        'threshold': 15,
                        'timestamp': timezone.now()
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking workload alerts: {e}")
        
        return alerts
    
    def _check_system_health_alerts(self) -> List[Dict[str, Any]]:
        """Check for system health alerts."""
        alerts = []
        
        try:
            # Check for low task completion rates system-wide
            recent_tasks = TaskHistory.objects.filter(
                daf_date__gte=timezone.now().date() - timedelta(days=1),
                mxpoint__gt=0
            )
            
            if recent_tasks.exists():
                completion_rates = []
                for task in recent_tasks:
                    if task.mxpoint > 0:
                        completion_rates.append(float(task.point) / float(task.mxpoint))
                
                if completion_rates:
                    avg_completion = sum(completion_rates) / len(completion_rates)
                    
                    if avg_completion < 0.3:
                        alerts.append({
                            'type': 'system',
                            'severity': 'critical',
                            'title': 'System-wide Performance Critical',
                            'description': f'Average completion rate is {avg_completion:.1%}',
                            'metric': 'system_completion_rate',
                            'value': avg_completion,
                            'threshold': 0.3,
                            'timestamp': timezone.now()
                        })
            
        except Exception as e:
            self.logger.error(f"Error checking system health alerts: {e}")
        
        return alerts
    
    def _check_data_quality_alerts(self) -> List[Dict[str, Any]]:
        """Check for data quality alerts."""
        alerts = []
        
        try:
            data_quality = self._get_data_quality_status()
            
            if data_quality['quality_score'] < self.thresholds['data_quality_critical']:
                alerts.append({
                    'type': 'data_quality',
                    'severity': 'critical',
                    'title': 'Data Quality Critical',
                    'description': f'Data quality score is {data_quality["quality_score"]:.1f}/100',
                    'metric': 'data_quality_score',
                    'value': data_quality['quality_score'],
                    'threshold': self.thresholds['data_quality_critical'],
                    'timestamp': timezone.now()
                })
            elif data_quality['quality_score'] < self.thresholds['data_quality_warning']:
                alerts.append({
                    'type': 'data_quality',
                    'severity': 'high',
                    'title': 'Data Quality Warning',
                    'description': f'Data quality score is {data_quality["quality_score"]:.1f}/100',
                    'metric': 'data_quality_score',
                    'value': data_quality['quality_score'],
                    'threshold': self.thresholds['data_quality_warning'],
                    'timestamp': timezone.now()
                })
            
        except Exception as e:
            self.logger.error(f"Error checking data quality alerts: {e}")
        
        return alerts
    
    def _prioritize_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize alerts by severity and recency."""
        severity_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        
        return sorted(
            alerts,
            key=lambda x: (
                severity_order.get(x['severity'], 5),
                x['timestamp']
            )
        )
    
    def _generate_alert_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert summary statistics."""
        if not alerts:
            return {
                'total_alerts': 0,
                'critical_count': 0,
                'high_count': 0,
                'by_type': {},
                'requires_attention': False
            }
        
        by_type = {}
        for alert in alerts:
            alert_type = alert['type']
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
        
        critical_count = len([a for a in alerts if a['severity'] == 'critical'])
        high_count = len([a for a in alerts if a['severity'] == 'high'])
        
        return {
            'total_alerts': len(alerts),
            'critical_count': critical_count,
            'high_count': high_count,
            'by_type': by_type,
            'requires_attention': critical_count > 0 or high_count > 5
        }
    
    def _calculate_dashboard_health(self, system_status: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
        """Calculate overall dashboard health."""
        critical_alerts = len([a for a in alerts if a['severity'] == 'critical'])
        high_alerts = len([a for a in alerts if a['severity'] == 'high'])
        
        if critical_alerts > 0:
            return 'critical'
        elif high_alerts > 3:
            return 'warning'
        elif system_status.get('status') == 'error':
            return 'error'
        else:
            return 'healthy'
    
    def _get_employee_current_workload(self, employee_id: int) -> Dict[str, Any]:
        """Get current workload for an employee."""
        try:
            # Count active tasks (last 7 days)
            recent_tasks = TaskHistory.objects.filter(
                employee_id=employee_id,
                daf_date__gte=timezone.now().date() - timedelta(days=7)
            )
            
            return {
                'active_tasks': recent_tasks.count(),
                'completed_tasks': recent_tasks.filter(mxpoint__gt=0).count(),
                'pending_tasks': recent_tasks.filter(mxpoint=0).count(),
                'workload_level': 'low' if recent_tasks.count() < 5 else 'medium' if recent_tasks.count() < 10 else 'high'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting employee workload: {e}")
            return {'active_tasks': 0, 'workload_level': 'unknown'}
    
    def _get_employee_recent_performance(self, employee_id: int) -> Dict[str, Any]:
        """Get recent performance for an employee."""
        try:
            recent_tasks = TaskHistory.objects.filter(
                employee_id=employee_id,
                daf_date__gte=timezone.now().date() - timedelta(days=7),
                mxpoint__gt=0
            )
            
            if recent_tasks.exists():
                completion_rates = []
                for task in recent_tasks:
                    if task.mxpoint > 0:
                        completion_rates.append(float(task.point) / float(task.mxpoint))
                
                avg_completion = sum(completion_rates) / len(completion_rates)
                return {
                    'avg_completion_rate': avg_completion,
                    'task_count': len(completion_rates),
                    'performance_level': 'high' if avg_completion > 0.8 else 'medium' if avg_completion > 0.5 else 'low'
                }
            else:
                return {
                    'avg_completion_rate': 0.0,
                    'task_count': 0,
                    'performance_level': 'no_data'
                }
                
        except Exception as e:
            self.logger.error(f"Error getting employee performance: {e}")
            return {'avg_completion_rate': 0.0, 'performance_level': 'error'}
    
    def _get_employee_active_tasks(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get active tasks for an employee."""
        try:
            active_tasks = TaskHistory.objects.filter(
                employee_id=employee_id,
                daf_date__gte=timezone.now().date() - timedelta(days=3)
            ).select_related('category')[:5]
            
            tasks = []
            for task in active_tasks:
                tasks.append({
                    'task_id': task.id,
                    'category': task.category.title if task.category else 'Unknown',
                    'date': task.daf_date,
                    'status': 'completed' if task.mxpoint > 0 and task.point > 0 else 'pending'
                })
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Error getting employee active tasks: {e}")
            return []
    
    def _check_employee_specific_alerts(self, employee_id: int, workload: Dict[str, Any], performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alerts specific to an employee."""
        alerts = []
        
        # Workload alerts
        if workload['workload_level'] == 'high':
            alerts.append({
                'type': 'workload',
                'severity': 'high',
                'title': 'High Workload',
                'description': f'Employee has {workload["active_tasks"]} active tasks',
                'timestamp': timezone.now()
            })
        
        # Performance alerts
        if performance['performance_level'] == 'low':
            alerts.append({
                'type': 'performance',
                'severity': 'high',
                'title': 'Low Performance',
                'description': f'Recent completion rate is {performance["avg_completion_rate"]:.1%}',
                'timestamp': timezone.now()
            })
        
        return alerts
    
    def _determine_employee_status(self, workload: Dict[str, Any], performance: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
        """Determine overall employee status."""
        if alerts and any(a['severity'] == 'critical' for a in alerts):
            return 'critical'
        elif alerts and any(a['severity'] == 'high' for a in alerts):
            return 'warning'
        elif workload['workload_level'] == 'high' or performance['performance_level'] == 'low':
            return 'attention'
        else:
            return 'good'
    
    def _get_department_metrics(self, employee_ids: List[int]) -> Dict[str, Any]:
        """Get metrics for a department."""
        try:
            recent_tasks = TaskHistory.objects.filter(
                employee_id__in=employee_ids,
                daf_date__gte=timezone.now().date() - timedelta(days=7)
            )
            
            if recent_tasks.exists():
                completed_tasks = recent_tasks.filter(mxpoint__gt=0)
                if completed_tasks.exists():
                    completion_rates = []
                    for task in completed_tasks:
                        if task.mxpoint > 0:
                            completion_rates.append(float(task.point) / float(task.mxpoint))
                    
                    avg_completion = sum(completion_rates) / len(completion_rates)
                else:
                    avg_completion = 0.0
                
                total_earnings = sum(float(task.mxearning) for task in recent_tasks)
                
                return {
                    'total_tasks': recent_tasks.count(),
                    'completed_tasks': completed_tasks.count(),
                    'avg_completion_rate': avg_completion,
                    'total_earnings': total_earnings,
                    'avg_earnings_per_task': total_earnings / recent_tasks.count() if recent_tasks.count() > 0 else 0
                }
            else:
                return {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'avg_completion_rate': 0.0,
                    'total_earnings': 0.0,
                    'avg_earnings_per_task': 0.0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting department metrics: {e}")
            return {'error': str(e)}
    
    def _check_department_alerts(self, employee_ids: List[int], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for department-specific alerts."""
        alerts = []
        
        if metrics.get('avg_completion_rate', 0) < 0.3:
            alerts.append({
                'type': 'department_performance',
                'severity': 'critical',
                'title': 'Department Performance Critical',
                'description': f'Average completion rate is {metrics["avg_completion_rate"]:.1%}',
                'timestamp': timezone.now()
            })
        
        return alerts
    
    def _get_department_workload_distribution(self, employee_ids: List[int]) -> Dict[str, Any]:
        """Get workload distribution for a department."""
        try:
            employee_workloads = {}
            recent_tasks = TaskHistory.objects.filter(
                employee_id__in=employee_ids,
                daf_date__gte=timezone.now().date() - timedelta(days=7)
            )
            
            for task in recent_tasks:
                emp_id = task.employee.id
                employee_workloads[emp_id] = employee_workloads.get(emp_id, 0) + 1
            
            if employee_workloads:
                workloads = list(employee_workloads.values())
                return {
                    'average_workload': sum(workloads) / len(workloads),
                    'max_workload': max(workloads),
                    'min_workload': min(workloads),
                    'overloaded_employees': len([w for w in workloads if w > 10]),
                    'underloaded_employees': len([w for w in workloads if w < 2])
                }
            else:
                return {
                    'average_workload': 0,
                    'max_workload': 0,
                    'min_workload': 0,
                    'overloaded_employees': 0,
                    'underloaded_employees': len(employee_ids)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting workload distribution: {e}")
            return {'error': str(e)}
    
    def _determine_department_status(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
        """Determine overall department status."""
        if alerts and any(a['severity'] == 'critical' for a in alerts):
            return 'critical'
        elif metrics.get('avg_completion_rate', 0) < 0.5:
            return 'warning'
        else:
            return 'good'
