"""
Management command to analyze matching between TaskLinks evidence and Meeting records.

Usage:
    poetry run python coda/manage.py match_tasklinks_to_meetings
    poetry run python coda/manage.py match_tasklinks_to_meetings --task-id 123
    poetry run python coda/manage.py match_tasklinks_to_meetings --user-id 5 --days 14 --limit 50
    poetry run python coda/manage.py match_tasklinks_to_meetings --verbose

Phase 2B: Diagnostic tool for TaskLinks -> Meeting matching analysis.
"""

import logging
from datetime import timedelta

from ai_services.services.meeting_evidence_matcher import \
    MeetingEvidenceMatcher
from ai_services.utils.meeting_normalizer import normalize_url
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from management.models import Task, TaskLinks

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Analyze matching between TaskLinks evidence URLs and Meeting records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task-id",
            type=int,
            help="Analyze a specific task by ID",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Analyze tasks for a specific user (requires --days)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=14,
            help="Number of days back from now to scan (default: 14)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of tasks to analyze (default: 50)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed URL normalization and meeting candidates",
        )

    def handle(self, *args, **options):
        task_id = options.get("task_id")
        user_id = options.get("user_id")
        days = options.get("days", 14)
        limit = options.get("limit", 50)
        verbose = options.get("verbose", False)

        self.stdout.write(
            self.style.SUCCESS("\n📊 TaskLinks → Meeting Matching Analysis 📊\n")
        )

        # Initialize matcher
        matcher = MeetingEvidenceMatcher(enable_topic_fallback=True, time_window_days=2)

        # Determine task queryset
        if task_id:
            try:
                tasks = Task.objects.filter(id=task_id, is_active=True)
            except Task.DoesNotExist:
                raise CommandError(f"Task with ID {task_id} not found")
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f"User with ID {user_id} not found")

            since_date = timezone.now() - timedelta(days=days)
            tasks = Task.objects.filter(
                employee=user, is_active=True, submission__gte=since_date
            ).order_by("-submission")[:limit]
        else:
            # Default: recent active tasks
            since_date = timezone.now() - timedelta(days=days)
            tasks = Task.objects.filter(
                is_active=True, submission__gte=since_date
            ).order_by("-submission")[:limit]

        if not tasks.exists():
            self.stdout.write(self.style.WARNING("No tasks found matching criteria."))
            return

        self.stdout.write(f"Analyzing {tasks.count()} task(s)...\n")

        # Analyze each task
        matched_count = 0
        unmatched_count = 0
        total_duration = 0

        for task in tasks:
            # Get detailed matches
            detailed_matches = matcher.get_detailed_matches(task)

            if detailed_matches:
                matched_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Task {task.id} ({task.activity_name or 'No activity'}):"
                    )
                )

                for match in detailed_matches:
                    meeting = match["meeting"]
                    match_type = match["match_type"]
                    confidence = match["confidence"]

                    total_duration += meeting.duration_minutes or 0

                    match_reason = match.get("match_reason", "")
                    req_code_match = match.get("requirement_code_match")

                    # Confidence level label
                    if confidence >= 0.9:
                        conf_label = "VERY HIGH"
                    elif confidence >= 0.7:
                        conf_label = "MEDIUM"
                    else:
                        conf_label = "LOW"

                    req_status = ""
                    if req_code_match is True:
                        req_status = " | REQ: ✅ Match"
                    elif req_code_match is False:
                        req_status = " | REQ: ❌ Mismatch"
                    elif req_code_match is None and match_type == "url":
                        # URL match but no REQ code in meeting
                        req_status = " | REQ: ⚠️  Missing"

                    self.stdout.write(
                        f"   Meeting: {meeting.meeting_id} | "
                        f"Topic: {meeting.topic[:50]}... | "
                        f"Duration: {meeting.duration_minutes} min | "
                        f"Match: {match_type} | Confidence: {confidence:.2f} ({conf_label}){req_status}"
                    )

                    if verbose:
                        self.stdout.write(
                            f"   Start: {meeting.start_time.strftime('%Y-%m-%d %H:%M')} | "
                            f"Service: {meeting.service_name or 'N/A'} | "
                            f"Recording URL: {meeting.recording_url[:60] if meeting.recording_url else 'N/A'}..."
                        )
                        if meeting.requirement_code:
                            self.stdout.write(
                                f"   Meeting REQ code: {meeting.requirement_code}"
                            )
                        if match_type == "topic" and match_reason:
                            self.stdout.write(f"   Match reason: {match_reason}")
            else:
                unmatched_count += 1
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n❌ Task {task.id} ({task.activity_name or 'No activity'}): No matches"
                        )
                    )

                    # Show evidence URLs
                    task_links = TaskLinks.objects.filter(task=task, is_active=True)
                    evidence_urls = []
                    for task_link in task_links:
                        if task_link.link:
                            evidence_urls.append(task_link.link)
                        if task_link.drive_link:
                            evidence_urls.append(task_link.drive_link)

                    if evidence_urls:
                        self.stdout.write("   Evidence URLs:")
                        for url in evidence_urls[:3]:  # Show first 3
                            normalized = normalize_url(url)
                            self.stdout.write(f"     - {url[:60]}...")
                            if normalized != url:
                                self.stdout.write(
                                    f"       → Normalized: {normalized[:60]}..."
                                )
                    else:
                        self.stdout.write("   No evidence URLs found")

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  Tasks scanned: {tasks.count()}")
        self.stdout.write(f"  Matched tasks: {matched_count}")
        self.stdout.write(f"  Unmatched tasks: {unmatched_count}")

        if tasks.count() > 0:
            match_rate = (matched_count / tasks.count()) * 100
            self.stdout.write(f"  Match rate: {match_rate:.1f}%")

        if total_duration > 0:
            self.stdout.write(f"  Total duration found: {total_duration} minutes")

        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))
