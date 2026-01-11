"""
Management command to sync GoToMeeting meetings.

Usage:
    poetry run python coda/manage.py sync_goto_meetings
    poetry run python coda/manage.py sync_goto_meetings --hours 24
    poetry run python coda/manage.py sync_goto_meetings --start 2025-12-27 --end 2025-12-28

Phase 2A: First incremental step after OAuth is working.
"""

import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync GoToMeeting meetings for a specified time range"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Number of hours back from now to sync (default: 24)",
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date in YYYY-MM-DD format (UTC). If provided, --end must also be provided.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date in YYYY-MM-DD format (UTC). If provided, --start must also be provided.",
        )

    def handle(self, *args, **options):
        """Execute the sync command."""
        from ai_services.services.goto_meeting_sync_service import sync

        hours = options["hours"]
        start_str = options["start"]
        end_str = options["end"]

        # Validate arguments
        if (start_str and not end_str) or (end_str and not start_str):
            raise CommandError(
                "Both --start and --end must be provided together, or neither."
            )

        # Calculate start and end datetimes
        if start_str and end_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

                if start_date > end_date:
                    raise CommandError(
                        f"Start date ({start_str}) must be <= end date ({end_str})"
                    )

                # Convert to timezone-aware datetimes
                # Start at 00:00:00, end at 23:59:59
                start_dt = timezone.make_aware(
                    datetime.combine(start_date, datetime.min.time())
                )
                end_dt = timezone.make_aware(
                    datetime.combine(
                        end_date, datetime.max.time().replace(microsecond=0)
                    )
                )

            except ValueError as e:
                raise CommandError(f"Invalid date format. Use YYYY-MM-DD. Error: {e}")
        else:
            # Default: last N hours
            end_dt = timezone.now()
            start_dt = end_dt - timedelta(hours=hours)

        # Determine service_name (default to gotomeeting_external for backward compatibility)
        service_name = "gotomeeting_external"  # Default to external account

        self.stdout.write(
            f"Syncing GoToMeeting meetings for service '{service_name}' from {start_dt} to {end_dt}..."
        )

        try:
            result = sync(start_dt, end_dt, service_name=service_name)

            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Sync complete: "
                        f"{result['meetings_fetched']} meetings fetched, "
                        f"{result['meetings_created']} created, "
                        f"{result['meetings_updated']} updated, "
                        f"{result['attendees_created']} attendees created, "
                        f"{result['attendees_updated']} attendees updated"
                    )
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.stdout.write(self.style.ERROR(f"❌ Sync failed: {error_msg}"))
                raise CommandError(f"Meeting sync failed: {error_msg}")

        except RuntimeError as e:
            # OAuth token missing
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {str(e)}\n"
                    f"Please visit /management/oauth/login/ to authenticate first."
                )
            )
            raise CommandError("OAuth token not available")

        except Exception as e:
            logger.error(
                f"Unexpected error in sync_goto_meetings command: {e}", exc_info=True
            )
            raise CommandError(f"An unexpected error occurred: {e}")
