"""
Meeting Room Configuration

Maps activity types to GoToMeeting meeting rooms (meeting_id and join URLs).
This replaces the hardcoded activity_mapping dict and provides a single source of truth.

Usage:
    from ai_services.utils.meeting_room_config import get_meeting_room_for_activity
    
    room_id, join_url = get_meeting_room_for_activity('INTERNAL_TRAINING_SESSION')
"""

from typing import Optional, Tuple

from coda.config.activity_definitions import ACTIVITY_POLICIES

# Legacy mapping from ai_services/utils.py (for backward compatibility)
# Maps meeting_id -> activity_name (legacy format)
LEGACY_ACTIVITY_MAPPING = {
    "708385093": "PBR sessions",
    "632884285": "BI Sessions",
    "123530685": "DAF SESSION",
    "994131389": "General Meeting",
    "616024597": "PROJECT SESSION",
    "199103181": "SPRINT SESSION",
    "905794573": "REQUEST SESSION",
    "967944357": "BOG",
    "884917357": "BUDGET REVIEW MEETING",
    "931282277": "RECRUTMENT(APPLICANTS & DEVELOPERS)",
    "396508029": "APPROVAL SESSION",
}

# Activity type to meeting room mapping
# This should be populated from ActivityPolicy.meeting_room_id when available
# For now, we map based on legacy activity_mapping and known patterns
ACTIVITY_TO_MEETING_ROOM: dict[str, dict[str, str]] = {
    # Format: activity_slug -> {meeting_id, join_url}
    "PRODUCT_BACKLOG_REFINEMENT": {
        "meeting_id": "708385093",
        "join_url": "https://global.gotomeeting.com/join/708385093",  # Standard format
    },
    "INTERNAL_TRAINING_SESSION": {
        "meeting_id": "123530685",  # DAF SESSION (used for training)
        "join_url": "https://global.gotomeeting.com/join/123530685",
    },
    "UAT_TESTING_SUPPORT": {
        "meeting_id": "123530685",  # Can reuse DAF SESSION or create new
        "join_url": "https://global.gotomeeting.com/join/123530685",
    },
    "CLIENT_TRAINING_SESSION": {
        "meeting_id": "123530685",
        "join_url": "https://global.gotomeeting.com/join/123530685",
    },
    "SELF_TRAINING_SESSION": {
        "meeting_id": "123530685",
        "join_url": "https://global.gotomeeting.com/join/123530685",
    },
    # Add more mappings as needed
}


def get_meeting_room_for_activity(
    activity_slug: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get meeting room ID and join URL for an activity type.

    Priority:
    1. ActivityPolicy.meeting_room_id (if set)
    2. ACTIVITY_TO_MEETING_ROOM mapping
    3. None (no room configured)

    Args:
        activity_slug: Activity type slug (e.g., 'INTERNAL_TRAINING_SESSION')

    Returns:
        Tuple of (meeting_id, join_url) or (None, None) if not configured
    """
    # Check ActivityPolicy first
    policy = ACTIVITY_POLICIES.get(activity_slug.upper())
    if policy and policy.meeting_room_id:
        join_url = policy.meeting_join_url
        if not join_url and policy.meeting_room_id:
            # Generate standard GoToMeeting join URL
            join_url = f"https://global.gotomeeting.com/join/{policy.meeting_room_id}"
        return (policy.meeting_room_id, join_url)

    # Fallback to ACTIVITY_TO_MEETING_ROOM
    room_config = ACTIVITY_TO_MEETING_ROOM.get(activity_slug.upper())
    if room_config:
        return (room_config.get("meeting_id"), room_config.get("join_url"))

    return (None, None)


def get_activity_for_meeting_id(meeting_id: str) -> Optional[str]:
    """
    Get activity type slug for a meeting_id (reverse lookup).

    Uses legacy mapping and ACTIVITY_TO_MEETING_ROOM.

    Args:
        meeting_id: GoToMeeting meeting ID

    Returns:
        Activity slug or None if not found
    """
    # Check ActivityPolicy
    for slug, policy in ACTIVITY_POLICIES.items():
        if policy.meeting_room_id == meeting_id:
            return slug

    # Check ACTIVITY_TO_MEETING_ROOM
    for slug, config in ACTIVITY_TO_MEETING_ROOM.items():
        if config.get("meeting_id") == meeting_id:
            return slug

    # Legacy mapping (activity_name -> need to map to slug)
    legacy_activity = LEGACY_ACTIVITY_MAPPING.get(meeting_id)
    if legacy_activity:
        # Map legacy names to slugs (approximate)
        legacy_to_slug = {
            "PBR sessions": "PRODUCT_BACKLOG_REFINEMENT",
            "DAF SESSION": "INTERNAL_TRAINING_SESSION",
            # Add more as needed
        }
        return legacy_to_slug.get(legacy_activity)

    return None
