"""
Management command to import legacy GotoMeetings data into normalized Meeting + MeetingAttendee tables.

Usage:
    python manage.py import_legacy_gotomeetings
    python manage.py import_legacy_gotomeetings --service gotomeeting_internal --limit 100
    python manage.py import_legacy_gotomeetings --since 2024-01-01 --dry-run
"""

from datetime import datetime

from ai_services.services.legacy_gotomeeting_import_service import \
    import_legacy_rows
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Import legacy GotoMeetings data into normalized Meeting + MeetingAttendee tables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            default="gotomeeting_external",
            help="Service name to assign to imported meetings (default: gotomeeting_external)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of legacy rows to process (default: all)",
        )
        parser.add_argument(
            "--since",
            type=str,
            default=None,
            help="Only import rows created/updated after this date (YYYY-MM-DD format)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode - show what would be imported without saving",
        )

    def handle(self, *args, **options):
        service_name = options["service"]
        limit = options["limit"]
        since_str = options["since"]
        dry_run = options["dry_run"]

        # Parse since date
        since = None
        if since_str:
            try:
                since = datetime.strptime(since_str, "%Y-%m-%d")
                since = timezone.make_aware(since)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Invalid date format: {since_str}. Use YYYY-MM-DD format."
                    )
                )
                return

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Legacy GoToMeeting Import"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"Service name: {service_name}")
        if limit:
            self.stdout.write(f"Limit: {limit} rows")
        if since:
            self.stdout.write(f'Since: {since.strftime("%Y-%m-%d")}')
        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be saved")
            )
        self.stdout.write("")

        # Run import
        try:
            stats = import_legacy_rows(
                service_name=service_name, limit=limit, since=since, dry_run=dry_run
            )

            # Display results
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("Import Results"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f'Legacy rows scanned: {stats["legacy_rows_scanned"]}')
            self.stdout.write(f'Meetings created: {stats["meetings_created"]}')
            self.stdout.write(f'Meetings updated: {stats["meetings_updated"]}')
            self.stdout.write(f'Attendees created: {stats["attendees_created"]}')
            self.stdout.write(f'Attendees updated: {stats["attendees_updated"]}')
            self.stdout.write(f'Rows skipped: {stats["rows_skipped"]}')
            self.stdout.write(f'Parse failures: {stats["parse_failures"]}')
            self.stdout.write("")

            total_processed = (
                stats["meetings_created"]
                + stats["meetings_updated"]
                + stats["attendees_created"]
                + stats["attendees_updated"]
            )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"🔍 DRY RUN: Would process {total_processed} records"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully processed {total_processed} records"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            raise
