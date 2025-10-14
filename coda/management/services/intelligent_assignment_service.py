"""
Intelligent Task Assignment Service

This service uses AI predictions and optimization algorithms to automatically
assign tasks to the most suitable employees based on performance patterns,
skills, availability, and workload balancing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F

from management.models import TaskHistory, Task
from accounts.models import CustomerUser
from management.services.simple_ai_service import SimpleAIService


class IntelligentAssignmentService:
    """Service for intelligent task assignment using AI and optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_service = SimpleAIService()
        
        # Assignment strategy weights
        self.strategy_weights = {
            'performance': 0.4,      # 40% - Historical performance
            'workload': 0.25,        # 25% - Current workload balance
            'skills_match': 0.2,     # 20% - Skills and category match
            'availability': 0.1,     # 10% - Availability and schedule
            'team_dynamics': 0.05    # 5% - Team collaboration factors
        }
    
    def assign_task_optimally(self, task_data: Dict[str, Any], available_employees: List[int] = None) -> Dict[str, Any]:
        """Assign a task optimally to the best available employee."""
        try:
            self.logger.info(f"Starting optimal task assignment for task: {task_data.get('title', 'Unknown')}")
            
            # Get available employees
            if available_employees is None:
                available_employees = list(CustomerUser.objects.filter(is_active=True).values_list('id', flat=True))
            
            if not available_employees:
                return {
                    'success': False,
                    'message': 'No available employees for assignment',
                    'assignment': None
                }
            
            # Get task category
            task_category_id = task_data.get('category_id')
            if not task_category_id:
                return {
                    'success': False,
                    'message': 'Task category is required for assignment',
                    'assignment': None
                }
            
            # Calculate assignment scores for each employee
            assignment_scores = []
            for employee_id in available_employees:
                try:
                    score_result = self._calculate_assignment_score(
                        employee_id, task_data, task_category_id
                    )
                    
                    if score_result['success']:
                        assignment_scores.append({
                            'employee_id': employee_id,
                            'employee_name': score_result['employee_name'],
                            'total_score': score_result['total_score'],
                            'score_breakdown': score_result['score_breakdown'],
                            'predicted_completion_rate': score_result['predicted_completion_rate'],
                            'confidence': score_result['confidence'],
                            'workload_score': score_result['workload_score'],
                            'skills_match': score_result['skills_match']
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to calculate score for employee {employee_id}: {e}")
                    continue
            
            if not assignment_scores:
                return {
                    'success': False,
                    'message': 'No valid assignment scores calculated',
                    'assignment': None
                }
            
            # Sort by total score (highest first)
            assignment_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Generate assignment recommendation
            best_match = assignment_scores[0]
            assignment_recommendation = self._generate_assignment_recommendation(
                task_data, best_match, assignment_scores
            )
            
            return {
                'success': True,
                'task_data': task_data,
                'total_candidates': len(available_employees),
                'valid_scores': len(assignment_scores),
                'assignment': assignment_recommendation,
                'top_candidates': assignment_scores[:5],
                'assignment_strategy': self._get_assignment_strategy(assignment_scores),
                'workload_balance': self._analyze_workload_balance(assignment_scores)
            }
            
        except Exception as e:
            self.logger.error(f"Error in optimal task assignment: {e}")
            return {
                'success': False,
                'message': f'Assignment failed: {str(e)}',
                'assignment': None
            }
    
    def assign_multiple_tasks(self, tasks_data: List[Dict[str, Any]], available_employees: List[int] = None) -> Dict[str, Any]:
        """Assign multiple tasks optimally with workload balancing."""
        try:
            self.logger.info(f"Starting batch assignment for {len(tasks_data)} tasks")
            
            if not tasks_data:
                return {
                    'success': False,
                    'message': 'No tasks provided for assignment',
                    'assignments': []
                }
            
            # Get available employees
            if available_employees is None:
                available_employees = list(CustomerUser.objects.filter(is_active=True).values_list('id', flat=True))
            
            if not available_employees:
                return {
                    'success': False,
                    'message': 'No available employees for assignment',
                    'assignments': []
                }
            
            # Initialize workload tracking
            employee_workloads = {emp_id: 0 for emp_id in available_employees}
            assignments = []
            
            # Sort tasks by priority (if available)
            sorted_tasks = sorted(tasks_data, key=lambda t: t.get('priority', 0), reverse=True)
            
            # Assign each task
            for task_data in sorted_tasks:
                # Adjust strategy weights based on current workload balance
                adjusted_weights = self._adjust_weights_for_workload_balance(employee_workloads)
                
                # Find best assignment for this task
                assignment_result = self._assign_single_task_with_workload(
                    task_data, available_employees, employee_workloads, adjusted_weights
                )
                
                if assignment_result['success']:
                    assignments.append(assignment_result['assignment'])
                    # Update workload
                    assigned_employee = assignment_result['assignment']['employee_id']
                    employee_workloads[assigned_employee] += 1
                else:
                    assignments.append({
                        'task_data': task_data,
                        'assigned': False,
                        'reason': assignment_result['message']
                    })
            
            # Calculate assignment statistics
            successful_assignments = [a for a in assignments if a.get('assigned', False)]
            workload_distribution = self._calculate_workload_distribution(employee_workloads)
            
            return {
                'success': True,
                'total_tasks': len(tasks_data),
                'successful_assignments': len(successful_assignments),
                'assignments': assignments,
                'workload_distribution': workload_distribution,
                'balance_score': self._calculate_workload_balance_score(employee_workloads),
                'assignment_summary': self._generate_assignment_summary(assignments)
            }
            
        except Exception as e:
            self.logger.error(f"Error in batch task assignment: {e}")
            return {
                'success': False,
                'message': f'Batch assignment failed: {str(e)}',
                'assignments': []
            }
    
    def suggest_workload_rebalancing(self, department_name: str = None) -> Dict[str, Any]:
        """Suggest workload rebalancing across employees or departments."""
        try:
            self.logger.info(f"Analyzing workload balance for department: {department_name}")
            
            # Get employees to analyze
            if department_name:
                employees = self._get_department_employees(department_name)
            else:
                employees = list(CustomerUser.objects.filter(is_active=True))
            
            if not employees:
                return {
                    'success': False,
                    'message': 'No employees found for analysis',
                    'recommendations': []
                }
            
            # Calculate current workloads
            current_workloads = {}
            for employee in employees:
                workload = self._calculate_current_workload(employee.id)
                current_workloads[employee.id] = {
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'active_tasks': workload['active_tasks'],
                    'recent_completion_rate': workload['recent_completion_rate'],
                    'workload_score': workload['workload_score']
                }
            
            # Analyze workload distribution
            workload_analysis = self._analyze_workload_distribution(current_workloads)
            
            # Generate rebalancing recommendations
            recommendations = self._generate_rebalancing_recommendations(
                current_workloads, workload_analysis
            )
            
            return {
                'success': True,
                'department_name': department_name,
                'total_employees': len(employees),
                'current_workloads': current_workloads,
                'workload_analysis': workload_analysis,
                'recommendations': recommendations,
                'rebalancing_priority': self._calculate_rebalancing_priority(workload_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing workload balance: {e}")
            return {
                'success': False,
                'message': f'Workload analysis failed: {str(e)}',
                'recommendations': []
            }
    
    def _calculate_assignment_score(self, employee_id: int, task_data: Dict[str, Any], task_category_id: int) -> Dict[str, Any]:
        """Calculate comprehensive assignment score for an employee."""
        try:
            # Get employee
            employee = CustomerUser.objects.get(id=employee_id)
            
            # 1. Performance Score (40% weight)
            performance_prediction = self.ai_service.predict_employee_performance(employee_id, task_category_id)
            performance_score = 0.0
            predicted_completion_rate = 0.0
            confidence = 0.0
            
            if performance_prediction['success']:
                predicted_completion_rate = performance_prediction['predicted_completion_rate']
                confidence = performance_prediction['confidence']
                performance_score = predicted_completion_rate * confidence
            
            # 2. Workload Score (25% weight)
            workload_data = self._calculate_current_workload(employee_id)
            workload_score = workload_data['workload_score']
            
            # 3. Skills Match Score (20% weight)
            skills_match = self._calculate_skills_match(employee_id, task_category_id)
            
            # 4. Availability Score (10% weight)
            availability_score = self._calculate_availability_score(employee_id, task_data)
            
            # 5. Team Dynamics Score (5% weight)
            team_dynamics_score = self._calculate_team_dynamics_score(employee_id, task_category_id)
            
            # Calculate weighted total score
            score_breakdown = {
                'performance': performance_score * self.strategy_weights['performance'],
                'workload': workload_score * self.strategy_weights['workload'],
                'skills_match': skills_match * self.strategy_weights['skills_match'],
                'availability': availability_score * self.strategy_weights['availability'],
                'team_dynamics': team_dynamics_score * self.strategy_weights['team_dynamics']
            }
            
            total_score = sum(score_breakdown.values())
            
            return {
                'success': True,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'total_score': total_score,
                'score_breakdown': score_breakdown,
                'predicted_completion_rate': predicted_completion_rate,
                'confidence': confidence,
                'workload_score': workload_score,
                'skills_match': skills_match
            }
            
        except CustomerUser.DoesNotExist:
            return {'success': False, 'message': f'Employee {employee_id} not found'}
        except Exception as e:
            return {'success': False, 'message': f'Score calculation failed: {str(e)}'}
    
    def _calculate_current_workload(self, employee_id: int) -> Dict[str, Any]:
        """Calculate current workload for an employee."""
        # Count active tasks (last 30 days)
        recent_cutoff = timezone.now().date() - timedelta(days=30)
        active_tasks = TaskHistory.objects.filter(
            employee_id=employee_id,
            daf_date__gte=recent_cutoff
        ).count()
        
        # Calculate recent completion rate
        recent_tasks = TaskHistory.objects.filter(
            employee_id=employee_id,
            daf_date__gte=recent_cutoff,
            mxpoint__gt=0
        )
        
        if recent_tasks.exists():
            completion_rates = []
            for task in recent_tasks:
                if task.mxpoint > 0:
                    completion_rates.append(float(task.point) / float(task.mxpoint))
            
            recent_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
        else:
            recent_completion_rate = 0.0
        
        # Calculate workload score (lower is better for assignment)
        # Normalize based on typical workload (assume 10 tasks per month is normal)
        workload_score = max(0.0, 1.0 - (active_tasks / 10.0))
        
        return {
            'active_tasks': active_tasks,
            'recent_completion_rate': recent_completion_rate,
            'workload_score': workload_score
        }
    
    def _calculate_skills_match(self, employee_id: int, task_category_id: int) -> float:
        """Calculate skills match score between employee and task category."""
        # Get employee's performance in this category
        category_tasks = TaskHistory.objects.filter(
            employee_id=employee_id,
            category_id=task_category_id,
            mxpoint__gt=0
        )
        
        if not category_tasks.exists():
            # No experience in this category - neutral score
            return 0.5
        
        # Calculate average completion rate in this category
        completion_rates = []
        for task in category_tasks:
            if task.mxpoint > 0:
                completion_rates.append(float(task.point) / float(task.mxpoint))
        
        if completion_rates:
            avg_completion_rate = sum(completion_rates) / len(completion_rates)
            # Convert to skills match score (0-1 scale)
            return min(1.0, avg_completion_rate * 1.5)  # Boost slightly for category experience
        
        return 0.5
    
    def _calculate_availability_score(self, employee_id: int, task_data: Dict[str, Any]) -> float:
        """Calculate availability score for an employee."""
        # For now, assume all employees are equally available
        # In a real system, this would check schedules, time off, etc.
        return 1.0
    
    def _calculate_team_dynamics_score(self, employee_id: int, task_category_id: int) -> float:
        """Calculate team dynamics score for collaboration."""
        # For now, return neutral score
        # In a real system, this would analyze team collaboration patterns
        return 0.8
    
    def _adjust_weights_for_workload_balance(self, employee_workloads: Dict[int, int]) -> Dict[str, float]:
        """Adjust strategy weights based on current workload balance."""
        weights = self.strategy_weights.copy()
        
        # If workloads are very unbalanced, increase workload weight
        if employee_workloads:
            workload_values = list(employee_workloads.values())
            workload_variance = max(workload_values) - min(workload_values)
            
            if workload_variance > 5:  # Significant imbalance
                # Increase workload weight and decrease performance weight
                weights['workload'] = min(0.4, weights['workload'] + 0.1)
                weights['performance'] = max(0.3, weights['performance'] - 0.1)
        
        return weights
    
    def _assign_single_task_with_workload(self, task_data: Dict[str, Any], available_employees: List[int], 
                                        employee_workloads: Dict[int, int], weights: Dict[str, float]) -> Dict[str, Any]:
        """Assign a single task considering current workloads."""
        best_score = -1
        best_employee = None
        best_breakdown = None
        
        for employee_id in available_employees:
            try:
                # Temporarily adjust weights
                original_weights = self.strategy_weights.copy()
                self.strategy_weights = weights
                
                score_result = self._calculate_assignment_score(
                    employee_id, task_data, task_data.get('category_id')
                )
                
                # Restore original weights
                self.strategy_weights = original_weights
                
                if score_result['success'] and score_result['total_score'] > best_score:
                    best_score = score_result['total_score']
                    best_employee = employee_id
                    best_breakdown = score_result
                    
            except Exception as e:
                self.logger.warning(f"Error calculating score for employee {employee_id}: {e}")
                continue
        
        if best_employee is None:
            return {
                'success': False,
                'message': 'No suitable employee found for task assignment'
            }
        
        return {
            'success': True,
            'assignment': {
                'employee_id': best_employee,
                'employee_name': best_breakdown['employee_name'],
                'total_score': best_score,
                'score_breakdown': best_breakdown['score_breakdown'],
                'predicted_completion_rate': best_breakdown['predicted_completion_rate'],
                'confidence': best_breakdown['confidence']
            }
        }
    
    def _generate_assignment_recommendation(self, task_data: Dict[str, Any], best_match: Dict[str, Any], 
                                          all_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed assignment recommendation."""
        return {
            'recommended_employee_id': best_match['employee_id'],
            'recommended_employee_name': best_match['employee_name'],
            'assignment_score': best_match['total_score'],
            'predicted_success_rate': best_match['predicted_completion_rate'],
            'confidence': best_match['confidence'],
            'score_breakdown': best_match['score_breakdown'],
            'alternative_employees': [
                {
                    'employee_id': score['employee_id'],
                    'employee_name': score['employee_name'],
                    'score': score['total_score']
                }
                for score in all_scores[1:4]  # Top 3 alternatives
            ],
            'assignment_reasoning': self._generate_assignment_reasoning(best_match),
            'risk_assessment': self._assess_assignment_risk(best_match)
        }
    
    def _generate_assignment_reasoning(self, best_match: Dict[str, Any]) -> List[str]:
        """Generate human-readable reasoning for the assignment."""
        reasoning = []
        
        if best_match['predicted_completion_rate'] > 0.8:
            reasoning.append("High predicted completion rate")
        elif best_match['predicted_completion_rate'] > 0.6:
            reasoning.append("Good predicted completion rate")
        
        if best_match['workload_score'] > 0.8:
            reasoning.append("Currently has low workload")
        elif best_match['workload_score'] < 0.3:
            reasoning.append("Currently has high workload")
        
        if best_match['skills_match'] > 0.8:
            reasoning.append("Strong skills match for this task type")
        elif best_match['skills_match'] < 0.3:
            reasoning.append("Limited experience with this task type")
        
        return reasoning
    
    def _assess_assignment_risk(self, best_match: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks associated with the assignment."""
        risk_level = 'low'
        risks = []
        
        if best_match['predicted_completion_rate'] < 0.5:
            risk_level = 'high'
            risks.append("Low predicted completion rate")
        elif best_match['predicted_completion_rate'] < 0.7:
            risk_level = 'medium'
            risks.append("Moderate completion rate")
        
        if best_match['confidence'] < 0.6:
            risk_level = 'medium' if risk_level == 'low' else 'high'
            risks.append("Low prediction confidence")
        
        if best_match['workload_score'] < 0.3:
            risks.append("Employee may be overloaded")
        
        return {
            'risk_level': risk_level,
            'risks': risks,
            'mitigation_suggestions': self._get_risk_mitigation_suggestions(risks)
        }
    
    def _get_risk_mitigation_suggestions(self, risks: List[str]) -> List[str]:
        """Get suggestions to mitigate identified risks."""
        suggestions = []
        
        if "Low predicted completion rate" in risks:
            suggestions.append("Provide additional training or support")
            suggestions.append("Break task into smaller components")
        
        if "Low prediction confidence" in risks:
            suggestions.append("Monitor progress closely")
            suggestions.append("Have backup employee ready")
        
        if "Employee may be overloaded" in risks:
            suggestions.append("Consider redistributing other tasks")
            suggestions.append("Extend deadline if possible")
        
        return suggestions
    
    def _get_assignment_strategy(self, assignment_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get overall assignment strategy analysis."""
        if not assignment_scores:
            return {'strategy': 'no_candidates', 'confidence': 0.0}
        
        avg_score = sum(s['total_score'] for s in assignment_scores) / len(assignment_scores)
        score_variance = max(s['total_score'] for s in assignment_scores) - min(s['total_score'] for s in assignment_scores)
        
        if avg_score > 0.8:
            strategy = 'high_confidence'
        elif avg_score > 0.6:
            strategy = 'moderate_confidence'
        else:
            strategy = 'low_confidence'
        
        return {
            'strategy': strategy,
            'average_score': avg_score,
            'score_variance': score_variance,
            'top_score': max(s['total_score'] for s in assignment_scores),
            'bottom_score': min(s['total_score'] for s in assignment_scores)
        }
    
    def _analyze_workload_balance(self, assignment_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze workload balance across candidates."""
        workload_scores = [s['workload_score'] for s in assignment_scores]
        
        return {
            'average_workload': sum(workload_scores) / len(workload_scores),
            'workload_variance': max(workload_scores) - min(workload_scores),
            'overloaded_candidates': len([s for s in assignment_scores if s['workload_score'] < 0.3]),
            'available_candidates': len([s for s in assignment_scores if s['workload_score'] > 0.7])
        }
    
    def _calculate_workload_distribution(self, employee_workloads: Dict[int, int]) -> Dict[str, Any]:
        """Calculate workload distribution statistics."""
        if not employee_workloads:
            return {'average': 0, 'variance': 0, 'max': 0, 'min': 0}
        
        workloads = list(employee_workloads.values())
        return {
            'average': sum(workloads) / len(workloads),
            'variance': max(workloads) - min(workloads),
            'max': max(workloads),
            'min': min(workloads),
            'total': sum(workloads)
        }
    
    def _calculate_workload_balance_score(self, employee_workloads: Dict[int, int]) -> float:
        """Calculate overall workload balance score (0-1, higher is better)."""
        if not employee_workloads:
            return 0.0
        
        workloads = list(employee_workloads.values())
        if len(workloads) <= 1:
            return 1.0
        
        # Calculate coefficient of variation (lower is better)
        mean_workload = sum(workloads) / len(workloads)
        if mean_workload == 0:
            return 1.0
        
        variance = sum((w - mean_workload) ** 2 for w in workloads) / len(workloads)
        std_dev = variance ** 0.5
        cv = std_dev / mean_workload
        
        # Convert to balance score (0-1, higher is better)
        return max(0.0, min(1.0, 1.0 - cv))
    
    def _generate_assignment_summary(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of assignment results."""
        successful = [a for a in assignments if a.get('assigned', False)]
        failed = [a for a in assignments if not a.get('assigned', False)]
        
        return {
            'success_rate': len(successful) / len(assignments) if assignments else 0.0,
            'total_assignments': len(assignments),
            'successful_assignments': len(successful),
            'failed_assignments': len(failed),
            'failure_reasons': [a.get('reason', 'Unknown') for a in failed]
        }
    
    def _get_department_employees(self, department_name: str) -> List[CustomerUser]:
        """Get employees in a department."""
        category_mapping = {
            'IT': 1,
            'HR': 2,
            'Finance': 3,
            'Marketing': 4,
            'Operations': 5,
            'Other': 999
        }
        
        category = category_mapping.get(department_name)
        if category is not None:
            return list(CustomerUser.objects.filter(category=category))
        
        return []
    
    def _analyze_workload_distribution(self, current_workloads: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze workload distribution across employees."""
        if not current_workloads:
            return {'balanced': True, 'variance': 0.0, 'overloaded': []}
        
        workload_values = [data['active_tasks'] for data in current_workloads.values()]
        avg_workload = sum(workload_values) / len(workload_values)
        variance = max(workload_values) - min(workload_values)
        
        # Identify overloaded employees (more than 1.5x average)
        overloaded = []
        for emp_id, data in current_workloads.items():
            if data['active_tasks'] > avg_workload * 1.5:
                overloaded.append({
                    'employee_id': emp_id,
                    'employee_name': data['employee_name'],
                    'current_tasks': data['active_tasks'],
                    'average': avg_workload
                })
        
        return {
            'balanced': variance < avg_workload * 0.5,  # Low variance = balanced
            'variance': variance,
            'average_workload': avg_workload,
            'overloaded': overloaded,
            'underloaded': len([w for w in workload_values if w < avg_workload * 0.5])
        }
    
    def _generate_rebalancing_recommendations(self, current_workloads: Dict[int, Dict[str, Any]], 
                                            workload_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate workload rebalancing recommendations."""
        recommendations = []
        
        if not workload_analysis['balanced']:
            recommendations.append({
                'type': 'workload_redistribution',
                'priority': 'high',
                'title': 'Redistribute Workload',
                'description': f"Workload variance is {workload_analysis['variance']:.1f} tasks. Consider redistributing tasks.",
                'action': 'Review and reassign tasks from overloaded to underloaded employees'
            })
        
        if workload_analysis['overloaded']:
            recommendations.append({
                'type': 'reduce_overload',
                'priority': 'high',
                'title': 'Reduce Employee Overload',
                'description': f"{len(workload_analysis['overloaded'])} employees are overloaded",
                'action': 'Provide additional support or redistribute tasks'
            })
        
        if workload_analysis['underloaded'] > 0:
            recommendations.append({
                'type': 'increase_workload',
                'priority': 'medium',
                'title': 'Optimize Underloaded Employees',
                'description': f"{workload_analysis['underloaded']} employees could take on more tasks",
                'action': 'Assign additional tasks to underloaded employees'
            })
        
        return recommendations
    
    def _calculate_rebalancing_priority(self, workload_analysis: Dict[str, Any]) -> str:
        """Calculate priority level for workload rebalancing."""
        if not workload_analysis['balanced'] and workload_analysis['overloaded']:
            return 'critical'
        elif not workload_analysis['balanced']:
            return 'high'
        elif workload_analysis['overloaded']:
            return 'medium'
        else:
            return 'low'

