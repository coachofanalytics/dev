"""
Management command to generate match quality report.

Usage:
    poetry run python coda/manage.py match_quality_report
    poetry run python coda/manage.py match_quality_report --days 30
    poetry run python coda/manage.py match_quality_report --service external
    poetry run python coda/manage.py match_quality_report --export /tmp/match_quality.csv

Phase 2C+1: Operational tooling for analyzing match rates by activity type and service.
"""

import csv
from collections import defaultdict
from datetime import timedelta

from ai_services.models import Meeting
from ai_services.services.meeting_evidence_matcher import \
    MeetingEvidenceMatcher
from ai_services.utils.meeting_normalizer import \
    extract_candidate_activity_tags
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone
from management.models import Task, TaskLinks


class Command(BaseCommand):
    help = (
        "Generate match quality report showing match rates by activity type and service"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days back from now to analyze (default: 30)",
        )
        parser.add_argument(
            "--since",
            type=str,
            help="Start date in YYYY-MM-DD format. Overrides --days if provided.",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["external", "internal"],
            help="Filter by service name (external or internal)",
        )
        parser.add_argument(
            "--export",
            type=str,
            help="Export report to CSV file (optional)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        since_str = options["since"]
        service_filter = options.get("service")
        export_path = options.get("export")

        # Calculate date range
        end_date = timezone.now()
        if since_str:
            try:
                from datetime import datetime

                start_date = timezone.make_aware(
                    datetime.strptime(since_str, "%Y-%m-%d")
                )
            except ValueError:
                raise CommandError("Invalid date format for --since. Use YYYY-MM-DD.")
        else:
            start_date = end_date - timedelta(days=days)

        # Determine service_name for matcher
        service_name = f"gotomeeting_{service_filter}" if service_filter else None

        # Initialize matcher
        matcher = MeetingEvidenceMatcher(
            enable_topic_fallback=True,
            time_window_days=2,
            service_name=service_name,
            require_activity_tag_overlap=True,
        )

        # Query tasks in date range
        tasks = Task.objects.filter(
            is_active=True, submission__gte=start_date, submission__lte=end_date
        )

        total_tasks = tasks.count()

        if total_tasks == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"No tasks found in range {start_date.date()} to {end_date.date()}"
                )
            )
            return

        # Analyze matches
        match_stats_by_activity = defaultdict(
            lambda: {"total": 0, "matched": 0, "url_match": 0, "topic_match": 0}
        )
        match_stats_by_service = defaultdict(lambda: {"total": 0, "matched": 0})
        unmatched_patterns = defaultdict(int)
        unmatched_tasks = []

        for task in tasks:
            activity_name = task.activity_name or "Unknown"
            activity_type_slug = task.activity_type.slug if task.activity_type else None

            # Get service_name from task if we can infer it (future enhancement)
            # For now, use the filter service_name
            task_service_name = service_name

            # Track by activity
            match_stats_by_activity[activity_name]["total"] += 1
            if task_service_name:
                match_stats_by_service[task_service_name]["total"] += 1

            # Find matches
            detailed_matches = matcher.get_detailed_matches(task)

            if detailed_matches:
                match_stats_by_activity[activity_name]["matched"] += 1
                if task_service_name:
                    match_stats_by_service[task_service_name]["matched"] += 1

                # Count match types and confidence levels
                for match in detailed_matches:
                    match_type = match.get("match_type", "unknown")
                    confidence = match.get("confidence", 0.0)
                    req_code_match = match.get("requirement_code_match")

                    if match_type == "url":
                        match_stats_by_activity[activity_name]["url_match"] += 1
                        # Track REQ code matches for URL matches
                        if req_code_match:
                            match_stats_by_activity[activity_name]["url_req_match"] = (
                                match_stats_by_activity[activity_name].get(
                                    "url_req_match", 0
                                )
                                + 1
                            )
                    elif match_type == "topic":
                        match_stats_by_activity[activity_name]["topic_match"] += 1
                        # Track REQ code matches for topic matches
                        if req_code_match:
                            match_stats_by_activity[activity_name][
                                "topic_req_match"
                            ] = (
                                match_stats_by_activity[activity_name].get(
                                    "topic_req_match", 0
                                )
                                + 1
                            )

                    # Track confidence distribution
                    if confidence >= 0.9:
                        match_stats_by_activity[activity_name]["high_confidence"] = (
                            match_stats_by_activity[activity_name].get(
                                "high_confidence", 0
                            )
                            + 1
                        )
                    elif confidence >= 0.7:
                        match_stats_by_activity[activity_name]["medium_confidence"] = (
                            match_stats_by_activity[activity_name].get(
                                "medium_confidence", 0
                            )
                            + 1
                        )
                    else:
                        match_stats_by_activity[activity_name]["low_confidence"] = (
                            match_stats_by_activity[activity_name].get(
                                "low_confidence", 0
                            )
                            + 1
                        )
            else:
                # Unmatched task - collect patterns
                task_links = TaskLinks.objects.filter(task=task, is_active=True)
                evidence_urls = []
                for task_link in task_links:
                    if task_link.link:
                        evidence_urls.append(task_link.link)
                    if task_link.drive_link:
                        evidence_urls.append(task_link.drive_link)

                if evidence_urls:
                    # Use first URL as pattern (could be enhanced)
                    unmatched_patterns[evidence_urls[0][:50]] += 1

                unmatched_tasks.append(
                    {
                        "task_id": task.id,
                        "activity_name": activity_name,
                        "activity_type": activity_type_slug or "N/A",
                        "submission": (
                            task.submission.strftime("%Y-%m-%d")
                            if task.submission
                            else "N/A"
                        ),
                        "evidence_count": len(evidence_urls),
                    }
                )

        # Print report
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("Match Quality Report"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"\nDate Range: {start_date.date()} to {end_date.date()}")
        if service_filter:
            self.stdout.write(f"Service Filter: {service_filter}")
        self.stdout.write(f"Total Tasks Analyzed: {total_tasks}")

        # Match rate summary
        total_matched = sum(
            stats["matched"] for stats in match_stats_by_activity.values()
        )
        match_rate = (total_matched / total_tasks * 100) if total_tasks > 0 else 0
        self.stdout.write(
            f"Overall Match Rate: {total_matched}/{total_tasks} ({match_rate:.1f}%)"
        )

        # By activity type
        self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
        self.stdout.write(self.style.SUCCESS("Match Rate by Activity Type"))
        self.stdout.write(self.style.SUCCESS("-" * 80))
        self.stdout.write(
            f"{'Activity Name':<40s} {'Total':>8s} {'Matched':>8s} {'URL':>6s} {'Topic':>6s} {'Rate':>8s}"
        )
        self.stdout.write("-" * 80)

        # Sort by total count (descending)
        sorted_activities = sorted(
            match_stats_by_activity.items(), key=lambda x: x[1]["total"], reverse=True
        )

        for activity_name, stats in sorted_activities[:20]:  # Top 20
            rate = (
                (stats["matched"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            self.stdout.write(
                f"{activity_name[:39]:<40s} {stats['total']:>8d} {stats['matched']:>8d} "
                f"{stats['url_match']:>6d} {stats['topic_match']:>6d} {rate:>7.1f}%"
            )

        # By service (if applicable)
        if match_stats_by_service:
            self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
            self.stdout.write(self.style.SUCCESS("Match Rate by Service"))
            self.stdout.write(self.style.SUCCESS("-" * 80))
            self.stdout.write(
                f"{'Service':<30s} {'Total':>8s} {'Matched':>8s} {'Rate':>8s}"
            )
            self.stdout.write("-" * 80)

            for service_name, stats in sorted(
                match_stats_by_service.items(),
                key=lambda x: x[1]["total"],
                reverse=True,
            ):
                rate = (
                    (stats["matched"] / stats["total"] * 100)
                    if stats["total"] > 0
                    else 0
                )
                self.stdout.write(
                    f"{service_name:<30s} {stats['total']:>8d} {stats['matched']:>8d} {rate:>7.1f}%"
                )

        # Top unmatched patterns
        if unmatched_patterns:
            self.stdout.write(self.style.SUCCESS("\n" + "-" * 80))
            self.stdout.write(
                self.style.SUCCESS("Top Unmatched Patterns (Evidence URLs)")
            )
            self.stdout.write(self.style.SUCCESS("-" * 80))
            for pattern, count in sorted(
                unmatched_patterns.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                self.stdout.write(f"  {count:4d}x: {pattern[:70]}")

        # Export if requested
        if export_path:
            try:
                export_data = []
                for activity_name, stats in sorted_activities:
                    rate = (
                        (stats["matched"] / stats["total"] * 100)
                        if stats["total"] > 0
                        else 0
                    )
                    export_data.append(
                        {
                            "activity_name": activity_name,
                            "total_tasks": stats["total"],
                            "matched_tasks": stats["matched"],
                            "url_matches": stats["url_match"],
                            "topic_matches": stats["topic_match"],
                            "match_rate_pct": round(rate, 2),
                        }
                    )

                with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                    if export_data:
                        fieldnames = export_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(export_data)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Exported {len(export_data)} rows to: {export_path}"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Failed to export CSV: {e}"))

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("Report Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))
