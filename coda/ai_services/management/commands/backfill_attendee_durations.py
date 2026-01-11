"""
Backfill corrupted attendee durations (seconds stored as minutes).

This command:
1. Finds attendee rows where duration_minutes > meeting.duration_minutes * 5
2. Converts duration from seconds to minutes (CEIL(seconds/60))
3. Updates attendee rows safely
4. Reports statistics

Usage:
    poetry run python coda/manage.py backfill_attendee_durations --service all --days 120 --dry-run
    poetry run python coda/manage.py backfill_attendee_durations --service all --days 120
"""

import logging
import math
from datetime import timedelta

from ai_services.models import Meeting, MeetingAttendee
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill corrupted attendee durations (seconds stored as minutes)"

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
            default=None,
            help="Maximum number of attendees to process (default: no limit)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode (do not update, only report)",
        )
        parser.add_argument(
            "--threshold-multiplier",
            type=float,
            default=5.0,
            help="Multiplier threshold for detecting seconds (default: 5.0)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )

    def handle(self, *args, **options):
        service_option = options["service"]
        days = options["days"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        threshold_multiplier = options["threshold_multiplier"]
        verbose = options["verbose"]

        services_to_backfill = []
        if service_option in ["internal", "all"]:
            services_to_backfill.append("gotomeeting_internal")
        if service_option in ["external", "all"]:
            services_to_backfill.append("gotomeeting_external")

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f"Starting attendee duration backfill...")
        self.stdout.write(f"  Service(s): {', '.join(services_to_backfill)}")
        self.stdout.write(f"  Days: {days}")
        self.stdout.write(f"  Cutoff date: {cutoff_date.date()}")
        self.stdout.write(f"  Threshold multiplier: {threshold_multiplier}x")
        self.stdout.write(f"  Dry run: {dry_run}")
        self.stdout.write("")

        total_found = 0
        total_updated = 0
        total_skipped = 0

        for service_name in services_to_backfill:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing service: {service_name}")
            self.stdout.write(f"{'='*60}")

            # Find suspicious attendees: duration_minutes > meeting.duration_minutes * threshold
            # Only process attendees where both duration_minutes > 0 and meeting.duration_minutes > 0
            suspicious_qs = (
                MeetingAttendee.objects.select_related("meeting")
                .filter(
                    meeting__service_name=service_name,
                    meeting__start_time__gte=cutoff_date,
                    duration_minutes__gt=0,
                    meeting__duration_minutes__gt=0,
                )
                .annotate(meeting_duration=F("meeting__duration_minutes"))
                .filter(
                    duration_minutes__gt=F("meeting_duration") * threshold_multiplier
                )
            )

            if limit:
                suspicious_qs = suspicious_qs[:limit]

            suspicious_count = suspicious_qs.count()
            total_found += suspicious_count

            self.stdout.write(
                f"Found {suspicious_count} suspicious attendee duration(s)"
            )

            if suspicious_count == 0:
                continue

            # Process each suspicious attendee
            updated_count = 0
            skipped_count = 0

            for attendee in suspicious_qs:
                original_duration = attendee.duration_minutes
                meeting_duration = attendee.meeting.duration_minutes
                ratio = (
                    original_duration / meeting_duration if meeting_duration > 0 else 0
                )

                # Convert from seconds to minutes (ceiling)
                corrected_duration = math.ceil(original_duration / 60.0)

                if verbose or dry_run:
                    self.stdout.write(
                        f"  Attendee ID {attendee.id}: {attendee.attendee_name[:30]:<30} | "
                        f"Original: {original_duration:>6} min | Meeting: {meeting_duration:>6} min | "
                        f"Ratio: {ratio:>6.1f}x | Corrected: {corrected_duration:>6} min"
                    )

                if dry_run:
                    skipped_count += 1
                    continue

                # Update attendee duration
                try:
                    attendee.duration_minutes = corrected_duration
                    attendee.save(update_fields=["duration_minutes"])
                    updated_count += 1
                    total_updated += 1
                except Exception as e:
                    logger.error(f"Error updating attendee {attendee.id}: {e}")
                    skipped_count += 1
                    total_skipped += 1
                    if verbose:
                        self.stdout.write(f"    ❌ Error: {e}")

            if not dry_run:
                self.stdout.write(f"  ✅ Updated: {updated_count}")
            if skipped_count > 0:
                self.stdout.write(f"  ⚠️  Skipped: {skipped_count}")

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("SUMMARY")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Total suspicious attendees found: {total_found}")
        if dry_run:
            self.stdout.write(f"  (Dry run - no updates made)")
        else:
            self.stdout.write(f"Total updated: {total_updated}")
            self.stdout.write(f"Total skipped: {total_skipped}")

        self.stdout.write("\n✅ Backfill complete!")
