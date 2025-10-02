"""
AI-Enhanced Dashboard Views

These views provide comprehensive AI-powered dashboards for performance monitoring,
predictions, and optimization insights.
"""

import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache

from management.services.simple_ai_service import SimpleAIService
from management.services.intelligent_assignment_service import IntelligentAssignmentService
from management.services.department_optimization_service import DepartmentOptimizationService
from management.services.realtime_monitoring_service import RealTimeMonitoringService
from management.services.data_validation_service import DataValidationService


logger = logging.getLogger(__name__)


class AIEnhancedDashboardView(LoginRequiredMixin, TemplateView):
    """Main AI-enhanced dashboard view."""
    template_name = 'management/ai_dashboard.html'
    
    def __init__(self):
        super().__init__()
        self.ai_service = SimpleAIService()
        self.assignment_service = IntelligentAssignmentService()
        self.optimization_service = DepartmentOptimizationService()
        self.monitoring_service = RealTimeMonitoringService()
        self.validation_service = DataValidationService()
    
    def get_context_data(self, **kwargs):
        """Get dashboard context data."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get real-time dashboard data
            dashboard_data = self.monitoring_service.get_realtime_dashboard_data()
            context['dashboard_data'] = dashboard_data
            
            # Get performance alerts
            alerts_data = self.monitoring_service.check_performance_alerts()
            context['alerts_data'] = alerts_data
            
            # Get data quality status
            data_quality = self.validation_service.get_data_quality_dashboard()
            context['data_quality'] = data_quality
            
            # Get department comparison
            dept_comparison = self.optimization_service.compare_department_performance()
            context['department_comparison'] = dept_comparison
            
        except Exception as e:
            logger.error(f"Error getting dashboard context: {e}")
            context['error'] = str(e)
        
        return context


class EmployeePerformanceDashboardView(LoginRequiredMixin, TemplateView):
    """Employee performance prediction dashboard."""
    template_name = 'management/employee_performance_dashboard.html'
    
    def __init__(self):
        super().__init__()
        self.ai_service = SimpleAIService()
    
    def get_context_data(self, **kwargs):
        """Get employee performance context."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get top performing employees
            context['top_performers'] = self._get_top_performers()
            
            # Get employees needing attention
            context['attention_needed'] = self._get_employees_needing_attention()
            
            # Get performance trends
            context['performance_trends'] = self._get_performance_trends()
            
        except Exception as e:
            logger.error(f"Error getting employee performance context: {e}")
            context['error'] = str(e)
        
        return context
    
    def _get_top_performers(self):
        """Get top performing employees."""
        # This would typically query the database for top performers
        # For now, return sample data
        return [
            {
                'employee_name': 'Sample Employee 1',
                'completion_rate': 0.95,
                'predicted_rate': 0.92,
                'confidence': 0.88
            }
        ]
    
    def _get_employees_needing_attention(self):
        """Get employees who need attention."""
        return [
            {
                'employee_name': 'Sample Employee 2',
                'completion_rate': 0.35,
                'predicted_rate': 0.40,
                'confidence': 0.75,
                'issues': ['Low completion rate', 'High workload']
            }
        ]
    
    def _get_performance_trends(self):
        """Get performance trends data."""
        return {
            'overall_trend': 'improving',
            'trend_data': [
                {'date': '2025-01-01', 'rate': 0.15},
                {'date': '2025-02-01', 'rate': 0.18},
                {'date': '2025-03-01', 'rate': 0.20}
            ]
        }


class TaskAssignmentDashboardView(LoginRequiredMixin, TemplateView):
    """Intelligent task assignment dashboard."""
    template_name = 'management/task_assignment_dashboard.html'
    
    def __init__(self):
        super().__init__()
        self.assignment_service = IntelligentAssignmentService()
    
    def get_context_data(self, **kwargs):
        """Get task assignment context."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get assignment statistics
            context['assignment_stats'] = self._get_assignment_statistics()
            
            # Get workload balance
            context['workload_balance'] = self._get_workload_balance()
            
            # Get assignment recommendations
            context['recommendations'] = self._get_assignment_recommendations()
            
        except Exception as e:
            logger.error(f"Error getting task assignment context: {e}")
            context['error'] = str(e)
        
        return context
    
    def _get_assignment_statistics(self):
        """Get assignment statistics."""
        return {
            'total_assignments_today': 25,
            'successful_assignments': 23,
            'success_rate': 0.92,
            'avg_assignment_score': 0.75
        }
    
    def _get_workload_balance(self):
        """Get workload balance information."""
        return {
            'balance_score': 0.65,
            'overloaded_employees': 3,
            'underloaded_employees': 8,
            'balanced_employees': 12
        }
    
    def _get_assignment_recommendations(self):
        """Get assignment recommendations."""
        return [
            {
                'type': 'workload_rebalancing',
                'priority': 'high',
                'description': 'Redistribute tasks from overloaded to underloaded employees'
            }
        ]


class DepartmentOptimizationDashboardView(LoginRequiredMixin, TemplateView):
    """Department optimization dashboard."""
    template_name = 'management/department_optimization_dashboard.html'
    
    def __init__(self):
        super().__init__()
        self.optimization_service = DepartmentOptimizationService()
    
    def get_context_data(self, **kwargs):
        """Get department optimization context."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get department comparison
            comparison = self.optimization_service.compare_department_performance()
            context['department_comparison'] = comparison
            
            # Get optimization opportunities
            context['optimization_opportunities'] = self._get_optimization_opportunities()
            
        except Exception as e:
            logger.error(f"Error getting department optimization context: {e}")
            context['error'] = str(e)
        
        return context
    
    def _get_optimization_opportunities(self):
        """Get optimization opportunities."""
        return [
            {
                'department': 'IT',
                'opportunity': 'Improve completion rates',
                'potential_impact': 'high',
                'implementation_effort': 'medium'
            }
        ]


# API Views for AJAX requests

def get_realtime_dashboard_data(request):
    """API endpoint for real-time dashboard data."""
    try:
        monitoring_service = RealTimeMonitoringService()
        dashboard_data = monitoring_service.get_realtime_dashboard_data()
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time dashboard data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_performance_alerts(request):
    """API endpoint for performance alerts."""
    try:
        monitoring_service = RealTimeMonitoringService()
        alerts_data = monitoring_service.check_performance_alerts()
        
        return JsonResponse({
            'success': True,
            'data': alerts_data
        })
        
    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_employee_performance(request, employee_id):
    """API endpoint for individual employee performance."""
    try:
        ai_service = SimpleAIService()
        performance_data = ai_service.predict_employee_performance(int(employee_id))
        
        return JsonResponse({
            'success': True,
            'data': performance_data
        })
        
    except Exception as e:
        logger.error(f"Error getting employee performance: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_department_status(request, department_name):
    """API endpoint for department status."""
    try:
        monitoring_service = RealTimeMonitoringService()
        department_status = monitoring_service.get_department_realtime_status(department_name)
        
        return JsonResponse({
            'success': True,
            'data': department_status
        })
        
    except Exception as e:
        logger.error(f"Error getting department status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_task_assignment_recommendation(request):
    """API endpoint for task assignment recommendations."""
    try:
        assignment_service = IntelligentAssignmentService()
        
        # Get task data from request
        task_data = {
            'title': request.GET.get('title', 'Sample Task'),
            'category_id': int(request.GET.get('category_id', 1)),
            'priority': int(request.GET.get('priority', 5))
        }
        
        # Get available employees
        available_employees = request.GET.getlist('available_employees')
        if available_employees:
            available_employees = [int(emp_id) for emp_id in available_employees]
        else:
            available_employees = None
        
        # Get assignment recommendation
        assignment_result = assignment_service.assign_task_optimally(task_data, available_employees)
        
        return JsonResponse({
            'success': True,
            'data': assignment_result
        })
        
    except Exception as e:
        logger.error(f"Error getting task assignment recommendation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_department_optimization(request, department_name):
    """API endpoint for department optimization."""
    try:
        optimization_service = DepartmentOptimizationService()
        
        # Get optimization goals from request
        optimization_goals = {
            'target_completion_rate': float(request.GET.get('target_completion_rate', 0.8)),
            'target_efficiency': float(request.GET.get('target_efficiency', 0.9)),
            'workload_balance': float(request.GET.get('workload_balance', 0.8))
        }
        
        # Get optimization results
        optimization_result = optimization_service.optimize_department_performance(
            department_name, optimization_goals
        )
        
        return JsonResponse({
            'success': True,
            'data': optimization_result
        })
        
    except Exception as e:
        logger.error(f"Error getting department optimization: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_data_quality_report(request):
    """API endpoint for data quality report."""
    try:
        validation_service = DataValidationService()
        quality_report = validation_service.get_data_quality_dashboard()
        
        return JsonResponse({
            'success': True,
            'data': quality_report
        })
        
    except Exception as e:
        logger.error(f"Error getting data quality report: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def export_performance_report(request):
    """Export performance report as JSON."""
    try:
        # Get report type from request
        report_type = request.GET.get('type', 'comprehensive')
        
        # Generate report data
        if report_type == 'comprehensive':
            # Get comprehensive report data
            monitoring_service = RealTimeMonitoringService()
            dashboard_data = monitoring_service.get_realtime_dashboard_data()
            
            optimization_service = DepartmentOptimizationService()
            dept_comparison = optimization_service.compare_department_performance()
            
            validation_service = DataValidationService()
            data_quality = validation_service.get_data_quality_dashboard()
            
            report_data = {
                'report_type': 'comprehensive',
                'generated_at': timezone.now().isoformat(),
                'dashboard_data': dashboard_data,
                'department_comparison': dept_comparison,
                'data_quality': data_quality
            }
        
        elif report_type == 'performance':
            # Get performance report data
            ai_service = SimpleAIService()
            # This would include performance predictions for all employees
            report_data = {
                'report_type': 'performance',
                'generated_at': timezone.now().isoformat(),
                'performance_data': {}
            }
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown report type: {report_type}'
            })
        
        # Return as downloadable JSON
        response = HttpResponse(
            json.dumps(report_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="performance_report_{report_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting performance report: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
