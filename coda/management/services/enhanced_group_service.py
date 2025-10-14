"""
Enhanced Group System Service

Replaces the confusing Group A-E system with a clear, gamified
tier system: Bronze, Silver, Gold, Platinum with realistic point ranges.

New System:
- Bronze: 0-2000 points
- Silver: 2000-4000 points  
- Gold: 4000-7000 points
- Platinum: 7000+ points
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Import models
from management.models import Task, TaskHistory, TaskGroups
from accounts.models import CustomerUser

logger = logging.getLogger(__name__)
User = get_user_model()


class EnhancedGroupService:
    """
    Enhanced group system with clear tier progression.
    
    Provides:
    - Clear tier definitions (Bronze, Silver, Gold, Platinum)
    - Realistic point ranges
    - Automatic tier progression
    - Performance analytics
    - Gamification elements
    """
    
    def __init__(self):
        self.logger = logger
        
        # Define new tier system
        self.tiers = {
            'Bronze': {
                'min_points': 0,
                'max_points': 1999,
                'color': '#CD7F32',
                'description': 'Getting Started',
                'benefits': ['Basic access', 'Monthly reports']
            },
            'Silver': {
                'min_points': 2000,
                'max_points': 3999,
                'color': '#C0C0C0',
                'description': 'Consistent Performer',
                'benefits': ['Priority support', 'Quarterly bonuses']
            },
            'Gold': {
                'min_points': 4000,
                'max_points': 6999,
                'color': '#FFD700',
                'description': 'High Achiever',
                'benefits': ['Premium features', 'Annual bonuses']
            },
            'Platinum': {
                'min_points': 7000,
                'max_points': float('inf'),
                'color': '#E5E4E2',
                'description': 'Elite Performer',
                'benefits': ['VIP access', 'Leadership opportunities']
            }
        }
    
    def calculate_employee_tier(self, employee: User, target_month: int = None, target_year: int = None) -> Dict[str, Any]:
        """
        Calculate employee's current tier based on total points.
        
        Args:
            employee: User object
            target_month: Month to calculate for (defaults to current)
            target_year: Year to calculate for (defaults to current)
            
        Returns:
            dict: Tier information and statistics
        """
        try:
            if target_month is None or target_year is None:
                current_date = datetime.now()
                target_month = current_date.month
                target_year = current_date.year
            
            # Get employee's total points from TaskHistory
            total_points = self._calculate_total_points(employee, target_month, target_year)
            
            # Determine tier
            tier_info = self._determine_tier(total_points)
            
            # Get progression information
            progression_info = self._get_progression_info(total_points)
            
            return {
                'employee': employee,
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'total_points': total_points,
                'current_tier': tier_info['name'],
                'tier_info': tier_info,
                'progression': progression_info,
                'target_month': target_month,
                'target_year': target_year
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating tier for employee {employee.username}: {e}")
            return {
                'employee': employee,
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'total_points': 0,
                'current_tier': 'Bronze',
                'tier_info': self.tiers['Bronze'],
                'progression': {'points_to_next': 2000, 'next_tier': 'Silver'},
                'error': str(e)
            }
    
    def _calculate_total_points(self, employee: User, target_month: int, target_year: int) -> int:
        """
        Calculate total points for employee from TaskHistory.
        """
        try:
            # Get all TaskHistory records for the employee
            task_history = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            # Sum up all points
            total_points = sum(task.point for task in task_history if task.point)
            
            return total_points
            
        except Exception as e:
            self.logger.error(f"Error calculating total points for {employee.username}: {e}")
            return 0
    
    def _determine_tier(self, total_points: int) -> Dict[str, Any]:
        """
        Determine tier based on total points.
        """
        for tier_name, tier_data in self.tiers.items():
            if tier_data['min_points'] <= total_points <= tier_data['max_points']:
                return {
                    'name': tier_name,
                    'min_points': tier_data['min_points'],
                    'max_points': tier_data['max_points'],
                    'color': tier_data['color'],
                    'description': tier_data['description'],
                    'benefits': tier_data['benefits']
                }
        
        # Fallback to Bronze
        return {
            'name': 'Bronze',
            'min_points': self.tiers['Bronze']['min_points'],
            'max_points': self.tiers['Bronze']['max_points'],
            'color': self.tiers['Bronze']['color'],
            'description': self.tiers['Bronze']['description'],
            'benefits': self.tiers['Bronze']['benefits']
        }
    
    def _get_progression_info(self, total_points: int) -> Dict[str, Any]:
        """
        Get progression information (points to next tier, etc.).
        """
        current_tier = self._determine_tier(total_points)
        current_tier_name = current_tier['name']
        
        # Find next tier
        tier_names = list(self.tiers.keys())
        current_index = tier_names.index(current_tier_name)
        
        if current_index < len(tier_names) - 1:
            next_tier_name = tier_names[current_index + 1]
            next_tier_min = self.tiers[next_tier_name]['min_points']
            points_to_next = next_tier_min - total_points
            
            return {
                'points_to_next': max(0, points_to_next),
                'next_tier': next_tier_name,
                'progress_percentage': min(100, (total_points / next_tier_min) * 100) if next_tier_min > 0 else 100
            }
        else:
            # Already at highest tier
            return {
                'points_to_next': 0,
                'next_tier': None,
                'progress_percentage': 100
            }
    
    def update_all_employee_tiers(self, target_month: int = None, target_year: int = None) -> Dict[str, Any]:
        """
        Update tiers for all active employees.
        """
        try:
            if target_month is None or target_year is None:
                current_date = datetime.now()
                target_month = current_date.month
                target_year = current_date.year
            
            # Get all active employees
            employees = CustomerUser.objects.filter(
                is_staff=True,
                is_active=True
            )
            
            updated_count = 0
            tier_distribution = {tier: 0 for tier in self.tiers.keys()}
            errors = []
            
            for employee in employees:
                try:
                    tier_info = self.calculate_employee_tier(employee, target_month, target_year)
                    tier_distribution[tier_info['current_tier']] += 1
                    updated_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error updating tier for employee {employee.username}: {e}")
                    errors.append(f"{employee.username}: {str(e)}")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_employees': employees.count(),
                'tier_distribution': tier_distribution,
                'errors': errors,
                'target_month': target_month,
                'target_year': target_year
            }
            
        except Exception as e:
            self.logger.error(f"Error updating all employee tiers: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update employee tiers'
            }
    
    def get_tier_analytics(self, target_month: int = None, target_year: int = None) -> Dict[str, Any]:
        """
        Get analytics about tier distribution and performance.
        """
        try:
            if target_month is None or target_year is None:
                current_date = datetime.now()
                target_month = current_date.month
                target_year = current_date.year
            
            # Get all employees with their tiers
            employees = CustomerUser.objects.filter(
                is_staff=True,
                is_active=True
            )
            
            tier_data = []
            tier_distribution = {tier: 0 for tier in self.tiers.keys()}
            total_points = 0
            
            for employee in employees:
                tier_info = self.calculate_employee_tier(employee, target_month, target_year)
                tier_data.append(tier_info)
                tier_distribution[tier_info['current_tier']] += 1
                total_points += tier_info['total_points']
            
            # Calculate averages
            avg_points = total_points / len(employees) if employees.count() > 0 else 0
            
            # Find top performers
            top_performers = sorted(tier_data, key=lambda x: x['total_points'], reverse=True)[:5]
            
            return {
                'target_month': target_month,
                'target_year': target_year,
                'total_employees': employees.count(),
                'tier_distribution': tier_distribution,
                'total_points': total_points,
                'average_points': round(avg_points, 2),
                'top_performers': top_performers,
                'tier_breakdown': tier_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tier analytics: {e}")
            return {
                'error': str(e),
                'target_month': target_month,
                'target_year': target_year
            }
    
    def get_employee_tier_history(self, employee: User, months_back: int = 6) -> List[Dict[str, Any]]:
        """
        Get tier history for an employee over the past months.
        """
        try:
            history = []
            current_date = datetime.now()
            
            for i in range(months_back):
                target_date = current_date - timedelta(days=30 * i)
                target_month = target_date.month
                target_year = target_date.year
                
                tier_info = self.calculate_employee_tier(employee, target_month, target_year)
                history.append({
                    'month': target_month,
                    'year': target_year,
                    'tier': tier_info['current_tier'],
                    'points': tier_info['total_points'],
                    'tier_info': tier_info['tier_info']
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting tier history for {employee.username}: {e}")
            return []
    
    def get_tier_leaderboard(self, target_month: int = None, target_year: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get leaderboard of top performers by tier.
        """
        try:
            if target_month is None or target_year is None:
                current_date = datetime.now()
                target_month = current_date.month
                target_year = current_date.year
            
            # Get all employees with their tiers
            employees = CustomerUser.objects.filter(
                is_staff=True,
                is_active=True
            )
            
            leaderboard_data = []
            
            for employee in employees:
                tier_info = self.calculate_employee_tier(employee, target_month, target_year)
                leaderboard_data.append(tier_info)
            
            # Sort by points and return top performers
            leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
            
            return leaderboard_data[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting tier leaderboard: {e}")
            return []
    
    def get_tier_benefits(self, tier_name: str) -> Dict[str, Any]:
        """
        Get benefits and information for a specific tier.
        """
        if tier_name in self.tiers:
            return self.tiers[tier_name]
        else:
            return self.tiers['Bronze']  # Default to Bronze
    
    def get_all_tiers_info(self) -> Dict[str, Any]:
        """
        Get information about all tiers.
        """
        return self.tiers
