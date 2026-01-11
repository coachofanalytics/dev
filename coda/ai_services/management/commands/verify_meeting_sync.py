"""
Management command to verify meeting sync updates records over time.

Usage:
    poetry run python coda/manage.py verify_meeting_sync
    poetry run python coda/manage.py verify_meeting_sync --minutes 30
    poetry run python coda/manage.py verify_meeting_sync --service gotomeeting_internal
"""

import logging
from datetime import timedelta

from ai_services.models import Meeting
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verify meeting sync updates records over time (read-only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=60,
            help="Time window in minutes to check for updated meetings (default: 60)",
        )
        parser.add_argument(
            "--service",
            type=str,
            help="Filter by service_name (e.g., gotomeeting_internal, gotomeeting_external). If not provided, shows all services.",
        )

    def handle(self, *args, **options):
        minutes = options.get("minutes", 60)
        service_filter = options.get("service")

        self.stdout.write(
            self.style.SUCCESS(f"\n📊 Meeting Sync Verification Report\n")
        )
        self.stdout.write(f"Time window: Last {minutes} minutes\n")
        self.stdout.write("=" * 80 + "\n")

        # Build query
        queryset = Meeting.objects.all()
        if service_filter:
            queryset = queryset.filter(service_name=service_filter)

        # Get total meetings by service_name
        total_by_service = (
            queryset.values("service_name")
            .annotate(total=Count("id"))
            .order_by("service_name")
        )

        # Get max updated_at by service_name
        max_updated_by_service = (
            queryset.values("service_name")
            .annotate(max_updated_at=Max("updated_at"))
            .order_by("service_name")
        )

        # Get count of meetings updated in last N minutes by service_name
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent_updates_by_service = (
            queryset.filter(updated_at__gte=cutoff_time)
            .values("service_name")
            .annotate(recent_count=Count("id"))
            .order_by("service_name")
        )

        # Create a combined report
        service_dict = {}

        # Populate with totals
        for item in total_by_service:
            service_name = item["service_name"] or "(no service)"
            service_dict[service_name] = {
                "total": item["total"],
                "max_updated_at": None,
                "recent_count": 0,
            }

        # Add max updated_at
        for item in max_updated_by_service:
            service_name = item["service_name"] or "(no service)"
            if service_name in service_dict:
                service_dict[service_name]["max_updated_at"] = item["max_updated_at"]

        # Add recent counts
        recent_dict = {
            item["service_name"] or "(no service)": item["recent_count"]
            for item in recent_updates_by_service
        }
        for service_name in service_dict:
            service_dict[service_name]["recent_count"] = recent_dict.get(
                service_name, 0
            )

        # Print report
        if not service_dict:
            self.stdout.write(self.style.WARNING("⚠️  No meetings found in database."))
            return

        for service_name, data in sorted(service_dict.items()):
            self.stdout.write(f"\n📋 Service: {service_name}")
            self.stdout.write(f"   Total meetings: {data['total']}")

            if data["max_updated_at"]:
                max_updated_str = data["max_updated_at"].strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                age_minutes = (
                    timezone.now() - data["max_updated_at"]
                ).total_seconds() / 60
                self.stdout.write(
                    f"   Most recent update: {max_updated_str} ({age_minutes:.1f} minutes ago)"
                )
            else:
                self.stdout.write(f"   Most recent update: N/A")

            self.stdout.write(
                f"   Updated in last {minutes} min: {data['recent_count']}"
            )

            # Status indicator
            if data["recent_count"] > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ Status: Active (recent updates detected)"
                    )
                )
            elif data["max_updated_at"]:
                age_hours = age_minutes / 60
                if age_hours < 24:
                    self.stdout.write(
                        self.style.WARNING(
                            f"   ⚠️  Status: Stale (last update {age_hours:.1f} hours ago)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   ❌ Status: Very stale (last update {age_hours/24:.1f} days ago)"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Status: No update timestamp")
                )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("\n💡 To verify sync is working:")
        self.stdout.write(
            "   1. Run: poetry run python coda/manage.py sync_gotomeetings --service <service> --days 7"
        )
        self.stdout.write("   2. Wait a few minutes")
        self.stdout.write("   3. Run this command again to see updated counts\n")
