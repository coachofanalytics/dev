"""
Management command to check meeting room ID mapping and identify mismatches.

Usage:
    poetry run python coda/manage.py check_meeting_room_mapping
    poetry run python coda/manage.py check_meeting_room_mapping --service internal --days 30
"""

import logging
from datetime import timedelta

from ai_services.models import Meeting
from ai_services.utils.meeting_room_config import get_meeting_room_for_activity
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone

from coda.config.activity_definitions import ACTIVITY_POLICIES

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check meeting room ID mapping and identify mismatches between policy and actual meetings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["external", "internal", "all"],
            default="all",
            help="Service name filter: external (gotomeeting_external), internal (gotomeeting_internal), or all (default: all)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back for meetings (default: 30)",
        )

    def handle(self, *args, **options):
        service_option = options.get("service", "all")
        days = options.get("days", 30)

        # Map service option to service_name
        service_name = None
        if service_option == "external":
            service_name = "gotomeeting_external"
        elif service_option == "internal":
            service_name = "gotomeeting_internal"

        self.stdout.write(self.style.SUCCESS("\n🔍 Meeting Room ID Mapping Check 🔍\n"))

        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Build query
        query = Q(start_time__gte=start_date, start_time__lte=end_date)
        if service_name:
            query &= Q(service_name=service_name)

        # Get meeting counts by meeting_id
        meetings = Meeting.objects.filter(query)

        # Group by meeting_id and count
        meeting_id_counts = (
            meetings.values("meeting_id")
            .annotate(count=Count("id"), sample_subjects=Count("topic", distinct=True))
            .order_by("-count")[:20]
        )

        self.stdout.write(f"\n📊 Meeting IDs in Database (last {days} days):")
        self.stdout.write(f"   Service filter: {service_name or 'all'}")
        self.stdout.write(f"   Date range: {start_date.date()} to {end_date.date()}\n")

        if not meeting_id_counts:
            self.stdout.write(self.style.WARNING("   No meetings found in date range"))
        else:
            self.stdout.write(f"{'Meeting ID':<15} {'Count':<10} {'Sample Topics'}")
            self.stdout.write("-" * 80)
            for item in meeting_id_counts:
                meeting_id = item["meeting_id"] or "NULL"
                count = item["count"]
                # Get a sample topic
                sample_meeting = meetings.filter(meeting_id=item["meeting_id"]).first()
                sample_topic = (
                    sample_meeting.topic[:50]
                    if sample_meeting and sample_meeting.topic
                    else "N/A"
                )
                self.stdout.write(f"{meeting_id:<15} {count:<10} {sample_topic}")

        # Check ActivityPolicy configurations
        self.stdout.write(f"\n📋 ActivityPolicy Meeting Room Configurations:")
        self.stdout.write("-" * 80)

        training_activities = [
            "INTERNAL_TRAINING_SESSION",
            "DAILY_UPDATE_SESSION",
            "BUDGETING_FORECASTING_SESSION",
            "UAT_TESTING_SUPPORT",
            "CLIENT_TRAINING_SESSION",
            "SELF_TRAINING_SESSION",
        ]

        for activity_slug in training_activities:
            policy = ACTIVITY_POLICIES.get(activity_slug)
            if policy:
                meeting_room_id = policy.meeting_room_id
                if meeting_room_id:
                    # Check if this meeting_id exists in database
                    exists_in_db = meetings.filter(meeting_id=meeting_room_id).exists()
                    count_in_db = meetings.filter(meeting_id=meeting_room_id).count()

                    status = "✅" if exists_in_db else "❌"
                    self.stdout.write(
                        f"{status} {activity_slug:<35} meeting_room_id={meeting_room_id:<15} "
                        f"(found {count_in_db} meetings in DB)"
                    )
                else:
                    self.stdout.write(
                        f"⚠️  {activity_slug:<35} meeting_room_id=None (not configured)"
                    )

        # Check what get_meeting_room_for_activity returns
        self.stdout.write(f"\n🔧 get_meeting_room_for_activity() Results:")
        self.stdout.write("-" * 80)

        for activity_slug in training_activities:
            room_id, join_url = get_meeting_room_for_activity(activity_slug)
            if room_id:
                exists_in_db = meetings.filter(meeting_id=room_id).exists()
                count_in_db = meetings.filter(meeting_id=room_id).count()
                status = "✅" if exists_in_db else "❌"
                self.stdout.write(
                    f"{status} {activity_slug:<35} returns meeting_id={room_id:<15} "
                    f"(found {count_in_db} meetings in DB)"
                )
            else:
                self.stdout.write(f"⚠️  {activity_slug:<35} returns meeting_id=None")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ Check complete!\n"))
