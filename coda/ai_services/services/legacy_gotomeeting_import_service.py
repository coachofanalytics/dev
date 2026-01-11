"""
Legacy GoToMeeting Import Service

One-time utility to import historical meeting data from denormalized GotoMeetings
table into normalized Meeting + MeetingAttendee tables.

This service:
- Reads from GotoMeetings (db_table='getdata_gotomeetings')
- Groups rows by meeting_id
- Normalizes URLs and topics using existing utilities
- Upserts Meeting and MeetingAttendee records
- Provides idempotent import (safe to run multiple times)
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ai_services.models import GotoMeetings, Meeting, MeetingAttendee
from ai_services.utils.meeting_normalizer import (extract_requirement_code,
                                                  normalize_topic,
                                                  normalize_url)
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

User = get_user_model()

logger = logging.getLogger(__name__)


def parse_duration_string(duration_str: Optional[str]) -> Optional[int]:
    """
    Parse duration string to minutes.

    Handles various formats:
    - "60" (minutes as string)
    - "1:00" (hours:minutes)
    - "3600" (seconds)
    - "1h 30m" (human readable)

    Args:
        duration_str: Duration string from legacy data

    Returns:
        Duration in minutes, or None if unparseable
    """
    if not duration_str:
        return None

    duration_str = str(duration_str).strip()
    if not duration_str:
        return None

    try:
        # Try direct integer (assumed minutes)
        if duration_str.isdigit():
            return int(duration_str)

        # Try "HH:MM" format
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes

        # Try "Xh Ym" format
        if "h" in duration_str.lower() or "m" in duration_str.lower():
            total_minutes = 0
            # Extract hours
            import re

            hour_match = re.search(r"(\d+)\s*h", duration_str.lower())
            if hour_match:
                total_minutes += int(hour_match.group(1)) * 60
            # Extract minutes
            min_match = re.search(r"(\d+)\s*m", duration_str.lower())
            if min_match:
                total_minutes += int(min_match.group(1))
            if total_minutes > 0:
                return total_minutes

        # Try as seconds (if > 1000, assume seconds)
        if duration_str.isdigit() and int(duration_str) > 1000:
            return int(int(duration_str) / 60)

        # Last resort: try float and convert to int
        return int(float(duration_str))
    except (ValueError, AttributeError, TypeError) as e:
        logger.debug(f"Failed to parse duration '{duration_str}': {e}")
        return None


def parse_datetime_string(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse datetime string with best-effort parsing.

    Handles various formats that might exist in legacy data.

    Args:
        dt_str: Datetime string from legacy data

    Returns:
        Timezone-aware datetime, or None if unparseable
    """
    if not dt_str:
        return None

    dt_str = str(dt_str).strip()
    if not dt_str:
        return None

    # Try Django's parse_datetime first (handles ISO formats)
    parsed = parse_datetime(dt_str)
    if parsed:
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed)
        return parsed

    # Try common formats manually
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed)
            return parsed
        except (ValueError, TypeError):
            continue

    logger.debug(f"Failed to parse datetime '{dt_str}'")
    return None


def import_legacy_rows(
    service_name: str = "gotomeeting_external",
    limit: Optional[int] = None,
    since: Optional[datetime] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Import legacy GotoMeetings rows into normalized Meeting + MeetingAttendee tables.

    Args:
        service_name: Service name to assign to imported meetings
        limit: Maximum number of legacy rows to process (None = all)
        since: Only import rows created/updated after this datetime
        dry_run: If True, don't actually save, just return counts

    Returns:
        Dictionary with counts:
        - legacy_rows_scanned: Total rows from GotoMeetings
        - meetings_created: New Meeting records created
        - meetings_updated: Existing Meeting records updated
        - attendees_created: New MeetingAttendee records created
        - attendees_updated: Existing MeetingAttendee records updated
        - rows_skipped: Rows skipped (missing meeting_id, etc.)
        - parse_failures: Rows where datetime/duration parsing failed
    """
    # Query legacy rows
    queryset = GotoMeetings.objects.filter(is_active=True)

    if since:
        queryset = queryset.filter(created_at__gte=since)

    # Order BEFORE slicing (Django doesn't allow reordering after slice)
    queryset = queryset.order_by("meeting_id", "created_at")

    if limit:
        queryset = queryset[:limit]

    legacy_rows = list(queryset)

    logger.info(f"📊 Found {len(legacy_rows)} legacy GotoMeetings rows to import")

    # Initialize counters
    stats = {
        "legacy_rows_scanned": len(legacy_rows),
        "meetings_created": 0,
        "meetings_updated": 0,
        "attendees_created": 0,
        "attendees_updated": 0,
        "rows_skipped": 0,
        "parse_failures": 0,
    }

    # Group by meeting_id
    meetings_by_id = defaultdict(list)
    rows_without_meeting_id = 0
    for row in legacy_rows:
        meeting_id = row.meeting_id
        if not meeting_id or not meeting_id.strip():
            rows_without_meeting_id += 1
            continue
        meetings_by_id[meeting_id.strip()].append(row)

    # Count rows skipped due to missing meeting_id
    stats["rows_skipped"] = rows_without_meeting_id

    logger.info(f"📦 Grouped into {len(meetings_by_id)} unique meeting_ids")

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be saved")

    # Process each meeting group
    for meeting_id, rows in meetings_by_id.items():
        try:
            # Choose canonical topic (first non-empty meeting_topic)
            topic = None
            for row in rows:
                if row.meeting_topic and row.meeting_topic.strip():
                    topic = row.meeting_topic.strip()
                    break

            if not topic:
                topic = "Untitled Meeting"

            # Normalize topic
            topic_normalized = normalize_topic(topic) if topic else ""

            # Extract requirement code from topic (REQ-#### convention)
            requirement_code = extract_requirement_code(topic) if topic else None
            if requirement_code:
                requirement_code = requirement_code.upper()  # Normalize to uppercase

            # Determine recording_url and download_url
            recording_url = None
            download_url = None
            for row in rows:
                if row.recording and row.recording.strip():
                    recording_url = normalize_url(row.recording.strip())
                    break
            for row in rows:
                if row.download_url:
                    download_url = normalize_url(str(row.download_url))
                    break

            # If no recording_url but download_url exists, use it
            if not recording_url and download_url:
                recording_url = download_url

            # Determine meeting_type (first non-empty)
            meeting_type = ""
            for row in rows:
                if row.meeting_type and row.meeting_type.strip():
                    meeting_type = row.meeting_type.strip()
                    break

            # Parse start_time and end_time (best effort)
            start_time = None
            end_time = None
            parse_failed = False

            for row in rows:
                if not start_time and row.meeting_start_time:
                    start_time = parse_datetime_string(row.meeting_start_time)
                if not end_time and row.meeting_end_time:
                    end_time = parse_datetime_string(row.meeting_end_time)
                if start_time and end_time:
                    break

            # If we have start_time but no end_time, try to calculate from duration
            if start_time and not end_time:
                duration_minutes = None
                for row in rows:
                    if row.meeting_duration:
                        duration_minutes = parse_duration_string(row.meeting_duration)
                        if duration_minutes:
                            break
                if duration_minutes:
                    end_time = start_time + timedelta(minutes=duration_minutes)

            # If still no times, use created_at as fallback (but mark as parse failure)
            if not start_time:
                parse_failed = True
                # Use earliest created_at from rows as fallback
                earliest_created = min(row.created_at for row in rows)
                start_time = earliest_created
                end_time = earliest_created + timedelta(minutes=60)  # Default 1 hour

            # Calculate duration_minutes
            duration_minutes = 0
            if start_time and end_time and end_time > start_time:
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            else:
                # Try to parse from meeting_duration
                for row in rows:
                    if row.meeting_duration:
                        parsed_duration = parse_duration_string(row.meeting_duration)
                        if parsed_duration:
                            duration_minutes = parsed_duration
                            break

            # Determine is_recorded
            is_recorded = bool(recording_url or download_url)

            if parse_failed:
                stats["parse_failures"] += 1

            # Upsert Meeting
            if not dry_run:
                with transaction.atomic():
                    meeting, created = Meeting.objects.get_or_create(
                        meeting_id=meeting_id,
                        defaults={
                            "topic": topic,
                            "topic_normalized": topic_normalized,
                            "requirement_code": requirement_code,
                            "service_name": service_name,
                            "meeting_type": meeting_type,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_minutes": duration_minutes,
                            "recording_url": recording_url,
                            "download_url": download_url,
                            "is_recorded": is_recorded,
                        },
                    )

                    if created:
                        stats["meetings_created"] += 1
                        logger.debug(f"✅ Created meeting: {topic} ({meeting_id})")
                    else:
                        stats["meetings_updated"] += 1
                        # Update with new data if present (preserve existing if new is empty)
                        update_data = {}
                        if topic and topic != meeting.topic:
                            update_data["topic"] = topic
                            update_data["topic_normalized"] = topic_normalized
                        if (
                            requirement_code
                            and requirement_code != meeting.requirement_code
                        ):
                            update_data["requirement_code"] = requirement_code
                        if recording_url and recording_url != meeting.recording_url:
                            update_data["recording_url"] = recording_url
                        if download_url and download_url != meeting.download_url:
                            update_data["download_url"] = download_url
                        if meeting_type and meeting_type != meeting.meeting_type:
                            update_data["meeting_type"] = meeting_type
                        # Only update service_name if meeting doesn't have one yet
                        if not meeting.service_name and service_name:
                            update_data["service_name"] = service_name
                        # Update times if we have better data
                        if start_time and (
                            not meeting.start_time or start_time < meeting.start_time
                        ):
                            update_data["start_time"] = start_time
                        if end_time and (
                            not meeting.end_time or end_time > meeting.end_time
                        ):
                            update_data["end_time"] = end_time
                        if duration_minutes > meeting.duration_minutes:
                            update_data["duration_minutes"] = duration_minutes
                        if is_recorded and not meeting.is_recorded:
                            update_data["is_recorded"] = is_recorded

                        if update_data:
                            Meeting.objects.filter(id=meeting.id).update(**update_data)
                            logger.debug(f"⏭️ Updated meeting: {topic} ({meeting_id})")

                    # Process attendees
                    for row in rows:
                        if not row.attendee_email or not row.attendee_email.strip():
                            continue

                        attendee_email = row.attendee_email.strip()
                        attendee_name = (
                            row.attendee_name or ""
                        ).strip() or attendee_email
                        attendee_duration = (
                            parse_duration_string(row.attendee_duration) or 0
                        )

                        # Try to match to CODA user by email
                        user = None
                        try:
                            # Try CustomerUser first (if it exists)
                            try:
                                from accounts.models import CustomerUser

                                user = CustomerUser.objects.filter(
                                    email__iexact=attendee_email
                                ).first()
                            except (ImportError, AttributeError):
                                # Fallback to standard User model
                                user = User.objects.filter(
                                    email__iexact=attendee_email
                                ).first()
                        except Exception as e:
                            logger.debug(f"User lookup error for {attendee_email}: {e}")
                            user = None

                        attendee, created = MeetingAttendee.objects.get_or_create(
                            meeting=meeting,
                            attendee_email=attendee_email,
                            defaults={
                                "attendee_name": attendee_name,
                                "duration_minutes": attendee_duration,
                                "user": user,
                                "is_organizer": False,  # Legacy data doesn't have this
                            },
                        )

                        if created:
                            stats["attendees_created"] += 1
                        else:
                            stats["attendees_updated"] += 1
                            # Update duration if new value is higher, and update name if better
                            update_fields = []
                            if attendee_duration > attendee.duration_minutes:
                                attendee.duration_minutes = attendee_duration
                                update_fields.append("duration_minutes")
                            if (
                                attendee_name
                                and attendee_name != attendee.attendee_name
                            ):
                                attendee.attendee_name = attendee_name
                                update_fields.append("attendee_name")
                            if user and not attendee.user:
                                attendee.user = user
                                update_fields.append("user")
                            if update_fields:
                                attendee.save(update_fields=update_fields)
            else:
                # Dry run: just count
                existing = Meeting.objects.filter(meeting_id=meeting_id).exists()
                if existing:
                    stats["meetings_updated"] += 1
                else:
                    stats["meetings_created"] += 1

                # Dry run: count unique attendees
                unique_emails = set()
                for row in rows:
                    if row.attendee_email and row.attendee_email.strip():
                        unique_emails.add(row.attendee_email.strip())

                # Check how many already exist
                existing_meeting = Meeting.objects.filter(meeting_id=meeting_id).first()
                if existing_meeting:
                    existing_emails = set(
                        MeetingAttendee.objects.filter(
                            meeting=existing_meeting
                        ).values_list("attendee_email", flat=True)
                    )
                    new_emails = unique_emails - existing_emails
                    stats["attendees_created"] += len(new_emails)
                    stats["attendees_updated"] += len(unique_emails & existing_emails)
                else:
                    stats["attendees_created"] += len(unique_emails)
        except Exception as e:
            logger.error(
                f"Error processing meeting_id {meeting_id}: {e}", exc_info=True
            )
            # Count all rows in this meeting group as skipped due to error
            stats["rows_skipped"] += len(rows)

    return stats
