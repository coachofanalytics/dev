"""
Meeting Link Review Views

Phase 1: Evidence Automation - Manual Review UI
Allows users to review, approve, or override meeting-to-task links.
"""

import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator

from management.models import TaskLinks, Task
from accounts.models import CustomerUser
from ai_services.models import GotoMeetings
from management.services.meeting_linking_service import MeetingLinkingService

logger = logging.getLogger(__name__)


@login_required
def meeting_link_review_dashboard(request):
    """
    Dashboard for reviewing meeting-to-task links.
    
    Shows:
    - Pending links requiring review (confidence < 80%)
    - Recently auto-linked meetings
    - Statistics on linking performance
    """
    try:
        linking_service = MeetingLinkingService()
        
        # Get statistics
        stats = linking_service.get_linking_statistics(days=30)
        
        # Get pending reviews (TaskLinks with low confidence or manual flag)
        # For now, we'll show recent links that might need review
        recent_links = TaskLinks.objects.filter(
            description__icontains='Attended meeting',
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('task', 'added_by', 'task__category').order_by('-created_at')[:50]
        
        # Paginate
        paginator = Paginator(recent_links, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'recent_links': page_obj,
            'stats': stats,
            'total_pending': recent_links.count(),
            'auto_link_rate': stats.get('auto_link_rate', 0),
            'target_met': stats.get('target_met', False)
        }
        
        return render(request, 'management/daf/meeting_link_review.html', context)
        
    except Exception as e:
        logger.error(f"Error in meeting_link_review_dashboard: {e}", exc_info=True)
        messages.error(request, f"Error loading review dashboard: {str(e)}")
        return redirect('management:management-home')


@login_required
@require_http_methods(["POST"])
def approve_meeting_link(request, link_id):
    """Approve a meeting-to-task link."""
    try:
        link = get_object_or_404(TaskLinks, id=link_id)
        
        # Mark as approved (we can add an approved_by field later)
        link.is_featured = True  # Using existing field as approval indicator
        link.save(update_fields=['is_featured'])
        
        logger.info(f"Meeting link {link_id} approved by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Link approved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error approving meeting link: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def override_meeting_link(request, link_id):
    """Override a meeting link to a different task."""
    try:
        link = get_object_or_404(TaskLinks, id=link_id)
        new_task_id = request.POST.get('task_id')
        
        if not new_task_id:
            return JsonResponse({
                'success': False,
                'message': 'task_id is required'
            }, status=400)
        
        new_task = get_object_or_404(Task, id=new_task_id)
        
        # Update link to new task
        link.task = new_task
        link.save(update_fields=['task'])
        
        logger.info(f"Meeting link {link_id} overridden to task {new_task_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Link overridden successfully',
            'new_task_id': new_task_id,
            'new_task_name': new_task.activity_name
        })
        
    except Exception as e:
        logger.error(f"Error overriding meeting link: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reject_meeting_link(request, link_id):
    """Reject/remove a meeting-to-task link."""
    try:
        link = get_object_or_404(TaskLinks, id=link_id)
        
        # Deactivate the link
        link.is_active = False
        link.save(update_fields=['is_active'])
        
        logger.info(f"Meeting link {link_id} rejected by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Link rejected successfully'
        })
        
    except Exception as e:
        logger.error(f"Error rejecting meeting link: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_meeting_link_suggestions(request, link_id):
    """Get alternative task suggestions for a meeting link."""
    try:
        link = get_object_or_404(TaskLinks, id=link_id)
        
        # Get meeting info from link description
        # This is a simplified version - in production, we'd have a proper Meeting model
        linking_service = MeetingLinkingService()
        
        # Get user's tasks as alternatives
        user_tasks = Task.objects.filter(
            employee=link.added_by,
            is_active=True
        ).exclude(id=link.task.id).select_related('category')[:10]
        
        suggestions = []
        for task in user_tasks:
            suggestions.append({
                'task_id': task.id,
                'activity_name': task.activity_name,
                'category': task.category.title if task.category else 'General',
                'description': task.description
            })
        
        return JsonResponse({
            'success': True,
            'current_task': {
                'id': link.task.id,
                'activity_name': link.task.activity_name
            },
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error getting meeting link suggestions: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}',
            'suggestions': []
        }, status=500)

