"""
Management command to sample and analyze existing meetings in the database.

Usage:
    poetry run python coda/manage.py sample_meetings
    poetry run python coda/manage.py sample_meetings --limit 25
    poetry run python coda/manage.py sample_meetings --days 30 --limit 50
    poetry run python coda/manage.py sample_meetings --since "2025-12-01" --limit 100
    poetry run python coda/manage.py sample_meetings --export /tmp/meetings_sample.csv

Phase 2A+1: Meeting analysis and normalization (no API calls).
"""

import csv
from collections import Counter
from datetime import datetime, timedelta

from ai_services.models import Meeting, MeetingAttendee
from ai_services.utils.meeting_normalizer import (
    extract_candidate_activity_tags, normalize_topic)
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Sample and analyze existing meetings in the database (no API calls)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=14,
            help="Number of days back from now to analyze (default: 14)",
        )
        parser.add_argument(
            "--since",
            type=str,
            help="Start date in YYYY-MM-DD format. Overrides --days if provided.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=25,
            help="Maximum number of sample rows to display (default: 25)",
        )
        parser.add_argument(
            "--export",
            type=str,
            help="Export sample to CSV file (optional)",
        )

    def handle(self, *args, **options):
        """Execute the analysis command."""
        days = options["days"]
        since_str = options["since"]
        limit = options["limit"]
        export_path = options["export"]

        # Calculate date range
        end_date = timezone.now()
        if since_str:
            try:
                start_date = timezone.make_aware(
                    datetime.strptime(since_str, "%Y-%m-%d")
                )
            except ValueError:
                raise CommandError(f"Invalid date format for --since. Use YYYY-MM-DD.")
        else:
            start_date = end_date - timedelta(days=days)

        # Query meetings
        meetings = Meeting.objects.filter(
            start_time__gte=start_date, start_time__lte=end_date
        ).order_by("-start_time")

        total_count = meetings.count()

        if total_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"No meetings found in range {start_date.date()} to {end_date.date()}"
                )
            )
            return

        # Calculate statistics
        recorded_count = meetings.filter(is_recorded=True).count()
        recorded_pct = (recorded_count / total_count * 100) if total_count > 0 else 0

        with_recording_url = (
            meetings.exclude(recording_url__isnull=True)
            .exclude(recording_url="")
            .count()
        )
        with_download_url = (
            meetings.exclude(download_url__isnull=True).exclude(download_url="").count()
        )

        # Analyze topic patterns (normalized)
        topic_patterns = Counter()
        topic_to_sample = {}  # Store first meeting_id for each normalized topic

        for meeting in meetings:
            normalized = normalize_topic(meeting.topic) if meeting.topic else ""
            if normalized:
                topic_patterns[normalized] += 1
                # Store first meeting_id for this pattern (for reference)
                if normalized not in topic_to_sample:
                    topic_to_sample[normalized] = meeting.meeting_id

        # Get top 20 topic patterns
        top_patterns = topic_patterns.most_common(20)

        # Extract candidate activity tags
        all_tags = Counter()
        for meeting in meetings:
            if meeting.topic:
                tags = extract_candidate_activity_tags(meeting.topic)
                for tag in tags:
                    all_tags[tag] += 1

        # Print report
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("Meeting Analysis Report"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"\nDate Range: {start_date.date()} to {end_date.date()}")
        self.stdout.write(f"Total Meetings: {total_count}")
        self.stdout.write(f"Recorded: {recorded_count} ({recorded_pct:.1f}%)")
        self.stdout.write(f"With Recording URL: {with_recording_url}")
        self.stdout.write(f"With Download URL: {with_download_url}")

        # Top topic patterns
        self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
        self.stdout.write(self.style.SUCCESS("Top 20 Topic Patterns (Normalized)"))
        self.stdout.write(self.style.SUCCESS("-" * 80))
        for normalized_topic, count in top_patterns:
            percentage = (count / total_count * 100) if total_count > 0 else 0
            sample_id = topic_to_sample.get(normalized_topic, "N/A")
            self.stdout.write(
                f"  {count:4d} ({percentage:5.1f}%): {normalized_topic[:60]:60s} [sample: {sample_id}]"
            )

        # Candidate activity tags
        if all_tags:
            self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
            self.stdout.write(
                self.style.SUCCESS("Candidate Activity Tags (Keyword-Based)")
            )
            self.stdout.write(self.style.SUCCESS("-" * 80))
            for tag, count in all_tags.most_common():
                percentage = (count / total_count * 100) if total_count > 0 else 0
                self.stdout.write(
                    f"  {tag:20s}: {count:4d} meetings ({percentage:5.1f}%)"
                )

        # Sample rows
        self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
        self.stdout.write(self.style.SUCCESS(f"Sample Rows (showing up to {limit})"))
        self.stdout.write(self.style.SUCCESS("-" * 80))
        self.stdout.write(
            f"{'Meeting ID':<15s} {'Start Time':<20s} {'Duration':<10s} "
            f"{'Topic':<40s} {'Has Recording':<15s} {'Has Download':<15s}"
        )
        self.stdout.write("-" * 115)

        sample_meetings = meetings[:limit]
        sample_data = []

        for meeting in sample_meetings:
            has_recording = (
                "✓"
                if (meeting.recording_url and meeting.recording_url.strip())
                else "✗"
            )
            has_download = (
                "✓" if (meeting.download_url and meeting.download_url.strip()) else "✗"
            )
            topic_short = (
                (meeting.topic[:37] + "...")
                if meeting.topic and len(meeting.topic) > 40
                else (meeting.topic or "")
            )
            start_str = (
                meeting.start_time.strftime("%Y-%m-%d %H:%M")
                if meeting.start_time
                else "N/A"
            )

            self.stdout.write(
                f"{meeting.meeting_id:<15s} {start_str:<20s} "
                f"{meeting.duration_minutes or 0:>4d} min    {topic_short:<40s} "
                f"{has_recording:<15s} {has_download:<15s}"
            )

            # Use stored normalized topic if available, otherwise compute
            topic_normalized_value = (
                meeting.topic_normalized
                if meeting.topic_normalized
                else (normalize_topic(meeting.topic) if meeting.topic else "")
            )
            candidate_tags_list = (
                extract_candidate_activity_tags(meeting.topic) if meeting.topic else []
            )

            sample_data.append(
                {
                    "meeting_id": meeting.meeting_id,
                    "start_time": (
                        meeting.start_time.isoformat() if meeting.start_time else ""
                    ),
                    "duration_minutes": meeting.duration_minutes or 0,
                    "topic": meeting.topic or "",
                    "topic_normalized": topic_normalized_value,
                    "service_name": meeting.service_name or "",
                    "has_recording_url": bool(
                        meeting.recording_url and meeting.recording_url.strip()
                    ),
                    "has_download_url": bool(
                        meeting.download_url and meeting.download_url.strip()
                    ),
                    "is_recorded": meeting.is_recorded,
                    "attendee_count": meeting.attendees.count(),
                    "candidate_tags": ", ".join(candidate_tags_list),
                }
            )

        # Export to CSV if requested
        if export_path:
            try:
                with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                    if sample_data:
                        fieldnames = sample_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(sample_data)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Exported {len(sample_data)} rows to: {export_path}"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Failed to export CSV: {e}"))

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("Analysis Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))
