"""
GoToMeeting Sync Service

Service for fetching and persisting GoToMeeting meetings.
Extracted from views.py to provide reusable, non-UI-dependent API.

Phase 2A: First incremental step after OAuth is working.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


def fetch_meetings(
    start_dt: datetime, end_dt: datetime, access_token: str
) -> List[Dict]:
    """
    Fetch meetings from GoToMeeting API for datetime range.

    Args:
        start_dt: Start datetime (timezone-aware)
        end_dt: End datetime (timezone-aware)
        access_token: OAuth access token

    Returns:
        List of meeting dicts with attendee info, or empty list on error

    Raises:
        ValueError: If access_token is empty
        requests.exceptions.RequestException: On network/API errors
    """
    if not access_token:
        raise ValueError("Access token is required")

    # Format dates as expected by GoToMeeting API (YYYY-MM-DDTHH:MM:SSZ)
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start_str}&endDate={end_str}"

    try:
        response = requests.get(url=url, headers=headers, timeout=30)
        response.raise_for_status()

        json_response = response.json()
        meetings = []

        logger.info(
            f"📊 Fetched {len(json_response)} meetings from API for {start_dt.date()} to {end_dt.date()}"
        )

        for meeting in json_response:
            try:
                meeting_id = meeting.get("meetingId")
                if not meeting_id:
                    logger.warning("Meeting missing meetingId, skipping")
                    continue

                recording = meeting.get("recording", {})
                download_url = recording.get("downloadUrl") if recording else None
                share_url = recording.get("shareUrl") if recording else None

                # INFO logging for recording data (to diagnose API payload)
                if recording or share_url or download_url:
                    recording_keys = (
                        list(recording.keys())
                        if isinstance(recording, dict)
                        else "not_dict"
                    )
                    logger.info(
                        f"📹 Recording data for meeting_id={meeting_id}: "
                        f"recording_keys={recording_keys}, "
                        f"share_url={share_url or 'None'}, "
                        f"download_url={download_url or 'None'}, "
                        f"shareId={recording.get('shareId') if isinstance(recording, dict) else 'None'}, "
                        f"token={recording.get('token') if isinstance(recording, dict) else 'None'}"
                    )

                # Normalize transcript URL to canonical format
                from ai_services.utils.meeting_normalizer import \
                    normalize_gotomeeting_transcript_url

                canonical_transcript_url = normalize_gotomeeting_transcript_url(
                    share_url=share_url,
                    download_url=download_url,
                    share_id=(
                        recording.get("shareId")
                        if isinstance(recording, dict)
                        else None
                    ),
                    token=(
                        recording.get("token") if isinstance(recording, dict) else None
                    ),
                )

                logger.info(
                    f"📹 Normalized transcript URL for meeting_id={meeting_id}: "
                    f"input_share_url={share_url or 'None'}, "
                    f"output={canonical_transcript_url or 'None'}"
                )

                # Extract sessionId from historicalMeetings response
                # Note: meetingInstanceKey is not in historicalMeetings response,
                # it comes from attendee API and will be set during attendee sync
                session_id = meeting.get("sessionId", "")

                # Also check for meetingInstanceKey in case it's present (some API versions may include it)
                meeting_instance_key = meeting.get("meetingInstanceKey", "")

                # HARD RULE: Only use canonical transcript URL if it's in the correct format
                # Never store bare host or non-canonical URLs
                # Include source tracking in meeting dict
                recording_url_for_dict = ""
                recording_url_source_for_dict = None

                if canonical_transcript_url and canonical_transcript_url.startswith(
                    "https://transcripts.gotomeeting.com/#/s/"
                ):
                    recording_url_for_dict = canonical_transcript_url
                    recording_url_source_for_dict = "provider"
                    logger.info(
                        f"✅ Using canonical transcript URL: {canonical_transcript_url} "
                        f"for meeting_id={meeting_id} (source=provider)"
                    )
                else:
                    # Do not store non-canonical URLs (including bare host)
                    if canonical_transcript_url:
                        logger.info(
                            f"⚠️  Skipping non-canonical URL for meeting_id={meeting_id}: {canonical_transcript_url}"
                        )
                    else:
                        logger.info(
                            f"ℹ️  No canonical transcript URL available for meeting_id={meeting_id} "
                            f"(no token extracted from API response)"
                        )

                meeting_dict["recording_url_source"] = recording_url_source_for_dict

                meeting_dict = {
                    "meetingId": meeting_id,
                    "sessionId": session_id,  # Store sessionId for session-scoped attendee fetching
                    "meetingInstanceKey": meeting_instance_key,  # Store if present
                    "downloadUrl": download_url or "",
                    "recording": recording_url_for_dict,  # Only canonical URL or empty
                    "recording_url_source": recording_url_source_for_dict,  # 'provider' or None
                    "subject": meeting.get("subject", "Untitled Meeting"),
                    "meetingType": meeting.get("meetingType", ""),
                    "startTime": meeting.get("startTime", ""),
                    "endTime": meeting.get("endTime", ""),
                    "duration": meeting.get("duration", 0),
                    "email": meeting.get("email", ""),
                    "attendeeNames": [],
                    "attendee_Info": [],  # Empty - attendees synced separately
                }

                # Log instance identifier extraction
                logger.info(
                    f"📋 Meeting sync: meeting_id={meeting_id}, "
                    f"meeting_type={meeting.get('meetingType', 'N/A')}, "
                    f"start_time={meeting.get('startTime', 'N/A')}, "
                    f"session_id={session_id or 'None'}, "
                    f"meeting_instance_key={meeting_instance_key or 'None'}"
                )
                meetings.append(meeting_dict)

                # NOTE: Attendee fetching removed from meeting sync
                # Attendees should be synced separately via sync_meeting_attendees command
                # This ensures consistent filtering by instance key and proper email normalization
                # Meeting sync now only persists meeting metadata and instance identifiers

            except Exception as e:
                logger.error(
                    f"Error processing meeting {meeting_id}: {e}", exc_info=True
                )
                continue

        logger.info(f"✅ Successfully processed {len(meetings)} meetings")
        return meetings

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error(
                "OAuth token expired or invalid - user needs to re-authenticate"
            )
        else:
            logger.error(f"HTTP error fetching meetings: {e}")
        raise
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout fetching meetings from GoToMeeting API: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching meetings: {e}", exc_info=True)
        raise
    except ValueError as e:
        logger.error(f"Invalid JSON response from GoToMeeting API: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fetch_meetings: {e}", exc_info=True)
        raise


def upsert_meetings(
    meetings_json: List[Dict], service_name: str = None
) -> Dict[str, int]:
    """
    Persist meetings to database using existing save_meeting_data logic.

    Args:
        meetings_json: List of meeting dicts from fetch_meetings()
        service_name: Optional service name for multi-account support (e.g., 'gotomeeting_external')

    Returns:
        Dict with counts: {
            'meetings_created': int,
            'meetings_updated': int,
            'attendees_created': int,
            'attendees_updated': int
        }
    """
    # Reuse existing save_meeting_data function
    # Add service_name to each meeting dict if provided
    if service_name:
        for meeting_dict in meetings_json:
            meeting_dict["service_name"] = service_name

    from ai_services.views import save_meeting_data

    result = save_meeting_data(meetings_json)
    return result


def sync(
    start_dt: datetime, end_dt: datetime, service_name: str = "gotomeeting"
) -> Dict[str, int]:
    """
    Orchestrate meeting sync: get token, fetch meetings, persist to DB.

    Args:
        start_dt: Start datetime (timezone-aware)
        end_dt: End datetime (timezone-aware)
        service_name: Service name for OAuth token lookup (default: "gotomeeting")
                      For multi-account support: "gotomeeting_external", "gotomeeting_internal"

    Returns:
        Dict with counts and status:
        {
            'meetings_fetched': int,
            'meetings_created': int,
            'meetings_updated': int,
            'attendees_created': int,
            'attendees_updated': int,
            'success': bool,
            'error': Optional[str]
        }

    Raises:
        RuntimeError: If OAuth token is missing
    """
    from ai_services.models import MeetingSyncRun
    from shared_core.utils.oauth import get_access_token

    # Create sync run record
    sync_run = MeetingSyncRun.objects.create(
        service_name=service_name,
        status="in_progress",
        window_start=start_dt,
        window_end=end_dt,
    )

    try:
        # Get access token for the specified service
        access_token = get_access_token(service_name=service_name)
        if not access_token:
            error_msg = f"OAuth token not available for service '{service_name}'. Please run /management/oauth/login/?service={service_name.split('_')[-1]} first."
            logger.error(error_msg)
            sync_run.status = "failed"
            sync_run.error_message = error_msg
            sync_run.finished_at = timezone.now()
            sync_run.save()
            raise RuntimeError(error_msg)

        # Mask token for logging (show only last 6 chars)
        token_mask = access_token[-6:] if len(access_token) >= 6 else "******"
        logger.info(
            f"🔑 Using OAuth token for service '{service_name}' (last 6: ...{token_mask})"
        )

        # Fetch meetings
        meetings = fetch_meetings(start_dt, end_dt, access_token)

        if not meetings:
            logger.info(f"ℹ️ No meetings found for {start_dt.date()} to {end_dt.date()}")
            sync_run.status = "success"
            sync_run.meetings_fetched_count = 0
            sync_run.meetings_upserted_count = 0
            sync_run.finished_at = timezone.now()
            sync_run.save()

            return {
                "meetings_fetched": 0,
                "meetings_created": 0,
                "meetings_updated": 0,
                "attendees_created": 0,
                "attendees_updated": 0,
                "success": True,
                "error": None,
            }

        # Persist meetings (with service_name for multi-account support)
        counts = upsert_meetings(meetings, service_name=service_name)

        # Update sync run record with success
        sync_run.status = "success"
        sync_run.meetings_fetched_count = len(meetings)
        sync_run.meetings_upserted_count = (
            counts["meetings_created"] + counts["meetings_updated"]
        )
        sync_run.finished_at = timezone.now()
        sync_run.save()

        logger.info(
            f"✅ Meeting sync complete for '{service_name}': {len(meetings)} meetings fetched, "
            f"{counts['meetings_created']} created, {counts['meetings_updated']} updated, "
            f"{counts['attendees_created']} attendees created, {counts['attendees_updated']} attendees updated"
        )

        return {
            "meetings_fetched": len(meetings),
            "meetings_created": counts["meetings_created"],
            "meetings_updated": counts["meetings_updated"],
            "attendees_created": counts["attendees_created"],
            "attendees_updated": counts["attendees_updated"],
            "success": True,
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"❌ Meeting sync failed for '{service_name}' ({start_dt.date()} to {end_dt.date()}): {error_msg}",
            exc_info=True,
        )

        # Update sync run record with failure
        sync_run.status = "failed"
        sync_run.error_message = error_msg[:1000]  # Limit error message length
        sync_run.finished_at = timezone.now()
        sync_run.save()

        return {
            "meetings_fetched": 0,
            "meetings_created": 0,
            "meetings_updated": 0,
            "attendees_created": 0,
            "attendees_updated": 0,
            "success": False,
            "error": error_msg,
        }


def get_last_successful_sync(service_name: str = "gotomeeting"):
    """
    Get the last successful sync run for a service.

    Args:
        service_name: Service name (default: "gotomeeting")

    Returns:
        MeetingSyncRun instance or None if no successful sync found
    """
    from ai_services.models import MeetingSyncRun

    try:
        return (
            MeetingSyncRun.objects.filter(service_name=service_name, status="success")
            .order_by("-finished_at")
            .first()
        )
    except Exception as e:
        logger.debug(f"Error getting last successful sync for '{service_name}': {e}")
        return None


def is_meeting_data_fresh(
    service_name: str = "gotomeeting", max_age_minutes: int = 1440
) -> bool:
    """
    Check if meeting data is fresh (last successful sync within max_age_minutes).

    Args:
        service_name: Service name (default: "gotomeeting")
        max_age_minutes: Maximum age in minutes before data is considered stale (default: 1440 = 24 hours)

    Returns:
        bool: True if data is fresh, False if stale or no sync found
    """
    last_sync = get_last_successful_sync(service_name)

    if not last_sync or not last_sync.finished_at:
        return False

    age_minutes = (timezone.now() - last_sync.finished_at).total_seconds() / 60
    return age_minutes <= max_age_minutes
