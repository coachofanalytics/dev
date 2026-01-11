"""
Management command to sync GoToMeeting meetings from API into database.

Phase M1: Non-UI-dependent meeting sync mechanism.

Usage:
    python manage.py sync_gotomeetings
    python manage.py sync_gotomeetings --start 2024-12-01 --end 2024-12-31
    python manage.py sync_gotomeetings --days 7
"""

import logging
import sys
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync GoToMeeting meetings from API into Meeting and MeetingAttendee models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=str,
            help="Start date (YYYY-MM-DD). If not provided, defaults to 7 days ago.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date (YYYY-MM-DD). If not provided, defaults to today.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days back from today to sync (default: 7). Ignored if --start is provided.",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["gotomeeting_internal", "gotomeeting_external", "all"],
            default="gotomeeting_internal",
            help='Service name to sync (default: gotomeeting_internal). Use "all" to sync both services.',
        )

    def handle(self, *args, **options):
        try:
            from ai_services.services.meeting_sync_service import \
                sync_meetings_for_range
            from shared_core.utils.oauth import get_access_token
        except ImportError as e:
            raise CommandError(f"Failed to import required modules: {e}")

        # Parse date arguments
        today = date.today()

        if options["start"]:
            try:
                start_date = date.fromisoformat(options["start"])
            except ValueError:
                raise CommandError(
                    f"Invalid --start date format: {options['start']}. Use YYYY-MM-DD."
                )
        else:
            # Default to --days back from today
            start_date = today - timedelta(days=options["days"])

        if options["end"]:
            try:
                end_date = date.fromisoformat(options["end"])
            except ValueError:
                raise CommandError(
                    f"Invalid --end date format: {options['end']}. Use YYYY-MM-DD."
                )
        else:
            end_date = today

        # Validate date range
        if start_date > end_date:
            raise CommandError(
                f"Start date ({start_date}) must be <= end date ({end_date})"
            )

        # Get service parameter
        service_param = options.get("service", "gotomeeting_internal")

        # Determine which services to sync
        if service_param == "all":
            services_to_sync = []
            from ai_services.utils.goto_service_registry import \
                list_goto_services

            try:
                services_to_sync = list_goto_services()
                if not services_to_sync:
                    raise CommandError(
                        "No GoToMeeting services configured. Please set up OAuth credentials."
                    )
            except ImportError:
                # Fallback to internal if registry not available
                services_to_sync = ["gotomeeting_internal"]
        else:
            services_to_sync = [service_param]

        # Display sync parameters
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🔄 Syncing GoToMeeting meetings from {start_date} to {end_date}...\n"
            )
        )

        # Sync each service
        total_meetings_created = 0
        total_meetings_updated = 0
        total_attendees_created = 0
        total_attendees_updated = 0
        total_meetings_fetched = 0

        for service_name in services_to_sync:
            # Check for OAuth token for this service
            access_token = get_access_token(service_name=service_name)
            if not access_token:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  No OAuth access token available for {service_name}. Skipping..."
                    )
                )
                continue

            self.stdout.write(f"\n📡 Syncing {service_name}...\n")

            # Call sync service
            try:
                result = sync_meetings_for_range(
                    start_date, end_date, service_name=service_name
                )

                if not result["success"]:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Sync failed for {service_name}: {result.get("error", "Unknown error")}'
                        )
                    )
                    continue

                # Accumulate results
                total_meetings_fetched += result["meetings_fetched"]
                total_meetings_created += result["meetings_created"]
                total_meetings_updated += result["meetings_updated"]
                total_attendees_created += result["attendees_created"]
                total_attendees_updated += result["attendees_updated"]

                # Display per-service results
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Synced {service_name}: {result["meetings_fetched"]} fetched, '
                        f'{result["meetings_created"]} created, {result["meetings_updated"]} updated'
                    )
                )

            except ValueError as e:
                raise CommandError(f"Invalid date range: {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error syncing {service_name}: {e}", exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Sync failed for {service_name} with unexpected error: {e}"
                    )
                )
                continue

        # Display summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Summary: {total_meetings_fetched} meetings fetched, "
                f"{total_meetings_created} created, {total_meetings_updated} updated, "
                f"{total_attendees_created} attendees created, {total_attendees_updated} attendees updated"
            )
        )

        if total_meetings_fetched == 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  No meetings found for the specified date range."
                )
            )
