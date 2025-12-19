"""
Utilities Service

This service consolidates all scattered utility functions from legacy files.
Provides unified interface for task, payroll, employee, and loan operations
with AI enhancement capabilities.

Following DRY principles and providing consistent error handling.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Q, Sum, F
from django.contrib.auth import get_user_model

# Import legacy utilities for backward compatibility
try:
    from management.deprecated.utilities_legacy.task_utils import TaskUtils
    from management.deprecated.utilities_legacy.payroll_utils import PayrollUtils
    from management.deprecated.utilities_legacy.employee_utils import EmployeeUtils
    from management.deprecated.utilities_legacy.loan_utils import LoanUtils
    LEGACY_UTILS_AVAILABLE = True
except ImportError:
    # Fallback if legacy utils not available
    TaskUtils = None
    PayrollUtils = None
    EmployeeUtils = None
    LoanUtils = None
    LEGACY_UTILS_AVAILABLE = False

# Import AI services for enhancement via interfaces
from shared_core.interfaces.ai_service import AIServiceInterface
from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter

def _get_ai_service() -> AIServiceInterface:
    """Get AI service via interface."""
    try:
        from ai_services.adapters.ai_service_adapter import AIServiceAdapter
        return AIServiceAdapter()
    except ImportError:
        return NoOpAIServiceAdapter()

# For backward compatibility, keep AI_SERVICE_AVAILABLE flag
AI_SERVICE_AVAILABLE = True  # Interface always available (NoOp if adapter missing)
RealAIService = None  # Deprecated - use _get_ai_service() instead

# Note: AIBudgetSuggestionService is not part of FinanceTaskServiceInterface
# If needed, it should be added to the interface or accessed differently
try:
    from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService
    BUDGET_SERVICE_AVAILABLE = True
except ImportError:
    BUDGET_SERVICE_AVAILABLE = False
    AIBudgetSuggestionService = None

# Import models
from management.models import Task, TaskHistory, TaskLinks
from shared_core.users import CustomerUser

logger = logging.getLogger(__name__)
User = get_user_model()


class UtilitiesService:
    """
    Enhanced utilities service consolidating all management app utility functions.
    
    This service replaces scattered utility functions with a unified, AI-enhanced approach
    that follows DRY principles and provides consistent error handling and logging.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Initialize legacy utility classes if available
        if LEGACY_UTILS_AVAILABLE:
            self.task_utils = TaskUtils() if TaskUtils else None
            self.payroll_utils = PayrollUtils() if PayrollUtils else None
            self.employee_utils = EmployeeUtils() if EmployeeUtils else None
            self.loan_utils = LoanUtils() if LoanUtils else None
        else:
            self.task_utils = None
            self.payroll_utils = None
            self.employee_utils = None
            self.loan_utils = None
        
        # Initialize AI services if available
        self.ai_service = RealAIService() if AI_SERVICE_AVAILABLE else None
        self.budget_service = AIBudgetSuggestionService() if BUDGET_SERVICE_AVAILABLE else None
        
        self.logger.info("UtilitiesService initialized - Legacy utils: %s, AI services: %s, Budget services: %s", 
                        LEGACY_UTILS_AVAILABLE, AI_SERVICE_AVAILABLE, BUDGET_SERVICE_AVAILABLE)
    
    # ============================================================================
    # TASK OPERATIONS - Consolidated from utils.py and task_utils.py
    # ============================================================================
    
    def get_tasks_with_ai_enhancement(self, employee: User, selected_month: int, selected_year: int, pay_type: str) -> Dict[str, Any]:
        """
        Enhanced task retrieval with AI insights.
        
        Consolidates get_tasks logic from utils.py and task_utils.py with AI enhancements.
        
        Args:
            employee: Employee object
            selected_month: Selected month for filtering
            selected_year: Selected year for filtering
            pay_type: Type of payment ('payslip', 'task_payslip', 'usertasks', etc.)
            
        Returns:
            Dict with tasks information and AI enhancements
        """
        try:
            self.logger.info(f"Getting tasks for employee {employee.id} for {selected_month}/{selected_year}, pay_type: {pay_type}")
            
            # Use existing task_utils for base functionality
            result = self.task_utils.get_tasks(employee, selected_month, selected_year, pay_type)
            
            tasks = result.get('tasks')
            total_pay = result.get('total_pay', 0)
            message = result.get('message')
            
            # Add AI enhancements if tasks exist and AI service is available
            ai_insights = None
            performance_metrics = None
            
            if tasks and tasks.exists() and self.ai_service:
                try:
                    ai_insights = self._get_ai_task_insights(tasks, employee)
                    performance_metrics = self._calculate_performance_metrics(tasks)
                except Exception as e:
                    self.logger.warning(f"AI insights failed for employee {employee.id}: {e}")
            
            return {
                'tasks': tasks,
                'total_pay': total_pay,
                'message': message,
                'ai_insights': ai_insights,
                'performance_metrics': performance_metrics,
                'ai_service_available': bool(self.ai_service)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tasks for employee {employee.id}: {e}")
            return {
                'tasks': None,
                'total_pay': 0,
                'message': f"Error retrieving tasks: {str(e)}",
                'ai_insights': None,
                'performance_metrics': None,
                'ai_service_available': False
            }
    
    def calculate_task_performance_score(self, tasks) -> Decimal:
        """
        Consolidated performance calculation replacing duplicate calculations.
        
        Replaces duplicate calculations from Task.get_pay and TaskHistory.get_pay.
        
        Args:
            tasks: QuerySet of Task or TaskHistory objects
            
        Returns:
            Average performance score
        """
        try:
            if not tasks or not tasks.exists():
                return Decimal('0.00')
            
            total_score = Decimal('0.00')
            task_count = 0
            
            for task in tasks:
                score = self._calculate_individual_task_score(task)
                total_score += score
                task_count += 1
            
            return total_score / task_count if task_count > 0 else Decimal('0.00')
            
        except Exception as e:
            self.logger.error(f"Error calculating task performance score: {e}")
            return Decimal('0.00')
    
    def process_evidence_with_ai(self, evidence_data: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """
        Consolidated evidence processing with AI validation.
        
        Consolidates evidence processing logic with AI validation.
        
        Args:
            evidence_data: Evidence data dictionary
            task: Task object
            
        Returns:
            Dict with validation results and AI insights
        """
        try:
            validation_result = {
                'validation_score': 0.75,  # Default score
                'recommendations': [],
                'quality_score': 0.75,
                'ai_service_used': False
            }
            
            # Add AI validation if service is available
            if self.ai_service:
                try:
                    ai_validation = self.ai_service.get_prediction(
                        analysis_type='evidence_validation',
                        input_data={
                            'task_activity': task.activity_name,
                            'evidence_data': evidence_data,
                            'task_category': task.category.title if task.category else 'General'
                        },
                        session_id=f"evidence_validation_{task.id}_{timezone.now().timestamp()}"
                    )
                    
                    validation_result.update({
                        'validation_score': ai_validation.get('confidence_score', 0.75),
                        'recommendations': ai_validation.get('recommendations', []),
                        'quality_score': ai_validation.get('quality_score', 0.75),
                        'ai_service_used': True
                    })
                    
                except Exception as e:
                    self.logger.warning(f"AI evidence validation failed for task {task.id}: {e}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error processing evidence for task {task.id}: {e}")
            return {
                'validation_score': 0.0,
                'recommendations': ['Error processing evidence'],
                'quality_score': 0.0,
                'ai_service_used': False
            }
    
    # ============================================================================
    # PAYROLL OPERATIONS - Consolidated from payroll_utils.py and utils.py
    # ============================================================================
    
    def calculate_comprehensive_payroll(self, employee: User, month: int, year: int) -> Dict[str, Any]:
        """
        Consolidated payroll calculation replacing scattered calculations.
        
        Consolidates payroll calculations from multiple files with AI enhancements.
        
        Args:
            employee: Employee object
            month: Month for payroll calculation
            year: Year for payroll calculation
            
        Returns:
            Dict with comprehensive payroll data
        """
        try:
            self.logger.info(f"Calculating comprehensive payroll for employee {employee.id} for {month}/{year}")
            
            # Get base payroll data using existing payroll_utils
            base_pay = self.payroll_utils.calculate_total_pay(employee, month, year)
            deductions = self.payroll_utils.deductions(employee, {}, {})
            bonuses = self.payroll_utils.bonus([], 0, {})
            
            # Calculate comprehensive payroll
            total_earnings = base_pay.get('total_pay', 0)
            total_deductions = deductions.get('total_deductions', 0)
            total_bonuses = bonuses.get('total_bonus', 0)
            
            net_pay = total_earnings + total_bonuses - total_deductions
            
            # Add AI predictions if service is available
            ai_predictions = None
            performance_impact = None
            
            if self.ai_service:
                try:
                    ai_predictions = self._get_ai_payroll_predictions(employee, month, year)
                    performance_impact = self._calculate_performance_impact(employee, month, year)
                except Exception as e:
                    self.logger.warning(f"AI payroll predictions failed for employee {employee.id}: {e}")
            
            return {
                'base_pay': total_earnings,
                'bonuses': total_bonuses,
                'deductions': total_deductions,
                'net_pay': net_pay,
                'ai_predictions': ai_predictions,
                'performance_impact': performance_impact,
                'ai_service_available': bool(self.ai_service),
                'calculation_date': timezone.now(),
                'period': f"{month}/{year}"
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating comprehensive payroll for employee {employee.id}: {e}")
            return {
                'base_pay': 0,
                'bonuses': 0,
                'deductions': 0,
                'net_pay': 0,
                'ai_predictions': None,
                'performance_impact': None,
                'ai_service_available': False,
                'calculation_date': timezone.now(),
                'period': f"{month}/{year}",
                'error': str(e)
            }
    
    def get_selected_month_year(self, request: Any, pay_type: str) -> Dict[str, Any]:
        """
        Get selected month and year from request.
        
        Consolidates get_selected_month_year logic from multiple files.
        
        Args:
            request: Django request object
            pay_type: Type of payment
            
        Returns:
            Dict with selected month, year, and form
        """
        try:
            # Use existing payroll_utils implementation
            result = self.payroll_utils.get_selected_month_year(request, pay_type)
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting selected month/year: {e}")
            # Fallback to current month/year
            current_date = timezone.now()
            return {
                'selected_month': current_date.month,
                'selected_year': current_date.year,
                'form': None,
                'error': str(e)
            }
    
    # ============================================================================
    # EMPLOYEE OPERATIONS - Consolidated from employee_utils.py
    # ============================================================================
    
    def get_employee_profile_data(self, employee: User) -> Dict[str, Any]:
        """
        Get comprehensive employee profile data.
        
        Consolidates employee data retrieval with AI enhancement.
        
        Args:
            employee: Employee object
            
        Returns:
            Dict with employee profile data
        """
        try:
            # Use existing employee_utils
            profile_data = self.employee_utils.get_employee_profile(employee)
            
            # Add AI-enhanced insights if available
            ai_insights = None
            if self.ai_service:
                try:
                    ai_insights = self._get_ai_employee_insights(employee)
                except Exception as e:
                    self.logger.warning(f"AI employee insights failed for {employee.id}: {e}")
            
            profile_data.update({
                'ai_insights': ai_insights,
                'ai_service_available': bool(self.ai_service)
            })
            
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error getting employee profile for {employee.id}: {e}")
            return {
                'employee': employee,
                'error': str(e),
                'ai_insights': None,
                'ai_service_available': False
            }
    
    # ============================================================================
    # LOAN OPERATIONS - Consolidated from loan_utils.py
    # ============================================================================
    
    def calculate_loan_payment(self, employee: User, loan_amount: Decimal) -> Dict[str, Any]:
        """
        Calculate loan payment information.
        
        Consolidates loan calculation logic.
        
        Args:
            employee: Employee object
            loan_amount: Loan amount
            
        Returns:
            Dict with loan payment information
        """
        try:
            # Use existing loan_utils
            loan_data = self.loan_utils.calculate_loan_payment(employee, loan_amount)
            
            return loan_data
            
        except Exception as e:
            self.logger.error(f"Error calculating loan payment for {employee.id}: {e}")
            return {
                'error': str(e),
                'loan_amount': loan_amount,
                'monthly_payment': 0,
                'total_interest': 0
            }
    
    # ============================================================================
    # AI ENHANCEMENT METHODS - New functionality for AI integration
    # ============================================================================
    
    def _get_ai_task_insights(self, tasks, employee: User) -> Dict[str, Any]:
        """Get AI insights for task performance."""
        if not self.ai_service:
            return None
        
        try:
            # Prepare task data for AI analysis
            task_data = []
            for task in tasks:
                task_data.append({
                    'activity_name': task.activity_name,
                    'points': float(task.point),
                    'max_points': float(task.mxpoint),
                    'earnings': float(getattr(task, 'get_pay', lambda: 0)()),
                    'category': task.category.title if task.category else 'General'
                })
            
            # Get AI analysis
            ai_response = self.ai_service.get_prediction(
                analysis_type='task_performance_analysis',
                input_data={
                    'employee_id': employee.id,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'tasks': task_data,
                    'total_tasks': len(task_data)
                },
                session_id=f"task_insights_{employee.id}_{timezone.now().timestamp()}"
            )
            
            return {
                'confidence_score': ai_response.get('confidence_score', 0.75),
                'performance_summary': ai_response.get('performance_summary', 'Good performance'),
                'recommendations': ai_response.get('recommendations', []),
                'predicted_completion_rate': ai_response.get('predicted_completion_rate', 0.85),
                'model_used': ai_response.get('model_used', 'fallback')
            }
            
        except Exception as e:
            self.logger.warning(f"AI task insights failed: {e}")
            return {
                'confidence_score': 0.5,
                'performance_summary': 'Analysis unavailable',
                'recommendations': ['Review task performance manually'],
                'predicted_completion_rate': 0.75,
                'model_used': 'fallback'
            }
    
    def _calculate_performance_metrics(self, tasks) -> Dict[str, Any]:
        """Calculate performance metrics from tasks."""
        try:
            if not tasks or not tasks.exists():
                return {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'completion_rate': 0.0,
                    'average_score': 0.0,
                    'total_earnings': 0.0
                }
            
            total_tasks = tasks.count()
            completed_tasks = 0
            total_points = Decimal('0.00')
            total_max_points = Decimal('0.00')
            total_earnings = Decimal('0.00')
            
            for task in tasks:
                if task.point >= task.mxpoint * Decimal('0.8'):  # 80% completion threshold
                    completed_tasks += 1
                
                total_points += task.point
                total_max_points += task.mxpoint
                total_earnings += getattr(task, 'get_pay', lambda: Decimal('0.00'))()
            
            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0
            average_score = (total_points / total_max_points) if total_max_points > 0 else 0.0
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': float(completion_rate),
                'average_score': float(average_score),
                'total_earnings': float(total_earnings)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'completion_rate': 0.0,
                'average_score': 0.0,
                'total_earnings': 0.0,
                'error': str(e)
            }
    
    def _calculate_individual_task_score(self, task) -> Decimal:
        """Calculate individual task performance score."""
        try:
            if hasattr(task, 'mxpoint') and task.mxpoint > 0:
                return Decimal(str(task.point / task.mxpoint))
            return Decimal('0.00')
        except (ZeroDivisionError, AttributeError, TypeError):
            return Decimal('0.00')
    
    def _get_ai_payroll_predictions(self, employee: User, month: int, year: int) -> Dict[str, Any]:
        """Get AI predictions for payroll."""
        if not self.ai_service:
            return None
        
        try:
            # Get historical performance for predictions
            historical_tasks = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=month,
                daf_date__year=year
            )
            
            ai_response = self.ai_service.get_prediction(
                analysis_type='payroll_prediction',
                input_data={
                    'employee_id': employee.id,
                    'month': month,
                    'year': year,
                    'historical_performance': len(historical_tasks)
                },
                session_id=f"payroll_prediction_{employee.id}_{month}_{year}"
            )
            
            return {
                'predicted_earnings': ai_response.get('predicted_earnings', 0),
                'confidence_level': ai_response.get('confidence_level', 0.75),
                'recommendations': ai_response.get('recommendations', [])
            }
            
        except Exception as e:
            self.logger.warning(f"AI payroll predictions failed: {e}")
            return {
                'predicted_earnings': 0,
                'confidence_level': 0.5,
                'recommendations': ['Manual review recommended']
            }
    
    def _calculate_performance_impact(self, employee: User, month: int, year: int) -> Dict[str, Any]:
        """Calculate performance impact on payroll."""
        try:
            # Get current month tasks
            current_tasks = Task.objects.filter(
                employee=employee,
                created_at__month=month,
                created_at__year=year
            )
            
            # Calculate performance impact
            total_points = sum(task.point for task in current_tasks)
            total_max_points = sum(task.mxpoint for task in current_tasks)
            
            performance_ratio = (total_points / total_max_points) if total_max_points > 0 else 0
            
            return {
                'performance_ratio': float(performance_ratio),
                'tasks_completed': current_tasks.count(),
                'total_points_earned': float(total_points),
                'performance_tier': 'High' if performance_ratio >= 0.9 else 'Medium' if performance_ratio >= 0.7 else 'Low'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance impact: {e}")
            return {
                'performance_ratio': 0.0,
                'tasks_completed': 0,
                'total_points_earned': 0.0,
                'performance_tier': 'Unknown'
            }
    
    def _get_ai_employee_insights(self, employee: User) -> Dict[str, Any]:
        """Get AI insights for employee performance."""
        if not self.ai_service:
            return None
        
        try:
            # Get recent task performance
            recent_tasks = Task.objects.filter(employee=employee).order_by('-created_at')[:10]
            
            ai_response = self.ai_service.get_prediction(
                analysis_type='employee_analysis',
                input_data={
                    'employee_id': employee.id,
                    'recent_tasks': len(recent_tasks),
                    'department': employee.department.name if hasattr(employee, 'department') and employee.department else None
                },
                session_id=f"employee_analysis_{employee.id}"
            )
            
            return {
                'performance_summary': ai_response.get('performance_summary', 'Good performance'),
                'strengths': ai_response.get('strengths', []),
                'improvement_areas': ai_response.get('improvement_areas', []),
                'recommendations': ai_response.get('recommendations', [])
            }
            
        except Exception as e:
            self.logger.warning(f"AI employee insights failed: {e}")
            return {
                'performance_summary': 'Analysis unavailable',
                'strengths': [],
                'improvement_areas': [],
                'recommendations': ['Manual review recommended']
            }
    
    # ============================================================================
    # UTILITY METHODS - Helper methods for common operations
    # ============================================================================
    
    def get_service_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        return {
            'ai_service_available': bool(self.ai_service),
            'budget_service_available': bool(self.budget_service),
            'task_utils_available': bool(self.task_utils),
            'payroll_utils_available': bool(self.payroll_utils),
            'employee_utils_available': bool(self.employee_utils),
            'loan_utils_available': bool(self.loan_utils),
            'timestamp': timezone.now().isoformat()
        }
    
    def log_operation(self, operation: str, employee_id: int, details: Dict[str, Any] = None):
        """Log operations for debugging and monitoring."""
        self.logger.info(f"Operation: {operation}, Employee: {employee_id}, Details: {details}")
    
    def handle_service_error(self, operation: str, error: Exception, fallback_data: Any = None) -> Dict[str, Any]:
        """Handle service errors with fallback data."""
        self.logger.error(f"Service error in {operation}: {error}")
        return {
            'success': False,
            'error': str(error),
            'fallback_data': fallback_data,
            'timestamp': timezone.now().isoformat()
        }
