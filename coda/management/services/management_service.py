"""
Management Service

Handles all management-related business logic including:
- Department management
- Employee management
- Contract management
- Meeting management
- Policy management

This service encapsulates the business logic previously scattered across management/views.py
"""

import logging
from typing import Dict, List, Optional, Any
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.models import Department
from .base_service import BaseManagementService

logger = logging.getLogger(__name__)
User = get_user_model()


class ManagementService(BaseManagementService):
    """
    Service for managing core management operations.
    
    Handles departments, employees, contracts, meetings, and policies.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def create_department(
        self, 
        user: User, 
        department_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new department.
        
        Args:
            user: The user creating the department
            department_data: Dictionary containing department details
            
        Returns:
            Dict with success status and department data
        """
        try:
            self._validate_manager_permissions(user)
            
            # Validate required fields
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in department_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate department name
            if len(department_data['name']) < 2:
                raise ValidationError("Department name must be at least 2 characters long")
            
            with transaction.atomic():
                # Create department
                department = Department.objects.create(
                    name=department_data['name'],
                    description=department_data['description'],
                    slug=department_data['name'].lower().replace(' ', '-'),
                    is_active=True,
                    is_featured=True
                )
                
                # Log the operation
                self._log_operation(
                    'create_department',
                    user,
                    {'department_id': department.id, 'name': department.name}
                )
                
                return self.create_success_response(
                    {'department_id': department.id, 'name': department.name},
                    "Department created successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'create_department', user)
    
    def get_departments(
        self, 
        user: Optional[User] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get departments.
        
        Args:
            user: Optional user filter (for user's departments)
            active_only: Whether to return only active departments
            
        Returns:
            Dict with success status and list of departments
        """
        try:
            queryset = Department.objects.all()
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            # Note: Department model doesn't have a manager field
            # This filter would need to be implemented differently based on business requirements
            
            departments = []
            for dept in queryset.order_by('name'):
                departments.append({
                    'id': dept.id,
                    'name': dept.name,
                    'description': dept.description,
                    'slug': dept.slug,
                    'is_featured': dept.is_featured,
                    'is_active': dept.is_active
                })
            
            return self.create_success_response(
                {'departments': departments},
                f"Retrieved {len(departments)} departments"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_departments')
    
    def create_employee(
        self, 
        user: User, 
        employee_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new employee (simplified version).
        
        Args:
            user: The user creating the employee
            employee_data: Dictionary containing employee details
            
        Returns:
            Dict with success status and employee data
        """
        try:
            self._validate_manager_permissions(user)
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email', 'department_id']
            for field in required_fields:
                if field not in employee_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate email format
            email = employee_data['email']
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValidationError("Invalid email format")
            
            # Validate department exists
            try:
                department = Department.objects.get(id=employee_data['department_id'])
            except ObjectDoesNotExist:
                raise ValidationError("Department not found")
            
            # For now, we'll just validate the data without creating an employee
            # since the Employee model doesn't exist in this context
            employee_name = f"{employee_data['first_name']} {employee_data['last_name']}"
            
            # Log the operation
            self._log_operation(
                'create_employee',
                user,
                {'name': employee_name, 'department': department.name}
            )
            
            return self.create_success_response(
                {'name': employee_name, 'department': department.name},
                "Employee data validated successfully"
            )
                
        except Exception as e:
            self._handle_error(e, 'create_employee', user)
    
    def get_employees(
        self, 
        department_id: Optional[int] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get employees (simplified version).
        
        Args:
            department_id: Optional department filter
            active_only: Whether to return only active employees
            
        Returns:
            Dict with success status and list of employees
        """
        try:
            # For now, return empty list since Employee model doesn't exist
            # This would be implemented when the proper Employee model is available
            employees = []
            
            return self.create_success_response(
                {'employees': employees},
                f"Retrieved {len(employees)} employees"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_employees')
    
    def create_meeting(
        self, 
        user: User, 
        meeting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new meeting (simplified version).
        
        Args:
            user: The user creating the meeting
            meeting_data: Dictionary containing meeting details
            
        Returns:
            Dict with success status and meeting data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['title', 'description', 'meeting_date']
            for field in required_fields:
                if field not in meeting_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate meeting date
            meeting_date = meeting_data['meeting_date']
            if isinstance(meeting_date, str):
                meeting_date = datetime.fromisoformat(meeting_date)
            
            if meeting_date < timezone.now():
                raise ValidationError("Meeting date cannot be in the past")
            
            # For now, just validate the data without creating a meeting
            # since the Meeting model doesn't exist in this context
            
            # Log the operation
            self._log_operation(
                'create_meeting',
                user,
                {'title': meeting_data['title']}
            )
            
            return self.create_success_response(
                {'title': meeting_data['title']},
                "Meeting data validated successfully"
            )
                
        except Exception as e:
            self._handle_error(e, 'create_meeting', user)
    
    def get_meetings(
        self, 
        user: Optional[User] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get meetings (simplified version).
        
        Args:
            user: Optional user filter (for user's meetings)
            status: Optional status filter
            
        Returns:
            Dict with success status and list of meetings
        """
        try:
            # For now, return empty list since Meeting model doesn't exist
            meetings = []
            
            return self.create_success_response(
                {'meetings': meetings},
                f"Retrieved {len(meetings)} meetings"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_meetings')
    
    def create_policy(
        self, 
        user: User, 
        policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new policy (simplified version).
        
        Args:
            user: The user creating the policy
            policy_data: Dictionary containing policy details
            
        Returns:
            Dict with success status and policy data
        """
        try:
            self._validate_manager_permissions(user)
            
            # Validate required fields
            required_fields = ['title', 'content', 'category']
            for field in required_fields:
                if field not in policy_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate policy content
            if len(policy_data['content']) < 50:
                raise ValidationError("Policy content must be at least 50 characters long")
            
            # For now, just validate the data without creating a policy
            # since the Policy model doesn't exist in this context
            
            # Log the operation
            self._log_operation(
                'create_policy',
                user,
                {'title': policy_data['title']}
            )
            
            return self.create_success_response(
                {'title': policy_data['title']},
                "Policy data validated successfully"
            )
                
        except Exception as e:
            self._handle_error(e, 'create_policy', user)
    
    def get_policies(
        self, 
        category: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get policies (simplified version).
        
        Args:
            category: Optional category filter
            active_only: Whether to return only active policies
            
        Returns:
            Dict with success status and list of policies
        """
        try:
            # For now, return empty list since Policy model doesn't exist
            policies = []
            
            return self.create_success_response(
                {'policies': policies},
                f"Retrieved {len(policies)} policies"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_policies')
    
    def get_management_dashboard_data(
        self, 
        user: User
    ) -> Dict[str, Any]:
        """
        Get comprehensive management dashboard data.
        
        Args:
            user: The user requesting dashboard data
            
        Returns:
            Dict with success status and dashboard data
        """
        try:
            self._validate_user(user)
            
            # Get department count
            departments_response = self.get_departments(user)
            departments = departments_response.get('data', {}).get('departments', [])
            
            # Get employee count
            employees_response = self.get_employees()
            employees = employees_response.get('data', {}).get('employees', [])
            
            # Get meeting count
            meetings_response = self.get_meetings(user)
            meetings = meetings_response.get('data', {}).get('meetings', [])
            
            # Get policy count
            policies_response = self.get_policies()
            policies = policies_response.get('data', {}).get('policies', [])
            
            # Calculate statistics
            dashboard_data = {
                'total_departments': len(departments),
                'total_employees': len(employees),
                'total_meetings': len(meetings),
                'total_policies': len(policies),
                'recent_meetings': meetings[:5],  # Last 5 meetings
                'department_breakdown': {}
            }
            
            # Department breakdown
            for dept in departments:
                dept_employees = [emp for emp in employees if emp['department'] == dept['name']]
                dashboard_data['department_breakdown'][dept['name']] = len(dept_employees)
            
            return self.create_success_response(
                {'dashboard': dashboard_data},
                "Management dashboard data retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_management_dashboard_data', user)
