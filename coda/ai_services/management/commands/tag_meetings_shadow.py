"""
Management command to tag meetings with AI-suggested activity types (shadow mode).

This command processes meetings and generates activity type suggestions without
changing any data. Suggestions are stored for audit and review.
"""

import csv
from collections import Counter
from datetime import timedelta

from ai_services.models import Meeting
from ai_services.services.meeting_activity_tagging_service import \
    MeetingActivityTaggingService
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Tag meetings with AI-suggested activity types (shadow mode - no data changes)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to look back (default: 7)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of meetings to process (default: 100)",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["external", "internal"],
            help="Filter by service name (gotomeeting_external or gotomeeting_internal)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force regeneration even if cached suggestion exists",
        )
        parser.add_argument(
            "--export", type=str, help="Export results to CSV file (provide path)"
        )

    def handle(self, *args, **options):
        days = options["days"]
        limit = options["limit"]
        service_filter = options.get("service")
        force = options.get("force", False)
        export_path = options.get("export")

        self.stdout.write(
            self.style.SUCCESS("🔍 Meeting Activity Tagging (Shadow Mode)")
        )
        self.stdout.write("=" * 60)

        # Build query
        cutoff_date = timezone.now() - timedelta(days=days)
        meetings_qs = Meeting.objects.filter(start_time__gte=cutoff_date).order_by(
            "-start_time"
        )

        if service_filter:
            service_name = f"gotomeeting_{service_filter}"
            meetings_qs = meetings_qs.filter(service_name=service_name)
            self.stdout.write(f"📋 Service filter: {service_name}")

        meetings_qs = meetings_qs[:limit]
        total_meetings = meetings_qs.count()

        self.stdout.write(
            f"📊 Processing {total_meetings} meetings from last {days} days"
        )
        if limit < total_meetings:
            self.stdout.write(f"⚠️  Limited to {limit} meetings")

        # Initialize service
        service = MeetingActivityTaggingService()

        # Process meetings
        stats = {
            "processed": 0,
            "cached": 0,
            "created": 0,
            "rule_fallback": 0,
            "errors": 0,
            "confidences": [],
            "suggested_types": Counter(),
        }

        results = []

        for meeting in meetings_qs:
            try:
                suggestion = service.suggest_activity_type(meeting, force=force)

                if suggestion:
                    stats["processed"] += 1
                    stats["confidences"].append(suggestion.confidence)
                    stats["suggested_types"][suggestion.suggested_activity_type] += 1

                    # Check if it was cached or newly created
                    if not force:
                        # Check if suggestion existed before (simple heuristic: check created_at)
                        from ai_services.models import \
                            MeetingActivityTagSuggestion

                        existing = (
                            MeetingActivityTagSuggestion.objects.filter(
                                meeting=meeting, input_hash=suggestion.input_hash
                            )
                            .exclude(id=suggestion.id)
                            .exists()
                        )

                        if existing:
                            stats["cached"] += 1
                        else:
                            stats["created"] += 1
                    else:
                        stats["created"] += 1

                    # Track fallback
                    if suggestion.provider == "fallback":
                        stats["rule_fallback"] += 1

                    results.append(
                        {
                            "meeting_id": meeting.id,
                            "topic": meeting.topic[:100],
                            "requirement_code": meeting.requirement_code or "",
                            "service_name": meeting.service_name or "",
                            "suggested_activity_type": suggestion.suggested_activity_type,
                            "confidence": suggestion.confidence,
                            "reason": suggestion.reason[:200],
                            "provider": suggestion.provider,
                        }
                    )
                else:
                    stats["errors"] += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing meeting {meeting.id}: {e}")
                )
                stats["errors"] += 1

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("📊 Summary"))
        self.stdout.write(f'   Total processed: {stats["processed"]}')
        self.stdout.write(f'   Cached (reused): {stats["cached"]}')
        self.stdout.write(f'   Created new: {stats["created"]}')
        self.stdout.write(f'   Rule-based fallback: {stats["rule_fallback"]}')
        self.stdout.write(f'   Errors: {stats["errors"]}')

        if stats["confidences"]:
            avg_confidence = sum(stats["confidences"]) / len(stats["confidences"])
            self.stdout.write(f"   Average confidence: {avg_confidence:.2%}")

        if stats["suggested_types"]:
            self.stdout.write("\n   Top suggested activity types:")
            for activity_type, count in stats["suggested_types"].most_common(5):
                self.stdout.write(f"      {activity_type}: {count}")

        # Export to CSV if requested
        if export_path and results:
            try:
                with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = [
                        "meeting_id",
                        "topic",
                        "requirement_code",
                        "service_name",
                        "suggested_activity_type",
                        "confidence",
                        "reason",
                        "provider",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results)

                self.stdout.write(
                    f"\n✅ Exported {len(results)} results to: {export_path}"
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Export failed: {e}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Processing complete"))
