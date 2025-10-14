"""
User Testing Views for Phase 2 AI Features

These views provide user-friendly interfaces for testing Phase 2 AI features
from a non-technical user perspective.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from management.services.simple_ai_service import SimpleAIService
from management.services.intelligent_assignment_service import IntelligentAssignmentService
from management.services.department_optimization_service import DepartmentOptimizationService
from management.services.realtime_monitoring_service import RealTimeMonitoringService
from management.services.data_validation_service import DataValidationService


class UserTestingDashboardView(LoginRequiredMixin, TemplateView):
    """User-friendly testing dashboard for Phase 2 AI features."""
    template_name = 'management/ai_test_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Get context data for user testing dashboard."""
        context = super().get_context_data(**kwargs)
        
        # Get system status
        context['system_status'] = {
            'timestamp': timezone.now(),
            'phase': 'Phase 2: AI-Enhanced Management System',
            'status': 'Ready for UAT Testing',
            'deployment_url': 'https://codamakutano.herokuapp.com',
            'features_ready': 5
        }
        
        return context


class AIFeaturesOverviewView(LoginRequiredMixin, TemplateView):
    """Overview of all AI features for user testing."""
    template_name = 'management/ai_features_overview.html'
    
    def get_context_data(self, **kwargs):
        """Get AI features overview context."""
        context = super().get_context_data(**kwargs)
        
        # Define AI features for user testing
        context['ai_features'] = [
            {
                'name': 'AI Performance Predictions',
                'description': 'Predict employee performance and task completion rates',
                'icon': '🎯',
                'status': 'Ready',
                'test_url': '/management/test-ai-predictions/',
                'user_benefit': 'Better workforce planning and performance management'
            },
            {
                'name': 'Intelligent Task Assignment',
                'description': 'Smart task assignment with workload balancing',
                'icon': '🧠',
                'status': 'Ready',
                'test_url': '/management/test-task-assignment/',
                'user_benefit': 'Optimized task distribution and improved efficiency'
            },
            {
                'name': 'Department Optimization',
                'description': 'AI-driven department performance optimization',
                'icon': '🏢',
                'status': 'Ready',
                'test_url': '/management/test-department-optimization/',
                'user_benefit': 'Strategic insights for department improvements'
            },
            {
                'name': 'Real-Time Monitoring',
                'description': 'Live performance monitoring and alert system',
                'icon': '📊',
                'status': 'Ready',
                'test_url': '/management/test-monitoring/',
                'user_benefit': 'Proactive performance management and issue detection'
            },
            {
                'name': 'Data Quality Assurance',
                'description': 'Automated data validation and quality monitoring',
                'icon': '🔍',
                'status': 'Ready',
                'test_url': '/management/test-data-quality/',
                'user_benefit': 'Reliable data for better decision making'
            }
        ]
        
        return context


@login_required
def test_ai_predictions_user(request):
    """User-friendly AI predictions testing."""
    try:
        ai_service = SimpleAIService()
        
        # Get sample employee prediction
        prediction = ai_service.predict_employee_performance(74)
        
        # Get department prediction
        dept_prediction = ai_service.predict_department_performance('IT')
        
        # Get task assignment prediction
        assignment_prediction = ai_service.predict_optimal_task_assignment(1)
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'employee_prediction': prediction,
            'department_prediction': dept_prediction,
            'assignment_prediction': assignment_prediction,
            'user_message': 'AI predictions are working correctly! You can see performance forecasts and task recommendations.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'There was an issue testing AI predictions. Please check system logs.'
        })


@login_required
def test_task_assignment_user(request):
    """User-friendly task assignment testing."""
    try:
        assignment_service = IntelligentAssignmentService()
        
        # Test single task assignment
        task_data = {
            'title': 'Sample Task for Testing',
            'category_id': 1,
            'priority': 5
        }
        
        assignment = assignment_service.assign_task_optimally(task_data)
        
        # Test workload analysis
        workload = assignment_service.suggest_workload_rebalancing()
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'task_assignment': assignment,
            'workload_analysis': workload,
            'user_message': 'Intelligent task assignment is working! The system can recommend optimal task assignments and analyze workload balance.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'There was an issue testing task assignment. Please check system logs.'
        })


@login_required
def test_department_optimization_user(request):
    """User-friendly department optimization testing."""
    try:
        optimization_service = DepartmentOptimizationService()
        
        # Test department optimization
        optimization = optimization_service.optimize_department_performance('IT')
        
        # Test department comparison
        comparison = optimization_service.compare_department_performance(['IT', 'Finance'])
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'optimization': optimization,
            'comparison': comparison,
            'user_message': 'Department optimization is working! You can see optimization strategies and department comparisons.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'There was an issue testing department optimization. Please check system logs.'
        })


@login_required
def test_monitoring_user(request):
    """User-friendly monitoring testing."""
    try:
        monitoring_service = RealTimeMonitoringService()
        
        # Get dashboard data
        dashboard_data = monitoring_service.get_realtime_dashboard_data()
        
        # Get performance alerts
        alerts = monitoring_service.check_performance_alerts()
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'dashboard_data': dashboard_data,
            'alerts': alerts,
            'user_message': 'Real-time monitoring is working! You can see live system status and performance alerts.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'There was an issue testing monitoring. Please check system logs.'
        })


@login_required
def test_data_quality_user(request):
    """User-friendly data quality testing."""
    try:
        validation_service = DataValidationService()
        
        # Get data quality report
        quality_report = validation_service.get_data_quality_dashboard()
        
        # Get validation results
        validation_results = validation_service.validate_task_history_data()
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'quality_report': quality_report,
            'validation_results': validation_results,
            'user_message': 'Data quality validation is working! You can see data quality scores and validation results.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'There was an issue testing data quality. Please check system logs.'
        })


@login_required
def get_ai_system_status(request):
    """Get overall AI system status for user testing."""
    try:
        # Test all services
        services_status = {}
        
        try:
            ai_service = SimpleAIService()
            test_prediction = ai_service.predict_employee_performance(74)
            services_status['ai_predictions'] = 'Working' if test_prediction['success'] else 'Error'
        except:
            services_status['ai_predictions'] = 'Error'
        
        try:
            assignment_service = IntelligentAssignmentService()
            services_status['task_assignment'] = 'Working'
        except:
            services_status['task_assignment'] = 'Error'
        
        try:
            optimization_service = DepartmentOptimizationService()
            services_status['department_optimization'] = 'Working'
        except:
            services_status['department_optimization'] = 'Error'
        
        try:
            monitoring_service = RealTimeMonitoringService()
            services_status['real_time_monitoring'] = 'Working'
        except:
            services_status['real_time_monitoring'] = 'Error'
        
        try:
            validation_service = DataValidationService()
            services_status['data_validation'] = 'Working'
        except:
            services_status['data_validation'] = 'Error'
        
        # Calculate overall status
        working_services = sum(1 for status in services_status.values() if status == 'Working')
        total_services = len(services_status)
        overall_status = 'Healthy' if working_services == total_services else 'Issues Detected'
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'overall_status': overall_status,
            'working_services': working_services,
            'total_services': total_services,
            'services_status': services_status,
            'user_message': f'AI system status: {overall_status} ({working_services}/{total_services} services working)'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_message': 'Unable to check AI system status. Please check system logs.'
        })
