"""
Meeting Auto-Linking Service

Phase 1: Evidence Automation
Intelligent matching of GoToMeeting meetings to tasks using ML/heuristic algorithms.

Target: ≥80% auto-link rate with confidence scoring
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, F, Max
from django.contrib.auth import get_user_model

from management.models import Task, TaskHistory, TaskLinks, TaskCategory
from accounts.models import CustomerUser
from ai_services.models import GotoMeetings, MeetingActivityMapping

logger = logging.getLogger(__name__)
User = get_user_model()


class MeetingLinkingService:
    """
    Service for intelligent meeting-to-task linking.
    
    Uses multiple strategies:
    1. Exact mapping (MeetingActivityMapping model)
    2. Keyword matching (meeting topic → task activity)
    3. Historical patterns (user's past meeting-task links)
    4. Category matching (meeting type → task category)
    5. Participant-based matching
    """
    
    def __init__(self):
        self.logger = logger
        self.min_confidence_threshold = 0.6  # 60% confidence minimum for auto-link
        self.auto_link_threshold = 0.8  # 80% confidence for automatic linking
        
    def link_meeting_to_tasks(
        self,
        meeting: GotoMeetings,
        attendee: CustomerUser,
        attendee_duration: int
    ) -> Dict[str, Any]:
        """
        Intelligently link a meeting to tasks for a specific attendee.
        
        Args:
            meeting: GotoMeetings instance
            attendee: CustomerUser who attended
            attendee_duration: Duration in minutes
            
        Returns:
            Dict with linking results and confidence scores
        """
        try:
            self.logger.info(f"Linking meeting {meeting.meeting_id} for {attendee.username}")
            
            # Get all potential task matches with confidence scores
            matches = self._find_task_matches(meeting, attendee, attendee_duration)
            
            if not matches:
                return {
                    'success': False,
                    'message': 'No task matches found',
                    'matches': [],
                    'auto_linked': False
                }
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            best_match = matches[0]
            
            # Determine if we should auto-link
            auto_link = best_match['confidence'] >= self.auto_link_threshold
            
            result = {
                'success': True,
                'meeting_id': meeting.meeting_id,
                'meeting_topic': meeting.meeting_topic,
                'attendee_id': attendee.id,
                'attendee_name': attendee.username,
                'attendee_duration': attendee_duration,
                'best_match': best_match,
                'all_matches': matches[:5],  # Top 5 matches
                'auto_linked': auto_link,
                'confidence': best_match['confidence'],
                'requires_review': best_match['confidence'] < self.auto_link_threshold
            }
            
            # Auto-link if confidence is high enough
            if auto_link:
                link_result = self._create_task_link(meeting, attendee, best_match['task'])
                result['link_created'] = link_result.get('success', False)
                result['task_link_id'] = link_result.get('task_link_id')
                
                # Award points if configured
                if best_match['task'].activity_name.lower() not in ['job support', 'job_support', 'jobsupport']:
                    self._award_task_points(best_match['task'], attendee)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error linking meeting to tasks: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Linking failed: {str(e)}',
                'matches': [],
                'auto_linked': False
            }
    
    def _find_task_matches(
        self,
        meeting: GotoMeetings,
        attendee: CustomerUser,
        attendee_duration: int
    ) -> List[Dict[str, Any]]:
        """Find all potential task matches with confidence scores."""
        matches = []
        
        # Strategy 1: Exact mapping (highest confidence)
        exact_match = self._check_exact_mapping(meeting)
        if exact_match:
            task = self._get_task_by_activity(exact_match['activity_name'], attendee)
            if task:
                matches.append({
                    'task': task,
                    'confidence': 0.95,  # Very high confidence for exact mapping
                    'strategy': 'exact_mapping',
                    'reason': f"Exact mapping: {exact_match['activity_name']}"
                })
        
        # Strategy 2: Keyword matching
        keyword_matches = self._keyword_match(meeting.meeting_topic, attendee)
        matches.extend(keyword_matches)
        
        # Strategy 3: Historical patterns
        historical_matches = self._historical_pattern_match(meeting, attendee)
        matches.extend(historical_matches)
        
        # Strategy 4: Category-based matching
        category_matches = self._category_match(meeting, attendee)
        matches.extend(category_matches)
        
        # Remove duplicates and combine confidence scores
        unique_matches = self._deduplicate_matches(matches)
        
        return unique_matches
    
    def _check_exact_mapping(self, meeting: GotoMeetings) -> Optional[Dict[str, Any]]:
        """Check if meeting has exact mapping in MeetingActivityMapping."""
        try:
            # Try exact meeting ID match
            mapping = MeetingActivityMapping.objects.filter(
                meeting_id_pattern=meeting.meeting_id,
                is_active=True
            ).first()
            
            if mapping:
                return {
                    'activity_name': mapping.activity_name,
                    'min_duration': mapping.min_duration_minutes,
                    'points': mapping.task_points
                }
            
            # Try pattern matching (if pattern contains wildcards)
            mappings = MeetingActivityMapping.objects.filter(is_active=True)
            for mapping in mappings:
                if self._pattern_match(meeting.meeting_id, mapping.meeting_id_pattern):
                    return {
                        'activity_name': mapping.activity_name,
                        'min_duration': mapping.min_duration_minutes,
                        'points': mapping.task_points
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error checking exact mapping: {e}")
            return None
    
    def _keyword_match(self, meeting_topic: str, attendee: CustomerUser) -> List[Dict[str, Any]]:
        """Match meeting topic to task activities using keyword matching."""
        matches = []
        
        if not meeting_topic:
            return matches
        
        # Normalize meeting topic
        topic_lower = meeting_topic.lower()
        
        # Get all active tasks for this employee
        employee_tasks = Task.objects.filter(
            employee=attendee,
            is_active=True
        ).select_related('category')
        
        # Keyword scoring
        for task in employee_tasks:
            activity_lower = task.activity_name.lower()
            confidence = 0.0
            
            # Exact match
            if activity_lower == topic_lower:
                confidence = 0.9
            # Contains match
            elif activity_lower in topic_lower or topic_lower in activity_lower:
                confidence = 0.7
            # Word overlap
            else:
                topic_words = set(re.findall(r'\w+', topic_lower))
                activity_words = set(re.findall(r'\w+', activity_lower))
                overlap = len(topic_words & activity_words)
                total_words = len(topic_words | activity_words)
                
                if total_words > 0:
                    confidence = (overlap / total_words) * 0.6
            
            if confidence >= 0.4:  # Minimum threshold
                matches.append({
                    'task': task,
                    'confidence': confidence,
                    'strategy': 'keyword_match',
                    'reason': f"Keyword match: '{meeting_topic}' → '{task.activity_name}'"
                })
        
        return matches
    
    def _historical_pattern_match(
        self,
        meeting: GotoMeetings,
        attendee: CustomerUser
    ) -> List[Dict[str, Any]]:
        """Match based on historical meeting-task links."""
        matches = []
        
        try:
            # Get user's past meeting-task links
            past_links = TaskLinks.objects.filter(
                added_by=attendee,
                is_active=True
            ).select_related('task').order_by('-created_at')[:50]
            
            if not past_links:
                return matches
            
            # Find patterns: meetings with similar topics linked to same tasks
            topic_lower = meeting.meeting_topic.lower()
            
            # Group by task
            task_link_counts = {}
            for link in past_links:
                task_id = link.task.id
                if task_id not in task_link_counts:
                    task_link_counts[task_id] = {
                        'task': link.task,
                        'count': 0,
                        'similar_topics': []
                    }
                
                # Check if past link had similar topic
                link_name_lower = (link.link_name or '').lower()
                if self._similarity_score(topic_lower, link_name_lower) > 0.5:
                    task_link_counts[task_id]['count'] += 1
                    task_link_counts[task_id]['similar_topics'].append(link.link_name)
            
            # Calculate confidence based on frequency
            for task_id, data in task_link_counts.items():
                if data['count'] > 0:
                    # More historical links = higher confidence
                    confidence = min(0.85, 0.5 + (data['count'] * 0.1))
                    
                    matches.append({
                        'task': data['task'],
                        'confidence': confidence,
                        'strategy': 'historical_pattern',
                        'reason': f"Historical pattern: {data['count']} similar links found"
                    })
            
        except Exception as e:
            self.logger.warning(f"Error in historical pattern matching: {e}")
        
        return matches
    
    def _category_match(
        self,
        meeting: GotoMeetings,
        attendee: CustomerUser
    ) -> List[Dict[str, Any]]:
        """Match based on meeting category/type."""
        matches = []
        
        # Common meeting type patterns
        meeting_type_patterns = {
            'general meeting': 'General Meeting',
            'standup': 'DAF Sessions',
            'daf': 'DAF Sessions',
            'bog': 'BOG',
            'bi session': 'BI Sessions',
            'project': 'Project',
            'web session': 'web sessions',
            'training': 'Training',
            'review': 'Review'
        }
        
        topic_lower = (meeting.meeting_topic or '').lower()
        
        for pattern, activity_name in meeting_type_patterns.items():
            if pattern in topic_lower:
                task = self._get_task_by_activity(activity_name, attendee)
                if task:
                    matches.append({
                        'task': task,
                        'confidence': 0.75,
                        'strategy': 'category_match',
                        'reason': f"Category match: '{pattern}' → '{activity_name}'"
                    })
        
        return matches
    
    def _get_task_by_activity(
        self,
        activity_name: str,
        attendee: CustomerUser
    ) -> Optional[Task]:
        """Get task by activity name for specific employee."""
        try:
            # First try employee-specific task
            task = Task.objects.filter(
                employee=attendee,
                activity_name=activity_name,
                is_active=True
            ).first()
            
            if task:
                return task
            
            # Fallback to any task with this activity
            task = Task.objects.filter(
                activity_name=activity_name,
                is_active=True
            ).first()
            
            return task
            
        except Exception as e:
            self.logger.warning(f"Error getting task by activity: {e}")
            return None
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches and combine confidence scores."""
        unique_matches = {}
        
        for match in matches:
            task_id = match['task'].id
            
            if task_id not in unique_matches:
                unique_matches[task_id] = match
            else:
                # Combine confidence scores (take maximum)
                existing = unique_matches[task_id]
                if match['confidence'] > existing['confidence']:
                    unique_matches[task_id] = match
                # Or average if close
                elif abs(match['confidence'] - existing['confidence']) < 0.1:
                    unique_matches[task_id]['confidence'] = (
                        existing['confidence'] + match['confidence']
                    ) / 2
                    unique_matches[task_id]['reason'] += f" + {match['reason']}"
        
        return list(unique_matches.values())
    
    def _pattern_match(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (supports wildcards)."""
        if '*' in pattern or '?' in pattern:
            # Convert to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            return bool(re.match(regex_pattern, text, re.IGNORECASE))
        return text.lower() == pattern.lower()
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate simple similarity score between two strings."""
        if not str1 or not str2:
            return 0.0
        
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _create_task_link(
        self,
        meeting: GotoMeetings,
        attendee: CustomerUser,
        task: Task
    ) -> Dict[str, Any]:
        """Create TaskLink record for meeting-task connection."""
        try:
            from django.utils.text import slugify
            
            task_link, created = TaskLinks.objects.get_or_create(
                task=task,
                added_by=attendee,
                link_name=slugify(f"{meeting.meeting_topic}_{attendee.username}"),
                defaults={
                    'description': f"Attended meeting '{meeting.meeting_topic}' (ID: {meeting.meeting_id})",
                    'link': meeting.recording or '',
                    'linkpassword': 'No Password Needed',
                    'is_active': True,
                    'is_featured': True,
                }
            )
            
            return {
                'success': True,
                'created': created,
                'task_link_id': task_link.id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating task link: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _award_task_points(self, task: Task, attendee: CustomerUser):
        """Award task points for meeting attendance."""
        try:
            if task.point < task.mxpoint:
                task.point = min(task.point + 1, task.mxpoint)
                task.save(update_fields=['point'])
                self.logger.info(f"Awarded point to {attendee.username} for task {task.activity_name}")
        except Exception as e:
            self.logger.warning(f"Error awarding task points: {e}")
    
    def get_linking_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics on meeting linking performance.
        
        Phase 1 Requirement: Track auto-link rate (target: ≥80%)
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Get all meetings in period
            meetings = GotoMeetings.objects.filter(created_at__gte=cutoff_date)
            total_meetings = meetings.count()
            
            # Get linked meetings
            linked_meetings = TaskLinks.objects.filter(
                created_at__gte=cutoff_date,
                description__icontains='Attended meeting'
            )
            linked_count = linked_meetings.count()
            
            # Calculate auto-link rate
            auto_link_rate = (linked_count / total_meetings * 100) if total_meetings > 0 else 0
            
            return {
                'total_meetings': total_meetings,
                'linked_meetings': linked_count,
                'auto_link_rate': round(auto_link_rate, 2),
                'target_met': auto_link_rate >= 80,
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting linking statistics: {e}")
            return {
                'total_meetings': 0,
                'linked_meetings': 0,
                'auto_link_rate': 0,
                'target_met': False,
                'error': str(e)
            }

