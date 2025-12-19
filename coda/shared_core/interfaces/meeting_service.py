"""
Meeting Service Interface

Abstract interface for meeting/evidence linking services used by management app.
Defines the contract for finding meetings, mapping them to tasks, and linking evidence.

This interface is implemented by:
- MeetingServiceAdapter (in ai_services app) - wraps GotoMeetings and MeetingActivityMapping
- NoOpMeetingServiceAdapter (in shared_core) - safe fallback when ai_services is not installed
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date


class MeetingServiceInterface(ABC):
    """
    Abstract interface for meeting services.
    
    This interface defines what management needs for meeting-to-task linking
    and evidence automation, without depending on concrete GotoMeetings models.
    
    All methods return dicts/list of dicts, never Django models, to ensure
    loose coupling between apps.
    """
    
    @abstractmethod
    def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting by its ID.
        
        Used by:
        - MeetingLinkingService to get meeting details for linking
        - Meeting review views to display meeting information
        
        Args:
            meeting_id: Unique meeting identifier (e.g., GoToMeeting ID)
            
        Returns:
            Dict with meeting details or None if not found:
            - meeting_id: str - Meeting ID
            - meeting_topic: str - Meeting topic/title
            - start_time: Optional[datetime] - Meeting start time
            - recording_url: Optional[str] - URL to recording
            - join_link: Optional[str] - URL to join meeting
            - created_at: Optional[datetime] - When meeting was created
            - Other meeting metadata
            
        Example:
            {
                'meeting_id': '123456789',
                'meeting_topic': 'Daily Standup',
                'start_time': datetime(...),
                'recording_url': 'https://...',
                'join_link': 'https://...',
                'created_at': datetime(...)
            }
        """
        pass
    
    @abstractmethod
    def get_recent_meetings_for_user(
        self,
        user_id: int,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent meetings for a user.
        
        Used by:
        - Meeting review dashboards
        - Meeting linking workflows
        
        Args:
            user_id: ID of the user to get meetings for
            since: Optional datetime - Only return meetings after this date
            limit: Maximum number of meetings to return
            
        Returns:
            List of meeting dicts (same structure as get_meeting_by_id)
            Ordered by start_time or created_at (most recent first)
        """
        pass
    
    @abstractmethod
    def find_meeting_by_topic(
        self,
        topic: str,
        date_range: Optional[Tuple[date, date]] = None,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a meeting by topic/keywords.
        
        Used by:
        - MeetingLinkingService._keyword_match() strategy
        - Meeting search functionality
        
        Args:
            topic: Meeting topic/title to search for (case-insensitive partial match)
            date_range: Optional tuple (start_date, end_date) to limit search
            user_id: Optional user ID to filter meetings
            
        Returns:
            Best matching meeting dict or None if not found
        """
        pass
    
    @abstractmethod
    def find_exact_mapping(
        self,
        meeting_id_pattern: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find exact mapping between meeting ID pattern and activity.
        
        Used by:
        - MeetingLinkingService._check_exact_mapping() strategy
        - MeetingActivityMapping lookups
        
        Args:
            meeting_id_pattern: Meeting ID pattern to match (supports wildcards)
            
        Returns:
            Dict with mapping details or None if not found:
            - activity_name: str - Task activity name this meeting maps to
            - min_duration_minutes: Optional[int] - Minimum duration required
            - task_points: Optional[float] - Points awarded for this meeting
            - meeting_id_pattern: str - Pattern that matched
            
        Example:
            {
                'activity_name': 'DAF Sessions',
                'min_duration_minutes': 30,
                'task_points': 10.0,
                'meeting_id_pattern': 'daily-standup-*'
            }
        """
        pass
    
    @abstractmethod
    def get_meetings_in_date_range(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all meetings in a date range.
        
        Used by:
        - Meeting linking statistics
        - Meeting review dashboards with date filters
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            user_id: Optional user ID to filter meetings
            
        Returns:
            List of meeting dicts in the date range
        """
        pass











