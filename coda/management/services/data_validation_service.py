"""
Data Validation Service

Validates task data integrity and enforces business rules.

Validations:
- point ≤ mxpoint
- mxearning > 0 (for paid employees)
- mxpoint > 0
- daf_date is within valid range
- No orphaned TaskHistory records
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date, datetime
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import Task, TaskHistory, TaskLinks

logger = logging.getLogger(__name__)
User = get_user_model()


class DataValidationService:
    """
    Service for validating task data integrity.
    """
    
    def __init__(self):
        self.logger = logger
    
    def validate_task(self, task: Task) -> Dict[str, Any]:
        """
        Validate a single Task object.
        
        Args:
            task: Task object to validate
        
        Returns:
            dict: {
                'is_valid': bool,
                'errors': [...],
                'warnings': [...]
            }
        """
        errors = []
        warnings = []
        
        # Validation 1: point ≤ mxpoint
        if task.point > task.mxpoint:
            errors.append(
                f"Task {task.id}: point ({task.point}) exceeds mxpoint ({task.mxpoint})"
            )
        
        # Validation 2: mxpoint > 0
        if task.mxpoint <= 0:
            errors.append(
                f"Task {task.id}: mxpoint must be greater than 0 (got {task.mxpoint})"
            )
        
        # Validation 3: mxearning > 0 (for paid employees)
        if task.employee and task.employee.is_staff and task.mxearning <= 0:
            warnings.append(
                f"Task {task.id}: mxearning is 0 for staff employee {task.employee.username}"
            )
        
        # Validation 4: point ≥ 0
        if task.point < 0:
            errors.append(
                f"Task {task.id}: point cannot be negative (got {task.point})"
            )
        
        # Validation 5: mxearning ≥ 0
        if task.mxearning < 0:
            errors.append(
                f"Task {task.id}: mxearning cannot be negative (got {task.mxearning})"
            )
        
        # Validation 6: Employee exists and is active
        if not task.employee:
            errors.append(f"Task {task.id}: No employee assigned")
        elif not task.employee.is_active:
            warnings.append(
                f"Task {task.id}: Employee {task.employee.username} is inactive"
            )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'task_id': task.id
        }
    
    def validate_taskhistory(self, taskhistory: TaskHistory) -> Dict[str, Any]:
        """
        Validate a single TaskHistory object.
        
        Args:
            taskhistory: TaskHistory object to validate
        
        Returns:
            dict: {
                'is_valid': bool,
                'errors': [...],
                'warnings': [...]
            }
        """
        errors = []
        warnings = []
        
        # Validation 1: point ≤ mxpoint
        if taskhistory.point > taskhistory.mxpoint:
            errors.append(
                f"TaskHistory {taskhistory.id}: point ({taskhistory.point}) exceeds mxpoint ({taskhistory.mxpoint})"
            )
        
        # Validation 2: mxpoint > 0
        if taskhistory.mxpoint <= 0:
            errors.append(
                f"TaskHistory {taskhistory.id}: mxpoint must be greater than 0 (got {taskhistory.mxpoint})"
            )
        
        # Validation 3: daf_date is within valid range
        if taskhistory.daf_date:
            # daf_date should not be in the future
            if taskhistory.daf_date > date.today():
                errors.append(
                    f"TaskHistory {taskhistory.id}: daf_date ({taskhistory.daf_date}) is in the future"
                )
            
            # daf_date should not be too old (more than 2 years)
            two_years_ago = date.today().replace(year=date.today().year - 2)
            if taskhistory.daf_date < two_years_ago:
                warnings.append(
                    f"TaskHistory {taskhistory.id}: daf_date ({taskhistory.daf_date}) is more than 2 years old"
                )
        else:
            errors.append(f"TaskHistory {taskhistory.id}: daf_date is missing")
        
        # Validation 4: Employee exists
        if not taskhistory.employee:
            errors.append(f"TaskHistory {taskhistory.id}: No employee assigned")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'taskhistory_id': taskhistory.id
        }
    
    def validate_all_tasks(
        self,
        employee: Optional[User] = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Validate all Task objects.
        
        Args:
            employee: Optional employee filter
            include_inactive: Include inactive employees
        
        Returns:
            dict: Validation summary
        """
        try:
            task_filter = Q()
            
            if employee:
                task_filter &= Q(employee=employee)
            
            if not include_inactive:
                task_filter &= Q(employee__is_active=True)
            
            tasks = Task.objects.filter(task_filter)
            
            total_tasks = tasks.count()
            valid_count = 0
            invalid_count = 0
            all_errors = []
            all_warnings = []
            
            for task in tasks:
                validation = self.validate_task(task)
                
                if validation['is_valid']:
                    valid_count += 1
                else:
                    invalid_count += 1
                
                all_errors.extend(validation['errors'])
                all_warnings.extend(validation['warnings'])
            
            return {
                'total_tasks': total_tasks,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'errors': all_errors,
                'warnings': all_warnings,
                'is_all_valid': invalid_count == 0
            }
            
        except Exception as e:
            self.logger.error(f"Error validating tasks: {e}", exc_info=True)
            return {
                'total_tasks': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'errors': [str(e)],
                'warnings': [],
                'is_all_valid': False
            }
    
    def validate_all_taskhistory(
        self,
        employee: Optional[User] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate all TaskHistory objects.
        
        Args:
            employee: Optional employee filter
            month: Optional month filter
            year: Optional year filter
        
        Returns:
            dict: Validation summary
        """
        try:
            taskhistory_filter = Q()
            
            if employee:
                taskhistory_filter &= Q(employee=employee)
            
            if month:
                taskhistory_filter &= Q(daf_date__month=month)
            
            if year:
                taskhistory_filter &= Q(daf_date__year=year)
            
            taskhistories = TaskHistory.objects.filter(taskhistory_filter)
            
            total_taskhistories = taskhistories.count()
            valid_count = 0
            invalid_count = 0
            all_errors = []
            all_warnings = []
            
            for taskhistory in taskhistories:
                validation = self.validate_taskhistory(taskhistory)
                
                if validation['is_valid']:
                    valid_count += 1
                else:
                    invalid_count += 1
                
                all_errors.extend(validation['errors'])
                all_warnings.extend(validation['warnings'])
            
            return {
                'total_taskhistories': total_taskhistories,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'errors': all_errors,
                'warnings': all_warnings,
                'is_all_valid': invalid_count == 0
            }
            
        except Exception as e:
            self.logger.error(f"Error validating taskhistories: {e}", exc_info=True)
            return {
                'total_taskhistories': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'errors': [str(e)],
                'warnings': [],
                'is_all_valid': False
            }
    
    def find_orphaned_taskhistory(self) -> Dict[str, Any]:
        """
        Find TaskHistory records that reference non-existent employees.
        
        Returns:
            dict: List of orphaned records
        """
        try:
            # Get all TaskHistory records
            all_taskhistories = TaskHistory.objects.all()
            
            orphaned = []
            for taskhistory in all_taskhistories:
                if not taskhistory.employee or not taskhistory.employee.is_active:
                    orphaned.append({
                        'id': taskhistory.id,
                        'employee_id': taskhistory.employee.id if taskhistory.employee else None,
                        'daf_date': taskhistory.daf_date,
                        'activity_name': taskhistory.activity_name
                    })
            
            return {
                'orphaned_count': len(orphaned),
                'orphaned_records': orphaned
            }
            
        except Exception as e:
            self.logger.error(f"Error finding orphaned taskhistories: {e}", exc_info=True)
            return {
                'orphaned_count': 0,
                'orphaned_records': [],
                'error': str(e)
            }
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get comprehensive validation report for all task data.
        
        Returns:
            dict: Complete validation report
        """
        try:
            tasks_validation = self.validate_all_tasks()
            taskhistory_validation = self.validate_all_taskhistory()
            orphaned = self.find_orphaned_taskhistory()
            
            return {
                'tasks': tasks_validation,
                'taskhistory': taskhistory_validation,
                'orphaned_records': orphaned,
                'overall_status': (
                    tasks_validation['is_all_valid'] and
                    taskhistory_validation['is_all_valid'] and
                    orphaned['orphaned_count'] == 0
                ),
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating validation report: {e}", exc_info=True)
            return {
                'error': str(e),
                'generated_at': timezone.now().isoformat()
            }
