"""
Management command to sync GoToMeeting meetings only if data is stale.

Usage:
    poetry run python coda/manage.py sync_goto_meetings_if_stale
    poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --max-age-minutes 60 --hours 24
    poetry run python coda/manage.py sync_goto_meetings_if_stale --service internal --max-age-minutes 120

This command is designed for scheduled execution (cron, Heroku Scheduler, Celery Beat).
It checks if the last successful sync is within max_age_minutes. If fresh, skips sync.
If stale or no sync found, runs the sync.

Phase 2C: Scheduled execution support with freshness checks.
"""

import logging
from datetime import timedelta

from ai_services.services.goto_meeting_sync_service import (
    get_last_successful_sync, is_meeting_data_fresh, sync)
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync GoToMeeting meetings only if data is stale (for scheduled execution)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            default="external",
            choices=["external", "internal"],
            help="Service account to sync (external or internal). Defaults to external.",
        )
        parser.add_argument(
            "--max-age-minutes",
            type=int,
            default=1440,  # 24 hours
            help="Maximum age in minutes before data is considered stale (default: 1440 = 24 hours)",
        )
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Number of hours back from now to sync. Defaults to 24.",
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date in YYYY-MM-DD format. If provided, --end must also be provided.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date in YYYY-MM-DD format. If provided, --start must also be provided.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force sync even if data is fresh (ignores freshness check)",
        )

    def handle(self, *args, **options):
        service_param = options["service"]
        service_name = f"gotomeeting_{service_param}"
        max_age_minutes = options["max_age_minutes"]
        hours_back = options["hours"]
        start_date_str = options.get("start")
        end_date_str = options.get("end")
        force = options.get("force", False)

        # Determine date range
        if start_date_str and end_date_str:
            try:
                from datetime import datetime

                start_dt = timezone.make_aware(
                    datetime.strptime(start_date_str, "%Y-%m-%d")
                )
                end_dt = timezone.make_aware(
                    datetime.strptime(end_date_str, "%Y-%m-%d")
                    + timedelta(days=1, microseconds=-1)
                )
            except ValueError:
                raise CommandError("Invalid date format. Use YYYY-MM-DD.")
            if start_dt > end_dt:
                raise CommandError("Start date must be less than or equal to end date.")
        elif start_date_str or end_date_str:
            raise CommandError(
                "Both --start and --end must be provided together, or neither."
            )
        else:
            # Default to last N hours
            end_dt = timezone.now()
            start_dt = end_dt - timedelta(hours=hours_back)

        # Check freshness (unless force is set)
        if not force:
            is_fresh = is_meeting_data_fresh(
                service_name, max_age_minutes=max_age_minutes
            )

            if is_fresh:
                last_sync = get_last_successful_sync(service_name)
                if last_sync and last_sync.finished_at:
                    age_minutes = int(
                        (timezone.now() - last_sync.finished_at).total_seconds() / 60
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Data is fresh for service '{service_name}' "
                            f"(last sync: {age_minutes} minutes ago, max age: {max_age_minutes} minutes). "
                            f"Skipping sync."
                        )
                    )
                    return
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ No previous successful sync found for '{service_name}'. Proceeding with sync."
                        )
                    )
            else:
                last_sync = get_last_successful_sync(service_name)
                if last_sync and last_sync.finished_at:
                    age_minutes = int(
                        (timezone.now() - last_sync.finished_at).total_seconds() / 60
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Data is stale for service '{service_name}' "
                            f"(last sync: {age_minutes} minutes ago, max age: {max_age_minutes} minutes). "
                            f"Proceeding with sync."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ No previous successful sync found for '{service_name}'. Proceeding with sync."
                        )
                    )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"🔄 Force flag set - skipping freshness check for '{service_name}'. Proceeding with sync."
                )
            )

        # Perform sync
        self.stdout.write(
            f"Syncing GoToMeeting meetings for service '{service_name}' from {start_dt} to {end_dt}..."
        )

        try:
            result = sync(start_dt, end_dt, service_name=service_name)

            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Sync complete for '{service_name}': {result['meetings_fetched']} meetings fetched, "
                        f"{result['meetings_created']} created, {result['meetings_updated']} updated, "
                        f"{result['attendees_created']} attendees created, {result['attendees_updated']} attendees updated"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Sync failed for '{service_name}': {result['error']}"
                    )
                )
                raise CommandError(f"Meeting sync failed: {result['error']}")

        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            self.stdout.write(
                self.style.NOTICE(
                    f"Please ensure you have authenticated with GoToMeeting for service '{service_param}' "
                    f"by visiting: /management/oauth/login/?service={service_param}"
                )
            )
            raise CommandError(f"OAuth token error: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during sync_goto_meetings_if_stale command: {e}",
                exc_info=True,
            )
            raise CommandError(f"An unexpected error occurred: {e}")
