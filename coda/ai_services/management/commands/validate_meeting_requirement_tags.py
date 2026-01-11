"""
Management command to validate meeting requirement tags (REQ-#### convention).

Scans meetings and reports:
- % of meetings missing REQ tag
- Top meeting topics missing tags
- Export CSV option

Usage:
    python manage.py validate_meeting_requirement_tags
    python manage.py validate_meeting_requirement_tags --days 60
    python manage.py validate_meeting_requirement_tags --days 30 --export /tmp/meeting_req_tags.csv
"""

import csv
from datetime import timedelta

from ai_services.models import Meeting
from ai_services.utils.meeting_normalizer import extract_requirement_code
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone


class Command(BaseCommand):
    help = "Validate meeting requirement tags (REQ-#### convention) and generate cleanliness report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back (default: 30)",
        )
        parser.add_argument(
            "--export",
            type=str,
            default=None,
            help="Export results to CSV file (optional)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        export_path = options["export"]

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS("Meeting Requirement Tag Validation Report")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            f'Date range: Last {days} days (since {cutoff_date.strftime("%Y-%m-%d")})'
        )
        self.stdout.write("")

        # Query meetings in date range
        meetings = Meeting.objects.filter(start_time__gte=cutoff_date).order_by(
            "-start_time"
        )

        total_meetings = meetings.count()

        if total_meetings == 0:
            self.stdout.write(
                self.style.WARNING("No meetings found in the specified date range.")
            )
            return

        # Analyze requirement codes
        meetings_with_req = meetings.exclude(
            Q(requirement_code__isnull=True) | Q(requirement_code="")
        )
        meetings_with_req_count = meetings_with_req.count()
        meetings_without_req = total_meetings - meetings_with_req_count

        req_coverage = (
            (meetings_with_req_count / total_meetings * 100)
            if total_meetings > 0
            else 0
        )

        # Detect multiple REQ codes in topics
        multiple_code_count = 0
        for meeting in meetings:
            if meeting.topic:
                # Count occurrences of REQ pattern
                import re

                req_matches = re.findall(
                    r"\bREQ\s*-\s*\d{3,6}\b", meeting.topic, re.IGNORECASE
                )
                if len(req_matches) > 1:
                    multiple_code_count += 1

        # Breakdown by service_name
        service_breakdown = {}
        for service_name in meetings.values_list("service_name", flat=True).distinct():
            if service_name:
                svc_meetings = meetings.filter(service_name=service_name)
                svc_total = svc_meetings.count()
                svc_with_req = svc_meetings.exclude(
                    Q(requirement_code__isnull=True) | Q(requirement_code="")
                ).count()
                svc_coverage = (svc_with_req / svc_total * 100) if svc_total > 0 else 0
                service_breakdown[service_name] = {
                    "total": svc_total,
                    "with_req": svc_with_req,
                    "coverage": svc_coverage,
                }

        # Statistics
        self.stdout.write(self.style.SUCCESS("Statistics:"))
        self.stdout.write(f"  Total meetings: {total_meetings}")
        self.stdout.write(
            f"  Meetings with REQ tag: {meetings_with_req_count} ({req_coverage:.1f}%)"
        )
        self.stdout.write(
            f"  Meetings missing REQ tag: {meetings_without_req} ({100 - req_coverage:.1f}%)"
        )
        self.stdout.write(
            f"  Meetings with multiple REQ codes in topic: {multiple_code_count}"
        )
        self.stdout.write("")

        # Service breakdown
        if service_breakdown:
            self.stdout.write(self.style.SUCCESS("Breakdown by Service:"))
            for service_name, stats in sorted(
                service_breakdown.items(), key=lambda x: x[1]["total"], reverse=True
            ):
                self.stdout.write(
                    f'  {service_name}: {stats["with_req"]}/{stats["total"]} '
                    f'({stats["coverage"]:.1f}% coverage)'
                )
            self.stdout.write("")

        # Top meeting topics missing tags
        meetings_missing_tags = meetings.filter(
            Q(requirement_code__isnull=True) | Q(requirement_code="")
        )

        # Group by topic (normalized) to find patterns
        topic_counts = {}
        for meeting in meetings_missing_tags:
            topic_key = (
                meeting.topic_normalized if meeting.topic_normalized else meeting.topic
            )
            if topic_key:
                topic_counts[topic_key] = topic_counts.get(topic_key, 0) + 1

        # Sort by count
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        if top_topics:
            self.stdout.write(
                self.style.WARNING("Top 20 Meeting Topics Missing REQ Tags:")
            )
            for topic, count in top_topics:
                self.stdout.write(f"  {count:3d}x: {topic[:80]}")
            self.stdout.write("")

        # Sample meetings missing tags
        sample_missing = meetings_missing_tags[:10]
        if sample_missing:
            self.stdout.write(self.style.WARNING("Sample Meetings Missing REQ Tags:"))
            for meeting in sample_missing:
                req_code_in_topic = (
                    extract_requirement_code(meeting.topic) if meeting.topic else None
                )
                status = (
                    f"REQ code in topic: {req_code_in_topic}"
                    if req_code_in_topic
                    else "No REQ code found in topic"
                )
                self.stdout.write(
                    f"  Meeting {meeting.id}: {meeting.topic[:60]}... "
                    f'({meeting.start_time.strftime("%Y-%m-%d")}) - {status}'
                )
            self.stdout.write("")

        # Export to CSV if requested
        if export_path:
            self.stdout.write(f"Exporting to: {export_path}")
            with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "meeting_id",
                        "start_time",
                        "topic",
                        "topic_normalized",
                        "requirement_code",
                        "has_req_code",
                        "req_code_in_topic",
                        "multiple_codes_in_topic",
                        "service_name",
                        "recording_url",
                    ]
                )

                for meeting in meetings:
                    req_code_in_topic = (
                        extract_requirement_code(meeting.topic)
                        if meeting.topic
                        else None
                    )
                    # Check for multiple codes
                    import re

                    multiple_codes = "No"
                    if meeting.topic:
                        req_matches = re.findall(
                            r"\bREQ\s*-\s*\d{3,6}\b", meeting.topic, re.IGNORECASE
                        )
                        if len(req_matches) > 1:
                            multiple_codes = f"Yes ({len(req_matches)} found)"

                    writer.writerow(
                        [
                            meeting.meeting_id,
                            (
                                meeting.start_time.isoformat()
                                if meeting.start_time
                                else ""
                            ),
                            meeting.topic or "",
                            meeting.topic_normalized or "",
                            meeting.requirement_code or "",
                            "Yes" if meeting.requirement_code else "No",
                            req_code_in_topic or "",
                            multiple_codes,
                            meeting.service_name or "",
                            meeting.recording_url or "",
                        ]
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Exported {total_meetings} meetings to {export_path}"
                )
            )

        # Summary
        self.stdout.write("")
        if req_coverage >= 80:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Good coverage: {req_coverage:.1f}% of meetings have REQ tags"
                )
            )
        elif req_coverage >= 50:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Moderate coverage: {req_coverage:.1f}% of meetings have REQ tags"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Low coverage: Only {req_coverage:.1f}% of meetings have REQ tags"
                )
            )

        self.stdout.write("")
        self.stdout.write("Recommendations:")
        if req_coverage < 80:
            self.stdout.write(
                "  - Encourage users to include REQ-#### in meeting titles"
            )
            self.stdout.write(
                "  - Run backfill script to extract REQ codes from existing topics"
            )
            self.stdout.write("  - Add validation at meeting creation time")
        else:
            self.stdout.write("  - Continue enforcing REQ tag convention")
            self.stdout.write("  - Monitor for new meetings without tags")
