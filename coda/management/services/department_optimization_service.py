"""
Department Performance Optimization Service

This service provides AI-powered optimization for department performance,
resource allocation, and strategic planning based on historical data and predictions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F, Max, Min

from management.models import TaskHistory
from shared_core.users import CustomerUser
from management.services.simple_ai_service import SimpleAIService
from management.services.intelligent_assignment_service import IntelligentAssignmentService


class DepartmentOptimizationService:
    """Service for optimizing department performance and resource allocation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_service = SimpleAIService()
        self.assignment_service = IntelligentAssignmentService()
        
        # Department category mapping
        self.department_mapping = {
            'IT': 1,
            'HR': 2,
            'Finance': 3,
            'Marketing': 4,
            'Operations': 5,
            'Other': 999
        }
    
    def optimize_department_performance(self, department_name: str, optimization_goals: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimize department performance based on goals and constraints."""
        try:
            self.logger.info(f"Starting department optimization for {department_name}")
            
            # Set default optimization goals
            if optimization_goals is None:
                optimization_goals = {
                    'target_completion_rate': 0.8,
                    'target_efficiency': 0.9,
                    'workload_balance': 0.8,
                    'cost_optimization': 0.7
                }
            
            # Get department data
            department_data = self._get_department_data(department_name)
            
            if not department_data['employees']:
                return {
                    'success': False,
                    'message': f'No employees found in department {department_name}',
                    'optimization': None
                }
            
            # Analyze current performance
            current_analysis = self._analyze_current_performance(department_data)
            
            # Generate optimization strategies
            optimization_strategies = self._generate_optimization_strategies(
                department_data, current_analysis, optimization_goals
            )
            
            # Calculate optimization impact
            impact_analysis = self._calculate_optimization_impact(
                department_data, current_analysis, optimization_strategies
            )
            
            # Generate implementation plan
            implementation_plan = self._generate_implementation_plan(
                optimization_strategies, impact_analysis
            )
            
            return {
                'success': True,
                'department_name': department_name,
                'optimization_goals': optimization_goals,
                'current_performance': current_analysis,
                'optimization_strategies': optimization_strategies,
                'impact_analysis': impact_analysis,
                'implementation_plan': implementation_plan,
                'recommended_actions': self._generate_recommended_actions(
                    optimization_strategies, impact_analysis
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing department performance: {e}")
            return {
                'success': False,
                'message': f'Department optimization failed: {str(e)}',
                'optimization': None
            }
    
    def compare_department_performance(self, departments: List[str] = None) -> Dict[str, Any]:
        """Compare performance across departments."""
        try:
            self.logger.info("Starting department performance comparison")
            
            if departments is None:
                departments = list(self.department_mapping.keys())
            
            comparison_results = {}
            
            for department_name in departments:
                try:
                    department_data = self._get_department_data(department_name)
                    if department_data['employees']:
                        current_analysis = self._analyze_current_performance(department_data)
                        comparison_results[department_name] = current_analysis
                except Exception as e:
                    self.logger.warning(f"Failed to analyze department {department_name}: {e}")
                    continue
            
            if not comparison_results:
                return {
                    'success': False,
                    'message': 'No departments could be analyzed',
                    'comparison': {}
                }
            
            # Calculate benchmarks and rankings
            benchmarks = self._calculate_department_benchmarks(comparison_results)
            rankings = self._calculate_department_rankings(comparison_results)
            
            # Generate insights
            insights = self._generate_comparison_insights(comparison_results, rankings)
            
            return {
                'success': True,
                'departments_analyzed': len(comparison_results),
                'comparison_results': comparison_results,
                'benchmarks': benchmarks,
                'rankings': rankings,
                'insights': insights,
                'recommendations': self._generate_comparison_recommendations(
                    comparison_results, rankings
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing department performance: {e}")
            return {
                'success': False,
                'message': f'Department comparison failed: {str(e)}',
                'comparison': {}
            }
    
    def predict_department_capacity(self, department_name: str, time_horizon_days: int = 30) -> Dict[str, Any]:
        """Predict department capacity and resource requirements."""
        try:
            self.logger.info(f"Predicting capacity for department {department_name} over {time_horizon_days} days")
            
            # Get department data
            department_data = self._get_department_data(department_name)
            
            if not department_data['employees']:
                return {
                    'success': False,
                    'message': f'No employees found in department {department_name}',
                    'capacity_prediction': None
                }
            
            # Analyze historical capacity
            historical_capacity = self._analyze_historical_capacity(department_data, time_horizon_days)
            
            # Predict future capacity
            capacity_predictions = self._predict_future_capacity(
                department_data, historical_capacity, time_horizon_days
            )
            
            # Calculate resource requirements
            resource_requirements = self._calculate_resource_requirements(
                department_data, capacity_predictions
            )
            
            # Generate capacity optimization recommendations
            optimization_recommendations = self._generate_capacity_recommendations(
                department_data, capacity_predictions, resource_requirements
            )
            
            return {
                'success': True,
                'department_name': department_name,
                'time_horizon_days': time_horizon_days,
                'current_capacity': historical_capacity['current'],
                'predicted_capacity': capacity_predictions,
                'resource_requirements': resource_requirements,
                'optimization_recommendations': optimization_recommendations,
                'capacity_trends': historical_capacity['trends'],
                'bottlenecks': self._identify_capacity_bottlenecks(
                    department_data, capacity_predictions
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting department capacity: {e}")
            return {
                'success': False,
                'message': f'Capacity prediction failed: {str(e)}',
                'capacity_prediction': None
            }
    
    def _get_department_data(self, department_name: str) -> Dict[str, Any]:
        """Get comprehensive data for a department."""
        category = self.department_mapping.get(department_name)
        
        if category is None:
            return {'employees': [], 'tasks': [], 'performance_data': []}
        
        # Get employees
        employees = list(CustomerUser.objects.filter(category=category))
        employee_ids = [emp.id for emp in employees]
        
        # Get tasks
        tasks = TaskHistory.objects.filter(employee_id__in=employee_ids)
        
        # Get performance data
        performance_data = []
        for task in tasks:
            if task.mxpoint and task.mxpoint > 0:
                performance_data.append({
                    'completion_rate': float(task.point) / float(task.mxpoint),
                    'employee_id': task.employee.id,
                    'category_id': task.category.id if task.category else None,
                    'date': task.daf_date,
                    'earnings': float(task.mxearning)
                })
        
        return {
            'employees': employees,
            'tasks': tasks,
            'performance_data': performance_data,
            'employee_ids': employee_ids,
            'department_name': department_name,
            'category': category
        }
    
    def _analyze_current_performance(self, department_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current department performance."""
        performance_data = department_data['performance_data']
        
        if not performance_data:
            return {
                'completion_rate': 0.0,
                'efficiency_score': 0.0,
                'workload_balance': 0.0,
                'employee_count': len(department_data['employees']),
                'task_count': 0,
                'total_earnings': 0.0,
                'performance_trend': 'stable'
            }
        
        # Calculate metrics
        completion_rates = [p['completion_rate'] for p in performance_data]
        avg_completion_rate = sum(completion_rates) / len(completion_rates)
        
        total_earnings = sum(p['earnings'] for p in performance_data)
        
        # Calculate efficiency score (completion rate * earnings efficiency)
        earnings_per_task = total_earnings / len(performance_data) if performance_data else 0
        efficiency_score = avg_completion_rate * min(1.0, earnings_per_task / 1000)  # Normalize
        
        # Calculate workload balance
        employee_task_counts = {}
        for task in department_data['tasks']:
            emp_id = task.employee.id
            employee_task_counts[emp_id] = employee_task_counts.get(emp_id, 0) + 1
        
        if employee_task_counts:
            task_counts = list(employee_task_counts.values())
            workload_variance = max(task_counts) - min(task_counts)
            workload_balance = max(0.0, 1.0 - (workload_variance / max(task_counts)))
        else:
            workload_balance = 1.0
        
        # Calculate performance trend
        recent_data = [p for p in performance_data if p['date'] and p['date'] >= timezone.now().date() - timedelta(days=30)]
        older_data = [p for p in performance_data if p['date'] and p['date'] < timezone.now().date() - timedelta(days=30)]
        
        if recent_data and older_data:
            recent_avg = sum(p['completion_rate'] for p in recent_data) / len(recent_data)
            older_avg = sum(p['completion_rate'] for p in older_data) / len(older_data)
            
            if recent_avg > older_avg * 1.1:
                performance_trend = 'improving'
            elif recent_avg < older_avg * 0.9:
                performance_trend = 'declining'
            else:
                performance_trend = 'stable'
        else:
            performance_trend = 'stable'
        
        return {
            'completion_rate': avg_completion_rate,
            'efficiency_score': efficiency_score,
            'workload_balance': workload_balance,
            'employee_count': len(department_data['employees']),
            'task_count': len(performance_data),
            'total_earnings': total_earnings,
            'performance_trend': performance_trend,
            'top_performers': self._identify_top_performers(department_data),
            'underperformers': self._identify_underperformers(department_data)
        }
    
    def _generate_optimization_strategies(self, department_data: Dict[str, Any], 
                                        current_analysis: Dict[str, Any], 
                                        goals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization strategies based on current performance and goals."""
        strategies = []
        
        # Strategy 1: Improve completion rates
        if current_analysis['completion_rate'] < goals['target_completion_rate']:
            strategies.append({
                'type': 'completion_rate_improvement',
                'priority': 'high',
                'title': 'Improve Task Completion Rates',
                'description': f"Current completion rate ({current_analysis['completion_rate']:.1%}) is below target ({goals['target_completion_rate']:.1%})",
                'actions': [
                    'Provide additional training for underperforming employees',
                    'Implement task complexity assessment',
                    'Set up mentoring programs',
                    'Review and optimize task assignment algorithms'
                ],
                'expected_impact': 'medium',
                'implementation_effort': 'medium',
                'estimated_improvement': min(0.2, goals['target_completion_rate'] - current_analysis['completion_rate'])
            })
        
        # Strategy 2: Optimize workload balance
        if current_analysis['workload_balance'] < goals['workload_balance']:
            strategies.append({
                'type': 'workload_balancing',
                'priority': 'high',
                'title': 'Optimize Workload Distribution',
                'description': f"Current workload balance ({current_analysis['workload_balance']:.1%}) needs improvement",
                'actions': [
                    'Implement intelligent task assignment system',
                    'Redistribute tasks from overloaded to underloaded employees',
                    'Monitor real-time workload metrics',
                    'Establish workload balancing policies'
                ],
                'expected_impact': 'high',
                'implementation_effort': 'low',
                'estimated_improvement': min(0.3, goals['workload_balance'] - current_analysis['workload_balance'])
            })
        
        # Strategy 3: Enhance efficiency
        if current_analysis['efficiency_score'] < goals['target_efficiency']:
            strategies.append({
                'type': 'efficiency_enhancement',
                'priority': 'medium',
                'title': 'Enhance Operational Efficiency',
                'description': f"Efficiency score ({current_analysis['efficiency_score']:.1%}) can be improved",
                'actions': [
                    'Automate repetitive tasks',
                    'Implement performance monitoring dashboards',
                    'Optimize task categorization and routing',
                    'Provide efficiency training programs'
                ],
                'expected_impact': 'medium',
                'implementation_effort': 'high',
                'estimated_improvement': min(0.2, goals['target_efficiency'] - current_analysis['efficiency_score'])
            })
        
        # Strategy 4: Cost optimization
        if current_analysis['total_earnings'] > 0:
            cost_per_task = current_analysis['total_earnings'] / current_analysis['task_count']
            strategies.append({
                'type': 'cost_optimization',
                'priority': 'medium',
                'title': 'Optimize Cost Per Task',
                'description': f"Current cost per task is ${cost_per_task:.2f}",
                'actions': [
                    'Optimize task assignment for cost efficiency',
                    'Implement performance-based incentives',
                    'Review and optimize task complexity',
                    'Monitor cost per completion metrics'
                ],
                'expected_impact': 'low',
                'implementation_effort': 'medium',
                'estimated_improvement': 0.1
            })
        
        return strategies
    
    def _calculate_optimization_impact(self, department_data: Dict[str, Any], 
                                     current_analysis: Dict[str, Any], 
                                     strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the expected impact of optimization strategies."""
        if not strategies:
            return {
                'overall_impact': 'none',
                'expected_improvements': {},
                'implementation_timeline': 0,
                'roi_estimate': 0.0
            }
        
        # Calculate cumulative improvements
        improvements = {
            'completion_rate': 0.0,
            'efficiency_score': 0.0,
            'workload_balance': 0.0,
            'cost_optimization': 0.0
        }
        
        implementation_effort_days = 0
        
        for strategy in strategies:
            strategy_type = strategy['type']
            improvement = strategy.get('estimated_improvement', 0.0)
            effort = strategy.get('implementation_effort', 'medium')
            
            # Map effort to days
            effort_days = {'low': 7, 'medium': 14, 'high': 30}.get(effort, 14)
            implementation_effort_days += effort_days
            
            # Add improvement to relevant metric
            if 'completion_rate' in strategy_type:
                improvements['completion_rate'] += improvement
            elif 'efficiency' in strategy_type:
                improvements['efficiency_score'] += improvement
            elif 'workload' in strategy_type:
                improvements['workload_balance'] += improvement
            elif 'cost' in strategy_type:
                improvements['cost_optimization'] += improvement
        
        # Calculate projected performance
        projected_performance = {
            'completion_rate': min(1.0, current_analysis['completion_rate'] + improvements['completion_rate']),
            'efficiency_score': min(1.0, current_analysis['efficiency_score'] + improvements['efficiency_score']),
            'workload_balance': min(1.0, current_analysis['workload_balance'] + improvements['workload_balance'])
        }
        
        # Calculate ROI estimate (simplified)
        current_monthly_earnings = current_analysis['total_earnings']
        projected_monthly_earnings = current_monthly_earnings * (1 + sum(improvements.values()))
        monthly_improvement = projected_monthly_earnings - current_monthly_earnings
        implementation_cost_estimate = implementation_effort_days * 500  # $500/day estimate
        roi_estimate = (monthly_improvement * 12) / implementation_cost_estimate if implementation_cost_estimate > 0 else 0
        
        # Determine overall impact level
        total_improvement = sum(improvements.values())
        if total_improvement > 0.3:
            overall_impact = 'high'
        elif total_improvement > 0.15:
            overall_impact = 'medium'
        elif total_improvement > 0.05:
            overall_impact = 'low'
        else:
            overall_impact = 'minimal'
        
        return {
            'overall_impact': overall_impact,
            'expected_improvements': improvements,
            'projected_performance': projected_performance,
            'implementation_timeline': implementation_effort_days,
            'roi_estimate': roi_estimate,
            'monthly_earnings_improvement': monthly_improvement,
            'payback_period_months': implementation_cost_estimate / monthly_improvement if monthly_improvement > 0 else 0
        }
    
    def _generate_implementation_plan(self, strategies: List[Dict[str, Any]], 
                                    impact_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed implementation plan."""
        if not strategies:
            return {
                'phases': [],
                'timeline': 0,
                'resources_required': [],
                'success_metrics': []
            }
        
        # Sort strategies by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        sorted_strategies = sorted(strategies, key=lambda s: priority_order.get(s.get('priority', 'low'), 3))
        
        # Create implementation phases
        phases = []
        current_phase = 1
        phase_duration = 0
        
        for i, strategy in enumerate(sorted_strategies):
            effort = strategy.get('implementation_effort', 'medium')
            effort_days = {'low': 7, 'medium': 14, 'high': 30}.get(effort, 14)
            
            phases.append({
                'phase': current_phase,
                'strategy': strategy['title'],
                'duration_days': effort_days,
                'actions': strategy['actions'],
                'expected_impact': strategy['expected_impact'],
                'success_metrics': self._define_success_metrics(strategy)
            })
            
            phase_duration += effort_days
            
            # Start new phase if current one is getting long
            if phase_duration > 21 and i < len(sorted_strategies) - 1:
                current_phase += 1
                phase_duration = 0
        
        return {
            'phases': phases,
            'timeline': sum(p['duration_days'] for p in phases),
            'resources_required': self._calculate_resource_requirements_implementation(strategies),
            'success_metrics': self._define_overall_success_metrics(strategies),
            'risk_mitigation': self._identify_implementation_risks(strategies)
        }
    
    def _generate_recommended_actions(self, strategies: List[Dict[str, Any]], 
                                    impact_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized recommended actions."""
        actions = []
        
        # Immediate actions (high priority, low effort)
        immediate_strategies = [s for s in strategies if s.get('priority') == 'high' and s.get('implementation_effort') == 'low']
        
        for strategy in immediate_strategies:
            actions.append({
                'type': 'immediate',
                'priority': 'critical',
                'title': f"Implement {strategy['title']}",
                'description': strategy['description'],
                'timeline': '1-2 weeks',
                'expected_impact': strategy['expected_impact'],
                'actions': strategy['actions'][:2]  # Top 2 actions
            })
        
        # Short-term actions (medium-high priority)
        short_term_strategies = [s for s in strategies if s.get('priority') in ['high', 'medium'] and s.get('implementation_effort') == 'medium']
        
        for strategy in short_term_strategies:
            actions.append({
                'type': 'short_term',
                'priority': 'high',
                'title': f"Plan {strategy['title']}",
                'description': strategy['description'],
                'timeline': '2-4 weeks',
                'expected_impact': strategy['expected_impact'],
                'actions': strategy['actions'][:2]
            })
        
        # Long-term actions (all others)
        long_term_strategies = [s for s in strategies if s not in immediate_strategies and s not in short_term_strategies]
        
        for strategy in long_term_strategies:
            actions.append({
                'type': 'long_term',
                'priority': 'medium',
                'title': f"Evaluate {strategy['title']}",
                'description': strategy['description'],
                'timeline': '1-3 months',
                'expected_impact': strategy['expected_impact'],
                'actions': strategy['actions'][:1]  # Top action
            })
        
        return actions
    
    def _identify_top_performers(self, department_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify top performing employees in the department."""
        employee_performance = {}
        
        for task in department_data['tasks']:
            if task.mxpoint and task.mxpoint > 0:
                emp_id = task.employee.id
                completion_rate = float(task.point) / float(task.mxpoint)
                
                if emp_id not in employee_performance:
                    employee_performance[emp_id] = {
                        'employee_name': f"{task.employee.first_name} {task.employee.last_name}",
                        'tasks': [],
                        'total_earnings': 0.0
                    }
                
                employee_performance[emp_id]['tasks'].append(completion_rate)
                employee_performance[emp_id]['total_earnings'] += float(task.mxearning)
        
        # Calculate averages and sort
        top_performers = []
        for emp_id, data in employee_performance.items():
            if data['tasks']:
                avg_completion = sum(data['tasks']) / len(data['tasks'])
                top_performers.append({
                    'employee_id': emp_id,
                    'employee_name': data['employee_name'],
                    'avg_completion_rate': avg_completion,
                    'task_count': len(data['tasks']),
                    'total_earnings': data['total_earnings']
                })
        
        return sorted(top_performers, key=lambda x: x['avg_completion_rate'], reverse=True)[:3]
    
    def _identify_underperformers(self, department_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify underperforming employees in the department."""
        employee_performance = {}
        
        for task in department_data['tasks']:
            if task.mxpoint and task.mxpoint > 0:
                emp_id = task.employee.id
                completion_rate = float(task.point) / float(task.mxpoint)
                
                if emp_id not in employee_performance:
                    employee_performance[emp_id] = {
                        'employee_name': f"{task.employee.first_name} {task.employee.last_name}",
                        'tasks': []
                    }
                
                employee_performance[emp_id]['tasks'].append(completion_rate)
        
        # Calculate averages and identify underperformers
        underperformers = []
        for emp_id, data in employee_performance.items():
            if data['tasks']:
                avg_completion = sum(data['tasks']) / len(data['tasks'])
                if avg_completion < 0.5:  # Below 50% completion rate
                    underperformers.append({
                        'employee_id': emp_id,
                        'employee_name': data['employee_name'],
                        'avg_completion_rate': avg_completion,
                        'task_count': len(data['tasks']),
                        'improvement_needed': 0.5 - avg_completion
                    })
        
        return sorted(underperformers, key=lambda x: x['improvement_needed'], reverse=True)[:3]
    
    def _calculate_department_benchmarks(self, comparison_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate benchmarks across departments."""
        if not comparison_results:
            return {}
        
        completion_rates = [r['completion_rate'] for r in comparison_results.values()]
        efficiency_scores = [r['efficiency_score'] for r in comparison_results.values()]
        workload_balances = [r['workload_balance'] for r in comparison_results.values()]
        
        return {
            'completion_rate': {
                'average': sum(completion_rates) / len(completion_rates),
                'highest': max(completion_rates),
                'lowest': min(completion_rates),
                'standard_deviation': self._calculate_std_dev(completion_rates)
            },
            'efficiency_score': {
                'average': sum(efficiency_scores) / len(efficiency_scores),
                'highest': max(efficiency_scores),
                'lowest': min(efficiency_scores),
                'standard_deviation': self._calculate_std_dev(efficiency_scores)
            },
            'workload_balance': {
                'average': sum(workload_balances) / len(workload_balances),
                'highest': max(workload_balances),
                'lowest': min(workload_balances),
                'standard_deviation': self._calculate_std_dev(workload_balances)
            }
        }
    
    def _calculate_department_rankings(self, comparison_results: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Calculate department rankings."""
        if not comparison_results:
            return {}
        
        # Rank by completion rate
        completion_ranking = sorted(
            comparison_results.items(),
            key=lambda x: x[1]['completion_rate'],
            reverse=True
        )
        
        # Rank by efficiency score
        efficiency_ranking = sorted(
            comparison_results.items(),
            key=lambda x: x[1]['efficiency_score'],
            reverse=True
        )
        
        # Rank by workload balance
        workload_ranking = sorted(
            comparison_results.items(),
            key=lambda x: x[1]['workload_balance'],
            reverse=True
        )
        
        return {
            'completion_rate': [dept for dept, _ in completion_ranking],
            'efficiency_score': [dept for dept, _ in efficiency_ranking],
            'workload_balance': [dept for dept, _ in workload_ranking],
            'overall': self._calculate_overall_ranking(comparison_results)
        }
    
    def _calculate_overall_ranking(self, comparison_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """Calculate overall department ranking."""
        overall_scores = {}
        
        for dept, data in comparison_results.items():
            # Weighted average of key metrics
            overall_score = (
                data['completion_rate'] * 0.4 +
                data['efficiency_score'] * 0.3 +
                data['workload_balance'] * 0.3
            )
            overall_scores[dept] = overall_score
        
        return sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_comparison_insights(self, comparison_results: Dict[str, Dict[str, Any]], 
                                    rankings: Dict[str, List[str]]) -> List[str]:
        """Generate insights from department comparison."""
        insights = []
        
        if not comparison_results:
            return insights
        
        # Best performing department
        best_dept = rankings['overall'][0][0]
        insights.append(f"{best_dept} is the top-performing department overall")
        
        # Completion rate insights
        completion_ranking = rankings['completion_rate']
        if len(completion_ranking) >= 2:
            best_completion = completion_ranking[0]
            worst_completion = completion_ranking[-1]
            insights.append(f"{best_completion} has the highest completion rate, while {worst_completion} needs improvement")
        
        # Workload balance insights
        workload_ranking = rankings['workload_balance']
        if len(workload_ranking) >= 2:
            best_workload = workload_ranking[0]
            worst_workload = workload_ranking[-1]
            insights.append(f"{best_workload} has the best workload balance, {worst_workload} may need rebalancing")
        
        return insights
    
    def _generate_comparison_recommendations(self, comparison_results: Dict[str, Dict[str, Any]], 
                                           rankings: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on department comparison."""
        recommendations = []
        
        if not comparison_results:
            return recommendations
        
        # Find departments that need improvement
        overall_ranking = rankings['overall']
        if len(overall_ranking) >= 2:
            bottom_dept = overall_ranking[-1][0]
            bottom_performance = comparison_results[bottom_dept]
            
            recommendations.append({
                'type': 'department_improvement',
                'priority': 'high',
                'title': f'Improve {bottom_dept} Department Performance',
                'description': f'{bottom_dept} ranks lowest overall and needs targeted improvement',
                'actions': [
                    'Analyze specific performance gaps',
                    'Implement targeted training programs',
                    'Review task assignment strategies',
                    'Monitor progress closely'
                ]
            })
        
        return recommendations
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _analyze_historical_capacity(self, department_data: Dict[str, Any], time_horizon_days: int) -> Dict[str, Any]:
        """Analyze historical capacity patterns."""
        # This is a simplified implementation
        # In a real system, this would analyze detailed historical patterns
        
        tasks = department_data['tasks']
        current_tasks = len([t for t in tasks if t.daf_date and t.daf_date >= timezone.now().date() - timedelta(days=30)])
        
        return {
            'current': current_tasks,
            'trends': {
                'monthly_average': current_tasks,
                'peak_capacity': current_tasks * 1.5,
                'sustainable_capacity': current_tasks * 1.2
            }
        }
    
    def _predict_future_capacity(self, department_data: Dict[str, Any], 
                               historical_capacity: Dict[str, Any], 
                               time_horizon_days: int) -> Dict[str, Any]:
        """Predict future department capacity."""
        current = historical_capacity['current']
        
        # Simple prediction based on current capacity and trends
        return {
            'predicted_daily_capacity': current / 30,  # Current monthly / 30 days
            'predicted_monthly_capacity': current,
            'peak_capacity': historical_capacity['trends']['peak_capacity'],
            'recommended_capacity': historical_capacity['trends']['sustainable_capacity']
        }
    
    def _calculate_resource_requirements(self, department_data: Dict[str, Any], 
                                       capacity_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource requirements based on capacity predictions."""
        employee_count = len(department_data['employees'])
        recommended_capacity = capacity_predictions['recommended_capacity']
        
        return {
            'current_employees': employee_count,
            'recommended_employees': max(employee_count, int(recommended_capacity / 10)),  # Assume 10 tasks per employee
            'additional_employees_needed': max(0, int(recommended_capacity / 10) - employee_count),
            'training_hours_needed': len(department_data['employees']) * 8,  # 8 hours per employee
            'estimated_cost': max(0, int(recommended_capacity / 10) - employee_count) * 5000  # $5000 per new employee
        }
    
    def _generate_capacity_recommendations(self, department_data: Dict[str, Any], 
                                         capacity_predictions: Dict[str, Any], 
                                         resource_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate capacity optimization recommendations."""
        recommendations = []
        
        if resource_requirements['additional_employees_needed'] > 0:
            recommendations.append({
                'type': 'hiring',
                'priority': 'high',
                'title': 'Hire Additional Employees',
                'description': f"Need {resource_requirements['additional_employees_needed']} additional employees",
                'estimated_cost': resource_requirements['estimated_cost']
            })
        
        if resource_requirements['training_hours_needed'] > 0:
            recommendations.append({
                'type': 'training',
                'priority': 'medium',
                'title': 'Implement Training Program',
                'description': f"Provide {resource_requirements['training_hours_needed']} hours of training",
                'estimated_cost': resource_requirements['training_hours_needed'] * 50  # $50 per hour
            })
        
        return recommendations
    
    def _identify_capacity_bottlenecks(self, department_data: Dict[str, Any], 
                                     capacity_predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential capacity bottlenecks."""
        bottlenecks = []
        
        # Check for overloaded employees
        employee_task_counts = {}
        for task in department_data['tasks']:
            emp_id = task.employee.id
            employee_task_counts[emp_id] = employee_task_counts.get(emp_id, 0) + 1
        
        if employee_task_counts:
            max_tasks = max(employee_task_counts.values())
            avg_tasks = sum(employee_task_counts.values()) / len(employee_task_counts)
            
            if max_tasks > avg_tasks * 2:
                bottlenecks.append({
                    'type': 'employee_overload',
                    'severity': 'high',
                    'description': 'Some employees are significantly overloaded',
                    'impact': 'Reduced quality and burnout risk'
                })
        
        return bottlenecks
    
    def _define_success_metrics(self, strategy: Dict[str, Any]) -> List[str]:
        """Define success metrics for a strategy."""
        strategy_type = strategy['type']
        
        if 'completion_rate' in strategy_type:
            return ['Task completion rate improvement', 'Employee satisfaction scores']
        elif 'workload' in strategy_type:
            return ['Workload balance score', 'Task distribution variance']
        elif 'efficiency' in strategy_type:
            return ['Efficiency score improvement', 'Cost per task reduction']
        elif 'cost' in strategy_type:
            return ['Cost per task reduction', 'ROI improvement']
        else:
            return ['Overall performance improvement']
    
    def _define_overall_success_metrics(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Define overall success metrics for all strategies."""
        return [
            'Department completion rate improvement',
            'Workload balance optimization',
            'Employee satisfaction scores',
            'Cost per task reduction',
            'Overall efficiency score improvement'
        ]
    
    def _calculate_resource_requirements_implementation(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Calculate resources required for implementation."""
        resources = []
        
        for strategy in strategies:
            effort = strategy.get('implementation_effort', 'medium')
            if effort == 'high':
                resources.append(f"Senior consultant for {strategy['title']}")
            elif effort == 'medium':
                resources.append(f"Project manager for {strategy['title']}")
            else:
                resources.append(f"Team lead for {strategy['title']}")
        
        return list(set(resources))  # Remove duplicates
    
    def _identify_implementation_risks(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify risks associated with implementation."""
        risks = []
        
        high_effort_strategies = [s for s in strategies if s.get('implementation_effort') == 'high']
        if high_effort_strategies:
            risks.append({
                'risk': 'Implementation complexity',
                'probability': 'medium',
                'impact': 'high',
                'mitigation': 'Phased implementation with pilot programs'
            })
        
        return risks

