"""
Tests for GoToMeeting Phase 3 Implementation

Tests analytics dashboard, automated sync, and configurable mappings.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from ai_services.models import Meeting, MeetingAttendee, MeetingActivityMapping

User = get_user_model()


@pytest.mark.django_db
class AnalyticsDashboardTests(TestCase):
    """Test analytics dashboard"""
    
    def setUp(self):
        """Create test data"""
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='test123',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='test123')
        
        # Create test meetings
        for i in range(5):
            meeting = Meeting.objects.create(
                meeting_id=f'TEST{i}',
                topic=f'Test Meeting {i}',
                start_time=timezone.now() - timedelta(days=i),
                end_time=timezone.now() - timedelta(days=i) + timedelta(hours=1),
                duration_minutes=60,
            )
            
            # Add attendees
            MeetingAttendee.objects.create(
                meeting=meeting,
                attendee_name='User 1',
                attendee_email='user1@test.com',
                duration_minutes=50,
            )
    
    def test_dashboard_accessible(self):
        """Test dashboard loads for staff"""
        response = self.client.get('/getdata/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_shows_statistics(self):
        """Test dashboard displays correct statistics"""
        response = self.client.get('/getdata/analytics/dashboard/')
        
        # Should show 5 meetings
        self.assertContains(response, '5')


@pytest.mark.django_db
class ActivityMappingTests(TestCase):
    """Test configurable activity mapping"""
    
    def test_populate_mappings_command(self):
        """Test populate_meeting_mappings command"""
        from django.core.management import call_command
        
        # Run command
        call_command('populate_meeting_mappings')
        
        # Should have created 11 mappings
        count = MeetingActivityMapping.objects.count()
        self.assertGreaterEqual(count, 11)
        
        # Verify specific mapping
        pbr_mapping = MeetingActivityMapping.objects.get(meeting_id_pattern='708385093')
        self.assertEqual(pbr_mapping.activity_name, 'PBR sessions')


@pytest.mark.django_db
class DailySyncTests(TestCase):
    """Test automated daily sync"""
    
    @patch('ai_services.tasks.getmeetingresponse')
    @patch('ai_services.tasks.save_meeting_data')
    def test_daily_sync_task(self, mock_save, mock_fetch):
        """Test daily_meeting_sync_task runs successfully"""
        from ai_services.tasks import daily_meeting_sync_task
        
        # Mock API response
        mock_fetch.return_value = [
            {'meetingId': 'DAILY123', 'subject': 'Daily Sync Test'}
        ]
        
        # Run task
        result = daily_meeting_sync_task()
        
        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['meetings_count'], 1)


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

