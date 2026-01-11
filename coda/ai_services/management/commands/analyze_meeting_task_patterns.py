"""
Management command to analyze meeting-task patterns from database.

DB-only analysis pipeline to discover real matching patterns between Tasks and Meetings.
No GoToMeeting API calls - uses only existing database records.

Usage:
    poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal
    poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal --out patterns.csv --verbose
"""

import csv
import json
import logging
from datetime import timedelta

from ai_services.models import Meeting, MeetingAttendee
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone
from management.models import Task

from coda.config.activity_definitions import ACTIVITY_POLICIES

logger = logging.getLogger(__name__)
User = get_user_model()


# Activity keyword mappings for subject matching
ACTIVITY_KEYWORD_MAPPINGS = {
    "INTERNAL_TRAINING_SESSION": [
        "training",
        "learn",
        "skill",
        "session",
        "workshop",
        "internal",
        "daf",
        "meeting",
    ],
    "DAILY_UPDATE_SESSION": [
        "daily",
        "update",
        "standup",
        "status",
        "progress",
        "daf",
        "session",
    ],
    "BUDGETING_FORECASTING_SESSION": [
        "budget",
        "forecast",
        "financial",
        "planning",
        "finance",
    ],
    "UAT_TESTING_SUPPORT": ["uat", "testing", "test", "qa", "quality", "support"],
    "CLIENT_TRAINING_SESSION": ["client", "training", "customer", "onboarding"],
    "SELF_TRAINING_SESSION": ["self", "training", "learning", "study"],
    "PRODUCT_BACKLOG_REFINEMENT": [
        "pbr",
        "backlog",
        "refinement",
        "sprint",
        "planning",
    ],
}


def normalize_name(name: str) -> str:
    """Normalize name for matching: lowercase, strip punctuation, collapse whitespace."""
    if not name:
        return ""
    import re

    normalized = re.sub(r"[^\w\s]", "", name.lower())
    normalized = " ".join(normalized.split())
    return normalized


def calculate_subject_keyword_score(subject: str, activity_slug: str) -> float:
    """
    Calculate keyword match score between meeting subject and activity type.

    Returns score 0.0-1.0 based on keyword overlap.
    """
    if not subject or not activity_slug:
        return 0.0

    keywords = ACTIVITY_KEYWORD_MAPPINGS.get(activity_slug.upper(), [])
    if not keywords:
        return 0.0

    subject_normalized = normalize_name(subject)
    subject_tokens = set(subject_normalized.split())

    matches = 0
    for keyword in keywords:
        keyword_normalized = normalize_name(keyword)
        if (
            keyword_normalized in subject_tokens
            or keyword_normalized in subject_normalized
        ):
            matches += 1

    # Score based on proportion of keywords matched
    if not keywords:
        return 0.0
    return min(1.0, matches / len(keywords))


def calculate_attendee_name_score(
    attendee_names: list, employee_first_name: str, employee_last_name: str
) -> float:
    """
    Calculate name match score between attendee names and employee name.

    Returns score 0.0-1.0.
    """
    if not attendee_names or not employee_first_name:
        return 0.0

    employee_first_normalized = normalize_name(employee_first_name)
    employee_last_normalized = (
        normalize_name(employee_last_name) if employee_last_name else ""
    )
    employee_full_normalized = (
        f"{employee_first_normalized} {employee_last_normalized}".strip()
    )

    best_score = 0.0
    for attendee_name in attendee_names:
        if not attendee_name:
            continue

        attendee_normalized = normalize_name(attendee_name)
        attendee_tokens = set(attendee_normalized.split())

        # Check full name match
        if attendee_normalized == employee_full_normalized:
            best_score = max(best_score, 1.0)
            continue

        # Check if contains both first and last
        has_first = employee_first_normalized in attendee_tokens
        has_last = (
            employee_last_normalized in attendee_tokens
            if employee_last_normalized
            else False
        )

        if has_first and has_last:
            best_score = max(best_score, 1.0)
        elif has_first:
            # First name only - lower score
            best_score = max(best_score, 0.7)

    return best_score


def check_meeting_id_recurring_boost(meeting_id: str, meetings_queryset) -> float:
    """
    Check if meeting_id repeats with similar subjects (recurring meeting pattern).

    Accepts either a QuerySet or a list of Meeting objects.

    Returns boost score 0.0-0.2.
    """
    if not meeting_id:
        return 0.0

    # Count occurrences of this meeting_id
    # Handle both QuerySet and list
    if hasattr(meetings_queryset, "filter"):
        # It's a QuerySet
        count = meetings_queryset.filter(meeting_id=meeting_id).count()
    else:
        # It's a list - count manually
        count = sum(
            1
            for meeting in meetings_queryset
            if getattr(meeting, "meeting_id", None) == meeting_id
        )

    if count >= 3:
        return 0.2  # Strong recurring pattern
    elif count >= 2:
        return 0.1  # Weak recurring pattern

    return 0.0


class Command(BaseCommand):
    help = "Analyze meeting-task patterns from database (DB-only, no API calls)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="User ID to analyze patterns for (single user mode)",
        )
        parser.add_argument(
            "--group",
            type=str,
            choices=["A", "B", "C"],
            help="Employee group for cohort analysis (A, B, or C)",
        )
        parser.add_argument(
            "--department-id",
            type=int,
            help="Department ID for cohort analysis",
        )
        parser.add_argument(
            "--limit-users",
            type=int,
            help="Limit number of users in cohort analysis (default: no limit)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days to look back (default: 90)",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="internal",
            help="Service filter: internal (gotomeeting_internal), external (gotomeeting_external), or all (default: internal)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Maximum number of meetings/tasks to consider per user (default: 200)",
        )
        parser.add_argument(
            "--out",
            type=str,
            help="Output file path (CSV or JSON). If not provided, prints to stdout",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        group = options.get("group")
        department_id = options.get("department_id")
        limit_users = options.get("limit_users")
        days = options["days"]
        service_option = options["service"]
        limit = options["limit"]
        output_path = options.get("out")
        verbose = options.get("verbose", False)

        # Validate arguments
        if not user_id and not group and not department_id:
            raise CommandError(
                "Must provide either --user-id, --group, or --department-id"
            )

        # Map service option to service_name
        service_name = None
        if service_option == "external":
            service_name = "gotomeeting_external"
        elif service_option == "internal":
            service_name = "gotomeeting_internal"

        self.stdout.write(
            self.style.SUCCESS(f"\n🔍 Meeting-Task Pattern Analysis (DB-Only) 🔍\n")
        )

        # Get candidate employees
        if user_id:
            # Single user mode
            try:
                users = [User.objects.get(id=user_id)]
                self.stdout.write(f"Mode: Single user")
                self.stdout.write(f"User ID: {user_id}")
            except User.DoesNotExist:
                raise CommandError(f"User with ID {user_id} not found")
        else:
            # Cohort mode
            from django.contrib.auth import get_user_model
            from management.models import EmployeeCareerState
            from management.services.employee_filter_service import \
                get_filtered_employees_queryset

            User = get_user_model()

            class MockRequest:
                def __init__(self):
                    self.user = type(
                        "User", (), {"is_staff": True, "is_superuser": True}
                    )()
                    self.GET = {}

            mock_request = MockRequest()

            # Debug: Check EmployeeCareerState counts
            if verbose:
                career_state_counts = (
                    EmployeeCareerState.objects.values("group")
                    .annotate(count=Count("id"))
                    .order_by("group")
                )
                self.stdout.write(f"\nEmployeeCareerState counts by group:")
                for item in career_state_counts:
                    self.stdout.write(
                        f"  Group {item['group']}: {item['count']} employees"
                    )
                total_career_states = EmployeeCareerState.objects.count()
                self.stdout.write(
                    f"  Total EmployeeCareerState records: {total_career_states}"
                )

            # Get base employee queryset
            users_qs = get_filtered_employees_queryset(
                mock_request, test_patterns=None, include_inactive=False
            )

            base_count = users_qs.count()
            if verbose:
                self.stdout.write(
                    f"Base employees (from get_filtered_employees_queryset): {base_count}"
                )

            # Apply group filter
            if group:
                # Check if any EmployeeCareerState records exist for this group
                group_count = EmployeeCareerState.objects.filter(group=group).count()
                if verbose:
                    self.stdout.write(
                        f"Employees with Group {group} in EmployeeCareerState: {group_count}"
                    )

                if group_count == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  No EmployeeCareerState records found for Group {group}. "
                            f"Employees may not have groups assigned yet. "
                            f"Consider using --department-id instead, or seed EmployeeCareerState records."
                        )
                    )

                # Use select_related to avoid N+1 queries
                users_qs = users_qs.select_related("career_state").filter(
                    career_state__group=group
                )
                self.stdout.write(f"Mode: Cohort (Group {group})")

            # Apply department filter
            if department_id:
                users_qs = users_qs.filter(department_id=department_id)
                self.stdout.write(f"Mode: Cohort (Department {department_id})")

            # Debug: Show count after filters
            filtered_count = users_qs.count()
            if verbose:
                self.stdout.write(f"Employees after filters: {filtered_count}")

            if filtered_count == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  No employees found matching criteria. "
                        f"Base count: {base_count}, After filters: {filtered_count}"
                    )
                )
                if group:
                    self.stdout.write(
                        self.style.WARNING(
                            f"💡 TIP: If Group {group} filtering returns 0, try: "
                            f"1. Check EmployeeCareerState records exist: "
                            f"SELECT COUNT(*) FROM management_employeecareerstate WHERE group = '{group}'; "
                            f"2. Use --department-id instead: --department-id <id> "
                            f"3. Seed EmployeeCareerState records via admin or employee groups UI"
                        )
                    )

            # Limit users if specified
            if limit_users:
                users_qs = users_qs[:limit_users]

            users = list(users_qs)
            self.stdout.write(f"Users in cohort: {len(users)}")

            if len(users) == 0:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ No users found in cohort. Cannot proceed with analysis."
                    )
                )
                return

        self.stdout.write(f"Days: {days}")
        self.stdout.write(f"Service: {service_option}\n")

        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get meeting-required tasks (from ActivityPolicy)
        from coda.config.activity_definitions import (ACTIVITY_POLICIES,
                                                      get_activity_policy)

        meeting_required_slugs = [
            slug
            for slug, policy in ACTIVITY_POLICIES.items()
            if policy.meeting_required
        ]

        # Build activity filter
        activity_filter = Q()
        for slug in meeting_required_slugs:
            activity_filter |= Q(activity_type__slug__iexact=slug)
            activity_filter |= Q(activity_type__name__iexact=slug)
            activity_filter |= Q(activity_name__iexact=slug)

        # 1) Get all meetings in date range (FIX: apply all filters first, slice at end)
        meetings_query = Meeting.objects.filter(
            start_time__gte=start_date, start_time__lte=end_date
        )

        if service_name:
            meetings_query = meetings_query.filter(service_name=service_name)

        # Materialize meetings list (apply all filters, then slice)
        all_meetings = list(
            meetings_query.order_by("-start_time")[: limit * 10]
        )  # Get more for filtering later
        meeting_count = len(all_meetings)

        self.stdout.write(f"📅 Meetings found: {meeting_count}")
        if verbose and all_meetings:
            for meeting in all_meetings[:10]:
                self.stdout.write(
                    f"  - Meeting {meeting.meeting_id}: {meeting.topic[:50] if meeting.topic else 'N/A'} ({meeting.start_time.date()})"
                )

        # 2) Get attendees for all meetings (FIX: use materialized list)
        meeting_db_ids = [m.id for m in all_meetings]
        attendees = MeetingAttendee.objects.filter(
            meeting_id__in=meeting_db_ids
        ).select_related("meeting", "user")

        # Build attendee map: meeting.id -> [attendee_names]
        attendee_map = {}
        attendees_with_names = 0
        for attendee in attendees:
            meeting_id_key = attendee.meeting.id
            if meeting_id_key not in attendee_map:
                attendee_map[meeting_id_key] = []
            if attendee.attendee_name:
                attendee_map[meeting_id_key].append(attendee.attendee_name)
                attendees_with_names += 1

        self.stdout.write(
            f"👥 Attendees found: {attendees.count()} total, {attendees_with_names} with names, across {len(attendee_map)} meetings"
        )

        if verbose and len(attendee_map) > 0:
            sample_meeting_id = list(attendee_map.keys())[0]
            sample_names = attendee_map[sample_meeting_id][:3]
            self.stdout.write(f"  Sample attendee names: {', '.join(sample_names)}")

        self.stdout.write("")

        # 3) Process each user in cohort
        all_results = []
        total_tasks_analyzed = 0

        for user in users:
            if verbose:
                self.stdout.write(
                    f"\n📋 Processing user: {user.username} (ID: {user.id})"
                )

            # Get tasks for this user
            tasks = (
                Task.objects.filter(employee_id=user.id, is_active=True)
                .filter(activity_filter)
                .select_related("activity_type", "requirement", "employee")
            )

            # Get tasks within relevant window
            tasks_in_window = tasks.filter(
                Q(submission__gte=start_date, submission__lte=end_date)
                | Q(submission__isnull=True)
            )

            tasks_to_analyze = list(tasks_in_window.distinct()[:limit])
            task_count = len(tasks_to_analyze)
            total_tasks_analyzed += task_count

            if verbose:
                self.stdout.write(f"  Tasks found: {task_count}")
                for task in tasks_to_analyze[:5]:
                    activity_slug = (
                        task.activity_type.slug
                        if task.activity_type
                        else task.activity_name
                    )
                    task_date_str = (
                        task.submission.date().isoformat()
                        if task.submission
                        else "no submission"
                    )
                    self.stdout.write(
                        f"    - Task {task.id}: {activity_slug} (submission: {task_date_str})"
                    )

            # 4) Build candidate matrix per task
            for task in tasks_to_analyze:
                # Use submission date (matches DAF evaluation)
                # Task model has NO created_at field
                task_date = task.submission
                if not task_date:
                    continue

                # Get activity policy to determine window mode
                activity_slug = None
                if task.activity_type:
                    activity_slug = task.activity_type.slug or task.activity_type.name
                elif task.activity_name:
                    activity_slug = task.activity_name.upper().replace(" ", "_")

                policy = get_activity_policy(activity_slug) if activity_slug else None
                window_mode = policy.window_mode if policy else "submission_window"

                # Define time window based on window_mode
                if window_mode == "recent_window":
                    # Ongoing meetings: use NOW()-days..NOW() window
                    task_start = end_date - timedelta(days=2)
                    task_end = end_date
                else:
                    # Cycle-based: use submission anchor
                    time_window_days = 2
                    task_start = task_date - timedelta(days=time_window_days)
                    task_end = task_date + timedelta(days=time_window_days)

                    # Ensure we don't go beyond today
                    if task_end > timezone.now():
                        task_end = timezone.now()

                # Filter meetings by time window overlap (FIX: filter materialized list in Python)
                candidate_meetings = [
                    m
                    for m in all_meetings
                    if m.start_time.date() >= task_start.date()
                    and m.start_time.date() <= task_end.date()
                ]

                # Score each candidate meeting
                scored_meetings = []

                # Get meeting room ID for boost signal
                meeting_room_id = None
                if activity_slug:
                    try:
                        from ai_services.utils.meeting_room_config import \
                            get_meeting_room_for_activity

                        meeting_room_id, _ = get_meeting_room_for_activity(
                            activity_slug
                        )
                    except Exception:
                        pass

                for meeting in candidate_meetings:
                    signals_hit = []
                    score = 0.0

                    # Signal: time_window_hit
                    signals_hit.append("time_window")

                    # Signal: meeting_room_id boost (only if matches)
                    if meeting_room_id and meeting.meeting_id == meeting_room_id:
                        signals_hit.append("meeting_room_id")
                        score += 0.15  # Boost: 15%

                    # Signal: subject_keyword_score
                    subject_score = 0.0
                    if activity_slug and meeting.topic:
                        subject_score = calculate_subject_keyword_score(
                            meeting.topic, activity_slug
                        )
                        if subject_score > 0:
                            signals_hit.append(f"subject_keyword_{subject_score:.2f}")
                            score += subject_score * 0.3  # Weight: 30%

                    # Signal: attendee-name inference (match employee name against attendee_name)
                    attendee_names = attendee_map.get(meeting.id, [])
                    name_score = 0.0
                    if task.employee:
                        name_score = calculate_attendee_name_score(
                            attendee_names,
                            task.employee.first_name or "",
                            task.employee.last_name or "",
                        )
                        if name_score > 0:
                            signals_hit.append(f"attendee_name_{name_score:.2f}")
                            score += name_score * 0.5  # Weight: 50%

                    # Signal: meeting_id_recurring_boost (FIX: use materialized list)
                    recurring_boost = check_meeting_id_recurring_boost(
                        meeting.meeting_id, all_meetings
                    )
                    if recurring_boost > 0:
                        signals_hit.append(f"recurring_boost_{recurring_boost:.2f}")
                        score += recurring_boost

                    # Base score for time window
                    score += 0.2  # Base: 20%

                # Build explanation
                explanation_parts = []
                if subject_score > 0:
                    explanation_parts.append(
                        f"subject keywords match ({subject_score:.2f})"
                    )
                if name_score > 0:
                    explanation_parts.append(f"attendee name match ({name_score:.2f})")
                if recurring_boost > 0:
                    explanation_parts.append(f"recurring meeting pattern")
                if not explanation_parts:
                    explanation_parts.append("time window only")

                    explanation = "; ".join(explanation_parts)

                    scored_meetings.append(
                        {
                            "meeting_id": meeting.meeting_id,
                            "start_time": (
                                meeting.start_time.isoformat()
                                if meeting.start_time
                                else None
                            ),
                            "subject": meeting.topic or "N/A",
                            "duration_minutes": meeting.duration_minutes,
                            "score": score,
                            "signals_hit": signals_hit,
                            "explanation": explanation,
                            "service_name": meeting.service_name,
                        }
                    )

                # Sort by score (highest first) and take top 10
                scored_meetings.sort(key=lambda x: x["score"], reverse=True)
                top_meetings = scored_meetings[:10]

                all_results.append(
                    {
                        "user_id": user.id,
                        "task_id": task.id,
                        "activity_slug": activity_slug,
                        "task_submission": (
                            task_date.date().isoformat() if task_date else None
                        ),
                        "candidate_meetings_count": len(scored_meetings),
                        "top_meetings": top_meetings,
                    }
                )

        self.stdout.write(f"\n📋 Total tasks analyzed: {total_tasks_analyzed}")

        # 5) Output results
        results = all_results

        # Calculate summary statistics
        tasks_with_top_score_high = 0  # >= 0.8
        tasks_with_top_score_medium = 0  # >= 0.6
        tasks_unmatched = 0

        for result in results:
            if result["top_meetings"]:
                top_score = result["top_meetings"][0]["score"]
                if top_score >= 0.8:
                    tasks_with_top_score_high += 1
                elif top_score >= 0.6:
                    tasks_with_top_score_medium += 1
            else:
                tasks_unmatched += 1

        total_tasks = len(results)

        # Output results
        if output_path:
            if output_path.endswith(".json"):
                # JSON output
                with open(output_path, "w") as f:
                    json.dump(results, f, indent=2)
                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ Results written to {output_path} (JSON)")
                )
            else:
                # CSV output (updated format)
                with open(output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "user_id",
                            "task_id",
                            "activity_slug",
                            "task_submission",
                            "candidate_meeting_id",
                            "meeting_start",
                            "meeting_topic",
                            "score",
                            "signals_hit",
                            "explanation",
                        ]
                    )

                    for result in results:
                        for rank, meeting in enumerate(result["top_meetings"], 1):
                            writer.writerow(
                                [
                                    result["user_id"],
                                    result["task_id"],
                                    result["activity_slug"],
                                    result["task_submission"] or "",
                                    meeting["meeting_id"],
                                    meeting["start_time"],
                                    meeting["subject"],
                                    f"{meeting['score']:.3f}",
                                    ", ".join(meeting["signals_hit"]),
                                    meeting["explanation"],
                                ]
                            )

                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ Results written to {output_path} (CSV)")
                )
        else:
            # Print to stdout (verbose report)
            if verbose:
                self.stdout.write(f"\n{'='*100}")
                self.stdout.write(f"📊 Analysis Results (Sample)\n")
                self.stdout.write(f"{'='*100}\n")

                for result in results[:20]:  # Show first 20 tasks
                    self.stdout.write(
                        f"\nUser {result['user_id']} - Task {result['task_id']}: {result['activity_slug']}"
                    )
                    self.stdout.write(
                        f"  Submission: {result['task_submission'] or 'N/A'}"
                    )
                    self.stdout.write(
                        f"  Candidates: {result['candidate_meetings_count']}"
                    )

                    if result["top_meetings"]:
                        self.stdout.write(f"  Top Meetings:")
                        for i, meeting in enumerate(result["top_meetings"][:3], 1):
                            self.stdout.write(
                                f"    {i}. {meeting['meeting_id']} | Score: {meeting['score']:.3f}"
                            )
                            self.stdout.write(
                                f"       Subject: {meeting['subject'][:60]}"
                            )
                            self.stdout.write(
                                f"       Signals: {', '.join(meeting['signals_hit'][:3])}"
                            )
                            self.stdout.write(
                                f"       Explanation: {meeting['explanation']}"
                            )
                    else:
                        self.stdout.write(f"  No candidate meetings found")

        # Summary statistics
        tasks_with_candidates = sum(
            1 for r in results if r["candidate_meetings_count"] > 0
        )

        # Find most common meeting_ids
        meeting_id_counts = {}
        for result in results:
            for meeting in result["top_meetings"]:
                mid = meeting["meeting_id"]
                if mid:
                    meeting_id_counts[mid] = meeting_id_counts.get(mid, 0) + 1

        top_meeting_ids = sorted(
            meeting_id_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        self.stdout.write(f"\n{'='*100}")
        self.stdout.write(f"📈 Summary Statistics\n")
        self.stdout.write(f"{'='*100}")
        self.stdout.write(f"Total tasks analyzed: {total_tasks}")
        self.stdout.write(f"Tasks with candidate meetings: {tasks_with_candidates}")
        self.stdout.write(f"Tasks without candidates: {tasks_unmatched}")

        if total_tasks > 0:
            pct_high = (tasks_with_top_score_high / total_tasks) * 100
            pct_medium = (tasks_with_top_score_medium / total_tasks) * 100
            pct_unmatched = (tasks_unmatched / total_tasks) * 100

            self.stdout.write(f"\nScore Distribution:")
            self.stdout.write(
                f"  Top score >= 0.8: {tasks_with_top_score_high} ({pct_high:.1f}%)"
            )
            self.stdout.write(
                f"  Top score >= 0.6: {tasks_with_top_score_medium} ({pct_medium:.1f}%)"
            )
            self.stdout.write(f"  Unmatched: {tasks_unmatched} ({pct_unmatched:.1f}%)")

        if top_meeting_ids:
            self.stdout.write(f"\nMost common meeting_ids:")
            for meeting_id, count in top_meeting_ids:
                # Get sample subject from materialized list
                sample_meeting = next(
                    (m for m in all_meetings if m.meeting_id == meeting_id), None
                )
                subject = (
                    sample_meeting.topic[:50]
                    if sample_meeting and sample_meeting.topic
                    else "N/A"
                )
                self.stdout.write(f"  {meeting_id}: {count} matches ({subject})")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Analysis complete!\n"))
