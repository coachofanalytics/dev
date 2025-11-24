"""
Insights Views

Views for displaying TaskHistory analysis insights and performance dashboards.

Phase 1 Component - Week 3-4: Data Collection & Analysis
"""

import json
import logging
from typing import Dict, Any
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse

# Import services
from management.services.taskhistory_analyzer import TaskHistoryAnalyzer
from management.services.utilities_service import UtilitiesService

# Import models
from management.models import TaskHistory
from shared_core.users import Department

logger = logging.getLogger(__name__)


class PerformanceInsightsDashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Performance insights dashboard view.
    
    Displays comprehensive analysis of TaskHistory data with AI-enhanced insights.
    """
    
    template_name = 'management/insights/performance_dashboard.html'
    
    def test_func(self):
        """Only staff and admin users can access."""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        """Get context data with comprehensive analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get analysis parameters
        months = int(self.request.GET.get('months', 12))
        department_id = self.request.GET.get('department')
        
        # Initialize analyzer
        analyzer = TaskHistoryAnalyzer()
        
        # Perform comprehensive analysis
        analysis_result = analyzer.analyze_complete_performance_patterns(months_back=months)
        
        # Add to context
        context.update({
            'analysis': analysis_result,
            'months_analyzed': months,
            'department_id': department_id,
            'departments': Department.objects.filter(is_active=True),
            'analysis_timestamp': timezone.now(),
            'total_records': analysis_result.get('total_records', 0),
            'success': analysis_result.get('success', False)
        })
        
        # Add quick stats for dashboard cards
        if analysis_result.get('success'):
            context['quick_stats'] = self._get_quick_stats(analysis_result)
            context['performance_charts'] = self._prepare_chart_data(analysis_result)
        
        return context
    
    def _get_quick_stats(self, analysis_result) -> Dict[str, Any]:
        """Extract quick statistics for dashboard cards."""
        return {
            'total_employees': analysis_result.get('employee_performance', {}).get('total_employees', 0),
            'total_departments': analysis_result.get('department_analysis', {}).get('total_departments', 0),
            'overall_completion_rate': analysis_result.get('completion_rates', {}).get('overall_completion_rate', 0),
            'total_earnings': analysis_result.get('earning_patterns', {}).get('total_earnings', 0),
            'high_performance_percentage': analysis_result.get('completion_rates', {}).get('high_performance_percentage', 0),
            'total_insights': len(analysis_result.get('key_insights', [])),
            'total_recommendations': len(analysis_result.get('actionable_recommendations', []))
        }
    
    def _prepare_chart_data(self, analysis_result) -> Dict[str, Any]:
        """Prepare data for charts and visualizations."""
        try:
            # Monthly trends chart data
            monthly_trends = analysis_result.get('temporal_patterns', {}).get('monthly_trends', [])
            months_labels = [f"{int(m.get('year', 0))}-{int(m.get('month', 0)):02d}" for m in monthly_trends]
            completion_rates = [m.get('avg_completion_rate', 0) for m in monthly_trends]
            earnings_data = [m.get('total_earnings', 0) for m in monthly_trends]
            
            # Department comparison chart data
            dept_stats = analysis_result.get('department_analysis', {}).get('department_statistics', [])
            dept_names = [d.get('employee__department__name', 'Unknown') for d in dept_stats]
            dept_completion = [d.get('avg_completion_rate', 0) for d in dept_stats]
            
            # Category performance chart data
            category_stats = analysis_result.get('category_analysis', {}).get('category_statistics', [])
            category_names = [c.get('category__title', 'Unknown') for c in category_stats]
            category_tasks = [c.get('total_tasks', 0) for c in category_stats]
            
            return {
                'monthly_trends': {
                    'labels': months_labels,
                    'completion_rates': completion_rates,
                    'earnings': earnings_data
                },
                'department_comparison': {
                    'labels': dept_names,
                    'completion_rates': dept_completion
                },
                'category_performance': {
                    'labels': category_names,
                    'task_counts': category_tasks
                }
            }
            
        except Exception as e:
            logger.error(f"Error preparing chart data: {e}")
            return {}


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def export_insights_report(request):
    """Export insights report as JSON or text."""
    try:
        # Get parameters
        months = int(request.GET.get('months', 12))
        export_format = request.GET.get('format', 'json')
        
        # Initialize analyzer
        analyzer = TaskHistoryAnalyzer()
        
        if export_format == 'json':
            # Export as JSON
            analysis_result = analyzer.export_analysis_to_json(months_back=months)
            response = HttpResponse(
                json.dumps(analysis_result, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="taskhistory_analysis_{timezone.now().strftime("%Y%m%d")}.json"'
            return response
            
        elif export_format == 'text':
            # Export as text report
            report = analyzer.generate_summary_report(months_back=months)
            response = HttpResponse(report, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="taskhistory_report_{timezone.now().strftime("%Y%m%d")}.txt"'
            return response
        
        else:
            return JsonResponse({'error': 'Invalid format. Use json or text'}, status=400)
            
    except Exception as e:
        logger.error(f"Error exporting insights report: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_insights_api(request):
    """API endpoint for getting insights data."""
    try:
        # Get parameters
        months = int(request.GET.get('months', 12))
        analysis_type = request.GET.get('type', 'complete')
        
        # Initialize analyzer
        analyzer = TaskHistoryAnalyzer()
        
        if analysis_type == 'complete':
            result = analyzer.analyze_complete_performance_patterns(months_back=months)
        else:
            result = {'error': 'Invalid analysis type'}
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in insights API: {e}")
        return JsonResponse({'error': str(e)}, status=500)