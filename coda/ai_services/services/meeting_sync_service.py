"""
Meeting Sync Service

Reusable service for syncing GoToMeeting meetings into the normalized Meeting and MeetingAttendee models.

This service provides a clean, non-UI-dependent API for:
- Management commands
- Celery tasks
- Programmatic meeting sync

Phase M1: Extract sync logic from views into reusable service.
"""

import logging
from datetime import date
from typing import Dict, Optional, TypedDict

logger = logging.getLogger(__name__)


class MeetingSyncResult(TypedDict, total=False):
    """Result of meeting sync operation."""

    meetings_created: int
    meetings_updated: int
    attendees_created: int
    attendees_updated: int
    meetings_fetched: int
    success: bool
    error: Optional[str]


def sync_meetings_for_range(
    start: date, end: date, service_name: str = "gotomeeting"
) -> MeetingSyncResult:
    """
    Fetch meetings from GoToMeeting API for [start, end] and persist them into
    Meeting and MeetingAttendee models.

    Reuses the same underlying logic as the existing meetingFormView/getmeetingresponse/save_meeting_data
    so that we have a single source of truth for ingestion.

    Args:
        start: Start date (inclusive)
        end: End date (inclusive)
        service_name: Service name for OAuth token and meeting storage (default: "gotomeeting")
                     For multi-account: "gotomeeting_external", "gotomeeting_internal"

    Returns:
        MeetingSyncResult dict with counts and status

    Raises:
        ValueError: If start > end
        RuntimeError: If OAuth token is missing or API call fails critically
    """
    if start > end:
        raise ValueError(f"Start date ({start}) must be <= end date ({end})")

    try:
        # Import here to avoid circular imports
        from ai_services.views import getmeetingresponse, save_meeting_data

        # Convert dates to strings (YYYY-MM-DD) as expected by getmeetingresponse
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        logger.info(
            f"🔄 Starting meeting sync for range: {start_str} to {end_str} (service: {service_name})"
        )

        # Fetch meetings from API
        meetings_data = getmeetingresponse(
            start_str, end_str, service_name=service_name
        )

        if not meetings_data:
            logger.info(
                f"ℹ️ No meetings found for {start_str} to {end_str} (service: {service_name})"
            )
            return {
                "meetings_created": 0,
                "meetings_updated": 0,
                "attendees_created": 0,
                "attendees_updated": 0,
                "meetings_fetched": 0,
                "success": True,
                "error": None,
            }

        # Save to database with service_name
        # save_meeting_data now returns counts (Phase M1 enhancement)
        save_result = save_meeting_data(meetings_data, service_name=service_name)

        logger.info(
            f"✅ Meeting sync complete: {len(meetings_data)} meetings fetched, "
            f"{save_result['meetings_created']} created, {save_result['meetings_updated']} updated, "
            f"{save_result['attendees_created']} attendees created, {save_result['attendees_updated']} attendees updated"
        )

        # Return result with counts from save_meeting_data
        return {
            "meetings_created": save_result["meetings_created"],
            "meetings_updated": save_result["meetings_updated"],
            "attendees_created": save_result["attendees_created"],
            "attendees_updated": save_result["attendees_updated"],
            "meetings_fetched": len(meetings_data),
            "success": True,
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"❌ Meeting sync failed for {start} to {end}: {error_msg}", exc_info=True
        )

        return {
            "meetings_created": 0,
            "meetings_updated": 0,
            "attendees_created": 0,
            "attendees_updated": 0,
            "meetings_fetched": 0,
            "success": False,
            "error": error_msg,
        }
