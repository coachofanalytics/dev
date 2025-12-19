"""
No-Op Meeting Service Adapter

Fallback implementation of MeetingServiceInterface that provides safe default behavior
when the ai_services app is not installed or unavailable.

This adapter ensures that management app can run standalone without crashing,
while gracefully degrading meeting linking functionality when AI services are unavailable.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date

from shared_core.interfaces.meeting_service import MeetingServiceInterface


logger = logging.getLogger(__name__)


class NoOpMeetingServiceAdapter(MeetingServiceInterface):
    """
    No-operation meeting service adapter.
    
    Implements MeetingServiceInterface with safe defaults that indicate:
    - No meetings available
    - Empty lists instead of errors
    - None instead of crashing
    
    This allows the management app to run without the ai_services app installed,
    while clearly indicating that meeting linking features are unavailable.
    
    Usage:
        # In management services:
        try:
            from ai_services.adapters.meeting_service_adapter import MeetingServiceAdapter
            meeting_service = MeetingServiceAdapter()
        except ImportError:
            from shared_core.services.adapters.noop_meeting_adapter import NoOpMeetingServiceAdapter
            meeting_service = NoOpMeetingServiceAdapter()
    """
    
    def __init__(self):
        """Initialize the no-op adapter with logging."""
        self.logger = logger
        self.logger.info("NoOpMeetingServiceAdapter initialized - Meeting services unavailable")
    
    def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Return None when meeting services are unavailable.
        
        Returns None instead of raising an error, allowing calling code to
        handle the absence of meetings gracefully.
        """
        self.logger.debug(f"NoOp: get_meeting_by_id called for meeting_id={meeting_id}")
        return None
    
    def get_recent_meetings_for_user(
        self,
        user_id: int,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Return empty list when meeting services are unavailable.
        
        Returns empty list instead of crashing, allowing calling code to
        display "no meetings found" or skip meeting-related features.
        """
        self.logger.debug(
            f"NoOp: get_recent_meetings_for_user called for user_id={user_id}, "
            f"since={since}, limit={limit}"
        )
        return []
    
    def find_meeting_by_topic(
        self,
        topic: str,
        date_range: Optional[Tuple[date, date]] = None,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Return None when meeting services are unavailable.
        
        Returns None to indicate no matching meeting found, allowing calling
        code to fall back to other matching strategies or manual linking.
        """
        self.logger.debug(
            f"NoOp: find_meeting_by_topic called for topic={topic}, "
            f"date_range={date_range}, user_id={user_id}"
        )
        return None
    
    def find_exact_mapping(
        self,
        meeting_id_pattern: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return None when meeting mapping services are unavailable.
        
        Returns None to indicate no mapping found, allowing calling code to
        fall back to other matching strategies (keyword matching, historical patterns).
        """
        self.logger.debug(
            f"NoOp: find_exact_mapping called for pattern={meeting_id_pattern}"
        )
        return None
    
    def get_meetings_in_date_range(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Return empty list when meeting services are unavailable.
        
        Returns empty list instead of crashing, allowing calling code to
        display empty statistics or skip meeting-related analytics.
        """
        self.logger.debug(
            f"NoOp: get_meetings_in_date_range called for "
            f"start_date={start_date}, end_date={end_date}, user_id={user_id}"
        )
        return []











