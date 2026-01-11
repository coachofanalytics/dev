"""
Management command to sync meeting attendees from GoToMeeting API.

DB-first approach: selects meetings needing attendee refresh, then fetches attendees.

Usage:
    poetry run python coda/manage.py sync_meeting_attendees --service internal --days 120
    poetry run python coda/manage.py sync_meeting_attendees --service external --days 90 --limit 50
    poetry run python coda/manage.py sync_meeting_attendees --service all --days 30
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync meeting attendees from GoToMeeting API (DB-first selection)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="internal",
            help="Service to sync: internal (gotomeeting_internal), external (gotomeeting_external), or all (default: internal)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=120,
            help="Number of days to look back for meetings (default: 120)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of meetings to process (default: no limit)",
        )
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=24,
            help="Maximum age of attendee data before considered stale, in hours (default: 24)",
        )
        parser.add_argument(
            "--no-split-names",
            action="store_true",
            help='Disable splitting of combined attendee names (e.g., "EUNICE, JUDY AND NOREEN")',
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )
        parser.add_argument(
            "--reconcile",
            action="store_true",
            help="Run meeting-task reconciliation after attendee sync (creates TaskLinks)",
        )

    def handle(self, *args, **options):
        service_option = options["service"]
        days = options["days"]
        limit = options.get("limit")
        max_age_hours = options["max_age_hours"]
        split_names = not options["no_split_names"]
        verbose = options.get("verbose", False)

        # Map service option
        if service_option == "internal":
            service_name = "gotomeeting_internal"
        elif service_option == "external":
            service_name = "gotomeeting_external"
        else:
            service_name = None

        self.stdout.write(
            self.style.SUCCESS(f"\n🔄 Syncing Meeting Attendees (DB-First Selection)\n")
        )
        self.stdout.write(f"Service: {service_option}")
        self.stdout.write(f"Days: {days}")
        if limit:
            self.stdout.write(f"Limit: {limit}")
        self.stdout.write(f"Max age (stale threshold): {max_age_hours} hours")
        self.stdout.write(f"Split combined names: {split_names}\n")

        # Determine which services to sync
        if service_option == "all":
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
            services_to_sync = [service_name]

        # Import here to avoid circular imports
        from ai_services.services.attendee_sync_service import (
            get_meetings_needing_attendee_sync, sync_attendees_for_meetings)
        from shared_core.utils.oauth import get_access_token

        # Sync each service
        total_meetings_processed = 0
        total_meetings_success = 0
        total_meetings_failed = 0
        total_meetings_quarantined = 0
        total_attendees_created = 0
        total_attendees_updated = 0
        all_errors = []

        for svc_name in services_to_sync:
            # Check for OAuth token
            access_token = get_access_token(service_name=svc_name)
            if not access_token:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  No OAuth access token available for {svc_name}. Skipping..."
                    )
                )
                continue

            self.stdout.write(f"\n📡 Syncing {svc_name}...\n")

            # Get meetings needing attendee sync (DB-first)
            meetings = get_meetings_needing_attendee_sync(
                service_name=svc_name,
                days=days,
                limit=limit,
                max_age_hours=max_age_hours,
            )

            meeting_count = len(meetings)
            self.stdout.write(f"Found {meeting_count} meetings needing attendee sync")

            if meeting_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ No meetings need attendee sync for {svc_name}"
                    )
                )
                continue

            if verbose:
                # Show sample meetings
                for meeting in meetings[:5]:
                    # Use annotation if available (attendee_count_db), otherwise use property
                    attendee_count = getattr(meeting, "attendee_count_db", None)
                    if attendee_count is None:
                        attendee_count = (
                            meeting.attendee_count
                        )  # Use property as fallback
                    latest_update = getattr(meeting, "latest_attendee_update", None)
                    update_str = (
                        latest_update.strftime("%Y-%m-%d %H:%M")
                        if latest_update
                        else "never"
                    )
                    self.stdout.write(
                        f"  - Meeting {meeting.meeting_id}: {meeting.topic[:50]} "
                        f"(attendees: {attendee_count}, last updated: {update_str})"
                    )
                if meeting_count > 5:
                    self.stdout.write(f"  ... and {meeting_count - 5} more")

            # Sync attendees
            try:
                result = sync_attendees_for_meetings(
                    meetings, svc_name, access_token=access_token
                )

                if verbose:
                    # Show which identifiers were used
                    self.stdout.write(f"\n📋 Sample meetings processed:")
                    for meeting in meetings[:5]:
                        # Safe fallback: meeting_instance_key -> session_id -> meeting_id
                        identifier_used = (
                            getattr(meeting, "meeting_instance_key", None)
                            or getattr(meeting, "session_id", None)
                            or meeting.meeting_id
                        )
                        instance_key_display = (
                            getattr(meeting, "meeting_instance_key", None)
                            or getattr(meeting, "session_id", None)
                            or "N/A"
                        )
                        self.stdout.write(
                            f"  Meeting {meeting.meeting_id} ({meeting.service_name or 'N/A'}): "
                            f"identifier={identifier_used}, "
                            f"sessionId={getattr(meeting, 'session_id', None) or 'N/A'}, "
                            f"instanceKey={instance_key_display}"
                        )

                # Accumulate results
                total_meetings_processed += result["meetings_processed"]
                total_meetings_success += result["meetings_success"]
                total_meetings_failed += result["meetings_failed"]
                total_meetings_quarantined += result.get("meetings_quarantined", 0)
                total_attendees_created += result["attendees_created"]
                total_attendees_updated += result["attendees_updated"]
                all_errors.extend(result["errors"])

                # Display per-service results
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Synced {svc_name}: {result["meetings_success"]}/{result["meetings_processed"]} meetings '
                        f'(quarantined: {result.get("meetings_quarantined", 0)}), '
                        f'{result["attendees_created"]} attendees created, {result["attendees_updated"]} updated'
                    )
                )

                if result["errors"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  {len(result["errors"])} errors occurred (see logs for details)'
                        )
                    )

            except Exception as e:
                logger.error(
                    f"Unexpected error syncing attendees for {svc_name}: {e}",
                    exc_info=True,
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Sync failed for {svc_name} with unexpected error: {e}"
                    )
                )
                continue

        # Display summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Summary: {total_meetings_processed} meetings processed, "
                f"{total_meetings_success} succeeded, {total_meetings_failed} failed, "
                f"{total_meetings_quarantined} quarantined (404/provider_not_found), "
                f"{total_attendees_created} attendees created, {total_attendees_updated} updated"
            )
        )

        if all_errors:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  {len(all_errors)} errors occurred. Check logs for details."
                )
            )

        if total_meetings_processed == 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  No meetings found needing attendee sync for the specified criteria."
                )
            )

        # Verification queries
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write("📋 Verification Queries")
        self.stdout.write(f'{"="*80}\n')

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write("-- Count attendees by service")
        self.stdout.write("SELECT service_name, COUNT(*) as meeting_count,")
        self.stdout.write(
            "       SUM((SELECT COUNT(*) FROM ai_services_meetingattendee WHERE meeting_id = m.id)) as attendee_count"
        )
        self.stdout.write("FROM ai_services_meeting m")
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write("GROUP BY service_name;\n")

        self.stdout.write("-- Latest attendee update timestamps")
        self.stdout.write("SELECT MAX(updated_at) as latest_attendee_update")
        self.stdout.write("FROM ai_services_meetingattendee ma")
        self.stdout.write("JOIN ai_services_meeting m ON ma.meeting_id = m.id")
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write(";\n")

        self.stdout.write("-- Top meetings by attendee count")
        self.stdout.write(
            "SELECT m.meeting_id, m.topic, m.service_name, COUNT(ma.id) as attendee_count"
        )
        self.stdout.write("FROM ai_services_meeting m")
        self.stdout.write(
            "LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id"
        )
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write("GROUP BY m.id, m.meeting_id, m.topic, m.service_name")
        self.stdout.write("ORDER BY attendee_count DESC")
        self.stdout.write("LIMIT 10;\n")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Attendee sync complete!\n"))

        # Optional: Run reconciliation after attendee sync
        if options.get("reconcile"):
            self.stdout.write("\n🔄 Running meeting-task reconciliation...\n")
            try:
                from management.services.meeting_task_reconciliation_service import \
                    MeetingTaskReconciliationService

                # Run reconciliation for the same date range
                service = MeetingTaskReconciliationService(
                    time_window_days=7, dry_run=False
                )
                recon_stats = service.reconcile_meetings(
                    start_date=timezone.now() - timedelta(days=days),
                    end_date=timezone.now(),
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Reconciliation complete: {recon_stats['meetings_linked']} meetings linked, "
                        f"{recon_stats['tasklinks_created']} TaskLinks created, "
                        f"{recon_stats['tasklinks_updated']} TaskLinks updated"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Reconciliation failed: {e}"))
                logger.error(f"Reconciliation error: {e}", exc_info=True)
