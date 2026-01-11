"""
Management command to backfill attendee duration_minutes for historical data.

Fixes attendee rows where duration_minutes appears to be stored in seconds
instead of minutes.

Logic:
- For each attendee joined to meeting, if attendee.duration_minutes > meeting.duration_minutes * 5
  then set attendee.duration_minutes = ceil(attendee.duration_minutes / 60)
"""

import logging
import math
from datetime import timedelta

from ai_services.models import Meeting, MeetingAttendee
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill attendee duration_minutes for historical data (convert seconds to minutes)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="all",
            help="Service to process (default: all)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=260,
            help="Number of days to look back (default: 260)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="Maximum attendees to process (default: 1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=5.0,
            help="Multiplier threshold for detecting seconds (default: 5.0)",
        )

    def handle(self, *args, **options):
        service_name = options.get("service", "all")
        days = options.get("days", 260)
        limit = options.get("limit", 1000)
        dry_run = options.get("dry_run", False)
        threshold = options.get("threshold", 5.0)

        self.stdout.write(
            self.style.SUCCESS("🔧 Backfilling attendee duration_minutes...\n")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("  ⚠️  DRY RUN MODE - No changes will be made\n")
            )

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Build service filter
        if service_name == "all":
            service_filter = {}
        else:
            service_name_full = f"gotomeeting_{service_name}"
            service_filter = {"service_name": service_name_full}

        # Find attendees with suspicious duration
        # Join with Meeting to check duration_minutes against meeting.duration_minutes
        attendees = (
            MeetingAttendee.objects.filter(
                meeting__start_time__gte=start_date,
                meeting__start_time__lte=end_date,
                **service_filter,
            )
            .select_related("meeting")
            .order_by("-meeting__start_time")[:limit]
        )

        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(
            f"  Processing up to {limit} attendees from last {days} days...\n"
        )

        with transaction.atomic():
            for attendee in attendees:
                meeting = attendee.meeting

                # Skip if meeting duration is missing or zero
                if not meeting.duration_minutes or meeting.duration_minutes <= 0:
                    skipped_count += 1
                    continue

                # Check if attendee duration looks like seconds
                if attendee.duration_minutes > meeting.duration_minutes * threshold:
                    # Likely in seconds, convert to minutes
                    old_duration = attendee.duration_minutes
                    new_duration = math.ceil(attendee.duration_minutes / 60)

                    if dry_run:
                        self.stdout.write(
                            f"  Would update: Attendee {attendee.id} "
                            f"(meeting {meeting.meeting_id}, {meeting.start_time.date()}) "
                            f"{old_duration} -> {new_duration} minutes "
                            f"(meeting duration: {meeting.duration_minutes} min)"
                        )
                    else:
                        try:
                            attendee.duration_minutes = new_duration
                            attendee.save(
                                update_fields=["duration_minutes", "updated_at"]
                            )
                            updated_count += 1

                            if updated_count % 100 == 0:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"  ✅ Updated {updated_count} attendees..."
                                    )
                                )
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error updating attendee {attendee.id}: {e}")
                else:
                    skipped_count += 1

        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n✅ Backfill complete!\n"))
        if dry_run:
            self.stdout.write(f"  Would update: {updated_count}")
        else:
            self.stdout.write(f"  Updated: {updated_count}")
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(
            f"  Total processed: {updated_count + skipped_count + error_count}\n"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  This was a dry run. Run without --dry-run to apply changes.\n"
                )
            )
