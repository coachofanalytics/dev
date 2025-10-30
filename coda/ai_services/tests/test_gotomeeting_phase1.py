"""
Tests for GoToMeeting Phase 1 Implementation

Tests the normalized Meeting + MeetingAttendee models, token encryption,
and data migration functionality.

Usage:
    python manage.py test ai_services.tests.test_gotomeeting_phase1
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from ai_services.models import (
    Meeting, MeetingAttendee, OAuthToken, MeetingActivityMapping, GotoMeetings
)
from ai_services.services.token_encryption_service import (
    TokenEncryptionService, OAuthTokenManager
)
from accounts.models import CustomerUser


@pytest.mark.django_db
class MeetingModelTests(TestCase):
    """Test the normalized Meeting model"""
    
    def setUp(self):
        """Create test data"""
        self.meeting = Meeting.objects.create(
            meeting_id='TEST123',
            topic='Test Meeting',
            meeting_type='General Meeting',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
            is_recorded=True,
        )
    
    def test_meeting_creation(self):
        """Test meeting can be created"""
        self.assertEqual(self.meeting.meeting_id, 'TEST123')
        self.assertEqual(self.meeting.topic, 'Test Meeting')
        self.assertEqual(self.meeting.duration_minutes, 60)
    
    def test_unique_meeting_id(self):
        """Test meeting_id must be unique"""
        with self.assertRaises(Exception):
            Meeting.objects.create(
                meeting_id='TEST123',  # Duplicate!
                topic='Another Meeting',
                start_time=timezone.now(),
                end_time=timezone.now(),
            )
    
    def test_attendee_count_property(self):
        """Test attendee_count computed property"""
        self.assertEqual(self.meeting.attendee_count, 0)
        
        # Add 3 attendees
        for i in range(3):
            MeetingAttendee.objects.create(
                meeting=self.meeting,
                attendee_email=f'user{i}@test.com',
                attendee_name=f'User {i}',
                duration_minutes=30,
            )
        
        self.assertEqual(self.meeting.attendee_count, 3)
    
    def test_average_attendance_duration(self):
        """Test average_attendance_duration computed property"""
        # Add attendees with different durations
        MeetingAttendee.objects.create(
            meeting=self.meeting,
            attendee_email='user1@test.com',
            attendee_name='User 1',
            duration_minutes=60,
        )
        MeetingAttendee.objects.create(
            meeting=self.meeting,
            attendee_email='user2@test.com',
            attendee_name='User 2',
            duration_minutes=30,
        )
        
        # Average: (60 + 30) / 2 = 45
        self.assertEqual(self.meeting.average_attendance_duration, 45.0)


@pytest.mark.django_db
class MeetingAttendeeModelTests(TestCase):
    """Test the MeetingAttendee model"""
    
    def setUp(self):
        """Create test data"""
        self.meeting = Meeting.objects.create(
            meeting_id='TEST456',
            topic='Test Meeting',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration_minutes=60,
        )
        
        self.attendee = MeetingAttendee.objects.create(
            meeting=self.meeting,
            attendee_email='test@example.com',
            attendee_name='Test User',
            duration_minutes=30,
        )
    
    def test_attendee_creation(self):
        """Test attendee can be created"""
        self.assertEqual(self.attendee.attendee_email, 'test@example.com')
        self.assertEqual(self.attendee.duration_minutes, 30)
    
    def test_unique_constraint(self):
        """Test unique constraint on meeting + email"""
        with self.assertRaises(Exception):
            MeetingAttendee.objects.create(
                meeting=self.meeting,
                attendee_email='test@example.com',  # Duplicate!
                attendee_name='Another Name',
                duration_minutes=20,
            )
    
    def test_attendance_percentage(self):
        """Test attendance_percentage property"""
        # Attended 30 min of 60 min meeting = 50%
        self.assertEqual(self.attendee.attendance_percentage, 50.0)
    
    def test_qualifies_for_points(self):
        """Test qualifies_for_points property"""
        # 30 minutes > 3 minutes = qualifies
        self.assertTrue(self.attendee.qualifies_for_points)
        
        # Create attendee with < 3 minutes
        short_attendee = MeetingAttendee.objects.create(
            meeting=self.meeting,
            attendee_email='short@example.com',
            attendee_name='Short Attendee',
            duration_minutes=2,
        )
        self.assertFalse(short_attendee.qualifies_for_points)


@pytest.mark.django_db
class OAuthTokenModelTests(TestCase):
    """Test the OAuthToken model"""
    
    def setUp(self):
        """Create test token"""
        self.token = OAuthToken.objects.create(
            service_name='gotomeeting',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at=timezone.now() + timedelta(hours=1),
        )
    
    def test_token_creation(self):
        """Test token can be created"""
        self.assertEqual(self.token.service_name, 'gotomeeting')
        self.assertTrue(self.token.is_valid)
    
    def test_is_expired_property(self):
        """Test is_expired property"""
        # Token expires in 1 hour - not expired
        self.assertFalse(self.token.is_expired)
        
        # Create expired token
        expired_token = OAuthToken.objects.create(
            service_name='expired_service',
            access_token='expired',
            refresh_token='expired',
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(expired_token.is_expired)
    
    def test_needs_refresh_property(self):
        """Test needs_refresh property (expires in < 5 min)"""
        # Token expires in 1 hour - doesn't need refresh yet
        self.assertFalse(self.token.needs_refresh)
        
        # Create token expiring in 2 minutes
        soon_token = OAuthToken.objects.create(
            service_name='soon_service',
            access_token='soon',
            refresh_token='soon',
            expires_at=timezone.now() + timedelta(minutes=2),
        )
        self.assertTrue(soon_token.needs_refresh)


@pytest.mark.django_db
class TokenEncryptionServiceTests(TestCase):
    """Test the token encryption service"""
    
    def setUp(self):
        """Initialize encryption service"""
        self.service = TokenEncryptionService()
    
    def test_encrypt_decrypt(self):
        """Test basic encryption/decryption"""
        original_token = "my_secret_access_token_12345"
        
        # Encrypt
        encrypted = self.service.encrypt_token(original_token)
        self.assertNotEqual(encrypted, original_token)
        
        # Decrypt
        decrypted = self.service.decrypt_token(encrypted)
        self.assertEqual(decrypted, original_token)
    
    def test_encrypt_empty_token_fails(self):
        """Test encrypting empty token raises error"""
        with self.assertRaises(ValueError):
            self.service.encrypt_token("")
        
        with self.assertRaises(ValueError):
            self.service.encrypt_token(None)
    
    def test_is_token_valid(self):
        """Test token validation"""
        token = "test_token_123"
        encrypted = self.service.encrypt_token(token)
        
        # Valid encrypted token
        self.assertTrue(self.service.is_token_valid(encrypted))
        
        # Invalid token (tampered)
        self.assertFalse(self.service.is_token_valid("tampered_data"))


@pytest.mark.django_db
class OAuthTokenManagerTests(TestCase):
    """Test the OAuth token manager"""
    
    def setUp(self):
        """Initialize token manager"""
        self.manager = OAuthTokenManager('test_service')
    
    def test_save_tokens(self):
        """Test saving tokens to database"""
        access_token = "test_access_token"
        refresh_token = "test_refresh_token"
        
        token_obj = self.manager.save_tokens(access_token, refresh_token, expires_in=3600)
        
        self.assertEqual(token_obj.service_name, 'test_service')
        self.assertTrue(token_obj.is_valid)
        self.assertNotEqual(token_obj.access_token, access_token)  # Should be encrypted
    
    def test_get_access_token(self):
        """Test retrieving access token from database"""
        access_token = "test_access_token"
        refresh_token = "test_refresh_token"
        
        # Save tokens
        self.manager.save_tokens(access_token, refresh_token)
        
        # Retrieve token
        retrieved = self.manager.get_access_token()
        self.assertEqual(retrieved, access_token)
    
    def test_get_token_when_none_exists(self):
        """Test retrieving token when none exists"""
        manager = OAuthTokenManager('nonexistent_service')
        token = manager.get_access_token()
        self.assertIsNone(token)
    
    def test_invalidate_tokens(self):
        """Test invalidating tokens"""
        self.manager.save_tokens("access", "refresh")
        
        # Invalidate
        result = self.manager.invalidate_tokens()
        self.assertTrue(result)
        
        # Token should be invalid now
        token = self.manager.get_access_token()
        self.assertIsNone(token)


@pytest.mark.django_db
class MeetingActivityMappingTests(TestCase):
    """Test the MeetingActivityMapping model"""
    
    def test_mapping_creation(self):
        """Test creating activity mapping"""
        mapping = MeetingActivityMapping.objects.create(
            meeting_id_pattern='123456789',
            activity_name='PBR Sessions',
            task_points=10,
            min_duration_minutes=5,
        )
        
        self.assertEqual(mapping.meeting_id_pattern, '123456789')
        self.assertEqual(mapping.activity_name, 'PBR Sessions')
        self.assertTrue(mapping.is_active)
    
    def test_unique_pattern(self):
        """Test meeting ID pattern must be unique"""
        MeetingActivityMapping.objects.create(
            meeting_id_pattern='123456789',
            activity_name='Test Activity',
        )
        
        with self.assertRaises(Exception):
            MeetingActivityMapping.objects.create(
                meeting_id_pattern='123456789',  # Duplicate!
                activity_name='Another Activity',
            )


@pytest.mark.django_db
class DataMigrationTests(TestCase):
    """Test data migration from old to new models"""
    
    def setUp(self):
        """Create legacy test data"""
        # Create duplicate records (old model style)
        GotoMeetings.objects.create(
            meeting_id='OLD123',
            meeting_topic='Old Meeting',
            meeting_start_time='2025-01-01T10:00:00+00:00',
            meeting_end_time='2025-01-01T11:00:00+00:00',
            meeting_duration='60',
            attendee_name='User 1',
            attendee_email='user1@test.com',
            attendee_duration='45',
        )
        GotoMeetings.objects.create(
            meeting_id='OLD123',  # Same meeting, different attendee
            meeting_topic='Old Meeting',
            meeting_start_time='2025-01-01T10:00:00+00:00',
            meeting_end_time='2025-01-01T11:00:00+00:00',
            meeting_duration='60',
            attendee_name='User 2',
            attendee_email='user2@test.com',
            attendee_duration='30',
        )
    
    def test_deduplication(self):
        """Test that migration deduplicates meetings"""
        from django.core.management import call_command
        
        # Run migration
        call_command('migrate_gotomeeting_data')
        
        # Should have 1 meeting (not 2)
        self.assertEqual(Meeting.objects.count(), 1)
        
        # Should have 2 attendees
        self.assertEqual(MeetingAttendee.objects.count(), 2)
        
        # Verify meeting data
        meeting = Meeting.objects.get(meeting_id='OLD123')
        self.assertEqual(meeting.topic, 'Old Meeting')
        self.assertEqual(meeting.duration_minutes, 60)
    
    def test_attendee_data_preserved(self):
        """Test that all attendee data is preserved"""
        from django.core.management import call_command
        
        call_command('migrate_gotomeeting_data')
        
        # Check both attendees exist
        user1 = MeetingAttendee.objects.get(attendee_email='user1@test.com')
        user2 = MeetingAttendee.objects.get(attendee_email='user2@test.com')
        
        self.assertEqual(user1.attendee_name, 'user 1')  # Normalized to lowercase
        self.assertEqual(user1.duration_minutes, 45)
        
        self.assertEqual(user2.attendee_name, 'user 2')
        self.assertEqual(user2.duration_minutes, 30)


@pytest.mark.django_db
class SaveMeetingDataTests(TestCase):
    """Test the updated save_meeting_data function"""
    
    def test_save_meeting_with_attendees(self):
        """Test saving meeting with attendees"""
        from ai_services.views import save_meeting_data
        
        meeting_data = [{
            'meetingId': 'NEW123',
            'subject': 'New Test Meeting',
            'meetingType': 'General',
            'startTime': '2025-10-27T14:00:00+00:00',
            'endTime': '2025-10-27T15:00:00+00:00',
            'duration': 60,
            'recording': 'https://example.com/recording',
            'downloadUrl': 'https://example.com/download',
            'attendee_Info': [
                {
                    'attendee_name': 'Alice',
                    'attendee_email': 'alice@test.com',
                    'attendee_duration': 50,
                },
                {
                    'attendee_name': 'Bob',
                    'attendee_email': 'bob@test.com',
                    'attendee_duration': 40,
                }
            ]
        }]
        
        save_meeting_data(meeting_data)
        
        # Verify meeting created
        meeting = Meeting.objects.get(meeting_id='NEW123')
        self.assertEqual(meeting.topic, 'New Test Meeting')
        self.assertEqual(meeting.attendee_count, 2)
        
        # Verify attendees created
        alice = MeetingAttendee.objects.get(attendee_email='alice@test.com')
        bob = MeetingAttendee.objects.get(attendee_email='bob@test.com')
        
        self.assertEqual(alice.duration_minutes, 50)
        self.assertEqual(bob.duration_minutes, 40)
    
    def test_duplicate_prevention(self):
        """Test that re-saving same meeting doesn't create duplicates"""
        from ai_services.views import save_meeting_data
        
        meeting_data = [{
            'meetingId': 'DUP123',
            'subject': 'Duplicate Test',
            'startTime': '2025-10-27T14:00:00+00:00',
            'endTime': '2025-10-27T15:00:00+00:00',
            'duration': 60,
            'attendee_Info': [
                {
                    'attendee_name': 'User',
                    'attendee_email': 'user@test.com',
                    'attendee_duration': 30,
                }
            ]
        }]
        
        # Save once
        save_meeting_data(meeting_data)
        
        # Save again (should update, not create new)
        save_meeting_data(meeting_data)
        
        # Should only have 1 meeting
        self.assertEqual(Meeting.objects.filter(meeting_id='DUP123').count(), 1)
        
        # Should only have 1 attendee
        self.assertEqual(MeetingAttendee.objects.filter(attendee_email='user@test.com').count(), 1)


@pytest.mark.django_db
class EnvironmentAwareOAuthTests(TestCase):
    """Test environment-aware OAuth configuration"""
    
    def test_get_redirect_uri(self):
        """Test redirect URI changes based on environment"""
        from ai_services.views import get_oauth_redirect_uri
        from django.conf import settings
        
        # Test different environments
        original_env = getattr(settings, 'ENVIRONMENT', 'local')
        
        # Production
        settings.ENVIRONMENT = 'production'
        uri = get_oauth_redirect_uri()
        self.assertIn('codanalytics.net', uri)
        
        # Staging
        settings.ENVIRONMENT = 'staging'
        uri = get_oauth_redirect_uri()
        self.assertIn('codamakutano.herokuapp.com', uri)
        
        # Local
        settings.ENVIRONMENT = 'local'
        uri = get_oauth_redirect_uri()
        self.assertIn('localhost', uri)
        
        # Restore original
        settings.ENVIRONMENT = original_env


# ==================== REGRESSION TESTS ====================

@pytest.mark.django_db
class RegressionTests(TestCase):
    """Tests to prevent bugs from returning"""
    
    def test_no_duplicate_meetings_on_refetch(self):
        """
        REGRESSION TEST: Ensure re-fetching same date range doesn't create duplicates
        
        Original Issue: ISSUE-006 - No duplicate prevention
        """
        from ai_services.views import save_meeting_data
        
        meeting_data = [{
            'meetingId': 'REG123',
            'subject': 'Regression Test Meeting',
            'startTime': '2025-10-27T14:00:00+00:00',
            'endTime': '2025-10-27T15:00:00+00:00',
            'duration': 60,
            'attendee_Info': []
        }]
        
        # Save 3 times (simulating re-fetch)
        save_meeting_data(meeting_data)
        save_meeting_data(meeting_data)
        save_meeting_data(meeting_data)
        
        # Should only have 1 meeting
        count = Meeting.objects.filter(meeting_id='REG123').count()
        self.assertEqual(count, 1, f"Expected 1 meeting, found {count} (duplicate prevention failed)")
    
    def test_datetime_fields_not_charfield(self):
        """
        REGRESSION TEST: Ensure datetime fields are proper DateTimeField
        
        Original Issue: ISSUE-007 - CharField for dates
        """
        meeting = Meeting.objects.create(
            meeting_id='DATETIME_TEST',
            topic='Test',
            start_time=timezone.now(),
            end_time=timezone.now(),
        )
        
        # Should be DateTimeField, not CharField
        field = Meeting._meta.get_field('start_time')
        self.assertEqual(field.get_internal_type(), 'DateTimeField')
    
    def test_token_persistence_after_cache_clear(self):
        """
        REGRESSION TEST: Tokens should persist in database, not cache
        
        Original Issue: ISSUE-014 - Cache-only token storage
        """
        manager = OAuthTokenManager('persistence_test')
        
        # Save token
        manager.save_tokens("access_123", "refresh_456")
        
        # Simulate cache clear (in real scenario, this would be server restart)
        from django.core.cache import cache
        cache.clear()
        
        # Token should still be retrievable from database
        token = manager.get_access_token()
        self.assertEqual(token, "access_123")


# ==================== INTEGRATION TESTS ====================

@pytest.mark.django_db
class MeetingWorkflowIntegrationTests(TestCase):
    """End-to-end workflow tests"""
    
    def test_complete_meeting_workflow(self):
        """Test complete flow: fetch → save → display → task award"""
        from ai_services.views import save_meeting_data
        
        # 1. Simulate API response
        meeting_data = [{
            'meetingId': 'WORKFLOW123',
            'subject': 'Workflow Test Meeting',
            'startTime': '2025-10-27T14:00:00+00:00',
            'endTime': '2025-10-27T15:00:00+00:00',
            'duration': 60,
            'attendee_Info': [
                {
                    'attendee_name': 'Test User',
                    'attendee_email': 'workflow@test.com',
                    'attendee_duration': 50,  # >3 minutes, qualifies for points
                }
            ]
        }]
        
        # 2. Save to database
        save_meeting_data(meeting_data)
        
        # 3. Verify meeting created
        meeting = Meeting.objects.get(meeting_id='WORKFLOW123')
        self.assertEqual(meeting.topic, 'Workflow Test Meeting')
        
        # 4. Verify attendee created
        attendee = MeetingAttendee.objects.get(attendee_email='workflow@test.com')
        self.assertEqual(attendee.duration_minutes, 50)
        self.assertTrue(attendee.qualifies_for_points)
        
        # 5. Verify can query by date range
        meetings = Meeting.objects.filter(
            start_time__gte='2025-10-27T00:00:00+00:00',
            start_time__lte='2025-10-27T23:59:59+00:00'
        )
        self.assertEqual(meetings.count(), 1)


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

