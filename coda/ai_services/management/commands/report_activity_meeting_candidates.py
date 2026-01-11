"""
Management command to report activity → meeting ID candidates.

Helps identify which meeting rooms (meeting_ids) are most commonly used
for each activity type, based on:
- Meeting frequency (count of meetings with matching patterns)
- TaskLink associations (if tasks link to meetings)
- Attendee overlap (if available)

Usage:
    python manage.py report_activity_meeting_candidates --service internal --days 60
    python manage.py report_activity_meeting_candidates --service all --days 90 --min-count 5
    python manage.py report_activity_meeting_candidates --seed-mapping --dry-run
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from ai_services.models import Meeting, MeetingAttendee
from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from django.utils import timezone
from management.models import ActivityType, Task, TaskLinks

from coda.config.activity_definitions import ACTIVITY_POLICIES


class Command(BaseCommand):
    help = "Report activity → meeting ID candidates for mapping decisions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            default="internal",
            choices=["internal", "external", "all"],
            help="Service name filter (default: internal)",
        )
        parser.add_argument(
            "--days", type=int, default=60, help="Time window in days (default: 60)"
        )
        parser.add_argument(
            "--limit-activities",
            type=int,
            default=None,
            help="Limit number of activities to process",
        )
        parser.add_argument(
            "--min-count",
            type=int,
            default=1,
            help="Minimum meeting count to include candidate (default: 1)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )
        parser.add_argument(
            "--seed-mapping",
            action="store_true",
            help="Propose seeding MeetingActivityMapping for dominant candidates",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=True,
            help="Dry run mode (default: True, set --no-dry-run to actually seed)",
        )
        parser.add_argument(
            "--dominance-threshold",
            type=float,
            default=0.6,
            help="Dominance threshold for seeding (default: 0.6 = 60%%)",
        )

    def handle(self, *args, **options):
        service_filter = options["service"]
        days = options["days"]
        limit_activities = options["limit_activities"]
        min_count = options["min_count"]
        verbose = options["verbose"]
        seed_mapping = options["seed_mapping"]
        dry_run = options["dry_run"]
        dominance_threshold = options["dominance_threshold"]

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS("Activity → Meeting ID Candidate Report"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
        self.stdout.write(f"Time window: Last {days} days (since {cutoff_date.date()})")
        self.stdout.write(f"Service filter: {service_filter}")
        self.stdout.write(f"Min count: {min_count}\n")

        # Get all active activity types
        activity_types = ActivityType.objects.filter(is_active=True).order_by("slug")
        if limit_activities:
            activity_types = activity_types[:limit_activities]

        # Service filter
        if service_filter == "internal":
            service_names = ["gotomeeting_internal"]
        elif service_filter == "external":
            service_names = ["gotomeeting_external"]
        else:
            service_names = ["gotomeeting_internal", "gotomeeting_external"]

        # Process each activity
        results = []
        for activity_type in activity_types:
            activity_slug = activity_type.slug or activity_type.name.upper().replace(
                " ", "_"
            )
            activity_name = activity_type.name

            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(
                self.style.WARNING(f"Activity: {activity_name} ({activity_slug})")
            )
            self.stdout.write(f"{'-'*80}")

            # Find meetings in time window for this service
            meetings_qs = Meeting.objects.filter(
                service_name__in=service_names, start_time__gte=cutoff_date
            )

            # Try to match by meeting_room_id from policy/config
            meeting_room_id = None
            try:
                from ai_services.utils.meeting_room_config import \
                    get_meeting_room_for_activity

                meeting_room_id, _ = get_meeting_room_for_activity(activity_slug)
            except Exception:
                pass

            # Count meetings by meeting_id
            meeting_counts = defaultdict(int)
            meeting_topics = defaultdict(list)

            # Get meetings that might be related to this activity
            # Strategy 1: Match by meeting_room_id if configured
            if meeting_room_id:
                room_meetings = meetings_qs.filter(meeting_id=meeting_room_id)
                for meeting in room_meetings:
                    meeting_counts[meeting.meeting_id] += 1
                    if (
                        meeting.topic
                        and meeting.topic not in meeting_topics[meeting.meeting_id]
                    ):
                        meeting_topics[meeting.meeting_id].append(meeting.topic[:50])

            # Strategy 2: Find TaskLinks that link tasks of this activity to meetings
            task_links = TaskLinks.objects.filter(
                task__activity_type=activity_type,
                task__is_active=True,
                meeting_id__isnull=False,
                is_active=True,
            ).select_related("task")

            tasklink_meeting_ids = defaultdict(int)
            for link in task_links:
                if link.meeting_id:
                    tasklink_meeting_ids[link.meeting_id] += 1

            # Strategy 3: Count meetings by frequency (all meetings in time window)
            # This is a fallback if no direct links exist
            all_meetings = (
                meetings_qs.values("meeting_id", "topic")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            # Combine strategies
            candidates = defaultdict(
                lambda: {
                    "count": 0,
                    "tasklink_count": 0,
                    "topics": set(),
                    "total_meetings": 0,
                }
            )

            # Add tasklink-based candidates
            for meeting_id, count in tasklink_meeting_ids.items():
                candidates[meeting_id]["tasklink_count"] = count
                candidates[meeting_id]["count"] += count * 2  # Weight tasklinks higher

            # Add meeting_room_id matches
            if meeting_room_id and meeting_room_id in meeting_counts:
                candidates[meeting_room_id]["count"] += meeting_counts[meeting_room_id]
                candidates[meeting_room_id]["topics"].update(
                    meeting_topics[meeting_room_id]
                )

            # Add frequency-based candidates (if no strong signals)
            if not candidates:
                for meeting_data in all_meetings[:10]:  # Top 10 by frequency
                    meeting_id = meeting_data["meeting_id"]
                    count = meeting_data["count"]
                    topic = meeting_data.get("topic", "")
                    candidates[meeting_id]["count"] += count
                    candidates[meeting_id]["total_meetings"] = count
                    if topic:
                        candidates[meeting_id]["topics"].add(topic[:50])

            # Sort candidates by score
            sorted_candidates = sorted(
                candidates.items(),
                key=lambda x: (x[1]["count"], x[1]["tasklink_count"]),
                reverse=True,
            )

            # Filter by min_count
            sorted_candidates = [
                (mid, data)
                for mid, data in sorted_candidates
                if data["count"] >= min_count
            ]

            if not sorted_candidates:
                self.stdout.write(self.style.WARNING("  No candidates found"))
                continue

            # Calculate dominance
            total_count = sum(data["count"] for _, data in sorted_candidates)
            top_candidate_id, top_candidate_data = sorted_candidates[0]
            dominance_ratio = (
                top_candidate_data["count"] / total_count if total_count > 0 else 0
            )

            # Display results
            self.stdout.write(f"\n  Top candidates:")
            for idx, (meeting_id, data) in enumerate(sorted_candidates[:5], 1):
                topics_str = (
                    ", ".join(list(data["topics"])[:2]) if data["topics"] else "N/A"
                )
                marker = (
                    "⭐"
                    if idx == 1 and dominance_ratio >= dominance_threshold
                    else "  "
                )
                self.stdout.write(
                    f"  {marker} {idx}. Meeting ID: {meeting_id} "
                    f"(score: {data['count']}, tasklinks: {data['tasklink_count']}, "
                    f"meetings: {data['total_meetings']})"
                )
                if topics_str and verbose:
                    self.stdout.write(f"      Topics: {topics_str}")

            self.stdout.write(
                f"\n  Dominance: {top_candidate_id} = {dominance_ratio:.1%} of total"
            )
            if meeting_room_id:
                self.stdout.write(f"  Current config: {meeting_room_id}")

            # Store for seeding
            if seed_mapping and dominance_ratio >= dominance_threshold:
                results.append(
                    {
                        "activity_type": activity_type,
                        "activity_slug": activity_slug,
                        "activity_name": activity_name,
                        "top_meeting_id": top_candidate_id,
                        "dominance_ratio": dominance_ratio,
                        "candidate_data": top_candidate_data,
                    }
                )

        # Seed mapping if requested
        if seed_mapping and results:
            self.stdout.write(f"\n\n{'='*80}")
            self.stdout.write(self.style.SUCCESS("Seeding MeetingActivityMapping"))
            self.stdout.write(f"{'='*80}\n")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING("DRY RUN MODE - No changes will be made\n")
                )

            from ai_services.models import MeetingActivityMapping

            for result in results:
                activity_type = result["activity_type"]
                activity_name = result["activity_name"]
                meeting_id = result["top_meeting_id"]
                dominance = result["dominance_ratio"]

                # Check if mapping already exists
                existing = MeetingActivityMapping.objects.filter(
                    activity_name__iexact=activity_name, is_active=True
                ).first()

                if existing:
                    if existing.meeting_id_pattern == meeting_id:
                        self.stdout.write(
                            f"  ✓ {activity_name}: Already mapped to {meeting_id}"
                        )
                    else:
                        self.stdout.write(
                            f"  ⚠ {activity_name}: Exists but different "
                            f"(current: {existing.meeting_id_pattern}, "
                            f"proposed: {meeting_id}, dominance: {dominance:.1%})"
                        )
                        if not dry_run:
                            existing.meeting_id_pattern = meeting_id
                            existing.save()
                            self.stdout.write(f"    → Updated to {meeting_id}")
                else:
                    self.stdout.write(
                        f"  + {activity_name}: Would create mapping to {meeting_id} "
                        f"(dominance: {dominance:.1%})"
                    )
                    if not dry_run:
                        MeetingActivityMapping.objects.create(
                            activity_name=activity_name,
                            meeting_id_pattern=meeting_id,
                            is_active=True,
                        )
                        self.stdout.write(f"    → Created mapping")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING("\nRun with --no-dry-run to apply changes")
                )

        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS("Report complete!"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
