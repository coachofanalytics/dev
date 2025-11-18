"""
Task Assignment Views with Intelligent Assignment Integration

Phase 1: AI-Assisted Assignment
Integrates intelligent_assignment_service into task creation workflow.
"""

import logging
from typing import Dict, Any, List, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from management.services.intelligent_assignment_service import IntelligentAssignmentService
from management.models import Task, TaskCategory, TaskHistory
from accounts.models import CustomerUser, TaskGroups
from management.utils import employee_group_level

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def get_intelligent_assignment_suggestions(request):
    """
    API endpoint to get intelligent task assignment suggestions.
    
    Phase 1 Requirement: AI-assisted assignment with confidence scores
    
    POST Parameters:
        category_id: Task category ID
        activity_name: Task activity name
        description: Task description (optional)
        group_id: Task group ID (optional)
        mxpoint: Maximum points (optional)
        mxearning: Maximum earning (optional)
        available_employee_ids: Comma-separated list of employee IDs (optional)
    
    Returns:
        JSON with assignment suggestions sorted by score
    """
    try:
        # Get parameters
        category_id = request.POST.get('category_id')
        activity_name = request.POST.get('activity_name')
        description = request.POST.get('description', '')
        group_id = request.POST.get('group_id')
        mxpoint = request.POST.get('mxpoint', 0)
        mxearning = request.POST.get('mxearning', 0)
        available_employee_ids = request.POST.get('available_employee_ids')
        
        if not category_id or not activity_name:
            return JsonResponse({
                'success': False,
                'message': 'category_id and activity_name are required',
                'suggestions': []
            }, status=400)
        
        # Prepare task data
        task_data = {
            'category_id': int(category_id),
            'activity_name': activity_name,
            'description': description,
            'group_id': int(group_id) if group_id else None,
            'mxpoint': float(mxpoint) if mxpoint else 0,
            'mxearning': float(mxearning) if mxearning else 0,
        }
        
        # Get available employees
        available_employees = None
        if available_employee_ids:
            try:
                available_employees = [int(eid.strip()) for eid in available_employee_ids.split(',')]
            except ValueError:
                logger.warning(f"Invalid employee IDs format: {available_employee_ids}")
        
        # Initialize service
        assignment_service = IntelligentAssignmentService()
        
        # Get assignment suggestions
        result = assignment_service.assign_task_optimally(task_data, available_employees)
        
        if not result.get('success'):
            return JsonResponse({
                'success': False,
                'message': result.get('message', 'Assignment failed'),
                'suggestions': []
            }, status=400)
        
        # Format response
        assignment = result.get('assignment', {})
        top_candidates = result.get('top_candidates', [])
        
        suggestions = []
        for candidate in top_candidates:
            suggestions.append({
                'employee_id': candidate['employee_id'],
                'employee_name': candidate['employee_name'],
                'total_score': round(candidate['total_score'], 3),
                'confidence': round(candidate['confidence'], 3),
                'predicted_completion_rate': round(candidate['predicted_completion_rate'], 3),
                'workload_score': round(candidate['workload_score'], 3),
                'skills_match': round(candidate['skills_match'], 3),
                'score_breakdown': candidate.get('score_breakdown', {})
            })
        
        response_data = {
            'success': True,
            'task_data': task_data,
            'best_match': {
                'employee_id': assignment.get('recommended_employee_id'),
                'employee_name': assignment.get('recommended_employee_name'),
                'total_score': round(assignment.get('total_score', 0), 3),
                'confidence': round(assignment.get('confidence', 0), 3),
                'reason': assignment.get('assignment_reason', '')
            } if assignment else None,
            'suggestions': suggestions,
            'total_candidates': result.get('total_candidates', 0),
            'valid_scores': result.get('valid_scores', 0),
            'assignment_strategy': result.get('assignment_strategy', {}),
            'workload_balance': result.get('workload_balance', {})
        }
        
        logger.info(f"Intelligent assignment suggestions generated for task: {activity_name}")
        
        return JsonResponse(response_data, status=200)
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid parameter: {str(e)}',
            'suggestions': []
        }, status=400)
    except Exception as e:
        logger.error(f"Error in get_intelligent_assignment_suggestions: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Internal server error: {str(e)}',
            'suggestions': []
        }, status=500)


def enhance_task_creation_with_intelligent_assignment(
    request,
    category_id: int,
    activity_name: str,
    description: str,
    group_id: int,
    mxpoint: float,
    mxearning: float,
    employee_ids: List[int]
) -> Dict[str, Any]:
    """
    Enhanced task creation that uses intelligent assignment to suggest optimal employees.
    
    This function can be called from newtaskcreation view to get assignment suggestions
    before creating tasks, or to validate employee selections.
    
    Returns:
        Dict with assignment suggestions and recommendations
    """
    try:
        # Prepare task data
        task_data = {
            'category_id': category_id,
            'activity_name': activity_name,
            'description': description,
            'group_id': group_id,
            'mxpoint': mxpoint,
            'mxearning': mxearning,
        }
        
        # Initialize service
        assignment_service = IntelligentAssignmentService()
        
        # Get assignment suggestions for all available employees
        result = assignment_service.assign_task_optimally(task_data, None)
        
        if not result.get('success'):
            logger.warning(f"Intelligent assignment failed: {result.get('message')}")
            return {
                'success': False,
                'message': result.get('message'),
                'suggestions': [],
                'recommended_employees': employee_ids  # Fallback to original selection
            }
        
        # Get top recommendations
        top_candidates = result.get('top_candidates', [])
        recommended_employee_ids = [c['employee_id'] for c in top_candidates[:len(employee_ids)]]
        
        # Compare selected employees with recommendations
        selected_scores = {}
        for emp_id in employee_ids:
            # Find score for this employee
            for candidate in top_candidates:
                if candidate['employee_id'] == emp_id:
                    selected_scores[emp_id] = {
                        'score': candidate['total_score'],
                        'confidence': candidate['confidence'],
                        'rank': top_candidates.index(candidate) + 1
                    }
                    break
        
        return {
            'success': True,
            'suggestions': top_candidates,
            'recommended_employees': recommended_employee_ids,
            'selected_employees': employee_ids,
            'selected_scores': selected_scores,
            'assignment': result.get('assignment'),
            'warnings': _generate_assignment_warnings(employee_ids, top_candidates)
        }
        
    except Exception as e:
        logger.error(f"Error in enhance_task_creation_with_intelligent_assignment: {e}")
        return {
            'success': False,
            'message': str(e),
            'suggestions': [],
            'recommended_employees': employee_ids
        }


def _generate_assignment_warnings(selected_employees: List[int], top_candidates: List[Dict]) -> List[str]:
    """Generate warnings if selected employees are not optimal."""
    warnings = []
    
    if not top_candidates:
        return warnings
    
    # Get top 3 recommended employee IDs
    top_3_ids = [c['employee_id'] for c in top_candidates[:3]]
    
    # Check if any selected employee is not in top recommendations
    for emp_id in selected_employees:
        if emp_id not in top_3_ids:
            # Find employee's rank
            for idx, candidate in enumerate(top_candidates):
                if candidate['employee_id'] == emp_id:
                    rank = idx + 1
                    if rank > 5:
                        warnings.append(
                            f"Employee {candidate.get('employee_name', emp_id)} is ranked #{rank} "
                            f"(score: {candidate['total_score']:.2f}). Consider top candidates."
                        )
                    break
    
    return warnings

