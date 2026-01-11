"""
Reconcile GoToMeeting meetings: fetch from API and mark DB meetings as provider_not_found if missing.

This command:
1. Fetches meetings from GoToMeeting API for a date range
2. Upserts them using composite keys (existing logic)
3. Identifies DB meetings in the window that are NOT present in API response
4. Marks those meetings as provider_not_found=True (or optionally deletes them)
5. Produces a summary: inserted/updated/quarantined/deleted

Usage:
    poetry run python coda/manage.py reconcile_gotomeeting_meetings --service external --days 120 --dry-run
    poetry run python coda/manage.py reconcile_gotomeeting_meetings --service external --days 120 --delete-missing
"""

import logging
from datetime import timedelta

from ai_services.models import Meeting
from ai_services.services.goto_meeting_sync_service import (fetch_meetings,
                                                            upsert_meetings)
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from shared_core.utils.oauth import get_access_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reconcile GoToMeeting meetings: fetch from API and mark missing DB meetings as provider_not_found"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="external",
            help="Service to reconcile (default: external)",
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
            help="Maximum number of meetings to process (default: no limit)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode (do not update, only report)",
        )
        parser.add_argument(
            "--delete-missing",
            action="store_true",
            help="Delete missing meetings instead of marking provider_not_found (use with caution)",
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
        delete_missing = options["delete_missing"]
        verbose = options["verbose"]

        services_to_reconcile = []
        if service_option in ["internal", "all"]:
            services_to_reconcile.append("gotomeeting_internal")
        if service_option in ["external", "all"]:
            services_to_reconcile.append("gotomeeting_external")

        cutoff_date = timezone.now() - timedelta(days=days)
        start_dt = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = timezone.now()

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("GoToMeeting Meeting Reconciliation")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Service(s): {', '.join(services_to_reconcile)}")
        self.stdout.write(
            f"Date range: {start_dt.date()} to {end_dt.date()} ({days} days)"
        )
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Delete missing: {delete_missing}")
        self.stdout.write("")

        total_inserted = 0
        total_updated = 0
        total_quarantined = 0
        total_deleted = 0

        for service_name in services_to_reconcile:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing service: {service_name}")
            self.stdout.write(f"{'='*60}")

            # Get access token
            try:
                access_token = get_access_token(service_name=service_name)
                if not access_token:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ OAuth token not available for {service_name}. "
                            f"Please run /management/oauth/login/?service={service_name.split('_')[-1]} first."
                        )
                    )
                    continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error getting access token for {service_name}: {e}"
                    )
                )
                continue

            # Fetch meetings from API
            self.stdout.write(f"📥 Fetching meetings from API...")
            try:
                api_meetings = fetch_meetings(start_dt, end_dt, access_token)
                self.stdout.write(f"   Found {len(api_meetings)} meetings in API")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error fetching meetings from API: {e}")
                )
                continue

            # Build set of API meeting identifiers (composite keys)
            api_meeting_keys = set()
            for meeting_dict in api_meetings:
                meeting_id = meeting_dict.get("meetingId") or meeting_dict.get(
                    "meeting_id", ""
                )
                session_id = (
                    meeting_dict.get("sessionId")
                    or meeting_dict.get("session_id")
                    or None
                )
                start_time_str = meeting_dict.get("startTime") or meeting_dict.get(
                    "start_time", ""
                )

                if session_id:
                    key = (meeting_id, session_id, "session")
                else:
                    # Use start_time as part of key if session_id missing
                    # We'll match by start_time in DB lookup
                    key = (meeting_id, start_time_str, "time")

                api_meeting_keys.add(key)

            if verbose:
                self.stdout.write(
                    f"   API meeting keys: {len(api_meeting_keys)} unique identifiers"
                )

            # Upsert API meetings
            self.stdout.write(f"💾 Upserting API meetings...")
            if not dry_run:
                try:
                    upsert_result = upsert_meetings(
                        api_meetings, service_name=service_name
                    )
                    inserted = upsert_result.get("meetings_created", 0)
                    updated = upsert_result.get("meetings_updated", 0)
                    total_inserted += inserted
                    total_updated += updated
                    self.stdout.write(f"   ✅ Inserted: {inserted}, Updated: {updated}")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error upserting meetings: {e}")
                    )
                    continue
            else:
                self.stdout.write(f"   (Dry run - skipping upsert)")

            # Find DB meetings in window that are NOT in API
            self.stdout.write(f"🔍 Identifying missing meetings in DB...")
            db_meetings = Meeting.objects.filter(
                service_name=service_name,
                start_time__gte=start_dt,
                start_time__lte=end_dt,
            )

            if limit:
                db_meetings = db_meetings[:limit]

            missing_meetings = []
            for db_meeting in db_meetings:
                # Build DB meeting key
                if db_meeting.session_id:
                    db_key = (db_meeting.meeting_id, db_meeting.session_id, "session")
                else:
                    # Match by meeting_id + start_time (within tolerance)
                    db_start_str = (
                        db_meeting.start_time.isoformat()
                        if db_meeting.start_time
                        else ""
                    )
                    db_key = (db_meeting.meeting_id, db_start_str, "time")

                # Check if this DB meeting exists in API
                found_in_api = False
                for api_key in api_meeting_keys:
                    # Match by meeting_id + session_id (exact) or meeting_id + start_time (approximate)
                    if api_key[0] == db_key[0]:  # Same meeting_id
                        if api_key[2] == "session" and db_key[2] == "session":
                            # Both have session_id, match exactly
                            if api_key[1] == db_key[1]:
                                found_in_api = True
                                break
                        elif api_key[2] == "time" and db_key[2] == "time":
                            # Both use start_time, match approximately (within 5 minutes)
                            try:
                                from dateutil import parser

                                api_start = parser.isoparse(api_key[1])
                                db_start = db_meeting.start_time
                                if (
                                    db_start
                                    and abs((api_start - db_start).total_seconds())
                                    < 300
                                ):
                                    found_in_api = True
                                    break
                            except Exception:
                                pass

                if not found_in_api:
                    missing_meetings.append(db_meeting)

            missing_count = len(missing_meetings)
            self.stdout.write(f"   Found {missing_count} DB meetings not in API")

            # Process missing meetings
            if missing_count > 0:
                if delete_missing:
                    self.stdout.write(
                        f"🗑️  Deleting {missing_count} missing meetings..."
                    )
                    if not dry_run:
                        deleted_ids = [m.id for m in missing_meetings]
                        deleted_count = Meeting.objects.filter(
                            id__in=deleted_ids
                        ).delete()[0]
                        total_deleted += deleted_count
                        self.stdout.write(f"   ✅ Deleted: {deleted_count} meetings")
                    else:
                        self.stdout.write(
                            f"   (Dry run - would delete {missing_count} meetings)"
                        )
                        if verbose:
                            for m in missing_meetings[:10]:  # Show first 10
                                self.stdout.write(
                                    f"      Would delete: {m.meeting_id} "
                                    f"({m.topic[:50]}, {m.start_time})"
                                )
                else:
                    self.stdout.write(
                        f"🏷️  Marking {missing_count} meetings as provider_not_found..."
                    )
                    if not dry_run:
                        from django.db.models import F

                        quarantined = Meeting.objects.filter(
                            id__in=[m.id for m in missing_meetings]
                        ).update(
                            provider_not_found=True,
                            provider_not_found_at=timezone.now(),
                        )
                        total_quarantined += quarantined
                        self.stdout.write(f"   ✅ Quarantined: {quarantined} meetings")
                    else:
                        self.stdout.write(
                            f"   (Dry run - would quarantine {missing_count} meetings)"
                        )
                        if verbose:
                            for m in missing_meetings[:10]:  # Show first 10
                                self.stdout.write(
                                    f"      Would quarantine: {m.meeting_id} "
                                    f"({m.topic[:50]}, {m.start_time})"
                                )

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("SUMMARY")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Inserted: {total_inserted}")
        self.stdout.write(f"Updated: {total_updated}")
        if delete_missing:
            self.stdout.write(f"Deleted: {total_deleted}")
        else:
            self.stdout.write(
                f"Quarantined (provider_not_found=True): {total_quarantined}"
            )

        if dry_run:
            self.stdout.write(f"\n⚠️  This was a dry run. No changes were made.")

        self.stdout.write("\n✅ Reconciliation complete!")
