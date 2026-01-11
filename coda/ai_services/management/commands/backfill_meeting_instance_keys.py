"""
Backfill meeting instance keys (sessionId and provider_meeting_instance_key) for existing meetings.

This command:
1. Fetches historical meetings from GoToMeeting API for a date range
2. Matches them to existing meetings in DB by (start_time ± tolerance, topic, service_name)
3. Updates sessionId and extracts meetingInstanceKey from attendee response
4. Stores provider_meeting_instance_key on Meeting model

Usage:
    poetry run python coda/manage.py backfill_meeting_instance_keys --service internal --days 120 --limit 50
"""

import logging
from datetime import timedelta

import requests
from ai_services.models import Meeting
from ai_services.services.attendee_sync_service import \
    fetch_attendees_for_meeting
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from shared_core.utils.oauth import get_access_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill meeting instance keys (sessionId and provider_meeting_instance_key) for existing meetings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="all",
            help="Service to backfill (default: all)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=120,
            help="Number of days to look back (default: 120)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of meetings to process (default: 50)",
        )
        parser.add_argument(
            "--tolerance-minutes",
            type=int,
            default=5,
            help="Time tolerance for matching meetings (default: 5 minutes)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force selection even when ambiguous (use with caution)",
        )

    def handle(self, *args, **options):
        service_option = options["service"]
        days = options["days"]
        limit = options["limit"]
        tolerance_minutes = options["tolerance_minutes"]
        verbose = options["verbose"]
        force = options["force"]

        services_to_backfill = []
        if service_option in ["internal", "all"]:
            services_to_backfill.append("gotomeeting_internal")
        if service_option in ["external", "all"]:
            services_to_backfill.append("gotomeeting_external")

        self.stdout.write(
            self.style.SUCCESS(f"\n🔄 Backfilling Meeting Instance Keys 🔄\n")
        )
        self.stdout.write(f"Service: {service_option}")
        self.stdout.write(f"Days: {days}")
        self.stdout.write(f"Limit: {limit} meetings per service")
        self.stdout.write(f"Tolerance: ±{tolerance_minutes} minutes\n")

        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for service_name in services_to_backfill:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"Processing: {service_name}")
            self.stdout.write(f"{'='*80}\n")

            # Get access token
            access_token = get_access_token(service_name=service_name)
            if not access_token:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  No OAuth token available for {service_name}. Skipping..."
                    )
                )
                continue

            # Get meetings from DB that need backfilling
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            # Focus on session_id backfill (provider_meeting_instance_key is secondary)
            meetings_to_backfill = (
                Meeting.objects.filter(
                    start_time__gte=start_date,
                    start_time__lte=end_date,
                    service_name=service_name,
                )
                .filter(Q(session_id__isnull=True) | Q(session_id=""))
                .order_by("-start_time")[:limit]
            )

            meeting_count = meetings_to_backfill.count()
            self.stdout.write(f"Found {meeting_count} meetings needing backfill\n")

            if meeting_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ All meetings already have instance keys")
                )
                continue

            # Fetch historical meetings from API
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start_str}&endDate={end_str}"

            try:
                response = requests.get(url=url, headers=headers, timeout=30)
                response.raise_for_status()
                api_meetings = response.json()

                self.stdout.write(f"📊 Fetched {len(api_meetings)} meetings from API\n")

                if not api_meetings:
                    self.stdout.write(f"  No meetings found in API for this period\n")
                    continue

                # Match API meetings to DB meetings
                updated_count = 0
                skipped_count = 0
                error_count = 0

                for db_meeting in meetings_to_backfill:
                    # Find matching API meeting(s) by start_time ± tolerance and topic
                    matching_api_meetings = []

                    for api_meeting in api_meetings:
                        api_meeting_id = api_meeting.get("meetingId")
                        if api_meeting_id != db_meeting.meeting_id:
                            continue

                        # Check start_time match (within tolerance)
                        api_start_str = api_meeting.get("startTime", "")
                        if api_start_str:
                            try:
                                from dateutil import parser

                                api_start = parser.isoparse(
                                    api_start_str.replace(".+", "+")
                                )
                                time_diff = abs(
                                    (api_start - db_meeting.start_time).total_seconds()
                                    / 60
                                )

                                if time_diff <= tolerance_minutes:
                                    # Also check topic similarity
                                    api_topic = api_meeting.get("subject", "").strip()
                                    db_topic = (
                                        db_meeting.topic.strip()
                                        if db_meeting.topic
                                        else ""
                                    )
                                    topic_match = (
                                        not api_topic
                                        or not db_topic
                                        or api_topic.lower() == db_topic.lower()
                                        or api_topic.lower() in db_topic.lower()
                                        or db_topic.lower() in api_topic.lower()
                                    )

                                    if topic_match:
                                        matching_api_meetings.append(
                                            (api_meeting, time_diff)
                                        )
                            except Exception as e:
                                if verbose:
                                    logger.debug(
                                        f"Could not parse API startTime for {api_meeting_id}: {e}"
                                    )

                    # Handle ambiguous matches
                    if len(matching_api_meetings) == 0:
                        skipped_count += 1
                        if verbose:
                            self.stdout.write(
                                f"  ⏭️  Skipped: {db_meeting.meeting_id} (no API match)"
                            )
                        continue
                    elif len(matching_api_meetings) > 1 and not force:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️  AMBIGUOUS: {db_meeting.meeting_id} matches {len(matching_api_meetings)} API meetings. "
                                f"Use --force to select best candidate."
                            )
                        )
                        continue

                    # Select best matching API meeting (closest time if multiple)
                    matching_api_meetings.sort(
                        key=lambda x: x[1]
                    )  # Sort by time difference
                    matching_api_meeting, _ = matching_api_meetings[0]

                    # Extract sessionId from API meeting
                    api_session_id = matching_api_meeting.get("sessionId", "")

                    # Fetch attendees to extract meetingInstanceKey using deterministic selection
                    extracted_instance_key = None
                    selection_reason = None
                    if api_session_id or db_meeting.meeting_id:
                        try:
                            attendees_data, extracted_instance_key, selection_reason = (
                                fetch_attendees_for_meeting(
                                    db_meeting.meeting_id,
                                    access_token,
                                    session_id=api_session_id,
                                    meeting_instance_key=None,  # Don't filter - we want to extract it
                                    meeting_start_time=db_meeting.start_time,
                                    verbose=verbose,
                                )
                            )

                            if verbose:
                                if extracted_instance_key:
                                    self.stdout.write(
                                        f"  Extracted meetingInstanceKey: {extracted_instance_key} "
                                        f"(reason: {selection_reason})"
                                    )
                                else:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"  ⚠️  Could not determine instance key (reason: {selection_reason})"
                                        )
                                    )

                            # Skip if ambiguous and not forced
                            if selection_reason == "ambiguous" and not force:
                                skipped_count += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  ⚠️  AMBIGUOUS instance key for {db_meeting.meeting_id}. "
                                        f"Use --force to override."
                                    )
                                )
                                continue
                        except Exception as e:
                            error_count += 1
                            if verbose:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  ❌ Error fetching attendees for {db_meeting.meeting_id}: {e}"
                                    )
                                )
                            continue

                    # Update DB meeting only if instance key selection is confident
                    if not extracted_instance_key or selection_reason in [
                        "ambiguous",
                        "no_instance_keys",
                        "no_attendees",
                    ]:
                        if selection_reason != "ambiguous" or not force:
                            skipped_count += 1
                            continue

                    update_fields = []
                    if api_session_id and db_meeting.session_id != api_session_id:
                        db_meeting.session_id = api_session_id
                        update_fields.append("session_id")

                    if extracted_instance_key and selection_reason not in [
                        "ambiguous",
                        "no_instance_keys",
                        "no_attendees",
                    ]:
                        if (
                            db_meeting.provider_meeting_instance_key
                            != extracted_instance_key
                        ):
                            db_meeting.provider_meeting_instance_key = (
                                extracted_instance_key
                            )
                            update_fields.append("provider_meeting_instance_key")
                    elif force and extracted_instance_key:
                        # Force update even if ambiguous
                        db_meeting.provider_meeting_instance_key = (
                            extracted_instance_key
                        )
                        update_fields.append("provider_meeting_instance_key")
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️  FORCED update for {db_meeting.meeting_id} "
                                    f"(ambiguous selection, reason: {selection_reason})"
                                )
                            )

                    if update_fields:
                        update_fields.append("updated_at")
                        db_meeting.save(update_fields=update_fields)
                        updated_count += 1

                        if verbose:
                            self.stdout.write(
                                f"  ✅ Updated: {db_meeting.meeting_id} "
                                f"(sessionId: {api_session_id or 'N/A'}, "
                                f"instanceKey: {extracted_instance_key or 'N/A'}, "
                                f"reason: {selection_reason})"
                            )
                    else:
                        skipped_count += 1
                        if verbose:
                            self.stdout.write(
                                f"  ⏭️  Skipped: {db_meeting.meeting_id} (no changes needed)"
                            )

                self.stdout.write(f"\n📊 Summary for {service_name}:")
                self.stdout.write(f"  Updated: {updated_count}")
                self.stdout.write(f"  Skipped: {skipped_count}")
                self.stdout.write(f"  Errors: {error_count}")

                total_updated += updated_count
                total_skipped += skipped_count
                total_errors += error_count

            except requests.exceptions.HTTPError as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ HTTP error for {service_name}: {e}")
                )
                if e.response.status_code == 401:
                    self.stdout.write("   OAuth token expired or invalid")
                total_errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error for {service_name}: {e}"))
                logger.exception("Error in backfill_meeting_instance_keys")
                total_errors += 1

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"📊 Overall Summary")
        self.stdout.write(f"{'='*80}\n")
        self.stdout.write(f"Total updated: {total_updated}")
        self.stdout.write(f"Total skipped: {total_skipped}")
        self.stdout.write(f"Total errors: {total_errors}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Backfill complete!\n"))
