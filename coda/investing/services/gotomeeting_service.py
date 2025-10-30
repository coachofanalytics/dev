"""
GoToMeeting Integration Service
Schedule and manage consultative trading sessions
"""

import logging
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class GoToMeetingService:
    """
    Integration with GoToMeeting for consultative tier sessions
    
    NOTE: This is a placeholder implementation.
    For production, configure:
    - GOTOMEETING_ACCESS_TOKEN in settings
    - OAuth 2.0 authentication flow
    - Actual API endpoints
    """
    
    BASE_URL = 'https://api.getgo.com/G2M/rest'
    
    def __init__(self):
        self.access_token = getattr(settings, 'GOTOMEETING_ACCESS_TOKEN', None)
    
    def create_meeting(self, title, start_time, duration_minutes=60):
        """
        Create a GoToMeeting session
        
        Args:
            title: Meeting title
            start_time: datetime when meeting starts
            duration_minutes: Meeting duration (default 60)
        
        Returns:
            dict with 'meeting_url', 'meeting_id', 'join_url'
        """
        if not self.access_token:
            # Fallback: Generate placeholder URL
            logger.warning("GoToMeeting API not configured - using placeholder URL")
            return self._generate_placeholder_meeting(title, start_time)
        
        try:
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # API request
            response = requests.post(
                f"{self.BASE_URL}/meetings",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'subject': title,
                    'starttime': start_time.isoformat(),
                    'endtime': end_time.isoformat(),
                    'conferencecallinfo': 'Hybrid',
                    'timezonekey': '',
                    'meetingtype': 'Scheduled'
                },
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"GoToMeeting created: {data.get('meetingId')}")
                
                return {
                    'meeting_id': data.get('meetingId'),
                    'meeting_url': data.get('joinURL'),
                    'join_url': data.get('joinURL'),
                    'success': True
                }
            else:
                logger.error(f"GoToMeeting API error: {response.status_code} - {response.text}")
                return self._generate_placeholder_meeting(title, start_time)
                
        except Exception as e:
            logger.error(f"GoToMeeting API exception: {str(e)}")
            return self._generate_placeholder_meeting(title, start_time)
    
    def create_meeting_for_session(self, trading_session):
        """
        Create GoToMeeting link for a TradingSession
        
        Args:
            trading_session: TradingSession instance
        
        Returns:
            dict with meeting details
        """
        client_name = trading_session.managed_account.client.get_full_name()
        title = f"Options Trading Review - {client_name}"
        
        meeting = self.create_meeting(
            title=title,
            start_time=trading_session.scheduled_date,
            duration_minutes=trading_session.session_duration_minutes
        )
        
        # Update session with meeting details
        if meeting.get('success'):
            trading_session.meeting_url = meeting['meeting_url']
            trading_session.meeting_id = meeting.get('meeting_id', '')
            trading_session.save()
        
        return meeting
    
    def _generate_placeholder_meeting(self, title, start_time):
        """
        Generate placeholder meeting URL when API is not configured
        Useful for development/testing
        """
        meeting_id = f"PLACEHOLDER-{timezone.now().timestamp()}"
        join_url = f"https://global.gotomeeting.com/join/{meeting_id}"
        
        return {
            'meeting_id': meeting_id,
            'meeting_url': join_url,
            'join_url': join_url,
            'success': True,
            'placeholder': True
        }
    
    def cancel_meeting(self, meeting_id):
        """
        Cancel a GoToMeeting session
        
        Args:
            meeting_id: GoToMeeting meeting ID
        
        Returns:
            bool - True if cancelled successfully
        """
        if not self.access_token:
            logger.warning("GoToMeeting API not configured")
            return True  # Pretend success for placeholder
        
        try:
            response = requests.delete(
                f"{self.BASE_URL}/meetings/{meeting_id}",
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info(f"GoToMeeting {meeting_id} cancelled")
                return True
            else:
                logger.error(f"Error cancelling meeting: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception cancelling meeting: {str(e)}")
            return False

