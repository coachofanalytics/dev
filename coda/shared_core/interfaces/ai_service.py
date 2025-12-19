"""
AI Service Interface

Abstract interface for AI-powered services used by management and other apps.
Defines the contract for AI predictions, task assignment suggestions, and analysis.

This interface is implemented by:
- AIServiceAdapter (in ai_services app) - wraps RealAIService
- NoOpAIServiceAdapter (in shared_core) - safe fallback when ai_services is not installed
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AIServiceInterface(ABC):
    """
    Abstract interface for AI services.
    
    This interface defines what management and other apps need from AI services,
    without depending on concrete implementations from ai_services app.
    
    All methods return dicts/list of dicts, never Django models, to ensure
    loose coupling between apps.
    """
    
    @abstractmethod
    def predict_employee_performance(
        self,
        employee_id: int,
        task_category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Predict performance for a specific employee on a task category.
        
        Used by:
        - IntelligentAssignmentService to score employees for task assignment
        - AIPredictionService for performance predictions
        
        Args:
            employee_id: ID of the employee to predict performance for
            task_category_id: Optional category ID to filter predictions
            
        Returns:
            Dict with keys:
            - success: bool - Whether prediction was successful
            - employee_id: int - Employee ID
            - employee_name: str - Employee full name
            - predicted_completion_rate: float - Predicted completion rate (0.0-1.0)
            - confidence: float - Confidence score (0.0-1.0)
            - historical_average: float - Historical average completion rate
            - task_count: int - Number of historical tasks used
            - insights: List[str] - Performance insights
            - recommendations: List[str] - Recommendations
            - message: str - Error message if success=False
            
        Example:
            {
                'success': True,
                'employee_id': 123,
                'employee_name': 'John Doe',
                'predicted_completion_rate': 0.85,
                'confidence': 0.8,
                'historical_average': 0.82,
                'task_count': 15,
                'insights': ['High performer', 'Improving over time'],
                'recommendations': ['Consider for challenging tasks']
            }
        """
        pass
    
    @abstractmethod
    def predict_optimal_task_assignment(
        self,
        task_category_id: int,
        available_employees: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Predict optimal employee assignment for a task category.
        
        Used by:
        - IntelligentAssignmentService to get assignment suggestions
        - Task assignment workflows
        
        Args:
            task_category_id: ID of the task category
            available_employees: Optional list of employee IDs to consider.
                                If None, considers all active employees.
                                
        Returns:
            Dict with keys:
            - success: bool - Whether prediction was successful
            - task_category_id: int - Category ID
            - total_candidates: int - Number of employees considered
            - valid_predictions: int - Number of valid predictions
            - top_performers: List[Dict] - Top 5 performers with predictions
            - recommendations: List[Dict] - Assignment recommendations
            - assignment_strategy: Dict - Strategy information
            - message: str - Error message if success=False
            
        Example:
            {
                'success': True,
                'task_category_id': 5,
                'total_candidates': 20,
                'valid_predictions': 18,
                'top_performers': [
                    {
                        'employee_id': 123,
                        'employee_name': 'John Doe',
                        'predicted_completion_rate': 0.92,
                        'confidence': 0.85
                    }
                ],
                'recommendations': [...]
            }
        """
        pass
    
    @abstractmethod
    def get_prediction(
        self,
        analysis_type: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generic AI prediction method for various analysis types.
        
        Used by:
        - UtilitiesService for evidence validation, task performance analysis
        - BaseModels for task/evidence validation
        - TaskHistoryAnalyzer for analysis enhancements
        
        Args:
            analysis_type: Type of analysis to perform. Common values:
                - 'evidence_validation'
                - 'task_performance_analysis'
                - 'payroll_prediction'
                - 'employee_analysis'
                - 'task_validation'
                - 'taskhistory_analysis_enhancement'
            input_data: Dict containing input data for the analysis
            session_id: Optional session ID for tracking
            
        Returns:
            Dict with keys (varies by analysis_type, but typically includes):
            - confidence_score: float - Confidence in the analysis (0.0-1.0)
            - recommendations: List[str] - AI-generated recommendations
            - model_used: str - Model identifier
            - Additional keys specific to analysis_type
            
        Example for 'evidence_validation':
            {
                'confidence_score': 0.85,
                'validation_passed': True,
                'recommendations': ['Evidence looks good'],
                'quality_score': 0.9,
                'model_used': 'gpt4_primary'
            }
        """
        pass
    
    @abstractmethod
    def predict_department_performance(
        self,
        department_name: str,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict department-level performance.
        
        Used by:
        - DepartmentOptimizationService
        - Analytics dashboards
        
        Args:
            department_name: Name of the department (e.g., 'IT', 'Finance')
            time_horizon_days: Number of days to predict ahead (default: 30)
            
        Returns:
            Dict with keys:
            - success: bool - Whether prediction was successful
            - department_name: str - Department name
            - time_horizon_days: int - Prediction horizon
            - total_employees: int - Number of employees in department
            - predicted_employees: int - Number with valid predictions
            - predicted_completion_rate: float - Average predicted rate
            - prediction_confidence: float - Average confidence
            - employee_predictions: List[Dict] - Individual predictions
            - insights: List[str] - Department-level insights
            - recommendations: List[str] - Recommendations
            - message: str - Error message if success=False
        """
        pass











