"""
No-Op AI Service Adapter

Fallback implementation of AIServiceInterface that provides safe default behavior
when the ai_services app is not installed or unavailable.

This adapter ensures that management app can run standalone without crashing,
while gracefully degrading functionality when AI services are unavailable.
"""

import logging
from typing import Dict, List, Optional, Any

from shared_core.interfaces.ai_service import AIServiceInterface


logger = logging.getLogger(__name__)


class NoOpAIServiceAdapter(AIServiceInterface):
    """
    No-operation AI service adapter.
    
    Implements AIServiceInterface with safe defaults that indicate:
    - No AI predictions available
    - Low/zero confidence scores
    - Empty recommendations
    - Success=False with helpful messages
    
    This allows the management app to run without the ai_services app installed,
    while clearly indicating that AI features are unavailable.
    
    Usage:
        # In management services:
        try:
            from ai_services.adapters.ai_service_adapter import AIServiceAdapter
            ai_service = AIServiceAdapter()
        except ImportError:
            from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter
            ai_service = NoOpAIServiceAdapter()
    """
    
    def __init__(self):
        """Initialize the no-op adapter with logging."""
        self.logger = logger
        self.logger.info("NoOpAIServiceAdapter initialized - AI services unavailable")
    
    def predict_employee_performance(
        self,
        employee_id: int,
        task_category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Return safe default when AI services are unavailable.
        
        Returns a response indicating AI is unavailable, allowing the calling
        code to fall back to non-AI logic (e.g., historical averages).
        """
        self.logger.debug(
            f"NoOp: predict_employee_performance called for employee {employee_id}, "
            f"category {task_category_id}"
        )
        
        return {
            'success': False,
            'employee_id': employee_id,
            'employee_name': 'Unknown',
            'predicted_completion_rate': 0.0,
            'confidence': 0.0,
            'historical_average': 0.0,
            'task_count': 0,
            'insights': [],
            'recommendations': ['AI service unavailable - using historical data only'],
            'message': 'AI service not available. Install ai_services app for AI predictions.'
        }
    
    def predict_optimal_task_assignment(
        self,
        task_category_id: int,
        available_employees: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Return safe default when AI assignment suggestions are unavailable.
        
        Returns an empty result, allowing the calling code to use non-AI
        assignment logic (e.g., round-robin, random, or manual assignment).
        """
        self.logger.debug(
            f"NoOp: predict_optimal_task_assignment called for category {task_category_id}, "
            f"employees: {len(available_employees) if available_employees else 0}"
        )
        
        return {
            'success': False,
            'task_category_id': task_category_id,
            'total_candidates': len(available_employees) if available_employees else 0,
            'valid_predictions': 0,
            'top_performers': [],
            'recommendations': [],
            'assignment_strategy': {
                'strategy': 'no_ai_available',
                'confidence': 0.0,
                'avg_predicted_rate': 0.0
            },
            'message': 'AI service not available. Use manual or rule-based assignment.'
        }
    
    def get_prediction(
        self,
        analysis_type: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return safe default for generic AI predictions.
        
        Returns a response indicating AI is unavailable, with low confidence
        and empty recommendations. The calling code should handle this gracefully.
        """
        self.logger.debug(
            f"NoOp: get_prediction called for analysis_type={analysis_type}, "
            f"session_id={session_id}"
        )
        
        # Return structure varies by analysis_type, but common defaults:
        base_response = {
            'confidence_score': 0.0,
            'model_used': 'noop_fallback',
            'recommendations': [],
        }
        
        # Add type-specific defaults
        if analysis_type == 'evidence_validation':
            base_response.update({
                'validation_passed': True,  # Don't block on missing AI
                'quality_score': 0.5,
                'message': 'AI validation unavailable - manual review recommended'
            })
        elif analysis_type == 'task_performance_analysis':
            base_response.update({
                'performance_summary': 'Analysis unavailable',
                'predicted_completion_rate': 0.0,
            })
        elif analysis_type in ['task_validation', 'task_creation_analysis']:
            base_response.update({
                'validation_passed': True,  # Don't block task creation
                'message': 'AI validation unavailable'
            })
        elif analysis_type == 'payroll_prediction':
            base_response.update({
                'predicted_earnings': 0,
                'confidence_level': 0.0,
            })
        elif analysis_type == 'employee_analysis':
            base_response.update({
                'performance_summary': 'Analysis unavailable',
                'strengths': [],
                'improvement_areas': [],
            })
        else:
            # Generic fallback for unknown analysis types
            base_response['message'] = f'AI analysis unavailable for type: {analysis_type}'
        
        return base_response
    
    def predict_department_performance(
        self,
        department_name: str,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Return safe default for department performance predictions.
        
        Returns an empty result, allowing the calling code to use non-AI
        department analysis (e.g., historical averages, manual reports).
        """
        self.logger.debug(
            f"NoOp: predict_department_performance called for department={department_name}, "
            f"horizon={time_horizon_days} days"
        )
        
        return {
            'success': False,
            'department_name': department_name,
            'time_horizon_days': time_horizon_days,
            'total_employees': 0,
            'predicted_employees': 0,
            'predicted_completion_rate': 0.0,
            'prediction_confidence': 0.0,
            'employee_predictions': [],
            'insights': [],
            'recommendations': ['AI service unavailable - use manual department analysis'],
            'message': 'AI service not available for department predictions.'
        }











