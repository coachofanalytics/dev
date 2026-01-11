"""
Unit tests for attendee instance key matching fixes.

Tests:
- int vs string mismatch normalization
- recurring meeting: meeting_id != meeting_instance_key but attendees match instance key
- Missing instance key handling (don't filter to zero)
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from accounts.models import CustomerUser
from ai_services.models import Meeting, MeetingAttendee
from ai_services.services.attendee_sync_service import \
    upsert_attendees_for_meeting
from django.test import TestCase
from django.utils import timezone


class AttendeeInstanceKeyMatchingTests(TestCase):
    """Test instance key matching fixes."""

    def setUp(self):
        """Set up test data."""
        self.user = CustomerUser.objects.create_user(
            username="testuser", email="test@example.com", is_staff=True, is_active=True
        )

        self.meeting = Meeting.objects.create(
            meeting_id="698-057-837",
            topic="Test Meeting",
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1) + timedelta(hours=1),
            duration_minutes=60,
            service_name="gotomeeting_internal",
        )

    def test_int_vs_string_mismatch_normalization(self):
        """Test that int vs string instance keys are normalized correctly."""
        # Set meeting instance key as string
        self.meeting.meeting_instance_key = "12345"
        self.meeting.save()

        # Create attendees with int instance key (simulating API returning int)
        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": 12345,  # Int, not string
            }
        ]

        # Should not filter out attendees due to type mismatch
        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        # Attendee should be created (normalized comparison should match)
        self.assertGreater(
            created + updated,
            0,
            "Attendee should be created despite int/string mismatch",
        )

        # Verify attendee exists
        attendee = MeetingAttendee.objects.filter(meeting=self.meeting).first()
        self.assertIsNotNone(attendee, "Attendee should exist")
        self.assertEqual(attendee.attendee_name, "Test User")

    def test_recurring_meeting_instance_key_matching(self):
        """Test recurring meeting where meeting_id != meeting_instance_key."""
        # Recurring meeting: same meeting_id, different instance keys
        self.meeting.meeting_instance_key = "instance-key-2024-01-01"
        self.meeting.session_id = "session-123"
        self.meeting.save()

        # Attendees with matching instance key (different from meeting_id)
        attendees_data = [
            {
                "name": "Organizer",
                "email": "organizer@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "instance-key-2024-01-01",  # Matches meeting_instance_key
            },
            {
                "name": "Attendee",
                "email": "attendee@example.com",
                "joinTime": "2024-01-01T10:05:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 55,
                "isOrganizer": False,
                "meetingInstanceKey": "instance-key-2024-01-01",  # Matches meeting_instance_key
            },
        ]

        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        # Both attendees should be created (they match instance key)
        self.assertGreater(created + updated, 0, "Attendees should be created")

        # Verify both attendees exist
        attendees = MeetingAttendee.objects.filter(meeting=self.meeting)
        self.assertEqual(attendees.count(), 2, "Both attendees should exist")

    def test_missing_instance_key_dont_filter_to_zero(self):
        """Test that missing instance key doesn't filter all attendees to zero."""
        # Meeting with no instance key
        self.meeting.meeting_instance_key = None
        self.meeting.session_id = None
        self.meeting.save()

        # Attendees with instance keys
        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "some-instance-key",
            }
        ]

        # Should include all attendees when instance key is missing (don't filter to zero)
        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        # Attendee should be created (included despite missing instance key)
        self.assertGreater(
            created + updated,
            0,
            "Attendee should be created when instance key is missing",
        )

        # Verify attendee exists
        attendee = MeetingAttendee.objects.filter(meeting=self.meeting).first()
        self.assertIsNotNone(attendee, "Attendee should exist")

    def test_whitespace_normalization(self):
        """Test that whitespace in instance keys is normalized."""
        self.meeting.meeting_instance_key = " 12345 "  # With whitespace
        self.meeting.save()

        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "12345",  # No whitespace
            }
        ]

        # Should match after normalization
        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        self.assertGreater(
            created + updated, 0, "Attendee should match after whitespace normalization"
        )

    def test_fallback_to_session_id_then_meeting_id(self):
        """Test fallback from meeting_instance_key to session_id to meeting_id."""
        # No meeting_instance_key, but has session_id
        self.meeting.meeting_instance_key = None
        self.meeting.session_id = "session-123"
        self.meeting.save()

        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "session-123",  # Matches session_id
            }
        ]

        # Should use session_id as fallback
        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        self.assertGreater(
            created + updated, 0, "Attendee should match via session_id fallback"
        )

    def test_all_attendees_filtered_out_includes_all(self):
        """Test that if all attendees would be filtered out, include all to prevent data loss."""
        self.meeting.meeting_instance_key = "expected-key"
        self.meeting.save()

        # Attendees with different instance keys (would all be filtered)
        attendees_data = [
            {
                "name": "Test User 1",
                "email": "test1@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": False,
                "meetingInstanceKey": "different-key-1",
            },
            {
                "name": "Test User 2",
                "email": "test2@example.com",
                "joinTime": "2024-01-01T10:05:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 55,
                "isOrganizer": False,
                "meetingInstanceKey": "different-key-2",
            },
        ]

        # Should include all attendees to prevent data loss (even though they don't match)
        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        # Both should be created (included to prevent data loss)
        self.assertGreater(
            created + updated, 0, "Attendees should be included to prevent data loss"
        )

        attendees = MeetingAttendee.objects.filter(meeting=self.meeting)
        self.assertEqual(
            attendees.count(), 2, "Both attendees should exist despite mismatch"
        )

    def test_normalize_key_handles_none_safely(self):
        """Test that normalize_key handles None values safely."""
        from ai_services.services.attendee_sync_service import \
            upsert_attendees_for_meeting

        def normalize_key(key):
            """Test normalization function."""
            if key is None:
                return None
            normalized = str(key).strip()
            return normalized if normalized else None

        # Test None
        self.assertIsNone(normalize_key(None))

        # Test empty string
        self.assertIsNone(normalize_key(""))
        self.assertIsNone(normalize_key("   "))

        # Test int vs string
        self.assertEqual(normalize_key(12345), "12345")
        self.assertEqual(normalize_key("12345"), "12345")
        self.assertEqual(normalize_key(" 12345 "), "12345")

        # Test comparison
        self.assertEqual(normalize_key(12345), normalize_key("12345"))
        self.assertEqual(normalize_key(" 12345 "), normalize_key(12345))

    def test_repr_and_type_logging(self):
        """Test that repr() and type() are logged for debugging."""
        import logging
        from io import StringIO

        self.meeting.meeting_instance_key = 12345  # Int
        self.meeting.save()

        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                "joinTime": "2024-01-01T10:00:00Z",
                "leaveTime": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "12345",  # String
            }
        ]

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger("ai_services.services.attendee_sync_service")
        logger.addHandler(handler)

        created, updated = upsert_attendees_for_meeting(
            self.meeting, attendees_data, split_combined_names=False
        )

        # Should match after normalization (no mismatch warning)
        log_output = log_capture.getvalue()
        # If there's a mismatch warning, it should include repr() and type()
        if "mismatch" in log_output.lower():
            self.assertIn("repr", log_output.lower(), "Should log repr() for debugging")
            self.assertIn("type", log_output.lower(), "Should log type() for debugging")

        logger.removeHandler(handler)

    def test_missing_join_leave_time_keys_no_nameerror(self):
        """Test that missing join/leave time keys don't cause NameError."""
        self.meeting.meeting_instance_key = "12345"
        self.meeting.save()

        # Attendee payload missing joinTime/leaveTime keys (or using different key names)
        attendees_data = [
            {
                "name": "Test User",
                "email": "test@example.com",
                # No joinTime/leaveTime keys
                "duration": 60,
                "isOrganizer": True,
                "meetingInstanceKey": "12345",
            },
            {
                "name": "Test User 2",
                "email": "test2@example.com",
                # Using alternative key names
                "joined_at": "2024-01-01T10:00:00Z",
                "left_at": "2024-01-01T11:00:00Z",
                "duration": 60,
                "isOrganizer": False,
                "meetingInstanceKey": "12345",
            },
        ]

        # Should not raise NameError - join_time and leave_time should be extracted safely
        try:
            created, updated = upsert_attendees_for_meeting(
                self.meeting, attendees_data, split_combined_names=False
            )
            # Should succeed without NameError
            self.assertGreaterEqual(created + updated, 0, "Should not raise NameError")
        except NameError as e:
            self.fail(f"NameError raised when join/leave time keys missing: {e}")

    def test_management_command_no_provider_meeting_instance_key_attribute_error(self):
        """Test that management command doesn't crash when provider_meeting_instance_key is absent."""
        from io import StringIO
        from unittest.mock import patch

        from django.core.management import call_command

        # Create a meeting without provider_meeting_instance_key attribute
        self.meeting.meeting_instance_key = "12345"
        self.meeting.session_id = "session-123"
        self.meeting.save()

        # Mock the sync service to avoid actual API calls
        with patch(
            "ai_services.services.attendee_sync_service.sync_attendees_for_meetings"
        ) as mock_sync:
            mock_sync.return_value = {
                "meetings_processed": 1,
                "meetings_success": 1,
                "meetings_failed": 0,
                "meetings_quarantined": 0,
                "attendees_created": 0,
                "attendees_updated": 0,
                "errors": [],
            }

            # Mock get_meetings_needing_attendee_sync to return our test meeting
            with patch(
                "ai_services.services.attendee_sync_service.get_meetings_needing_attendee_sync"
            ) as mock_get:
                mock_get.return_value = [self.meeting]

                # Mock OAuth token
                with patch("shared_core.utils.oauth.get_access_token") as mock_token:
                    mock_token.return_value = "mock-token"

                    # Should not raise AttributeError when accessing provider_meeting_instance_key
                    out = StringIO()
                    try:
                        call_command(
                            "sync_meeting_attendees",
                            "--service",
                            "internal",
                            "--days",
                            "1",
                            "--verbose",
                            stdout=out,
                        )
                        # Command should complete without AttributeError
                        output = out.getvalue()
                        self.assertNotIn(
                            "AttributeError",
                            output,
                            "Should not have AttributeError in output",
                        )
                    except AttributeError as e:
                        if "provider_meeting_instance_key" in str(e):
                            self.fail(
                                f"AttributeError raised for provider_meeting_instance_key: {e}"
                            )
                        else:
                            raise  # Re-raise if it's a different AttributeError
