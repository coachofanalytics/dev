"""
TaskHistory Analyzer Service

This service analyzes existing TaskHistory data to extract performance patterns,
insights, and recommendations. This is the foundation for AI-enhanced features.

Phase 1 Component - Week 3-4: Data Collection & Analysis
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, Avg, Count, Max, Min, F
from django.utils import timezone
from django.contrib.auth import get_user_model

# Import models
from management.models import Task, TaskHistory, TaskCategory, TaskLinks
from shared_core.users import CustomerUser, Department
from accounts.models import TaskGroups

# Import AI services for enhancement
try:
    from ai_services.ai_integration_service import RealAIService
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False
    RealAIService = None

logger = logging.getLogger(__name__)
User = get_user_model()


class TaskHistoryAnalyzer:
    """
    Service for analyzing TaskHistory data to extract patterns and insights.
    
    Provides comprehensive analysis of:
    - Employee performance patterns
    - Department effectiveness
    - Category performance
    - Seasonal trends
    - Completion rates
    - Earning patterns
    """
    
    def __init__(self):
        self.logger = logger
        self.ai_service = RealAIService() if AI_SERVICE_AVAILABLE else None
        
        self.logger.info("TaskHistoryAnalyzer initialized with AI service: %s", AI_SERVICE_AVAILABLE)
    
    # ============================================================================
    # MAIN ANALYSIS METHODS
    # ============================================================================
    
    def analyze_complete_performance_patterns(self, months_back: int = 12) -> Dict[str, Any]:
        """
        Comprehensive analysis of all performance patterns.
        
        Args:
            months_back: Number of months to analyze (default: 12)
            
        Returns:
            Dict with complete performance analysis
        """
        try:
            self.logger.info(f"Starting comprehensive performance analysis for last {months_back} months")
            
            # Calculate date range
            end_date = timezone.now()
            start_date = end_date - relativedelta(months=months_back)
            
            # Get all TaskHistory data in date range
            task_history = TaskHistory.objects.filter(
                daf_date__gte=start_date.date(),
                daf_date__lte=end_date.date()
            ).select_related('employee', 'category')
            
            # If no data with dates, get all data (for testing/development)
            if not task_history.exists():
                self.logger.warning("No TaskHistory data with dates found, using all available data")
                task_history = TaskHistory.objects.all().select_related('employee', 'category')
                
                if not task_history.exists():
                    return {
                        'success': False,
                        'message': 'No TaskHistory data available for analysis',
                        'months_analyzed': 0
                    }
            
            # Perform comprehensive analysis
            analysis_result = {
                'success': True,
                'months_analyzed': months_back,
                'date_range': {
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat()
                },
                'total_records': task_history.count(),
                
                # Core analyses
                'employee_performance': self._analyze_employee_performance(task_history),
                'department_analysis': self._analyze_department_performance(task_history),
                'category_analysis': self._analyze_category_performance(task_history),
                'temporal_patterns': self._analyze_temporal_patterns(task_history),
                'completion_rates': self._calculate_completion_rates(task_history),
                'earning_patterns': self._analyze_earning_patterns(task_history),
                
                # Advanced analyses
                'category_department_matrix': self._analyze_category_department_matrix(task_history),
                'performance_benchmarks': self._calculate_performance_benchmarks(task_history),
                'seasonal_trends': self._analyze_seasonal_trends(task_history),
                
                # Insights and recommendations
                'key_insights': self._generate_key_insights(task_history),
                'actionable_recommendations': self._generate_recommendations(task_history),
                
                # Metadata
                'analysis_timestamp': timezone.now().isoformat(),
                'ai_service_used': bool(self.ai_service)
            }
            
            # Add AI-enhanced insights if available
            if self.ai_service:
                try:
                    ai_insights = self._get_ai_enhanced_insights(analysis_result)
                    analysis_result['ai_enhanced_insights'] = ai_insights
                except Exception as e:
                    self.logger.warning(f"AI enhanced insights failed: {e}")
                    analysis_result['ai_enhanced_insights'] = None
            
            self.logger.info("Comprehensive performance analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive performance analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'months_analyzed': months_back
            }
    
    # ============================================================================
    # EMPLOYEE PERFORMANCE ANALYSIS
    # ============================================================================
    
    def _analyze_employee_performance(self, task_history) -> Dict[str, Any]:
        """Analyze individual employee performance patterns."""
        try:
            # Get basic employee statistics with safe division
            employee_stats = task_history.values('employee__id', 'employee__username', 
                                                  'employee__first_name', 'employee__last_name').annotate(
                total_tasks=Count('id'),
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings_raw=Sum(F('mxearning'))
            )
            
            # Calculate safe completion rates and earnings
            employee_stats_list = []
            for stat in employee_stats:
                total_tasks = stat.get('total_tasks', 0)
                total_points = stat.get('total_points', 0)
                total_max_points = stat.get('total_max_points', 0)
                total_earnings_raw = stat.get('total_earnings_raw', 0)
                
                # Safe division for completion rate
                if total_max_points and total_max_points > 0:
                    avg_completion_rate = total_points / total_max_points
                else:
                    avg_completion_rate = 0
                
                # Safe division for earnings
                if total_max_points and total_max_points > 0:
                    total_earnings = (total_points / total_max_points) * total_earnings_raw
                    avg_earnings_per_task = total_earnings / total_tasks if total_tasks > 0 else 0
                else:
                    total_earnings = 0
                    avg_earnings_per_task = 0
                
                stat.update({
                    'avg_completion_rate': avg_completion_rate,
                    'total_earnings': total_earnings,
                    'avg_earnings_per_task': avg_earnings_per_task
                })
                employee_stats_list.append(stat)
            
            # Sort by total earnings
            employee_stats_list.sort(key=lambda x: x.get('total_earnings', 0), reverse=True)
            
            # Identify top performers
            top_performers = employee_stats_list[:10]
            
            # Calculate overall statistics
            total_employees = len(employee_stats_list)
            
            return {
                'total_employees': total_employees,
                'employee_statistics': employee_stats_list,
                'top_performers': top_performers,
                'average_tasks_per_employee': sum(e['total_tasks'] for e in employee_stats_list) / total_employees if total_employees > 0 else 0,
                'average_completion_rate': sum(e['avg_completion_rate'] or 0 for e in employee_stats_list) / total_employees if total_employees > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing employee performance: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # DEPARTMENT PERFORMANCE ANALYSIS
    # ============================================================================
    
    def _analyze_department_performance(self, task_history) -> Dict[str, Any]:
        """Analyze department-level performance patterns using employee categories."""
        try:
            # Since there's no direct department relationship, use employee categories
            department_stats = task_history.values('employee__category').annotate(
                total_tasks=Count('id'),
                unique_employees=Count('employee', distinct=True),
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings_raw=Sum(F('mxearning'))
            )
            
            # Map category numbers to department names if possible
            category_to_dept = {
                '999': 'Other',
                '1': 'IT',
                '2': 'HR',
                '3': 'Finance',
                '4': 'Marketing',
                '5': 'Operations'
            }
            
            # Convert results to include department names with safe calculations
            dept_stats_list = []
            for stat in department_stats:
                category = str(stat.get('employee__category', 'Unknown'))
                dept_name = category_to_dept.get(category, f'Category_{category}')
                
                total_points = stat.get('total_points', 0)
                total_max_points = stat.get('total_max_points', 0)
                total_earnings_raw = stat.get('total_earnings_raw', 0)
                
                # Safe division for completion rate
                if total_max_points and total_max_points > 0:
                    avg_completion_rate = total_points / total_max_points
                else:
                    avg_completion_rate = 0
                
                # Safe division for earnings
                if total_max_points and total_max_points > 0:
                    total_earnings = (total_points / total_max_points) * total_earnings_raw
                else:
                    total_earnings = 0
                
                stat.update({
                    'department_name': dept_name,
                    'avg_completion_rate': avg_completion_rate,
                    'total_earnings': total_earnings
                })
                dept_stats_list.append(stat)
            
            # Sort by total earnings
            dept_stats_list.sort(key=lambda x: x.get('total_earnings', 0), reverse=True)
            
            return {
                'total_departments': len(dept_stats_list),
                'department_statistics': dept_stats_list,
                'top_department': dept_stats_list[0] if dept_stats_list else None
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing department performance: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # CATEGORY PERFORMANCE ANALYSIS
    # ============================================================================
    
    def _analyze_category_performance(self, task_history) -> Dict[str, Any]:
        """Analyze performance by task category."""
        try:
            category_stats = task_history.values('category__title').annotate(
                total_tasks=Count('id'),
                unique_employees=Count('employee', distinct=True),
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings_raw=Sum(F('mxearning'))
            )
            
            # Calculate safe completion rates and earnings
            category_stats_list = []
            for stat in category_stats:
                total_tasks = stat.get('total_tasks', 0)
                total_points = stat.get('total_points', 0)
                total_max_points = stat.get('total_max_points', 0)
                total_earnings_raw = stat.get('total_earnings_raw', 0)
                
                # Safe division for completion rate
                if total_max_points and total_max_points > 0:
                    avg_completion_rate = total_points / total_max_points
                else:
                    avg_completion_rate = 0
                
                # Safe division for earnings
                if total_max_points and total_max_points > 0:
                    total_earnings = (total_points / total_max_points) * total_earnings_raw
                    avg_earnings = total_earnings / total_tasks if total_tasks > 0 else 0
                else:
                    total_earnings = 0
                    avg_earnings = 0
                
                stat.update({
                    'avg_completion_rate': avg_completion_rate,
                    'avg_earnings': avg_earnings,
                    'total_earnings': total_earnings
                })
                category_stats_list.append(stat)
            
            # Sort by total tasks
            category_stats_list.sort(key=lambda x: x.get('total_tasks', 0), reverse=True)
            
            return {
                'total_categories': len(category_stats_list),
                'category_statistics': category_stats_list,
                'most_common_category': category_stats_list[0] if category_stats_list else None
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing category performance: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # TEMPORAL PATTERN ANALYSIS
    # ============================================================================
    
    def _analyze_temporal_patterns(self, task_history) -> Dict[str, Any]:
        """Analyze time-based patterns in task performance."""
        try:
            # Monthly performance trends
            monthly_stats = task_history.extra(
                select={'month': "EXTRACT(month FROM daf_date)", 'year': "EXTRACT(year FROM daf_date)"}
            ).values('month', 'year').annotate(
                total_tasks=Count('id'),
                avg_completion_rate=Avg(F('point') / F('mxpoint')),
                total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning'))
            ).order_by('year', 'month')
            
            return {
                'monthly_trends': list(monthly_stats),
                'total_months': monthly_stats.count()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing temporal patterns: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # COMPLETION RATE ANALYSIS
    # ============================================================================
    
    def _calculate_completion_rates(self, task_history) -> Dict[str, Any]:
        """Calculate completion rates across different dimensions."""
        try:
            total_tasks = task_history.count()
            if total_tasks == 0:
                return {'error': 'No tasks to analyze'}
            
            # Overall completion rate with safe division
            total_points = task_history.aggregate(total=Sum('point'))['total'] or 0
            total_max_points = task_history.aggregate(total=Sum('mxpoint'))['total'] or 0
            overall_rate = (total_points / total_max_points) if total_max_points > 0 else 0
            
            # High performers (>= 90% completion) with safe division
            high_performers = 0
            low_performers = 0
            
            for task in task_history:
                if task.mxpoint and task.mxpoint > 0:
                    completion_rate = task.point / task.mxpoint
                    if completion_rate >= 0.9:
                        high_performers += 1
                    elif completion_rate < 0.7:
                        low_performers += 1
            
            return {
                'overall_completion_rate': float(overall_rate),
                'total_tasks_analyzed': total_tasks,
                'high_performance_tasks': high_performers,
                'high_performance_percentage': (high_performers / total_tasks) * 100 if total_tasks > 0 else 0,
                'low_performance_tasks': low_performers,
                'low_performance_percentage': (low_performers / total_tasks) * 100 if total_tasks > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating completion rates: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # EARNING PATTERN ANALYSIS
    # ============================================================================
    
    def _analyze_earning_patterns(self, task_history) -> Dict[str, Any]:
        """Analyze earning patterns and distributions."""
        try:
            # Get raw data for safe calculations
            raw_stats = task_history.aggregate(
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings_raw=Sum('mxearning'),
                task_count=Count('id')
            )
            
            total_points = raw_stats.get('total_points', 0) or 0
            total_max_points = raw_stats.get('total_max_points', 0) or 0
            total_earnings_raw = raw_stats.get('total_earnings_raw', 0) or 0
            task_count = raw_stats.get('task_count', 0) or 0
            
            # Calculate total earnings safely
            if total_max_points and total_max_points > 0:
                total_earnings = (total_points / total_max_points) * total_earnings_raw
                avg_earnings_per_task = total_earnings / task_count if task_count > 0 else 0
            else:
                total_earnings = 0
                avg_earnings_per_task = 0
            
            # Calculate individual task earnings for min/max
            individual_earnings = []
            for task in task_history:
                if task.mxpoint and task.mxpoint > 0:
                    earnings = (task.point / task.mxpoint) * task.mxearning
                    individual_earnings.append(earnings)
            
            if individual_earnings:
                max_earnings = max(individual_earnings)
                min_earnings = min(individual_earnings)
                earnings_range = max_earnings - min_earnings
            else:
                max_earnings = 0
                min_earnings = 0
                earnings_range = 0
            
            return {
                'total_earnings': float(total_earnings),
                'average_earnings_per_task': float(avg_earnings_per_task),
                'max_earnings': float(max_earnings),
                'min_earnings': float(min_earnings),
                'earnings_range': float(earnings_range)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing earning patterns: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # ADVANCED ANALYSIS
    # ============================================================================
    
    def _analyze_category_department_matrix(self, task_history) -> Dict[str, Any]:
        """Create performance matrix between categories and departments."""
        try:
            matrix_data = task_history.values(
                'category__title', 'employee__department__name'
            ).annotate(
                task_count=Count('id'),
                avg_completion_rate=Avg(F('point') / F('mxpoint')),
                avg_earnings=Avg(F('point') / F('mxpoint') * F('mxearning')),
                unique_employees=Count('employee', distinct=True)
            ).order_by('category__title', 'employee__department__name')
            
            # Create matrix structure
            performance_matrix = {}
            for item in matrix_data:
                category = item['category__title']
                department = item['employee__department__name']
                
                if category not in performance_matrix:
                    performance_matrix[category] = {}
                
                performance_matrix[category][department] = {
                    'task_count': item['task_count'],
                    'completion_rate': float(item['avg_completion_rate'] or 0),
                    'avg_earnings': float(item['avg_earnings'] or 0),
                    'employee_count': item['unique_employees']
                }
            
            return {
                'performance_matrix': performance_matrix,
                'total_combinations': len(list(matrix_data))
            }
            
        except Exception as e:
            self.logger.error(f"Error creating category-department matrix: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_benchmarks(self, task_history) -> Dict[str, Any]:
        """Calculate performance benchmarks for comparison."""
        try:
            # Calculate benchmarks by category
            category_benchmarks = {}
            for category in TaskCategory.objects.all():
                category_tasks = task_history.filter(category=category)
                if category_tasks.exists():
                    avg_completion = category_tasks.aggregate(
                        avg=Avg(F('point') / F('mxpoint'))
                    )['avg'] or 0
                    
                    category_benchmarks[category.title] = {
                        'avg_completion_rate': float(avg_completion),
                        'task_count': category_tasks.count(),
                        'benchmark_tier': 'High' if avg_completion >= 0.85 else 'Medium' if avg_completion >= 0.7 else 'Low'
                    }
            
            # Calculate overall benchmark
            overall_benchmark = task_history.aggregate(
                avg=Avg(F('point') / F('mxpoint'))
            )['avg'] or 0
            
            return {
                'category_benchmarks': category_benchmarks,
                'overall_benchmark': float(overall_benchmark),
                'benchmark_calculation_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating benchmarks: {e}")
            return {'error': str(e)}
    
    def _analyze_seasonal_trends(self, task_history) -> Dict[str, Any]:
        """Analyze seasonal performance trends."""
        try:
            seasonal_stats = {}
            
            # Group by seasons
            for task in task_history:
                if task.daf_date:
                    month = task.daf_date.month
                    
                    # Determine season
                    if month in [12, 1, 2]:
                        season = 'Winter'
                    elif month in [3, 4, 5]:
                        season = 'Spring'
                    elif month in [6, 7, 8]:
                        season = 'Summer'
                    else:
                        season = 'Fall'
                    
                    if season not in seasonal_stats:
                        seasonal_stats[season] = {
                            'tasks': [],
                            'total_points': 0,
                            'total_max_points': 0,
                            'total_earnings': 0
                        }
                    
                    seasonal_stats[season]['tasks'].append(task.id)
                    seasonal_stats[season]['total_points'] += float(task.point)
                    seasonal_stats[season]['total_max_points'] += float(task.mxpoint)
                    
                    # Calculate earnings
                    if task.mxpoint > 0:
                        earnings = (task.point / task.mxpoint) * task.mxearning
                        seasonal_stats[season]['total_earnings'] += float(earnings)
            
            # Calculate averages for each season
            for season in seasonal_stats:
                task_count = len(seasonal_stats[season]['tasks'])
                if task_count > 0:
                    seasonal_stats[season]['task_count'] = task_count
                    seasonal_stats[season]['avg_completion_rate'] = (
                        seasonal_stats[season]['total_points'] / seasonal_stats[season]['total_max_points']
                    ) if seasonal_stats[season]['total_max_points'] > 0 else 0
                    seasonal_stats[season]['avg_earnings'] = (
                        seasonal_stats[season]['total_earnings'] / task_count
                    ) if task_count > 0 else 0
                    del seasonal_stats[season]['tasks']  # Remove task IDs from output
            
            return seasonal_stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonal trends: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # INSIGHTS GENERATION
    # ============================================================================
    
    def _generate_key_insights(self, task_history) -> List[Dict[str, str]]:
        """Generate key insights from the analysis."""
        insights = []
        
        try:
            # Insight 1: Top performing employees (safe calculation)
            employee_earnings = {}
            for task in task_history:
                if task.employee and task.mxpoint and task.mxpoint > 0:
                    earnings = (task.point / task.mxpoint) * task.mxearning
                    employee_username = task.employee.username if hasattr(task.employee, 'username') else str(task.employee)
                    
                    if employee_username not in employee_earnings:
                        employee_earnings[employee_username] = 0
                    employee_earnings[employee_username] += earnings
            
            if employee_earnings:
                top_employees = sorted(employee_earnings.items(), key=lambda x: x[1], reverse=True)[:3]
                top_names = [emp[0] for emp in top_employees]
                insights.append({
                    'type': 'top_performers',
                    'title': 'Top Performers Identified',
                    'description': f"Top performing employees: {', '.join(top_names)}",
                    'priority': 'high'
                })
            
            # Insight 2: Most effective category (safe calculation)
            category_rates = {}
            for task in task_history:
                if task.category and task.mxpoint and task.mxpoint > 0:
                    completion_rate = task.point / task.mxpoint
                    category_name = task.category.title if hasattr(task.category, 'title') else str(task.category)
                    
                    if category_name not in category_rates:
                        category_rates[category_name] = []
                    category_rates[category_name].append(completion_rate)
            
            if category_rates:
                avg_category_rates = {cat: sum(rates)/len(rates) for cat, rates in category_rates.items()}
                best_category = max(avg_category_rates.items(), key=lambda x: x[1])
                
                insights.append({
                    'type': 'effective_category',
                    'title': 'Most Effective Task Category',
                    'description': f"{best_category[0]} has the highest completion rate at {best_category[1]:.1%}",
                    'priority': 'medium'
                })
            
            # Insight 3: Performance trends (safe calculation)
            try:
                from dateutil.relativedelta import relativedelta
                cutoff_date = timezone.now().date() - relativedelta(months=3)
                
                recent_tasks = [task for task in task_history if task.daf_date and task.daf_date >= cutoff_date]
                older_tasks = [task for task in task_history if task.daf_date and task.daf_date < cutoff_date]
                
                if recent_tasks and older_tasks:
                    recent_rate = sum(task.point/task.mxpoint for task in recent_tasks if task.mxpoint > 0) / len([t for t in recent_tasks if t.mxpoint > 0])
                    older_rate = sum(task.point/task.mxpoint for task in older_tasks if task.mxpoint > 0) / len([t for t in older_tasks if t.mxpoint > 0])
                    
                    if recent_rate > older_rate:
                        insights.append({
                            'type': 'performance_trend',
                            'title': 'Performance Improving',
                            'description': f"Recent performance ({recent_rate:.1%}) is better than historical ({older_rate:.1%})",
                            'priority': 'high'
                        })
                    else:
                        insights.append({
                            'type': 'performance_trend',
                            'title': 'Performance Needs Attention',
                            'description': f"Recent performance ({recent_rate:.1%}) is lower than historical ({older_rate:.1%})",
                            'priority': 'critical'
                        })
            except:
                # If date comparison fails, skip this insight
                pass
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return [{'type': 'error', 'title': 'Error', 'description': str(e), 'priority': 'low'}]
    
    def _generate_recommendations(self, task_history) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        try:
            # Recommendation 1: Focus on low-performing categories (safe calculation)
            category_rates = {}
            for task in task_history:
                if task.category and task.mxpoint and task.mxpoint > 0:
                    completion_rate = task.point / task.mxpoint
                    category_name = task.category.title if hasattr(task.category, 'title') else str(task.category)
                    
                    if category_name not in category_rates:
                        category_rates[category_name] = []
                    category_rates[category_name].append(completion_rate)
            
            if category_rates:
                avg_category_rates = {cat: sum(rates)/len(rates) for cat, rates in category_rates.items()}
                low_performing_categories = [(cat, rate) for cat, rate in avg_category_rates.items() if rate < 0.7]
                
                for category, rate in low_performing_categories[:3]:
                    recommendations.append({
                        'type': 'improvement',
                        'title': f"Improve {category} Performance",
                        'description': f"Current completion rate of {rate:.1%} is below target. Consider additional training or resource allocation.",
                        'action': 'training_and_support',
                        'priority': 'high'
                    })
            
            # Recommendation 2: Leverage top performers (safe calculation)
            employee_rates = {}
            for task in task_history:
                if task.employee and task.mxpoint and task.mxpoint > 0:
                    completion_rate = task.point / task.mxpoint
                    employee_username = task.employee.username if hasattr(task.employee, 'username') else str(task.employee)
                    
                    if employee_username not in employee_rates:
                        employee_rates[employee_username] = []
                    employee_rates[employee_username].append(completion_rate)
            
            if employee_rates:
                avg_employee_rates = {emp: sum(rates)/len(rates) for emp, rates in employee_rates.items()}
                top_performer = max(avg_employee_rates.items(), key=lambda x: x[1])
                
                if top_performer[1] > 0.9:
                    recommendations.append({
                        'type': 'best_practice',
                        'title': 'Leverage Top Performer Best Practices',
                        'description': f"{top_performer[0]} achieves {top_performer[1]:.1%} completion rate. Document and share their approach.",
                        'action': 'knowledge_sharing',
                        'priority': 'medium'
                    })
            
            # Recommendation 3: Optimize task assignment
            recommendations.append({
                'type': 'optimization',
                'title': 'Implement AI-Powered Task Assignment',
                'description': 'Use historical performance data to optimize task-employee matching',
                'action': 'implement_ai_assignment',
                'priority': 'high'
            })
            
            # Recommendation 4: Automate evidence collection (safe calculation)
            try:
                from management.models import TaskLinks
                evidence_count = TaskLinks.objects.filter(
                    task__in=task_history.values_list('id', flat=True)
                ).count()
                
                total_tasks = task_history.count()
                if evidence_count < total_tasks * 0.5:
                    recommendations.append({
                        'type': 'automation',
                        'title': 'Increase Evidence Collection Rate',
                        'description': f'Only {evidence_count} evidence items for {total_tasks} tasks. Implement GoToMeeting automation.',
                        'action': 'implement_gotomeeting_automation',
                        'priority': 'critical'
                    })
            except:
                # If TaskLinks model doesn't exist or query fails, skip this recommendation
                pass
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return [{'type': 'error', 'title': 'Error', 'description': str(e), 'action': 'manual_review', 'priority': 'low'}]
    
    # ============================================================================
    # AI ENHANCEMENT
    # ============================================================================
    
    def _get_ai_enhanced_insights(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-enhanced insights from the analysis."""
        if not self.ai_service:
            return None
        
        try:
            # Prepare data for AI analysis
            ai_input = {
                'total_records': analysis_result.get('total_records', 0),
                'employee_stats': analysis_result.get('employee_performance', {}),
                'department_stats': analysis_result.get('department_analysis', {}),
                'category_stats': analysis_result.get('category_analysis', {}),
                'completion_rates': analysis_result.get('completion_rates', {}),
                'earning_patterns': analysis_result.get('earning_patterns', {})
            }
            
            ai_response = self.ai_service.get_prediction(
                analysis_type='taskhistory_analysis_enhancement',
                input_data=ai_input,
                session_id=f"taskhistory_analysis_{timezone.now().timestamp()}"
            )
            
            return {
                'ai_summary': ai_response.get('summary', 'No AI summary available'),
                'ai_recommendations': ai_response.get('recommendations', []),
                'ai_predictions': ai_response.get('predictions', {}),
                'confidence_score': ai_response.get('confidence_score', 0.75),
                'model_used': ai_response.get('model_used', 'unknown')
            }
            
        except Exception as e:
            self.logger.warning(f"AI enhanced insights failed: {e}")
            return {
                'ai_summary': 'AI analysis unavailable',
                'ai_recommendations': ['Manual analysis recommended'],
                'confidence_score': 0.5,
                'model_used': 'fallback'
            }
    
    # ============================================================================
    # EXPORT AND REPORTING
    # ============================================================================
    
    def export_analysis_to_json(self, months_back: int = 12) -> Dict[str, Any]:
        """Export complete analysis as JSON."""
        try:
            analysis = self.analyze_complete_performance_patterns(months_back)
            
            # Add metadata
            analysis['export_metadata'] = {
                'exported_at': timezone.now().isoformat(),
                'export_format': 'json',
                'data_quality': 'high' if analysis.get('success') else 'low'
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error exporting analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_summary_report(self, months_back: int = 12) -> str:
        """Generate human-readable summary report."""
        try:
            analysis = self.analyze_complete_performance_patterns(months_back)
            
            if not analysis.get('success'):
                return f"Analysis failed: {analysis.get('error', 'Unknown error')}"
            
            report = f"""
# TaskHistory Performance Analysis Report
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {months_back} months

## Summary Statistics
- Total Records Analyzed: {analysis.get('total_records', 0):,}
- Total Employees: {analysis.get('employee_performance', {}).get('total_employees', 0)}
- Total Departments: {analysis.get('department_analysis', {}).get('total_departments', 0)}
- Total Categories: {analysis.get('category_analysis', {}).get('total_categories', 0)}

## Performance Metrics
- Overall Completion Rate: {analysis.get('completion_rates', {}).get('overall_completion_rate', 0):.1%}
- High Performance Tasks: {analysis.get('completion_rates', {}).get('high_performance_percentage', 0):.1%}
- Total Earnings: ${analysis.get('earning_patterns', {}).get('total_earnings', 0):,.2f}
- Average Earnings per Task: ${analysis.get('earning_patterns', {}).get('average_earnings_per_task', 0):,.2f}

## Key Insights
"""
            # Add key insights
            for insight in analysis.get('key_insights', []):
                report += f"\n### {insight.get('title', 'Insight')}\n"
                report += f"{insight.get('description', 'No description')}\n"
            
            report += "\n## Recommendations\n"
            # Add recommendations
            for rec in analysis.get('actionable_recommendations', []):
                report += f"\n### {rec.get('title', 'Recommendation')}\n"
                report += f"{rec.get('description', 'No description')}\n"
                report += f"Action: {rec.get('action', 'N/A')} | Priority: {rec.get('priority', 'medium').upper()}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            return f"Error generating report: {str(e)}"

