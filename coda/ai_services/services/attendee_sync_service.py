"""
Attendee Sync Service for GoToMeeting.

Fetches and persists attendees for meetings using the correct API endpoint.
Handles both meeting_id and session_id (if available) for attendee fetching.

Key features:
- DB-first selection of meetings needing attendee refresh
- Idempotent upsert strategy
- Combined name splitting (e.g., "EUNICE, JUDY AND NOREEN")
- Support for both internal and external services
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from ai_services.models import Meeting, MeetingAttendee
from django.db.models import Count, Max, Q
from django.utils import timezone
from shared_core.utils.oauth import get_access_token

logger = logging.getLogger(__name__)


def split_combined_attendee_name(name: str) -> List[str]:
    """
    Split combined attendee names into individual names.

    Handles patterns like:
    - "EUNICE, JUDY AND NOREEN" -> ["EUNICE", "JUDY", "NOREEN"]
    - "John & Jane" -> ["John", "Jane"]
    - "Alice, Bob, Charlie" -> ["Alice", "Bob", "Charlie"]

    Does NOT split organization strings:
    - "CROWN DATA ANALYSIS AND CONSULTANCY SERVICES" -> ["CROWN DATA ANALYSIS AND CONSULTANCY SERVICES"]
    - "ACME CORPORATION & ASSOCIATES" -> ["ACME CORPORATION & ASSOCIATES"]

    Heuristics to detect organizations:
    - Contains business keywords: "DATA", "ANALYSIS", "CONSULTANCY", "SERVICES", "CORPORATION", "ASSOCIATES", "LLC", "INC"
    - All caps (likely organization)
    - Length > 30 characters (likely organization)

    Args:
        name: Combined attendee name string

    Returns:
        List of individual names (normalized, trimmed)
    """
    if not name or not isinstance(name, str):
        return []

    name = name.strip()
    if not name:
        return []

    # Heuristic: detect organization strings (don't split these)
    # Organizations typically have business keywords OR are very long without clear person delimiters
    organization_keywords = [
        "DATA",
        "ANALYSIS",
        "CONSULTANCY",
        "SERVICES",
        "CORPORATION",
        "ASSOCIATES",
        "LLC",
        "INC",
        "LTD",
        "COMPANY",
        "GROUP",
        "ENTERPRISES",
    ]
    name_upper = name.upper()

    # Check for business keywords first (strong signal)
    has_business_keywords = any(
        keyword in name_upper for keyword in organization_keywords
    )

    # Check for person delimiters (comma, " AND ", " & ")
    has_person_delimiters = bool(
        re.search(r",\s*|\s+AND\s+|\s+&\s+", name, flags=re.IGNORECASE)
    )

    # Organization detection: business keywords OR (very long AND no person delimiters)
    # G) FIX: Refined heuristic - all-caps is only strong signal if long (>20) AND no person delimiters
    is_likely_organization = (
        has_business_keywords
        or (len(name) > 40 and not has_person_delimiters)
        or (
            name.isupper() and len(name) > 20 and not has_person_delimiters
        )  # Changed from 30 to 20, must have no delimiters
    )

    if is_likely_organization:
        # Don't split organization names
        return [name]

    # Split by common delimiters: comma, " AND ", " & "
    # Pattern: split on comma, " AND ", or " & " (case-insensitive)
    parts = re.split(r",\s*|\s+AND\s+|\s+&\s+", name, flags=re.IGNORECASE)

    # Normalize each part
    names = []
    for part in parts:
        part = part.strip()
        if part:
            names.append(part)

    # If splitting didn't work (no delimiters), return original as single name
    if len(names) == 0:
        return [name]

    # If only one part after splitting, return as single name
    if len(names) == 1:
        return [name]

    return names


def determine_meeting_instance_key(
    attendees_data: List[Dict],
    meeting_start_time: Optional[datetime] = None,
    force: bool = False,
) -> Tuple[Optional[str], str]:
    """
    Deterministically select the correct meetingInstanceKey from attendee data.

    Strategy:
    1. Group attendees by meetingInstanceKey
    2. If timestamps exist, choose instance whose timestamps align best with meeting.start_time
    3. If no timestamps, only auto-select if exactly ONE distinct meetingInstanceKey exists
    4. If multiple instance keys and no reliable discriminator, mark as ambiguous and return None

    Args:
        attendees_data: List of attendee dicts from API (each has meetingInstanceKey)
        meeting_start_time: Optional meeting start time for timestamp alignment
        force: If True, allow selection even when ambiguous (default: False)

    Returns:
        Tuple of (selected_instance_key, reason):
        - selected_instance_key: The chosen meetingInstanceKey, or None if ambiguous
        - reason: Explanation of selection ("single_instance", "timestamp_aligned", "ambiguous", "forced")
    """
    if not attendees_data:
        return None, "no_attendees"

    # Group attendees by meetingInstanceKey
    instance_key_groups = {}
    for attendee in attendees_data:
        instance_key = attendee.get("meetingInstanceKey") or attendee.get(
            "meeting_instance_key"
        )
        if not instance_key:
            continue

        if instance_key not in instance_key_groups:
            instance_key_groups[instance_key] = []
        instance_key_groups[instance_key].append(attendee)

    if not instance_key_groups:
        return None, "no_instance_keys"

    distinct_keys = list(instance_key_groups.keys())

    # Case 1: Exactly one distinct instance key - safe to use
    if len(distinct_keys) == 1:
        return distinct_keys[0], "single_instance"

    # Case 2: Multiple instance keys - need discriminator
    if meeting_start_time:
        # Try timestamp alignment
        best_key = None
        best_score = float("inf")

        for instance_key, attendees in instance_key_groups.items():
            # Calculate average join time for this instance
            join_times = []
            for attendee in attendees:
                join_time_str = attendee.get("joinTime") or attendee.get(
                    "join_time", ""
                )
                if join_time_str:
                    try:
                        from dateutil import parser

                        join_dt = parser.isoparse(join_time_str.replace(".+", "+"))
                        join_times.append(join_dt)
                    except Exception:
                        pass

            if join_times:
                avg_join_time = sum(
                    (t - meeting_start_time).total_seconds() for t in join_times
                ) / len(join_times)
                time_diff = abs(avg_join_time)

                if time_diff < best_score:
                    best_score = time_diff
                    best_key = instance_key

        if best_key and best_score < 3600:  # Within 1 hour
            return best_key, "timestamp_aligned"

    # Case 3: Multiple instance keys, no reliable discriminator
    if force:
        # Force selection: pick the instance with most attendees
        best_key = max(
            instance_key_groups.keys(), key=lambda k: len(instance_key_groups[k])
        )
        return best_key, "forced"
    else:
        # Ambiguous - skip
        return None, "ambiguous"


def fetch_attendees_for_meeting(
    meeting_id: str,
    access_token: str,
    session_id: Optional[str] = None,
    meeting_instance_key: Optional[str] = None,
    meeting_start_time: Optional[datetime] = None,
    verbose: bool = False,
) -> Tuple[List[Dict], Optional[str], str]:
    """
    Fetch attendees for a meeting using GoToMeeting API.

    IMPORTANT: The /meetings/{meeting_id}/attendees endpoint returns ALL historical attendees
    for that meeting room across all sessions. We must filter by meetingInstanceKey to get
    only session-specific attendees.

    Args:
        meeting_id: Meeting ID (room ID, e.g., "698-057-837")
        access_token: OAuth access token
        session_id: Optional session ID from historicalMeetings API
        meeting_instance_key: Optional meetingInstanceKey to filter attendees (if known)
        verbose: If True, log detailed information

    Returns:
        Tuple of (attendees_list, extracted_meeting_instance_key, selection_reason):
        - attendees_list: List of attendee dicts with keys:
          - name: str - Attendee name
          - email: str - Attendee email (may be empty)
          - joinTime: str - Join time ISO string
          - leaveTime: str - Leave time ISO string
          - duration: int - Duration in minutes
          - isOrganizer: bool - Whether attendee is organizer
          - meetingInstanceKey: str - Meeting instance key from API (for filtering)
        - extracted_meeting_instance_key: The deterministically selected meetingInstanceKey (or None if ambiguous)
        - selection_reason: Explanation of selection ("single_instance", "timestamp_aligned", "ambiguous", etc.)
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    attendees = []
    extracted_instance_key = None
    selection_reason = "provided"  # Default if instance key was provided

    # Try meeting_id endpoint
    try:
        url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"
        if verbose:
            logger.info(f"🔍 Fetching attendees: {url}")

        response = requests.get(url=url, headers=headers, timeout=30)

        if verbose:
            logger.info(f"   HTTP {response.status_code} for meeting_id={meeting_id}")

        if response.status_code == 200:
            attendees_data = response.json()

            if verbose:
                logger.info(
                    f"   Raw response: {len(attendees_data)} attendees returned"
                )

            # Deterministically select meetingInstanceKey if not provided
            if not meeting_instance_key and attendees_data:
                # Extract all attendees with their instance keys for analysis
                raw_attendees = []
                for att in attendees_data:
                    instance_key = att.get("meetingInstanceKey") or att.get(
                        "meeting_instance_key"
                    )
                    if instance_key:
                        raw_attendees.append(
                            {
                                "meetingInstanceKey": instance_key,
                                "joinTime": att.get("joinTime")
                                or att.get("join_time", ""),
                                "leaveTime": att.get("leaveTime")
                                or att.get("leave_time", ""),
                            }
                        )

                if raw_attendees:
                    # Use deterministic selection with meeting start time if available
                    extracted_instance_key, selection_reason = (
                        determine_meeting_instance_key(
                            raw_attendees,
                            meeting_start_time=meeting_start_time,
                            force=False,
                        )
                    )

                    if verbose:
                        if extracted_instance_key:
                            logger.info(
                                f"   Selected meetingInstanceKey: {extracted_instance_key} (reason: {selection_reason})"
                            )
                        else:
                            logger.warning(
                                f"   ⚠️  Ambiguous instance key selection (reason: {selection_reason})"
                            )
                            distinct_count = len(
                                set(att["meetingInstanceKey"] for att in raw_attendees)
                            )
                            logger.warning(
                                f"   Found {distinct_count} distinct instance keys"
                            )
                else:
                    selection_reason = "no_instance_keys"
            elif meeting_instance_key:
                selection_reason = "provided"
            else:
                selection_reason = "no_attendees"

            # Use provided or extracted meetingInstanceKey for filtering
            filter_key = meeting_instance_key or extracted_instance_key

            # Normalize filter_key for comparison (handle None safely)
            def normalize_key(key):
                """Normalize key for comparison: handle None, convert to string, strip whitespace."""
                if key is None:
                    return None
                # Convert to string and strip - handles int vs string mismatches
                normalized = str(key).strip()
                # Return None for empty strings to be consistent
                return normalized if normalized else None

            normalized_filter_key = normalize_key(filter_key)

            # Log filter key details for debugging
            if verbose or not normalized_filter_key:
                logger.info(
                    f"   Filter key details:\n"
                    f"     Raw: {repr(filter_key)} (type: {type(filter_key).__name__})\n"
                    f"     Normalized: {repr(normalized_filter_key)} (type: {type(normalized_filter_key).__name__ if normalized_filter_key else 'NoneType'})"
                )

            # Normalize attendee data and filter by meetingInstanceKey if available
            for attendee in attendees_data:
                attendee_instance_key = attendee.get(
                    "meetingInstanceKey"
                ) or attendee.get("meeting_instance_key")

                normalized_attendee_key = normalize_key(attendee_instance_key)

                # Log comparison details for debugging (first few mismatches)
                if (
                    normalized_filter_key
                    and normalized_attendee_key
                    and normalized_attendee_key != normalized_filter_key
                ):
                    # Always log first mismatch with full details
                    logger.warning(
                        f"   Instance key mismatch detected:\n"
                        f"     Expected (normalized): {repr(normalized_filter_key)} (type: {type(normalized_filter_key).__name__})\n"
                        f"     Attendee (normalized):  {repr(normalized_attendee_key)} (type: {type(normalized_attendee_key).__name__})\n"
                        f"     Expected (raw): {repr(filter_key)} (type: {type(filter_key).__name__})\n"
                        f"     Attendee (raw):  {repr(attendee_instance_key)} (type: {type(attendee_instance_key).__name__})"
                    )

                # Filter: if we have a meetingInstanceKey, only include matching attendees
                # BUT: if filter_key is missing, include all attendees (don't filter to zero)
                if normalized_filter_key:
                    if (
                        normalized_attendee_key
                        and normalized_attendee_key != normalized_filter_key
                    ):
                        if verbose:
                            logger.debug(
                                f"   Skipping attendee (instance key mismatch: {normalized_attendee_key} != {normalized_filter_key})"
                            )
                        continue
                else:
                    # No filter key - include all attendees and log warning
                    logger.warning(
                        f"   ⚠️  No instance key available for filtering - including all attendees. "
                        f"This may include attendees from other meeting instances."
                    )

                attendee_name = attendee.get("name") or attendee.get("attendeeName", "")
                attendee_email = attendee.get("email") or attendee.get(
                    "attendeeEmail", ""
                )
                join_time = attendee.get("joinTime") or attendee.get("join_time", "")
                leave_time = attendee.get("leaveTime") or attendee.get("leave_time", "")

                # Calculate duration
                duration_minutes = 0
                if join_time and leave_time:
                    try:
                        from dateutil import parser

                        join_dt = parser.isoparse(join_time)
                        leave_dt = parser.isoparse(leave_time)
                        duration_minutes = int(
                            (leave_dt - join_dt).total_seconds() / 60
                        )
                    except Exception as e:
                        logger.debug(
                            f"Could not parse attendee duration for {meeting_id}: {e}"
                        )

                attendees.append(
                    {
                        "name": attendee_name,
                        "email": attendee_email,
                        "joinTime": join_time,
                        "leaveTime": leave_time,
                        "duration": duration_minutes,
                        "isOrganizer": attendee.get("isOrganizer", False)
                        or attendee.get("is_organizer", False),
                        "meetingInstanceKey": attendee_instance_key,  # Store for reference
                    }
                )

            if verbose:
                logger.info(
                    f"✅ Fetched {len(attendees)} attendees for meeting {meeting_id} (filtered by instance key: {filter_key})"
                )
                logger.info(f"   Before filtering: {len(attendees_data)} attendees")
                logger.info(f"   After filtering: {len(attendees)} attendees")
            else:
                logger.debug(
                    f"✅ Fetched {len(attendees)} attendees for meeting {meeting_id}"
                )

            return attendees, extracted_instance_key, selection_reason

        elif response.status_code == 404:
            # Meeting not found - this meeting does not exist in this account/service
            if verbose:
                logger.warning(f"   ❌ 404 Not Found for meeting_id={meeting_id}")
                logger.warning(
                    f"   💡 This meeting is not available in this account. Marking as provider_not_found."
                )
                if not meeting_instance_key:
                    logger.warning(
                        f"   💡 Suggestion: meetingInstanceKey may be required. Try backfilling instance keys."
                    )

            # Try session_id if available (though this likely won't work either)
            if session_id and session_id != meeting_id:
                logger.debug(
                    f"Meeting {meeting_id} not found, trying session_id {session_id}"
                )
                return fetch_attendees_for_meeting(
                    session_id, access_token, None, None, meeting_start_time, verbose
                )
            else:
                logger.warning(
                    f"Meeting {meeting_id} not found (404) - will mark as provider_not_found"
                )
                return [], None, "404_not_found"
        else:
            logger.warning(
                f"Failed to fetch attendees for meeting {meeting_id}: HTTP {response.status_code}"
            )
            return [], None, f"http_{response.status_code}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching attendees for meeting {meeting_id}: {e}")
        return [], None, "request_exception"


def normalize_attendee_email(email: Optional[str]) -> Optional[str]:
    """
    Normalize attendee email, treating missing values as None.

    Treats "NA", "N/A", "", None, "-", "NONE" as missing.

    Args:
        email: Raw email string from API

    Returns:
        Normalized email string or None if missing/invalid
    """
    if not email:
        return None

    email = str(email).strip()
    if not email:
        return None

    email_upper = email.upper()
    if email_upper in ["NA", "N/A", "NONE", "-"]:
        return None

    return email


def upsert_attendees_for_meeting(
    meeting: Meeting, attendees_data: List[Dict], split_combined_names: bool = True
) -> Tuple[int, int]:
    """
    Upsert attendees for a meeting (idempotent).

    Strategy:
    - Filter attendees by meeting instance key (session_id or meeting_instance_key)
    - Delete existing attendees for this meeting (fresh sync)
    - Create new attendees from filtered API data
    - Split combined names if enabled
    - Normalize missing emails

    SERVICE SCOPING SAFETY:
    - MeetingAttendee is scoped via Meeting FK (meeting.service_name)
    - Deleting by meeting=meeting only affects attendees for that specific meeting
    - No risk of cross-service collision since meetings are already filtered by service_name
    - Unique constraint: (meeting, attendee_email) ensures no duplicates per meeting

    Args:
        meeting: Meeting instance (already scoped by service_name)
        attendees_data: List of attendee dicts from API
        split_combined_names: Whether to split combined names (default: True)

    Returns:
        Tuple of (created_count, updated_count)
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    created_count = 0
    updated_count = 0

    # Log meeting instance key info
    logger.info(
        f"📋 Attendee sync start: meeting_id={meeting.meeting_id}, "
        f"start_time={meeting.start_time}, "
        f"session_id={meeting.session_id or 'None'}, "
        f"meeting_instance_key={meeting.meeting_instance_key or 'None'}"
    )

    api_attendee_count = len(attendees_data)
    logger.info(f"   API attendee_count (after fetch filtering): {api_attendee_count}")

    # Normalize key comparison helper
    def normalize_key(key):
        """Normalize key for comparison: handle None, convert to string, strip whitespace."""
        if key is None:
            return None
        # Convert to string and strip - handles int vs string mismatches
        normalized = str(key).strip()
        # Return None for empty strings to be consistent
        return normalized if normalized else None

    # Try meeting_instance_key first, then session_id, then meeting_id as fallback
    # Compare attendees' meetingInstanceKey to Meeting.meeting_instance_key first, then session_id, then meeting_id
    filter_key = (
        normalize_key(meeting.meeting_instance_key)
        or normalize_key(meeting.session_id)
        or normalize_key(meeting.meeting_id)
    )

    # Log filter key selection for debugging
    logger.debug(
        f"   Filter key selection for meeting {meeting.meeting_id}:\n"
        f"     meeting_instance_key: {repr(meeting.meeting_instance_key)} (type: {type(meeting.meeting_instance_key).__name__ if meeting.meeting_instance_key else 'NoneType'})\n"
        f"     session_id: {repr(meeting.session_id)} (type: {type(meeting.session_id).__name__ if meeting.session_id else 'NoneType'})\n"
        f"     meeting_id: {repr(meeting.meeting_id)} (type: {type(meeting.meeting_id).__name__})\n"
        f"     Selected filter_key: {repr(filter_key)} (type: {type(filter_key).__name__ if filter_key else 'NoneType'})"
    )

    filtered_attendees = []

    if not filter_key:
        logger.warning(
            f"   ⚠️  Meeting {meeting.meeting_id} has no instance key (meeting_instance_key, session_id, or meeting_id). "
            f"Including all attendees to prevent data loss."
        )
        # For meetings without instance key, include all attendees (legacy behavior)
        filtered_attendees = attendees_data
        logger.warning(
            f"   ⚠️  Including all {len(filtered_attendees)} attendees (no instance key to verify)"
        )
    else:
        # Safety check: verify all attendees match the meeting's instance key
        # Use normalized comparison to handle int vs string mismatches
        mismatches = []

        for attendee in attendees_data:
            attendee_instance_key = attendee.get("meetingInstanceKey") or attendee.get(
                "meeting_instance_key"
            )

            normalized_attendee_key = normalize_key(attendee_instance_key)

            # Compare normalized keys
            if normalized_attendee_key == filter_key:
                filtered_attendees.append(attendee)
            else:
                mismatches.append(
                    {
                        "name": attendee.get("name", "Unknown"),
                        "attendee_key": attendee_instance_key,
                        "normalized_attendee_key": normalized_attendee_key,
                    }
                )

        # Log mismatches with detailed debugging info (always log first few)
        if mismatches:
            logger.warning(
                f"   ⚠️  Found {len(mismatches)} attendee(s) with instance key mismatch for meeting {meeting.meeting_id}:"
            )
            for mismatch in mismatches[:5]:  # Log first 5
                logger.warning(
                    f"     Attendee: {mismatch['name']}\n"
                    f"       Expected (normalized): {repr(filter_key)} (type: {type(filter_key).__name__})\n"
                    f"       Attendee (normalized):  {repr(mismatch['normalized_attendee_key'])} (type: {type(mismatch['normalized_attendee_key']).__name__ if mismatch['normalized_attendee_key'] else 'NoneType'})\n"
                    f"       Expected (raw): {repr(meeting.meeting_instance_key or meeting.session_id or meeting.meeting_id)} (type: {type(meeting.meeting_instance_key or meeting.session_id or meeting.meeting_id).__name__})\n"
                    f"       Attendee (raw): {repr(mismatch['attendee_key'])} (type: {type(mismatch['attendee_key']).__name__ if mismatch['attendee_key'] else 'NoneType'})"
                )

        # If all attendees filtered out, but we have attendees_data, this is a problem
        # If expected_key is missing, do NOT filter to zero; persist attendees and log a warning
        if len(filtered_attendees) == 0 and len(attendees_data) > 0:
            if not filter_key:
                # No expected key - include all attendees
                logger.warning(
                    f"   ⚠️  Meeting {meeting.meeting_id} has no instance key. "
                    f"Including all {len(attendees_data)} attendees to prevent data loss."
                )
                filtered_attendees = attendees_data
            else:
                # Have filter key but all attendees filtered out - this is a mismatch issue
                logger.error(
                    f"   ❌ All {len(attendees_data)} attendees filtered out for meeting {meeting.meeting_id}. "
                    f"Expected key: {repr(filter_key)} (type: {type(filter_key).__name__})\n"
                    f"   This suggests an instance key mismatch. Including all attendees to prevent data loss."
                )
                # Don't filter to zero - include all attendees if filter would remove everything
                filtered_attendees = attendees_data
                logger.warning(
                    f"   ⚠️  Including all {len(filtered_attendees)} attendees to prevent data loss"
                )
        elif len(filtered_attendees) > 0:
            logger.debug(
                f"   ✅ Safety check passed: {len(filtered_attendees)}/{len(attendees_data)} attendees match instance key"
            )

    if len(filtered_attendees) == 0:
        logger.warning(
            f"   ⚠️  No attendees to persist for meeting {meeting.meeting_id}. "
            f"Reason: {'meeting instance key missing' if not filter_key else '0 attendees after filter'}"
        )
        return 0, 0

    # Delete existing attendees for this meeting (fresh sync approach)
    # SAFE: Only deletes attendees for this specific meeting (scoped via FK)
    # No risk of cross-service collision since meeting is already filtered by service_name
    existing_count = MeetingAttendee.objects.filter(meeting=meeting).count()
    if existing_count > 0:
        MeetingAttendee.objects.filter(meeting=meeting).delete()
        logger.debug(
            f"   Deleted {existing_count} existing attendees for meeting {meeting.meeting_id} (service: {meeting.service_name})"
        )

    # Process each attendee
    emails_normalized_count = 0
    for attendee_data in filtered_attendees:
        attendee_name = attendee_data.get("name") or attendee_data.get(
            "attendeeName", ""
        )
        if attendee_name:
            attendee_name = str(attendee_name).strip()

        attendee_email_raw = attendee_data.get("email") or attendee_data.get(
            "attendeeEmail", ""
        )
        attendee_email = normalize_attendee_email(attendee_email_raw)

        # Track normalization
        if not attendee_email and attendee_email_raw:
            emails_normalized_count += 1

        duration_raw = attendee_data.get("duration", 0)
        is_organizer = attendee_data.get("isOrganizer", False) or attendee_data.get(
            "is_organizer", False
        )

        if not attendee_name:
            logger.debug(f"   Skipping attendee with no name: {attendee_data}")
            continue

        # Defensive duration conversion and clamping: detect if duration is in seconds instead of minutes
        # Strategy: If duration_value > meeting.duration_minutes * 5, treat as seconds and convert
        # Then clamp to ensure attendee.duration_minutes <= meeting.duration_minutes * 1.5 (reasonable max)
        import math

        duration_minutes = duration_raw
        if (
            duration_raw > 0
            and meeting.duration_minutes
            and meeting.duration_minutes > 0
        ):
            if duration_raw > meeting.duration_minutes * 5:
                # Likely stored in seconds; convert to minutes (ceiling)
                duration_minutes = math.ceil(duration_raw / 60.0)
                if duration_minutes != duration_raw:
                    logger.debug(
                        f"Converted attendee duration from {duration_raw} to {duration_minutes} minutes "
                        f"(meeting duration: {meeting.duration_minutes} min, ratio: {duration_raw/meeting.duration_minutes:.1f}x)"
                    )

            # Clamp: attendee duration should not exceed meeting duration by more than 50%
            # (allows for join/leave timing differences, but prevents corruption)
            max_reasonable_duration = int(meeting.duration_minutes * 1.5)
            if duration_minutes > max_reasonable_duration:
                logger.warning(
                    f"Clamping attendee duration from {duration_minutes} to {max_reasonable_duration} minutes "
                    f"(meeting duration: {meeting.duration_minutes} min)"
                )
                duration_minutes = max_reasonable_duration
        elif duration_raw > 0 and not meeting.duration_minutes:
            # Meeting duration missing; if duration_raw > 600, likely seconds (10+ min)
            if duration_raw > 600:
                duration_minutes = math.ceil(duration_raw / 60.0)
                logger.debug(
                    f"Converted attendee duration from {duration_raw} to {duration_minutes} minutes "
                    f"(meeting duration missing, assumed seconds for large value)"
                )

        # Split combined names if enabled
        if split_combined_names:
            names = split_combined_attendee_name(attendee_name)
        else:
            names = [attendee_name]

        # Extract join/leave times from attendee_data (handle multiple key variants)
        join_time = (
            attendee_data.get("joinTime")
            or attendee_data.get("join_time")
            or attendee_data.get("joined_at")
            or attendee_data.get("joinTimeUtc")
            or ""
        )
        leave_time = (
            attendee_data.get("leaveTime")
            or attendee_data.get("leave_time")
            or attendee_data.get("left_at")
            or attendee_data.get("leaveTimeUtc")
            or ""
        )

        # Process each name (after splitting)
        for name in names:
            if not name:
                continue

            # Try to match to CODA user by email (if available)
            user = None
            if attendee_email:
                try:
                    user = User.objects.filter(Q(email__iexact=attendee_email)).first()
                except Exception as e:
                    logger.debug(f"   User lookup error for {attendee_email}: {e}")

            # Fallback: try username match by name if no email match
            if not user and name:
                try:
                    user = User.objects.filter(Q(username__iexact=name.lower())).first()
                except Exception as e:
                    logger.debug(f"   User lookup by name error for {name}: {e}")

            # Generate placeholder email if missing (to satisfy unique_together constraint)
            # Include meeting_instance_key and joinTime to ensure uniqueness for recurring meetings
            # This prevents "NA" attendees from collapsing into one record
            if not attendee_email:
                import hashlib

                instance_key = meeting.meeting_instance_key or meeting.session_id or ""

                # Create unique key: meeting_id + instance_key + name + joinTime (or leaveTime if joinTime missing)
                # Use leaveTime as fallback if joinTime is not available
                time_key = join_time or leave_time or ""
                unique_key = (
                    f"{meeting.meeting_id}-{instance_key}-{name}-{time_key}".encode()
                )
                name_hash = hashlib.md5(unique_key).hexdigest()[:12]
                attendee_email = f"no-email-{name_hash}@placeholder.local"
                logger.debug(
                    f"   Generated placeholder email for attendee without email: {name} (key includes instance_key={instance_key[:10] if instance_key else 'None'} and time={time_key[:19] if time_key else 'None'})"
                )

            # Create attendee (idempotent: unique_together on (meeting, attendee_email))
            attendee, created = MeetingAttendee.objects.get_or_create(
                meeting=meeting,
                attendee_email=attendee_email,
                defaults={
                    "user": user,
                    "attendee_name": name,
                    "duration_minutes": duration_minutes,
                    "is_organizer": is_organizer,
                },
            )

            if created:
                created_count += 1
            else:
                # Update existing attendee
                updated_count += 1
                update_fields = {
                    "attendee_name": name,
                    "duration_minutes": duration_minutes,
                    "is_organizer": is_organizer,
                }
                if user and not attendee.user:
                    update_fields["user"] = user
                elif (
                    user
                    and attendee.user
                    and attendee_email
                    and not attendee_email.startswith("no-email-")
                ):
                    # Prefer email-matched user
                    update_fields["user"] = user

                MeetingAttendee.objects.filter(id=attendee.id).update(**update_fields)

    # Log summary
    logger.info(
        f"✅ Attendee sync complete: meeting_id={meeting.meeting_id}, "
        f"created={created_count}, updated={updated_count}, "
        f"emails_normalized={emails_normalized_count}"
    )

    return created_count, updated_count


def sync_attendees_for_meetings(
    meetings: List[Meeting], service_name: str, access_token: Optional[str] = None
) -> Dict[str, int]:
    """
    Sync attendees for a list of meetings.

    Args:
        meetings: List of Meeting instances to sync attendees for
        service_name: Service name (for token lookup if access_token not provided)
        access_token: Optional access token (if not provided, will fetch)

    Returns:
        Dict with counts:
        {
            'meetings_processed': int,
            'meetings_success': int,
            'meetings_failed': int,
            'meetings_quarantined': int,  # 404/quarantined (not a failure)
            'attendees_created': int,
            'attendees_updated': int,
            'errors': List[str]
        }
    """
    if not access_token:
        access_token = get_access_token(service_name=service_name)
        if not access_token:
            error_msg = f"OAuth token not available for service '{service_name}'"
            logger.error(error_msg)
            return {
                "meetings_processed": 0,
                "meetings_success": 0,
                "meetings_failed": len(meetings),
                "attendees_created": 0,
                "attendees_updated": 0,
                "errors": [error_msg],
            }

    total_created = 0
    total_updated = 0
    success_count = 0
    failed_count = 0
    quarantined_count = 0
    errors = []

    for meeting in meetings:
        try:
            # Skip meetings marked as provider_not_found (unless forced)
            # Note: Force option would be passed as parameter if needed
            if meeting.provider_not_found:
                logger.debug(
                    f"Skipping meeting {meeting.meeting_id} (provider_not_found=True)"
                )
                quarantined_count += 1
                continue

            # Fetch attendees from API (with session-scoped filtering)
            attendees_data, extracted_instance_key, selection_reason = (
                fetch_attendees_for_meeting(
                    meeting.meeting_id,
                    access_token,
                    session_id=meeting.session_id,
                    meeting_instance_key=meeting.meeting_instance_key,
                    meeting_start_time=meeting.start_time,
                    verbose=False,  # Set to True for detailed logging
                )
            )

            # Store meetingInstanceKey only if selection is confident
            if extracted_instance_key and selection_reason not in [
                "ambiguous",
                "no_instance_keys",
                "no_attendees",
            ]:
                if not meeting.meeting_instance_key:
                    meeting.meeting_instance_key = extracted_instance_key
                    meeting.save(update_fields=["meeting_instance_key", "updated_at"])
                    logger.info(
                        f"Stored meetingInstanceKey {extracted_instance_key} for meeting {meeting.meeting_id} "
                        f"(reason: {selection_reason})"
                    )
            elif selection_reason == "ambiguous":
                logger.warning(
                    f"⚠️  Ambiguous instance key for meeting {meeting.meeting_id} - skipping storage. "
                    f"Use --force flag in backfill command to override."
                )

            # Handle 404_not_found - mark as quarantined (not a failure)
            if selection_reason == "404_not_found":
                # Meeting not found in this account - mark as provider_not_found
                from django.utils import timezone

                meeting.provider_not_found = True
                meeting.provider_not_found_at = timezone.now()
                meeting.save(
                    update_fields=[
                        "provider_not_found",
                        "provider_not_found_at",
                        "updated_at",
                    ]
                )

                quarantined_count += 1
                logger.info(
                    f"Meeting {meeting.meeting_id} not found (404) in account {service_name} - quarantined (provider_not_found=True)"
                )
                continue

            # Clear provider_not_found flag if fetch succeeded (meeting is now available)
            if meeting.provider_not_found:
                meeting.provider_not_found = False
                meeting.provider_not_found_at = None
                meeting.save(
                    update_fields=[
                        "provider_not_found",
                        "provider_not_found_at",
                        "updated_at",
                    ]
                )
                logger.info(
                    f"Cleared provider_not_found flag for meeting {meeting.meeting_id} (fetch succeeded)"
                )

            if not attendees_data:
                logger.warning(
                    f"   ⚠️  No attendees found for meeting {meeting.meeting_id}. "
                    f"Reason: {selection_reason}"
                )
                # Not an error - meeting might have no attendees
                success_count += 1
                continue

            # Upsert attendees (attendees_data is already filtered by instance key in fetch_attendees_for_meeting)
            created, updated = upsert_attendees_for_meeting(meeting, attendees_data)

            total_created += created
            total_updated += updated
            success_count += 1

            logger.info(
                f"✅ Synced attendees for meeting {meeting.meeting_id}: "
                f"{created} created, {updated} updated"
            )

        except Exception as e:
            failed_count += 1
            error_msg = f"Error syncing attendees for meeting {meeting.meeting_id}: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

    return {
        "meetings_processed": len(meetings),
        "meetings_success": success_count,
        "meetings_failed": failed_count,
        "meetings_quarantined": quarantined_count,
        "attendees_created": total_created,
        "attendees_updated": total_updated,
        "errors": errors,
    }


def get_meetings_needing_attendee_sync(
    service_name: Optional[str] = None,
    days: int = 120,
    limit: Optional[int] = None,
    max_age_hours: int = 24,
) -> List[Meeting]:
    """
    Get meetings that need attendee sync (DB-first selection).

    Criteria:
    - Meetings in last N days
    - Either have no attendees OR attendees are stale (>max_age_hours old)
    - Optional service_name filter
    - Optional limit

    Args:
        service_name: Optional service name filter
        days: Number of days to look back (default: 120)
        limit: Optional limit on number of meetings
        max_age_hours: Maximum age of attendee data before considered stale (default: 24)

    Returns:
        List of Meeting instances needing attendee sync
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    stale_threshold = end_date - timedelta(hours=max_age_hours)

    # Base query: meetings in date range
    meetings_query = Meeting.objects.filter(
        start_time__gte=start_date, start_time__lte=end_date
    )

    if service_name:
        meetings_query = meetings_query.filter(service_name=service_name)

    # Annotate with attendee info
    # Use attendee_count_db to avoid conflict with Meeting.attendee_count property
    meetings_query = meetings_query.annotate(
        attendee_count_db=Count("attendees"),
        latest_attendee_update=Max("attendees__updated_at"),
    )

    # Filter: meetings with no attendees OR stale attendees
    meetings_query = meetings_query.filter(
        Q(attendee_count_db=0)
        | Q(latest_attendee_update__lt=stale_threshold)
        | Q(latest_attendee_update__isnull=True)
    ).order_by(
        "-start_time"
    )  # G) FIX: Order BEFORE slicing to prevent "Cannot reorder after slice" error

    if limit:
        meetings_query = meetings_query[:limit]

    return list(meetings_query)
