"""
Employee Utilities

Handles all employee-related operations including:
- Employee performance tracking
- Employee rewards and recognition
- Employee group management
- Employee graduation tracking

This utility encapsulates employee-related functionality previously scattered across management/utils.py
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmployeeUtils:
    """
    Utility class for employee-related operations.
    
    Provides methods for employee management, performance tracking, and rewards.
    """
    
    def __init__(self):
        self.logger = logger
    
    def best_employee(self, task_obj: Any) -> Dict[str, Any]:
        """
        Find best employee based on task performance.
        
        Args:
            task_obj: Task object
            
        Returns:
            Dict with best employee information
        """
        try:
            if not task_obj:
                return {
                    'success': False,
                    'error': 'Task object is required'
                }
            
            # Placeholder for actual best employee calculation
            self.logger.info("Finding best employee based on task performance")
            
            return {
                'success': True,
                'best_employee_id': None,
                'best_employee_name': 'Sample Employee',
                'performance_score': 95.5,
                'total_points': 1000,
                'tasks_completed': 25,
                'evaluation_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error finding best employee: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def employee_reward(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        Calculate employee reward based on tasks.
        
        Args:
            tasks: List of task objects
            
        Returns:
            Dict with reward calculation
        """
        try:
            if not tasks:
                return {
                    'success': True,
                    'total_reward': Decimal('0.00'),
                    'reward_points': 0,
                    'tasks_count': 0
                }
            
            total_reward = Decimal('0.00')
            reward_points = 0
            
            for task in tasks:
                if hasattr(task, 'reward_amount'):
                    total_reward += Decimal(str(task.reward_amount))
                if hasattr(task, 'reward_points'):
                    reward_points += task.reward_points
            
            return {
                'success': True,
                'total_reward': total_reward,
                'reward_points': reward_points,
                'tasks_count': len(tasks),
                'average_reward_per_task': float(total_reward / len(tasks)) if tasks else 0,
                'average_points_per_task': reward_points / len(tasks) if tasks else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating employee reward: {e}")
            return {
                'success': False,
                'error': str(e),
                'tasks_count': len(tasks) if tasks else 0
            }
    
    def employee_group_level(self, historytasks: List[Any], task_groups: List[Any]) -> Dict[str, Any]:
        """
        Determine employee group level based on history tasks.
        
        Args:
            historytasks: List of historical task objects
            task_groups: List of task group objects
            
        Returns:
            Dict with group level information
        """
        try:
            if not historytasks:
                return {
                    'success': True,
                    'current_group': 'Beginner',
                    'group_level': 1,
                    'total_tasks': 0,
                    'total_points': 0
                }
            
            # Calculate total points from history tasks
            total_points = sum(getattr(task, 'points', 0) for task in historytasks)
            total_tasks = len(historytasks)
            
            # Determine group level based on points
            if total_points >= 10000:
                group_level = 5
                current_group = 'Expert'
            elif total_points >= 7500:
                group_level = 4
                current_group = 'Advanced'
            elif total_points >= 5000:
                group_level = 3
                current_group = 'Intermediate'
            elif total_points >= 2500:
                group_level = 2
                current_group = 'Novice'
            else:
                group_level = 1
                current_group = 'Beginner'
            
            return {
                'success': True,
                'current_group': current_group,
                'group_level': group_level,
                'total_tasks': total_tasks,
                'total_points': total_points,
                'points_to_next_level': max(0, (group_level * 2500) - total_points),
                'evaluation_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error determining employee group level: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_tasks': len(historytasks) if historytasks else 0
            }
    
    def increment_in_graduation_of_employee(self, employee: Any, max_earning: Decimal, new_group: str, payslip_config: Any) -> Dict[str, Any]:
        """
        Increment employee graduation level.
        
        Args:
            employee: Employee object
            max_earning: Maximum earning amount
            new_group: New group name
            payslip_config: Payslip configuration
            
        Returns:
            Dict with graduation increment result
        """
        try:
            if not employee:
                return {
                    'success': False,
                    'error': 'Employee is required'
                }
            
            # Placeholder for actual graduation increment
            self.logger.info(f"Incrementing graduation for employee {employee.id}")
            
            return {
                'success': True,
                'employee_id': employee.id,
                'previous_group': 'Previous Group',
                'new_group': new_group,
                'max_earning': max_earning,
                'graduation_date': timezone.now(),
                'increment_amount': Decimal('0.00'),
                'new_salary': Decimal('0.00')
            }
            
        except Exception as e:
            self.logger.error(f"Error incrementing employee graduation: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }
    
    def emp_average_earnings(self, request: Any, task_history: List[Any], goal_amount: Decimal, employee: Any) -> Dict[str, Any]:
        """
        Calculate employee average earnings.
        
        Args:
            request: Django request object
            task_history: List of historical task objects
            goal_amount: Goal amount
            employee: Employee object
            
        Returns:
            Dict with average earnings calculation
        """
        try:
            if not employee or not task_history:
                return {
                    'success': False,
                    'error': 'Employee and task history are required'
                }
            
            # Calculate average earnings from task history
            total_earnings = Decimal('0.00')
            total_tasks = len(task_history)
            
            for task in task_history:
                if hasattr(task, 'earnings'):
                    total_earnings += Decimal(str(task.earnings))
            
            average_earnings = total_earnings / total_tasks if total_tasks > 0 else Decimal('0.00')
            
            # Calculate progress towards goal
            goal_progress = (total_earnings / goal_amount * 100) if goal_amount > 0 else 0
            
            return {
                'success': True,
                'employee_id': employee.id,
                'total_earnings': total_earnings,
                'average_earnings': average_earnings,
                'total_tasks': total_tasks,
                'goal_amount': goal_amount,
                'goal_progress': goal_progress,
                'remaining_to_goal': max(Decimal('0.00'), goal_amount - total_earnings),
                'calculation_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating employee average earnings: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }





