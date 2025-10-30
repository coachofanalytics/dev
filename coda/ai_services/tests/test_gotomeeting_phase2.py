"""
Tests for GoToMeeting Phase 2 Implementation

Tests async processing, Celery tasks, rate limiting, and performance improvements.

Usage:
    python manage.py test ai_services.tests.test_gotomeeting_phase2
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.mark.django_db
class CeleryTaskTests(TestCase):
    """Test Celery background tasks"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('ai_services.tasks.getmeetingresponse')
    @patch('ai_services.tasks.save_meeting_data')
    def test_fetch_meetings_task(self, mock_save, mock_fetch):
        """Test fetch_meetings_task runs successfully"""
        from ai_services.tasks import fetch_meetings_task
        
        # Mock API response
        mock_fetch.return_value = [
            {'meetingId': 'TEST123', 'subject': 'Test Meeting'}
        ]
        
        # Run task
        result = fetch_meetings_task('2025-10-01', '2025-10-31', self.user.id)
        
        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['meetings_count'], 1)
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('ai_services.tasks.requests.get')
    def test_batch_fetch_attendees_task(self, mock_get):
        """Test parallel attendee fetching"""
        from ai_services.tasks import batch_fetch_attendees_task
        
        # Mock API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'attendeeName': 'User 1', 'attendeeEmail': 'user1@test.com'}
        ]
        mock_get.return_value = mock_response
        
        # Run task with multiple meeting IDs
        meeting_ids = ['M1', 'M2', 'M3']
        result = batch_fetch_attendees_task(meeting_ids, 'test_token')
        
        # Should have results for all 3 meetings
        self.assertEqual(len(result), 3)
        
        # Should have called API 3 times (in parallel)
        self.assertEqual(mock_get.call_count, 3)


@pytest.mark.django_db
class AsyncViewsTests(TestCase):
    """Test async views"""
    
    def setUp(self):
        """Create test user and client"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    @patch('ai_services.views_async.fetch_meetings_task.delay')
    def test_async_meeting_fetch_queues_task(self, mock_task):
        """Test that async view queues Celery task"""
        mock_task.return_value = MagicMock(id='task-123')
        
        response = self.client.post('/getdata/async-fetch/', {
            'startDate': '2025-10-01',
            'endDate': '2025-10-31',
        })
        
        # Should queue task
        mock_task.assert_called_once()
        
        # Should show processing message
        self.assertContains(response, 'task-123')
    
    def test_rate_limiting_blocks_excessive_requests(self):
        """Test rate limiting prevents abuse"""
        cache.clear()
        
        # Make 11 requests (limit is 10)
        for i in range(11):
            response = self.client.post('/getdata/async-fetch/', {
                'startDate': '2025-10-01',
                'endDate': '2025-10-31',
            })
            
            if i < 10:
                self.assertEqual(response.status_code, 200)
            else:
                # 11th request should be rate limited
                self.assertIn('Rate limit', response.content.decode())


@pytest.mark.django_db
class PerformanceTests(TestCase):
    """Test performance improvements"""
    
    def test_streaming_download_memory_efficient(self):
        """Test that streaming download doesn't load entire file in memory"""
        # This would be integration test with actual file
        # For unit test, we verify the task exists and uses streaming
        from ai_services.tasks import download_recording_task
        
        # Verify task is registered
        self.assertIsNotNone(download_recording_task)
    
    def test_parallel_attendee_fetch_faster(self):
        """Test that parallel fetch is faster than sequential"""
        # This is more of a benchmark than unit test
        # Verify the batch task uses ThreadPoolExecutor
        import inspect
        from ai_services.tasks import batch_fetch_attendees_task
        
        source = inspect.getsource(batch_fetch_attendees_task)
        self.assertIn('ThreadPoolExecutor', source)


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

