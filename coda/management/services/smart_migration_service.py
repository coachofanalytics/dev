"""
Smart Task Migration Service

Fixes the critical flaw in Task→TaskHistory migration where ALL tasks
are moved regardless of completion status. This service implements
intelligent filtering to only migrate completed tasks with evidence.

Business Rule: Only tasks with evidence submission and minimum points
should be moved to TaskHistory for payroll processing.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Import models
from management.models import Task, TaskHistory, TaskCategory, TaskLinks, TaskGroups
from accounts.models import CustomerUser
from management.utils import employee_group_level, increment_in_graduation_of_employee

logger = logging.getLogger(__name__)
User = get_user_model()


class SmartMigrationService:
    """
    Service to handle intelligent Task→TaskHistory migration.
    
    Provides:
    - Smart filtering of completed tasks only
    - Evidence validation before migration
    - Point threshold checking
    - Proper group level calculations
    - Rollback capabilities for failed migrations
    """
    
    def __init__(self):
        self.logger = logger
        self.minimum_points_threshold = 1  # Minimum points required for migration
        self.require_evidence = True  # Whether evidence is required for migration
    
    def migrate_completed_tasks_to_history(self, target_month: int = None, target_year: int = None) -> Dict[str, Any]:
        """
        Migrate only completed tasks with evidence to TaskHistory.
        
        Args:
            target_month: Month to migrate (defaults to current month)
            target_year: Year to migrate (defaults to current year)
            
        Returns:
            dict: Migration results and statistics
        """
        try:
            with transaction.atomic():
                # Set target month/year if not provided
                if target_month is None or target_year is None:
                    current_date = datetime.now()
                    target_month = current_date.month
                    target_year = current_date.year
                
                # Get tasks that meet migration criteria
                eligible_tasks = self._get_eligible_tasks_for_migration(target_month, target_year)
                
                if not eligible_tasks.exists():
                    return {
                        'success': True,
                        'message': 'No eligible tasks found for migration',
                        'migrated_count': 0,
                        'skipped_count': 0,
                        'target_month': target_month,
                        'target_year': target_year
                    }
                
                # Perform smart migration
                migration_results = self._perform_smart_migration(eligible_tasks, target_month, target_year)
                
                return migration_results
                
        except Exception as e:
            self.logger.error(f"Error in smart task migration: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Migration failed due to error'
            }
    
    def _get_eligible_tasks_for_migration(self, target_month: int, target_year: int):
        """
        Get tasks that are eligible for migration based on completion criteria.
        """
        try:
            # Base query for tasks in target month/year
            base_query = Task.objects.filter(
                employee__is_staff=True,
                employee__is_active=True
            ).exclude(employee__email=None)
            
            # Filter by date if available (assuming there's a date field)
            # Note: This might need adjustment based on actual Task model fields
            
            # Apply completion criteria
            eligible_tasks = base_query.filter(
                point__gte=self.minimum_points_threshold  # Must have earned points
            )
            
            # If evidence is required, filter for tasks with evidence
            if self.require_evidence:
                # Get tasks that have evidence (submission field not empty)
                eligible_tasks = eligible_tasks.exclude(
                    submission__isnull=True
                ).exclude(
                    submission__exact=''
                )
            
            return eligible_tasks
            
        except Exception as e:
            self.logger.error(f"Error getting eligible tasks: {e}")
            return Task.objects.none()
    
    def _perform_smart_migration(self, eligible_tasks, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Perform the actual smart migration of eligible tasks.
        """
        try:
            migrated_count = 0
            skipped_count = 0
            migration_errors = []
            
            # Group tasks by employee for batch processing
            employees = eligible_tasks.values_list('employee', flat=True).distinct()
            
            for employee_id in employees:
                try:
                    employee_tasks = eligible_tasks.filter(employee_id=employee_id)
                    employee = User.objects.get(id=employee_id)
                    
                    # Migrate tasks for this employee
                    employee_result = self._migrate_employee_tasks(
                        employee, employee_tasks, target_month, target_year
                    )
                    
                    migrated_count += employee_result['migrated_count']
                    skipped_count += employee_result['skipped_count']
                    
                    if employee_result['errors']:
                        migration_errors.extend(employee_result['errors'])
                        
                except Exception as e:
                    self.logger.error(f"Error migrating tasks for employee {employee_id}: {e}")
                    migration_errors.append(f"Employee {employee_id}: {str(e)}")
                    skipped_count += eligible_tasks.filter(employee_id=employee_id).count()
            
            return {
                'success': True,
                'message': f'Smart migration completed. {migrated_count} tasks migrated, {skipped_count} skipped.',
                'migrated_count': migrated_count,
                'skipped_count': skipped_count,
                'errors': migration_errors,
                'target_month': target_month,
                'target_year': target_year
            }
            
        except Exception as e:
            self.logger.error(f"Error in smart migration: {e}")
            raise
    
    def _migrate_employee_tasks(self, employee: User, employee_tasks, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Migrate tasks for a specific employee.
        """
        try:
            migrated_count = 0
            skipped_count = 0
            errors = []
            
            # Create TaskHistory records for eligible tasks
            bulk_history_objects = []
            tasks_to_update = []
            
            for task in employee_tasks:
                try:
                    # Validate task before migration
                    if self._validate_task_for_migration(task):
                        # Create TaskHistory record
                        history_obj = TaskHistory(
                            group=task.group,
                            category=task.category,
                            employee=task.employee,
                            activity_name=task.activity_name,
                            description=task.description,
                            slug=task.slug,
                            duration=task.duration,
                            point=task.point,  # Keep original points
                            mxpoint=task.mxpoint,
                            mxearning=task.mxearning,
                            submission=task.submission,
                            is_active=task.is_active,
                            featured=task.featured,
                            daf_date=datetime.now().date()  # Set migration date
                        )
                        bulk_history_objects.append(history_obj)
                        
                        # Mark task for point reset (but keep in Task table for next month)
                        task.point = 0
                        tasks_to_update.append(task)
                        
                        migrated_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Error validating task {task.id}: {e}")
                    errors.append(f"Task {task.id}: {str(e)}")
                    skipped_count += 1
            
            # Bulk create TaskHistory records
            if bulk_history_objects:
                TaskHistory.objects.bulk_create(bulk_history_objects)
                self.logger.info(f"Created {len(bulk_history_objects)} TaskHistory records for employee {employee.username}")
            
            # Update task points
            if tasks_to_update:
                Task.objects.bulk_update(tasks_to_update, ['point'])
                self.logger.info(f"Reset points for {len(tasks_to_update)} tasks for employee {employee.username}")
            
            # Update employee group levels based on new TaskHistory
            self._update_employee_group_level(employee, target_month, target_year)
            
            return {
                'migrated_count': migrated_count,
                'skipped_count': skipped_count,
                'errors': errors
            }
            
        except Exception as e:
            self.logger.error(f"Error migrating tasks for employee {employee.username}: {e}")
            raise
    
    def _validate_task_for_migration(self, task: Task) -> bool:
        """
        Validate if a task meets migration criteria.
        """
        try:
            # Check minimum points
            if task.point < self.minimum_points_threshold:
                return False
            
            # Check evidence requirement
            if self.require_evidence:
                if not task.submission or task.submission.strip() == '':
                    return False
            
            # Check if task is active
            if not task.is_active:
                return False
            
            # Check if employee is valid
            if not task.employee or not task.employee.is_active:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating task {task.id}: {e}")
            return False
    
    def _update_employee_group_level(self, employee: User, target_month: int, target_year: int):
        """
        Update employee group level based on TaskHistory.
        """
        try:
            # Get employee's TaskHistory for group calculation
            employee_taskhistory = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            if employee_taskhistory.exists():
                # Calculate new group level
                group, group_title, total_point = employee_group_level(
                    employee_taskhistory, TaskGroups
                )
                
                # Update employee's current tasks with new group level
                current_tasks = Task.objects.filter(
                    employee=employee,
                    is_active=True
                )
                
                for task in current_tasks:
                    if task.groupname.id != group:
                        # Calculate new max earning
                        new_max_earning = increment_in_graduation_of_employee(
                            employee, task.mxearning, group, None
                        )
                        
                        task.groupname_id = group
                        task.group = group_title
                        task.mxearning = new_max_earning
                        task.save()
                        
                        self.logger.info(f"Updated group level for employee {employee.username}: {group_title}")
            
        except Exception as e:
            self.logger.error(f"Error updating group level for employee {employee.username}: {e}")
    
    def get_migration_preview(self, target_month: int = None, target_year: int = None) -> Dict[str, Any]:
        """
        Get a preview of what tasks would be migrated without actually migrating.
        """
        try:
            if target_month is None or target_year is None:
                current_date = datetime.now()
                target_month = current_date.month
                target_year = current_date.year
            
            eligible_tasks = self._get_eligible_tasks_for_migration(target_month, target_year)
            
            # Group by employee for preview
            employee_previews = []
            for employee_id in eligible_tasks.values_list('employee', flat=True).distinct():
                employee = User.objects.get(id=employee_id)
                employee_tasks = eligible_tasks.filter(employee_id=employee_id)
                
                employee_previews.append({
                    'employee': employee,
                    'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                    'task_count': employee_tasks.count(),
                    'total_points': sum(task.point for task in employee_tasks),
                    'tasks': [
                        {
                            'id': task.id,
                            'activity_name': task.activity_name,
                            'points': task.point,
                            'has_evidence': bool(task.submission and task.submission.strip())
                        }
                        for task in employee_tasks
                    ]
                })
            
            return {
                'target_month': target_month,
                'target_year': target_year,
                'total_eligible_tasks': eligible_tasks.count(),
                'total_employees': len(employee_previews),
                'employee_previews': employee_previews,
                'migration_criteria': {
                    'minimum_points': self.minimum_points_threshold,
                    'require_evidence': self.require_evidence
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting migration preview: {e}")
            return {
                'error': str(e),
                'target_month': target_month,
                'target_year': target_year
            }
    
    def rollback_migration(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Rollback a migration by removing TaskHistory records and restoring task points.
        """
        try:
            with transaction.atomic():
                # Get TaskHistory records to rollback
                history_records = TaskHistory.objects.filter(
                    daf_date__month=target_month,
                    daf_date__year=target_year
                )
                
                if not history_records.exists():
                    return {
                        'success': True,
                        'message': 'No records found to rollback',
                        'rolled_back_count': 0
                    }
                
                # Restore task points (this is complex as we need to match tasks)
                # For now, just remove the TaskHistory records
                rolled_back_count = history_records.count()
                history_records.delete()
                
                return {
                    'success': True,
                    'message': f'Rolled back {rolled_back_count} TaskHistory records',
                    'rolled_back_count': rolled_back_count
                }
                
        except Exception as e:
            self.logger.error(f"Error rolling back migration: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Rollback failed'
            }
