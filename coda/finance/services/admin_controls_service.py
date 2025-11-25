"""
Admin Controls Service for CODA Finance System

Provides comprehensive admin controls for employee type regulations, custom compliance
thresholds, and override capabilities for special cases in the salary-budget integration.

Features:
- Employee type regulations (full-time, part-time, contractors)
- Custom compliance thresholds per employee type
- Override capabilities for special cases
- Admin permission management
- Audit logging for admin actions

Created: October 2025
Phase: Advanced Admin Features
"""

import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from shared_core.users import Department
from management.models import TaskHistory, Task
from management.utils import calculate_total_pay
from management.services.employee_compliance_service import EmployeeComplianceService

User = get_user_model()
logger = logging.getLogger(__name__)


class AdminControlsService:
    """
    Service for managing admin controls and regulations for the compliance system.
    
    Provides flexible configuration options for different employee types
    and special cases that require manual intervention.
    """
    
    # Default compliance thresholds by employee type
    DEFAULT_THRESHOLDS = {
        'full_time': 33.0,
        'part_time': 25.0,
        'contractor': 50.0,
        'intern': 20.0,
        'temporary': 30.0,
        'default': 33.0
    }
    
    # Employee type classifications
    EMPLOYEE_TYPES = {
        'full_time': 'Full-time Employee',
        'part_time': 'Part-time Employee', 
        'contractor': 'Contractor',
        'intern': 'Intern',
        'temporary': 'Temporary Employee'
    }
    
    def __init__(self):
        self.compliance_service = EmployeeComplianceService()
        self.logger = logging.getLogger(__name__)
    
    def get_employee_type_regulations(self) -> Dict[str, Any]:
        """
        Get current employee type regulations and thresholds.
        
        Returns comprehensive configuration for all employee types
        including compliance thresholds, salary inclusion rules, and special cases.
        """
        try:
            regulations = {
                'employee_types': self.EMPLOYEE_TYPES,
                'default_thresholds': self.DEFAULT_THRESHOLDS,
                'regulations': {
                    'full_time': {
                        'name': 'Full-time Employee',
                        'compliance_threshold': 33.0,
                        'salary_inclusion': True,
                        'requires_approval': False,
                        'special_rules': [],
                        'description': 'Standard full-time employees with 33% compliance requirement'
                    },
                    'part_time': {
                        'name': 'Part-time Employee',
                        'compliance_threshold': 25.0,
                        'salary_inclusion': True,
                        'requires_approval': False,
                        'special_rules': [],
                        'description': 'Part-time employees with reduced compliance requirement'
                    },
                    'contractor': {
                        'name': 'Contractor',
                        'compliance_threshold': 50.0,
                        'salary_inclusion': True,
                        'requires_approval': True,
                        'special_rules': ['project_based_payment', 'milestone_tracking'],
                        'description': 'Contractors with higher compliance threshold and approval requirement'
                    },
                    'intern': {
                        'name': 'Intern',
                        'compliance_threshold': 20.0,
                        'salary_inclusion': True,
                        'requires_approval': False,
                        'special_rules': ['learning_focused', 'mentor_approval'],
                        'description': 'Interns with learning-focused compliance requirements'
                    },
                    'temporary': {
                        'name': 'Temporary Employee',
                        'compliance_threshold': 30.0,
                        'salary_inclusion': True,
                        'requires_approval': False,
                        'special_rules': ['short_term_focus'],
                        'description': 'Temporary employees with flexible compliance requirements'
                    }
                },
                'global_settings': {
                    'default_threshold': 33.0,
                    'override_enabled': True,
                    'approval_required_for_overrides': True,
                    'audit_logging': True,
                    'notification_enabled': True
                },
                'last_updated': timezone.now(),
                'updated_by': 'system'
            }
            
            return regulations
            
        except Exception as e:
            self.logger.error(f"Error getting employee type regulations: {e}")
            return {'error': str(e)}
    
    def update_employee_type_threshold(self, employee_type: str, new_threshold: float, 
                                     updated_by: User) -> Dict[str, Any]:
        """
        Update compliance threshold for a specific employee type.
        
        Args:
            employee_type: Type of employee (full_time, part_time, etc.)
            new_threshold: New compliance threshold percentage
            updated_by: Admin user making the change
            
        Returns:
            Dict with update result and audit information
        """
        try:
            # Validate employee type
            if employee_type not in self.EMPLOYEE_TYPES:
                return {'error': f'Invalid employee type: {employee_type}'}
            
            # Validate threshold
            if not (0 <= new_threshold <= 100):
                return {'error': 'Threshold must be between 0 and 100'}
            
            # Get current regulations
            regulations = self.get_employee_type_regulations()
            old_threshold = regulations['regulations'][employee_type]['compliance_threshold']
            
            # Update threshold
            regulations['regulations'][employee_type]['compliance_threshold'] = new_threshold
            regulations['last_updated'] = timezone.now()
            regulations['updated_by'] = updated_by.username
            
            # Log the change
            self._log_admin_action(
                action='update_threshold',
                details={
                    'employee_type': employee_type,
                    'old_threshold': old_threshold,
                    'new_threshold': new_threshold,
                    'updated_by': updated_by.username
                }
            )
            
            return {
                'success': True,
                'employee_type': employee_type,
                'old_threshold': old_threshold,
                'new_threshold': new_threshold,
                'updated_at': timezone.now(),
                'updated_by': updated_by.username
            }
            
        except Exception as e:
            self.logger.error(f"Error updating employee type threshold: {e}")
            return {'error': str(e)}
    
    def create_employee_override(self, employee: User, override_type: str, 
                               override_data: Dict[str, Any], created_by: User) -> Dict[str, Any]:
        """
        Create an override for a specific employee.
        
        Args:
            employee: Employee to create override for
            override_type: Type of override (threshold, salary_inclusion, etc.)
            override_data: Override configuration data
            created_by: Admin user creating the override
            
        Returns:
            Dict with override creation result
        """
        try:
            # Validate override type
            valid_override_types = ['threshold', 'salary_inclusion', 'approval_bypass', 'special_case']
            if override_type not in valid_override_types:
                return {'error': f'Invalid override type: {override_type}'}
            
            # Create override record
            override_record = {
                'employee_id': employee.id,
                'employee_username': employee.username,
                'employee_name': employee.get_full_name(),
                'override_type': override_type,
                'override_data': override_data,
                'created_at': timezone.now(),
                'created_by': created_by.username,
                'is_active': True,
                'expires_at': override_data.get('expires_at'),
                'reason': override_data.get('reason', ''),
                'approval_required': override_data.get('approval_required', True)
            }
            
            # Log the override creation
            self._log_admin_action(
                action='create_override',
                details=override_record
            )
            
            return {
                'success': True,
                'override_record': override_record,
                'message': f'Override created for {employee.username}'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating employee override: {e}")
            return {'error': str(e)}
    
    def apply_employee_override(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Apply any active overrides for a specific employee.
        
        This method checks for active overrides and applies them to the
        employee's compliance calculation.
        """
        try:
            # Get employee's overrides (in a real implementation, this would query a database)
            overrides = self._get_employee_overrides(employee)
            
            if not overrides:
                return {'overrides_applied': False, 'message': 'No active overrides found'}
            
            # Apply overrides
            applied_overrides = []
            for override in overrides:
                if self._is_override_active(override):
                    applied_overrides.append(self._apply_single_override(employee, override, target_month, target_year))
            
            return {
                'overrides_applied': True,
                'applied_count': len(applied_overrides),
                'applied_overrides': applied_overrides,
                'message': f'Applied {len(applied_overrides)} overrides for {employee.username}'
            }
            
        except Exception as e:
            self.logger.error(f"Error applying employee overrides: {e}")
            return {'error': str(e)}
    
    def get_employee_compliance_with_overrides(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get employee compliance status with any applicable overrides applied.
        
        This method provides the final compliance determination after
        applying all relevant overrides and regulations.
        """
        try:
            # Get base compliance status
            from finance.services.integrated_budget_service import IntegratedBudgetService
            integrated_service = IntegratedBudgetService()
            base_compliance = integrated_service.get_employee_salary_details(employee, target_month, target_year)
            
            if 'error' in base_compliance:
                return base_compliance
            
            # Determine employee type
            employee_type = self._determine_employee_type(employee)
            
            # Get applicable threshold
            regulations = self.get_employee_type_regulations()
            default_threshold = regulations['regulations'][employee_type]['compliance_threshold']
            
            # Check for overrides
            overrides = self._get_employee_overrides(employee)
            applied_overrides = []
            final_threshold = default_threshold
            
            for override in overrides:
                if self._is_override_active(override) and override['override_type'] == 'threshold':
                    final_threshold = override['override_data']['threshold']
                    applied_overrides.append({
                        'type': 'threshold',
                        'original_threshold': default_threshold,
                        'override_threshold': final_threshold,
                        'reason': override['reason']
                    })
            
            # Calculate final compliance status
            compliance_rate = base_compliance['compliance_rate']
            is_compliant_with_overrides = compliance_rate >= final_threshold
            
            return {
                'employee': employee,
                'employee_type': employee_type,
                'base_compliance': base_compliance,
                'default_threshold': default_threshold,
                'final_threshold': final_threshold,
                'compliance_rate': compliance_rate,
                'is_compliant_base': compliance_rate >= default_threshold,
                'is_compliant_with_overrides': is_compliant_with_overrides,
                'applied_overrides': applied_overrides,
                'salary_amount': base_compliance.get('total_salary', 0),
                'calculated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting employee compliance with overrides: {e}")
            return {'error': str(e)}
    
    def get_admin_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data for the admin controls dashboard.
        
        Provides overview of all regulations, overrides, and system status
        for administrative management.
        """
        try:
            # Get current regulations
            regulations = self.get_employee_type_regulations()
            
            # Get override statistics
            override_stats = self._get_override_statistics()
            
            # Get employee type distribution
            employee_distribution = self._get_employee_type_distribution()
            
            # Get recent admin actions
            recent_actions = self._get_recent_admin_actions()
            
            return {
                'regulations': regulations,
                'override_statistics': override_stats,
                'employee_distribution': employee_distribution,
                'recent_admin_actions': recent_actions,
                'system_status': {
                    'total_employee_types': len(self.EMPLOYEE_TYPES),
                    'active_overrides': override_stats.get('active_count', 0),
                    'total_overrides': override_stats.get('total_count', 0),
                    'last_updated': timezone.now()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting admin dashboard data: {e}")
            return {'error': str(e)}
    
    def _determine_employee_type(self, employee: User) -> str:
        """
        Determine employee type based on user properties.
        
        In a real implementation, this would check user profile fields
        or department assignments to determine the employee type.
        """
        # For now, we'll use a simple heuristic based on username or other properties
        # In a real system, this would be based on actual employee type fields
        
        # Check if user has specific properties that indicate employee type
        if hasattr(employee, 'employee_type'):
            return getattr(employee, 'employee_type', 'full_time')
        
        # Default to full_time for now
        return 'full_time'
    
    def _get_employee_overrides(self, employee: User) -> List[Dict[str, Any]]:
        """
        Get active overrides for a specific employee.
        
        In a real implementation, this would query a database table
        storing employee overrides.
        """
        # For now, return empty list
        # In a real system, this would query EmployeeOverride model
        return []
    
    def _is_override_active(self, override: Dict[str, Any]) -> bool:
        """Check if an override is currently active."""
        if not override.get('is_active', False):
            return False
        
        expires_at = override.get('expires_at')
        if expires_at and timezone.now() > expires_at:
            return False
        
        return True
    
    def _apply_single_override(self, employee: User, override: Dict[str, Any], 
                             target_month: int, target_year: int) -> Dict[str, Any]:
        """Apply a single override to an employee's compliance calculation."""
        return {
            'override_id': override.get('id'),
            'override_type': override['override_type'],
            'applied_at': timezone.now(),
            'details': override['override_data']
        }
    
    def _get_override_statistics(self) -> Dict[str, Any]:
        """Get statistics about employee overrides."""
        # In a real implementation, this would query the database
        return {
            'total_count': 0,
            'active_count': 0,
            'by_type': {},
            'recent_created': 0
        }
    
    def _get_employee_type_distribution(self) -> Dict[str, Any]:
        """Get distribution of employees by type."""
        # In a real implementation, this would query the database
        return {
            'full_time': 0,
            'part_time': 0,
            'contractor': 0,
            'intern': 0,
            'temporary': 0
        }
    
    def _get_recent_admin_actions(self) -> List[Dict[str, Any]]:
        """Get recent admin actions for audit trail."""
        # In a real implementation, this would query an audit log
        return []
    
    def _log_admin_action(self, action: str, details: Dict[str, Any]) -> None:
        """
        Log admin actions for audit trail.
        
        In a real implementation, this would write to an audit log database table.
        """
        self.logger.info(f"Admin action: {action} - {details}")
        # In a real system, this would also write to an audit log table
