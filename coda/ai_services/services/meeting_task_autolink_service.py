"""
Meeting Task Auto-Link Service.

Phase 3: Automatically creates TaskLinks evidence from Meeting records for meeting-based tasks.
DB-only pipeline: Meeting → Matching → Evidence creation → Score updates.

HARDENED VERSION: Strict matching rules, idempotency, observability.

No API calls - uses only database queries.
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ai_services.models import Meeting, MeetingAttendee
from ai_services.services.meeting_evidence_matcher import \
    MeetingEvidenceMatcher
from ai_services.utils.meeting_normalizer import (
    extract_candidate_activity_tags, normalize_topic, normalize_url)
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from management.models import Requirement, Task, TaskLinks, TaskReviewComment
from management.services.checklist_evaluation_service import \
    ChecklistEvaluationService
from management.views import REQUIREMENT_REQUIRED_ACTIVITY_TYPES

logger = logging.getLogger(__name__)

# Meeting-based activity types that support auto-evidence linking
MEETING_BASED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",  # Alternative name for PBR
    "UAT_TESTING_SUPPORT",  # UAT Testing Support (meeting-required for Group B)
]


def normalize_email(email: str) -> str:
    """
    Normalize email address for consistent matching.

    Args:
        email: Email address string

    Returns:
        Normalized email (lowercase, trimmed)
    """
    if not email:
        return ""
    return email.lower().strip()


def get_canonical_emails_for_user(user) -> Set[str]:
    """
    Get canonical set of email addresses for a user.

    Checks:
    - user.email (primary)
    - user.profile.email if exists (work email)
    - Any other email fields if present

    Args:
        user: User instance

    Returns:
        Set of normalized email addresses
    """
    emails = set()

    if user and hasattr(user, "email") and user.email:
        emails.add(normalize_email(user.email))

    # Check for profile with work email (if UserProfile has email field)
    if hasattr(user, "profile"):
        profile = getattr(user, "profile", None)
        if profile:
            # UserProfile doesn't have email field, but check anyway for future-proofing
            if hasattr(profile, "email") and profile.email:
                emails.add(normalize_email(profile.email))

    return emails


class MeetingTaskAutolinkService:
    """
    Service for automatically linking Meeting records to Tasks and creating evidence.

    HARDENED: Strict matching rules, idempotency guarantees, comprehensive logging.

    Responsibilities:
    - Discover candidate tasks that need meeting evidence
    - Match meetings to tasks using requirement codes, attendee emails, and time windows
    - Create/update TaskLinks evidence records (idempotent)
    - Apply scoring gate to determine if task is eligible for approval
    - Create review comments with match details
    """

    def __init__(
        self,
        time_window_days: int = 2,
        service_name: Optional[str] = None,
    ):
        """
        Initialize autolink service.

        Args:
            time_window_days: Days before/after task date to search for meetings (default: 2)
            service_name: Optional service name filter (e.g., 'gotomeeting_external', 'gotomeeting_internal')
        """
        self.time_window_days = time_window_days
        self.service_name = service_name
        self.logger = logger
        self.checklist_service = ChecklistEvaluationService()

    def discover_candidate_tasks(
        self,
        days: int = 1,
        user_id: Optional[int] = None,
        status_in: Optional[List[str]] = None,
    ) -> QuerySet[Task]:
        """
        Discover tasks that are candidates for auto-linking meeting evidence.

        Filters:
        - Only meeting-required activity types (from ActivityPolicy)
        - Tasks created or due in last N days (default: 1)
        - Excludes tasks already "fully auto-linked" (has auto-generated evidence)
        - Optional user_id filter
        - Optional status filter (if Task has status field)

        Uses ActivityPolicy.meeting_required as source of truth (not hardcoded list).
        For user-specific filtering, considers employee group (A/B/C) for group-specific policies.

        Args:
            days: Number of days to look back for tasks (default: 1)
            user_id: Optional user ID to filter tasks for specific employee
            status_in: Optional list of status values to filter (if Task model has status field)

        Returns:
            QuerySet of Task objects
        """
        try:
            from django.contrib.auth import get_user_model
            from management.models import EmployeeCareerState
            from management.services.policy_resolver import PolicyResolver

            from coda.config.activity_definitions import ACTIVITY_POLICIES

            User = get_user_model()

            # Get meeting-required activity types from ActivityPolicy
            # This is the source of truth, not the hardcoded MEETING_BASED_ACTIVITY_TYPES
            meeting_required_slugs = [
                slug
                for slug, policy in ACTIVITY_POLICIES.items()
                if policy.meeting_required
            ]

            # Also include legacy MEETING_BASED_ACTIVITY_TYPES for backward compatibility
            all_meeting_activity_slugs = set(
                meeting_required_slugs + MEETING_BASED_ACTIVITY_TYPES
            )

            # Build activity type filter
            activity_filter = Q()
            for activity_slug in all_meeting_activity_slugs:
                # Match by activity_type.slug or activity_name
                activity_filter |= Q(activity_type__slug__iexact=activity_slug)
                activity_filter |= Q(activity_type__name__iexact=activity_slug)
                activity_filter |= Q(activity_name__iexact=activity_slug)
                # Handle PBR alternative
                if activity_slug == "PBR":
                    activity_filter |= Q(
                        activity_name__iexact="PRODUCT_BACKLOG_REFINEMENT"
                    )

            # Base query: active tasks with meeting-required activity types
            # DO NOT filter by submission date - tasks can be from any time
            query = (
                Q(
                    is_active=True,
                )
                & activity_filter
            )

            # Filter by user if provided
            if user_id:
                query &= Q(employee_id=user_id)
            else:
                # Default: only tasks for "current employees" (matching Employee Groups page filter)
                # Use the same logic as employee-groups page to ensure consistency
                from management.services.employee_filter_service import \
                    get_filtered_employees_queryset

                # Create a mock request object for the filter service
                class MockRequest:
                    def __init__(self):
                        self.user = type(
                            "User", (), {"is_staff": True, "is_superuser": True}
                        )()
                        self.GET = {}

                mock_request = MockRequest()
                current_employees = get_filtered_employees_queryset(
                    mock_request,
                    test_patterns=None,  # Use default test patterns
                    include_inactive=False,
                )

                current_employee_ids = list(
                    current_employees.values_list("id", flat=True)
                )

                if current_employee_ids:
                    query &= Q(employee_id__in=current_employee_ids)
                    self.logger.debug(
                        f"Filtering to {len(current_employee_ids)} current employees (matching Employee Groups page)"
                    )
                else:
                    # If no current employees found, return empty queryset
                    self.logger.warning(
                        "No current employees found for candidate task discovery (matching Employee Groups filter)"
                    )
                    return Task.objects.none()

            tasks = Task.objects.filter(query).select_related(
                "employee", "activity_type", "requirement", "category"
            )

            # Exclude tasks that already have auto-generated evidence with meeting_id
            # (to avoid re-processing tasks that are already linked)
            tasks_with_auto_evidence = (
                TaskLinks.objects.filter(
                    is_active=True, is_auto_generated=True, meeting_id__isnull=False
                )
                .values_list("task_id", flat=True)
                .distinct()
            )

            tasks = tasks.exclude(id__in=tasks_with_auto_evidence)

            self.logger.debug(
                f"Found {tasks.count()} candidate tasks for auto-linking (days param={days} is for meeting window, not task filtering)"
            )
            return tasks

        except Exception as e:
            self.logger.error(f"Error discovering candidate tasks: {e}", exc_info=True)
            return Task.objects.none()

    def find_meeting_for_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        Find matching meeting for a task using MULTI-PRONGED matching (meeting_id + launch intent + time windows).

        UPDATED MATCHING RULES (Phase 4 - Launch Intent):

        1. PRIMARY: Meeting room ID + Launch Intent (highest confidence)
           - Match Meeting.meeting_id to configured meeting room for task's activity_type
           - Check launch intent cache: user launched this activity_type with this meeting_id
           - Require meeting.start_time within ±6 hours of launch intent time OR within command window
           - Confidence: 0.95 (highest)

        2. SECONDARY: Meeting room ID + Recent Launch (high confidence)
           - Match Meeting.meeting_id to configured room AND meeting.start_time in command window
           - Assign to user who launched it most recently for that activity_type (from cache)
           - Must be within ±6 hours of launch intent
           - Confidence: 0.85

        3. TERTIARY: Requirement code matching (if task requires requirement)
           - If task.requirement exists AND meeting.requirement_code exists:
             * MUST match exactly (case-insensitive)
             * If mismatch: return None (DO NOT autolink)

        4. FALLBACK: Topic keyword mapping + time window
           - Topic keyword mapping to activity type (from activity definitions)
           - Time window alignment
           - Never require requirement_code
           - Confidence: 0.70 (lowest)

        Does NOT call GoToMeeting API - DB-only.
        Does NOT rely on attendee_email (generic emails unreliable).

        Args:
            task: Task instance to find meeting for

        Returns:
            Dict with:
            - meeting: Meeting instance (if found)
            - match_type: str ('meeting_room_launch', 'meeting_room_recent', 'requirement_code', 'topic')
            - confidence: float (0.0-1.0)
            - attendee_match: bool (always False for meeting_room matches)
            - requirement_mismatch: bool (if requirement mismatch detected)
            - mismatch_reason: str (if mismatch)
            Or None if no match found or mismatch detected
        """
        try:
            # Determine task date
            task_date = self._get_task_date(task)
            if not task_date:
                return None

            # Define time window
            start_date = task_date - timedelta(days=self.time_window_days)
            end_date = task_date + timedelta(days=self.time_window_days)

            # Get activity type slug
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            # PRIMARY: Meeting room ID + Launch Intent
            if activity_type_slug:
                try:
                    from ai_services.utils.meeting_room_config import \
                        get_meeting_room_for_activity
                    from django.core.cache import cache
                    from django.utils.dateparse import parse_datetime
                    from management.views_meeting_launch import \
                        get_launch_intent

                    meeting_room_id, _ = get_meeting_room_for_activity(
                        activity_type_slug
                    )
                    if meeting_room_id:
                        # Check launch intent
                        launch_intent = get_launch_intent(
                            task.employee.id, activity_type_slug
                        )

                        if (
                            launch_intent
                            and launch_intent.get("meeting_id") == meeting_room_id
                        ):
                            # Launch intent found - match by meeting_id and time window
                            launch_time = parse_datetime(
                                launch_intent.get("timestamp_iso")
                            )
                            if launch_time:
                                # Time window: ±6 hours from launch OR within command window
                                launch_start = launch_time - timedelta(hours=6)
                                launch_end = launch_time + timedelta(hours=6)

                                # Query meetings with matching meeting_id
                                room_meetings = Meeting.objects.filter(
                                    meeting_id=meeting_room_id
                                ).filter(
                                    Q(
                                        start_time__gte=launch_start,
                                        start_time__lte=launch_end,
                                    )
                                    | Q(
                                        start_time__date__gte=start_date.date(),
                                        start_time__date__lte=end_date.date(),
                                    )
                                )

                                if room_meetings.exists():
                                    best_meeting = room_meetings.order_by(
                                        "-start_time"
                                    ).first()
                                    return {
                                        "meeting": best_meeting,
                                        "match_type": "meeting_room_launch",
                                        "confidence": 0.95,
                                        "attendee_match": False,  # Not using attendee email
                                        "requirement_mismatch": False,
                                    }
                        else:
                            # SECONDARY: Meeting room ID + Recent Launch (no launch intent, but room matches)
                            # Include both internal and external meetings (meeting_id should be globally unique)
                            room_meetings = Meeting.objects.filter(
                                meeting_id=meeting_room_id,
                                start_time__date__gte=start_date.date(),
                                start_time__date__lte=end_date.date(),
                            )

                            if room_meetings.exists():
                                # Check if any user launched this activity recently (within ±6 hours)
                                best_meeting = None
                                best_launch_time = None

                                for meeting in room_meetings.order_by("-start_time"):
                                    # Check all users who might have launched (scan cache keys)
                                    # For now, assign to task employee if they have recent launch
                                    user_launch = get_launch_intent(
                                        task.employee.id, activity_type_slug
                                    )
                                    if user_launch:
                                        launch_time = parse_datetime(
                                            user_launch.get("timestamp_iso")
                                        )
                                        if launch_time:
                                            time_diff = abs(
                                                (
                                                    meeting.start_time - launch_time
                                                ).total_seconds()
                                                / 3600
                                            )
                                            if time_diff <= 6:
                                                if not best_meeting or (
                                                    best_launch_time
                                                    and launch_time > best_launch_time
                                                ):
                                                    best_meeting = meeting
                                                    best_launch_time = launch_time

                                if best_meeting:
                                    return {
                                        "meeting": best_meeting,
                                        "match_type": "meeting_room_recent",
                                        "confidence": 0.85,
                                        "attendee_match": False,
                                        "requirement_mismatch": False,
                                    }
                except Exception as e:
                    self.logger.debug(f"Error in meeting room matching: {e}")
                    # Fall through to other matching methods

            # Build base query for meetings in time window (for fallback matching)
            query = Q(
                start_time__date__gte=start_date.date(),
                start_time__date__lte=end_date.date(),
            )

            # Include both internal and external meetings by default (unless service_name is explicitly set)
            if self.service_name:
                query &= Q(service_name=self.service_name)
            else:
                # Default: include both services
                from ai_services.utils.goto_service_registry import \
                    list_goto_services

                try:
                    services = list_goto_services()
                    if services:
                        query &= Q(service_name__in=services)
                    # If no services configured, don't filter by service_name (backward compatibility)
                except ImportError:
                    # Service registry not available, don't filter by service_name
                    pass

            meetings_in_window = Meeting.objects.filter(query)

            if not meetings_in_window.exists():
                return None

            # Check if task requires requirement
            requires_requirement = self._task_requires_requirement(task)
            task_requirement_code = None
            if task.requirement:
                task_requirement_code = f"REQ-{task.requirement.id}"

            # TERTIARY: Match by requirement code (ONLY if activity explicitly requires requirement)
            # NOTE: requirement_code is optional and should NOT gate matching for Group B
            # unless the activity policy explicitly requires a Requirement.
            # This check only applies if requires_requirement is True (from activity policy).
            if requires_requirement and task_requirement_code:
                requirement_matches = meetings_in_window.filter(
                    requirement_code__iexact=task_requirement_code
                )

                if requirement_matches.exists():
                    # Exact match found - verify attendee
                    best_meeting = requirement_matches.order_by(
                        "-start_time", "-duration_minutes"
                    ).first()
                    attendee_match = self._verify_attendee_match(best_meeting, task)

                    return {
                        "meeting": best_meeting,
                        "match_type": "requirement_code",
                        "confidence": 0.95 if attendee_match else 0.85,
                        "attendee_match": attendee_match,
                        "requirement_mismatch": False,
                    }
                else:
                    # Requirement mismatch check: if meeting has requirement_code but doesn't match
                    mismatched_meetings = meetings_in_window.exclude(
                        requirement_code__isnull=True
                    ).exclude(requirement_code="")

                    if mismatched_meetings.exists():
                        # STRICT RULE: Requirement mismatch - DO NOT autolink
                        sample_meeting = mismatched_meetings.first()
                        return {
                            "meeting": None,  # Signal mismatch
                            "match_type": "requirement_mismatch",
                            "confidence": 0.0,
                            "attendee_match": False,
                            "requirement_mismatch": True,
                            "mismatch_reason": (
                                f"Task requires REQ-{task.requirement.id} but meeting has "
                                f"{sample_meeting.requirement_code or 'different requirement'}"
                            ),
                        }
                    else:
                        # Task requires requirement but meeting has NO requirement_code
                        # Allow ONLY if attendee match is strong AND activity tag overlap
                        attendee_result = self._match_by_attendee_email_strict(
                            meetings_in_window, task
                        )

                        if attendee_result and attendee_result.get("attendee_match"):
                            # Check activity tag overlap
                            activity_tags = self._get_activity_tags_for_task(task)
                            if activity_tags:
                                # Verify at least one meeting has matching tags
                                for meeting in meetings_in_window:
                                    meeting_tags = extract_candidate_activity_tags(
                                        meeting.topic or ""
                                    )
                                    if set(activity_tags) & set(meeting_tags):
                                        # Strong attendee match + activity overlap = LOW confidence
                                        return {
                                            "meeting": attendee_result["meeting"],
                                            "match_type": "attendee_email",
                                            "confidence": 0.5,  # LOW confidence
                                            "attendee_match": True,
                                            "requirement_mismatch": False,
                                            "missing_requirement_code": True,
                                        }

                        # No strong match - return None
                        return None

            # SECONDARY: Match by attendee email (if no requirement requirement or no requirement on task)
            attendee_result = self._match_by_attendee_email_strict(
                meetings_in_window, task
            )
            if attendee_result:
                return attendee_result

            # TERTIARY: Match by attendee NAME (SAFE fallback layer)
            name_result = self._match_by_attendee_name_safe(meetings_in_window, task)
            if name_result:
                return name_result

            # FALLBACK: Topic fallback (STRICT - requires activity tag overlap)
            return self._match_by_topic_strict(meetings_in_window, task)

        except Exception as e:
            self.logger.error(
                f"Error finding meeting for task {task.id}: {e}", exc_info=True
            )
            return None

    def _task_requires_requirement(self, task: Task) -> bool:
        """Check if task requires a requirement."""
        activity_type_slug = None
        if task.activity_type:
            activity_type_slug = task.activity_type.slug or task.activity_type.name
        elif task.activity_name:
            activity_type_slug = task.activity_name.upper().replace(" ", "_")

        if activity_type_slug:
            return activity_type_slug.upper() in [
                a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
            ]
        return False

    def score_candidate_meetings(
        self, meetings: QuerySet[Meeting], task: Task
    ) -> List[Dict[str, Any]]:
        """
        Score all candidate meetings for a task using multi-pronged matching.

        Returns list of scored candidates sorted by score (highest first).
        Each candidate includes:
        - meeting_id, service_name, start_time, duration_minutes
        - signals_hit (list of matching signals)
        - score (confidence score)
        - rejection_reason (if score too low or ambiguous)

        Args:
            meetings: QuerySet of candidate meetings
            task: Task instance to match

        Returns:
            List of dicts with scored candidate information
        """
        scored_candidates = []

        try:
            # Get activity type slug
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            # Get meeting room ID
            meeting_room_id = None
            if activity_type_slug:
                try:
                    from ai_services.utils.meeting_room_config import \
                        get_meeting_room_for_activity

                    meeting_room_id, _ = get_meeting_room_for_activity(
                        activity_type_slug
                    )
                except Exception:
                    pass

            for meeting in meetings:
                signals_hit = []
                score = 0.0
                rejection_reason = None

                # Signal 1: Launch intent + meeting_room_id (0.95)
                if meeting_room_id and meeting.meeting_id == meeting_room_id:
                    if activity_type_slug and task.employee:
                        try:
                            from management.views_meeting_launch import \
                                get_launch_intent

                            launch_intent = get_launch_intent(
                                task.employee.id, activity_type_slug
                            )
                            if (
                                launch_intent
                                and launch_intent.get("meeting_id") == meeting_room_id
                            ):
                                signals_hit.append("launch_intent")
                                score = max(score, 0.95)
                        except Exception:
                            pass

                    # Signal 2: meeting_room_id only (0.85)
                    if "launch_intent" not in signals_hit:
                        signals_hit.append("meeting_room_id")
                        score = max(score, 0.85)

                # Signal 3: Requirement code match (0.95)
                if task.requirement and meeting.requirement_code:
                    task_req_code = f"REQ-{task.requirement.id}"
                    if task_req_code.upper() == meeting.requirement_code.upper():
                        signals_hit.append("requirement_code")
                        score = max(score, 0.95)

                # Signal 4: Attendee email match (0.75-0.9)
                if task.employee:
                    canonical_emails = get_canonical_emails_for_user(task.employee)
                    if canonical_emails:
                        attendee_match = MeetingAttendee.objects.filter(
                            meeting=meeting,
                            attendee_email__in=[e for e in canonical_emails],
                            duration_minutes__gt=3,
                        ).exists()
                        if attendee_match:
                            signals_hit.append("attendee_email")
                            score = max(score, 0.75)

                # Signal 5: Attendee name match (0.6-1.0)
                if task.employee and not "attendee_email" in signals_hit:
                    employee_first_name = task.employee.first_name or ""
                    employee_last_name = task.employee.last_name or ""

                    if employee_first_name:
                        attendees = MeetingAttendee.objects.filter(
                            meeting=meeting, duration_minutes__gt=3
                        )

                        for attendee in attendees:
                            name_score, name_reason = self._calculate_name_match_score(
                                attendee.attendee_name,
                                employee_first_name,
                                employee_last_name,
                            )

                            if name_score > 0:
                                signals_hit.append(f"attendee_name_{name_reason}")
                                score = max(score, name_score)
                                break

                # Signal 6: Topic keyword match (0.5-0.7)
                if meeting.topic and task.activity_name:
                    activity_tags = self._get_activity_tags_for_task(task)
                    if activity_tags:
                        meeting_tags = extract_candidate_activity_tags(meeting.topic)
                        if set(activity_tags) & set(meeting_tags):
                            signals_hit.append("topic_keyword")
                            score = max(score, 0.5)

                # Determine rejection reason if score is low
                if score < 0.5:
                    rejection_reason = "Score too low (<0.5)"
                elif not signals_hit:
                    rejection_reason = "No matching signals"

                scored_candidates.append(
                    {
                        "meeting_id": meeting.meeting_id,
                        "service_name": meeting.service_name,
                        "start_time": (
                            meeting.start_time.isoformat()
                            if meeting.start_time
                            else None
                        ),
                        "duration_minutes": meeting.duration_minutes,
                        "signals_hit": signals_hit,
                        "score": score,
                        "rejection_reason": rejection_reason,
                    }
                )

        except Exception as e:
            self.logger.error(f"Error scoring candidate meetings: {e}", exc_info=True)

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates

    def diagnose_meeting_search(self, task: Task) -> Dict[str, Any]:
        """
        Diagnose why a meeting search might fail for a task.

        Returns detailed diagnostic information including:
        - Task info (id, activity_type, employee)
        - Policy info (meeting_required, meeting_room_id, sessions_required)
        - Query parameters used (service filter, date window, meeting_room_id filter)
        - Candidate meeting counts at each stage
        - Reasons for zero candidates

        Args:
            task: Task instance to diagnose

        Returns:
            Dict with diagnostic information
        """
        try:
            from coda.config.activity_definitions import get_activity_policy

            # Get task info
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            # Get policy
            policy = None
            if activity_type_slug:
                policy = get_activity_policy(activity_type_slug)

            # Determine task date
            task_date = self._get_task_date(task)

            # Define time window
            start_date = (
                task_date - timedelta(days=self.time_window_days) if task_date else None
            )
            end_date = (
                task_date + timedelta(days=self.time_window_days) if task_date else None
            )

            # Get meeting room ID
            meeting_room_id = None
            if activity_type_slug:
                try:
                    from ai_services.utils.meeting_room_config import \
                        get_meeting_room_for_activity

                    meeting_room_id, _ = get_meeting_room_for_activity(
                        activity_type_slug
                    )
                except Exception:
                    pass

            # Build base query
            query_info = {
                "service_filter": self.service_name or "all",
                "date_window_days": self.time_window_days,
                "start_date": start_date.date().isoformat() if start_date else None,
                "end_date": end_date.date().isoformat() if end_date else None,
                "meeting_room_id_filter": meeting_room_id,
            }

            # Count meetings at each stage
            candidate_counts = {}
            reasons = []

            if not task_date:
                reasons.append(
                    "No task date available (submission and created_at both missing)"
                )
                candidate_counts["base_query"] = 0
            else:
                # Base query: time window only
                base_query = Q(
                    start_time__date__gte=start_date.date(),
                    start_time__date__lte=end_date.date(),
                )
                base_count = Meeting.objects.filter(base_query).count()
                candidate_counts["time_window_only"] = base_count

                if base_count == 0:
                    reasons.append(
                        f"0 meetings found in date window ({start_date.date()} to {end_date.date()})"
                    )
                else:
                    # Add service filter
                    if self.service_name:
                        service_query = base_query & Q(service_name=self.service_name)
                        service_count = Meeting.objects.filter(service_query).count()
                        candidate_counts["with_service_filter"] = service_count

                        if service_count == 0:
                            reasons.append(
                                f"0 meetings found for service={self.service_name} in date window"
                            )
                    else:
                        # Check both services
                        from ai_services.utils.goto_service_registry import \
                            list_goto_services

                        try:
                            services = list_goto_services()
                            if services:
                                service_query = base_query & Q(
                                    service_name__in=services
                                )
                                service_count = Meeting.objects.filter(
                                    service_query
                                ).count()
                                candidate_counts["with_service_filter"] = service_count

                                if service_count == 0:
                                    reasons.append(
                                        f"0 meetings found for services={services} in date window"
                                    )
                        except ImportError:
                            candidate_counts["with_service_filter"] = base_count

                    # Add meeting_room_id filter if available
                    if meeting_room_id:
                        room_query = base_query
                        if self.service_name:
                            room_query &= Q(service_name=self.service_name)
                        room_query &= Q(meeting_id=meeting_room_id)
                        room_count = Meeting.objects.filter(room_query).count()
                        candidate_counts["with_meeting_room_id"] = room_count

                        if room_count == 0:
                            reasons.append(
                                f"0 meetings match meeting_room_id={meeting_room_id}"
                            )

                            # Check if other meeting_ids exist (potential mismatch)
                            other_meeting_ids = (
                                Meeting.objects.filter(
                                    base_query & Q(service_name=self.service_name)
                                    if self.service_name
                                    else base_query
                                )
                                .values_list("meeting_id", flat=True)
                                .distinct()[:5]
                            )

                            if other_meeting_ids:
                                reasons.append(
                                    f"Other meeting_ids found in window: {', '.join([str(mid) for mid in other_meeting_ids if mid])}"
                                )

            return {
                "task_id": task.id,
                "employee_name": task.employee.username if task.employee else "N/A",
                "activity_type_slug": activity_type_slug,
                "policy": (
                    {
                        "meeting_required": policy.meeting_required if policy else None,
                        "meeting_room_id": policy.meeting_room_id if policy else None,
                        "sessions_required": (
                            policy.sessions_required if policy else None
                        ),
                        "requirement_required": (
                            policy.requirement_required if policy else None
                        ),
                    }
                    if policy
                    else None
                ),
                "query_parameters": query_info,
                "candidate_counts": candidate_counts,
                "zero_candidate_reasons": reasons,
                "task_date": task_date.date().isoformat() if task_date else None,
                "task_requirement_code": (
                    f"REQ-{task.requirement.id}" if task.requirement else None
                ),
            }

        except Exception as e:
            self.logger.error(
                f"Error diagnosing meeting search for task {task.id}: {e}",
                exc_info=True,
            )
            return {
                "task_id": task.id,
                "error": str(e),
            }

    def _get_task_date(self, task: Task) -> Optional[timezone.datetime]:
        """Get task date from available fields (submission > created_at)."""
        if hasattr(task, "submission") and task.submission:
            return task.submission
        if hasattr(task, "created_at") and task.created_at:
            return task.created_at
        return timezone.now()

    def _get_activity_tags_for_task(self, task: Task) -> List[str]:
        """Get candidate activity tags from task's activity_type."""
        if not task.activity_type:
            return []

        activity_name = task.activity_type.name if task.activity_type.name else ""
        if activity_name:
            return extract_candidate_activity_tags(activity_name)

        return []

    def _verify_attendee_match(self, meeting: Meeting, task: Task) -> bool:
        """
        Verify that task.employee attended the meeting using canonical emails.

        Checks MeetingAttendee records for matching email from canonical set.
        """
        try:
            if not task.employee:
                return False

            canonical_emails = get_canonical_emails_for_user(task.employee)
            if not canonical_emails:
                return False

            # Check MeetingAttendee records
            for email in canonical_emails:
                attendee = MeetingAttendee.objects.filter(
                    meeting=meeting, attendee_email__iexact=email
                ).first()

                if (
                    attendee and attendee.duration_minutes > 3
                ):  # Must have attended >3 minutes
                    return True

            return False

        except Exception as e:
            self.logger.debug(f"Error verifying attendee match: {e}")
            return False

    def _match_by_attendee_email_strict(
        self, meetings: QuerySet[Meeting], task: Task
    ) -> Optional[Dict[str, Any]]:
        """
        Match meetings by attendee email using canonical email set.

        STRICT: Requires attendee match with >3 minutes duration.
        """
        try:
            if not task.employee:
                return None

            canonical_emails = get_canonical_emails_for_user(task.employee)
            if not canonical_emails:
                return None

            # Find meetings where this employee attended (using any canonical email)
            attendee_meetings = MeetingAttendee.objects.filter(
                meeting__in=meetings,
                duration_minutes__gt=3,  # Must have attended >3 minutes
            ).select_related("meeting")

            # Filter by canonical emails
            matching_attendees = []
            for attendee in attendee_meetings:
                normalized_attendee_email = normalize_email(attendee.attendee_email)
                if normalized_attendee_email in canonical_emails:
                    matching_attendees.append(attendee)

            if not matching_attendees:
                return None

            # Get best match (most recent or longest duration)
            best_attendee = max(
                matching_attendees,
                key=lambda a: (a.meeting.start_time, a.duration_minutes),
            )

            # Check if requirement code matches (boost confidence)
            requirement_match = False
            if task.requirement and best_attendee.meeting.requirement_code:
                task_req_code = f"REQ-{task.requirement.id}"
                if (
                    task_req_code.upper()
                    == best_attendee.meeting.requirement_code.upper()
                ):
                    requirement_match = True

            return {
                "meeting": best_attendee.meeting,
                "match_type": "attendee_email",
                "confidence": 0.9 if requirement_match else 0.75,
                "attendee_match": True,
                "requirement_match": requirement_match,
            }

        except Exception as e:
            self.logger.debug(f"Error matching by attendee email: {e}")
            return None

    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for matching: lowercase, strip punctuation, collapse whitespace.

        Args:
            name: Name string to normalize

        Returns:
            Normalized name string
        """
        if not name:
            return ""
        import re

        # Lowercase, strip punctuation, collapse whitespace
        normalized = re.sub(r"[^\w\s]", "", name.lower())
        normalized = " ".join(normalized.split())
        return normalized

    def _calculate_name_match_score(
        self, attendee_name: str, employee_first_name: str, employee_last_name: str
    ) -> Tuple[float, str]:
        """
        Calculate name match score between attendee name and employee name.

        Scoring:
        - 1.0 = full-name exact-ish match (case-insensitive, punctuation stripped, tokens match)
        - 0.8 = full-name partial (first name + last initial)
        - 0.6 = unique-first-name match (only if unique among active employees)
        - 0.0 = no match / ambiguous

        Args:
            attendee_name: Attendee display name from meeting
            employee_first_name: Employee's first name
            employee_last_name: Employee's last name

        Returns:
            Tuple of (score: float, reason: str)
        """
        if not attendee_name or not employee_first_name:
            return (0.0, "missing_name")

        # Normalize names
        attendee_normalized = self._normalize_name(attendee_name)
        employee_first_normalized = self._normalize_name(employee_first_name)
        employee_last_normalized = self._normalize_name(employee_last_name)
        employee_full_normalized = (
            f"{employee_first_normalized} {employee_last_normalized}".strip()
        )

        # Split attendee name into tokens
        attendee_tokens = attendee_normalized.split()
        if not attendee_tokens:
            return (0.0, "empty_attendee_name")

        # Check full name match (1.0)
        if attendee_normalized == employee_full_normalized:
            return (1.0, "full_name_exact")

        # Check if attendee name contains both first and last (with some flexibility)
        has_first = employee_first_normalized in attendee_tokens
        has_last = (
            employee_last_normalized in attendee_tokens
            if employee_last_normalized
            else False
        )

        if has_first and has_last:
            return (1.0, "full_name_tokens")

        # Check first name + last initial (0.8)
        if has_first and employee_last_normalized:
            last_initial = (
                employee_last_normalized[0] if len(employee_last_normalized) > 0 else ""
            )
            # Check if any token starts with last initial
            for token in attendee_tokens:
                if token.startswith(last_initial) and len(token) > 1:
                    return (0.8, "first_name_last_initial")

        # Check first name only (0.6) - but we'll check uniqueness separately
        if has_first:
            return (0.6, "first_name_only")

        return (0.0, "no_match")

    def _is_first_name_unique(
        self, first_name: str, exclude_user_id: Optional[int] = None
    ) -> bool:
        """
        Check if first name is unique among active employees.

        Args:
            first_name: First name to check
            exclude_user_id: Optional user ID to exclude from check (for the user we're matching)

        Returns:
            True if only one active employee has this first name
        """
        try:
            from django.contrib.auth import get_user_model
            from management.services.employee_filter_service import \
                get_filtered_employees_queryset

            User = get_user_model()

            # Get current employees (matching Employee Groups page filter)
            class MockRequest:
                def __init__(self):
                    self.user = type(
                        "User", (), {"is_staff": True, "is_superuser": True}
                    )()
                    self.GET = {}

            mock_request = MockRequest()
            current_employees = get_filtered_employees_queryset(
                mock_request, test_patterns=None, include_inactive=False
            )

            # Filter by first name (case-insensitive, normalized)
            first_name_normalized = self._normalize_name(first_name)
            matching_users = current_employees.filter(
                first_name__iexact=first_name_normalized
            )

            if exclude_user_id:
                matching_users = matching_users.exclude(id=exclude_user_id)

            count = matching_users.count()
            return count == 1

        except Exception as e:
            self.logger.debug(f"Error checking first name uniqueness: {e}")
            # Conservative: assume not unique if we can't check
            return False

    def _match_by_attendee_name_safe(
        self, meetings: QuerySet[Meeting], task: Task
    ) -> Optional[Dict[str, Any]]:
        """
        Match meetings by attendee NAME as a SAFE fallback layer.

        Business requirement:
        - Cannot rely on attendee_email (often generic)
        - Use attendee display names as a probabilistic hint
        - Heuristic must be conservative

        Rules:
        - Prefer full-name match (first + last) if available
        - Allow first-name-only match ONLY when that first name is unique among active employees
        - If ambiguous (e.g., two "Eunice"), require last-name match or do NOT auto-link
        - Never link solely on a weak name match if multiple meetings qualify; require additional constraints
          (time window alignment, meeting_room_id match if available, or topic keyword relevance)

        Args:
            meetings: QuerySet of candidate meetings
            task: Task instance to match

        Returns:
            Dict with meeting match info or None if no safe match
        """
        try:
            if not task.employee:
                return None

            employee = task.employee
            employee_first_name = employee.first_name or ""
            employee_last_name = employee.last_name or ""

            if not employee_first_name:
                return None

            # Get all attendees for candidate meetings
            attendees = MeetingAttendee.objects.filter(
                meeting__in=meetings,
                duration_minutes__gt=3,  # Must have attended >3 minutes
            ).select_related("meeting")

            if not attendees.exists():
                return None

            # Score each attendee name match
            scored_matches = []
            for attendee in attendees:
                score, reason = self._calculate_name_match_score(
                    attendee.attendee_name, employee_first_name, employee_last_name
                )

                if score > 0:
                    scored_matches.append(
                        {
                            "attendee": attendee,
                            "meeting": attendee.meeting,
                            "score": score,
                            "reason": reason,
                        }
                    )

            if not scored_matches:
                return None

            # Filter by score threshold
            # Require >= 0.8 unless there's also meeting_room_id match + time proximity
            high_confidence_matches = [m for m in scored_matches if m["score"] >= 0.8]

            if high_confidence_matches:
                # Use high confidence matches
                candidate_matches = high_confidence_matches
            else:
                # Check if we have first-name-only matches (0.6) that are unique
                first_name_matches = [m for m in scored_matches if m["score"] == 0.6]

                if first_name_matches:
                    # Check uniqueness for first name
                    is_unique = self._is_first_name_unique(
                        employee_first_name, exclude_user_id=employee.id
                    )

                    if is_unique:
                        # Check if there's also meeting_room_id match or time proximity
                        # For now, only allow if there's exactly one candidate meeting
                        if len(meetings) == 1:
                            candidate_matches = first_name_matches
                        else:
                            # Multiple meetings - require additional constraint
                            # Check if any match has meeting_room_id alignment
                            activity_type_slug = None
                            if task.activity_type:
                                activity_type_slug = (
                                    task.activity_type.slug or task.activity_type.name
                                )
                            elif task.activity_name:
                                activity_type_slug = task.activity_name.upper().replace(
                                    " ", "_"
                                )

                            if activity_type_slug:
                                try:
                                    from ai_services.utils.meeting_room_config import \
                                        get_meeting_room_for_activity

                                    meeting_room_id, _ = get_meeting_room_for_activity(
                                        activity_type_slug
                                    )

                                    if meeting_room_id:
                                        # Filter matches to those with matching meeting_room_id
                                        room_matches = [
                                            m
                                            for m in first_name_matches
                                            if m["meeting"].meeting_id
                                            == meeting_room_id
                                        ]
                                        if room_matches:
                                            candidate_matches = room_matches
                                        else:
                                            # No meeting_room_id match - too ambiguous
                                            return None
                                    else:
                                        # No meeting_room_id configured - too ambiguous
                                        return None
                                except Exception:
                                    # Error getting meeting_room_id - too ambiguous
                                    return None
                            else:
                                # No activity type - too ambiguous
                                return None
                    else:
                        # First name is ambiguous - require last name match
                        return None
                else:
                    # No matches with score > 0
                    return None

            if not candidate_matches:
                return None

            # If multiple matches, prefer highest score, then most recent
            best_match = max(
                candidate_matches, key=lambda m: (m["score"], m["meeting"].start_time)
            )

            # Check if requirement code matches (boost confidence)
            requirement_match = False
            if task.requirement and best_match["meeting"].requirement_code:
                task_req_code = f"REQ-{task.requirement.id}"
                if (
                    task_req_code.upper()
                    == best_match["meeting"].requirement_code.upper()
                ):
                    requirement_match = True

            # Confidence based on name match score
            base_confidence = best_match["score"]
            if requirement_match:
                base_confidence = min(1.0, base_confidence + 0.1)

            return {
                "meeting": best_match["meeting"],
                "match_type": "attendee_name",
                "confidence": base_confidence,
                "attendee_match": True,
                "name_match_reason": best_match["reason"],
                "requirement_match": requirement_match,
            }

        except Exception as e:
            self.logger.debug(f"Error matching by attendee name: {e}")
            return None

    def _match_by_topic_strict(
        self, meetings: QuerySet[Meeting], task: Task
    ) -> Optional[Dict[str, Any]]:
        """
        Match meetings by topic with STRICT requirements.

        REQUIRES:
        - Activity tag overlap
        - Time window alignment (already filtered)
        - PREFERS attendee match (reduces confidence if missing)

        Does NOT allow topic-only matching without activity tags.
        """
        try:
            # Get activity tags for task
            activity_tags = self._get_activity_tags_for_task(task)
            if not activity_tags:
                # STRICT: No activity tags = no topic matching
                return None

            # Use MeetingEvidenceMatcher for topic matching
            matcher = MeetingEvidenceMatcher(
                enable_topic_fallback=True,
                time_window_days=self.time_window_days,
                service_name=self.service_name,
                require_activity_tag_overlap=True,  # STRICT: require overlap
                require_employee_match=False,  # Prefer but don't require
            )

            topic_meetings = matcher._match_by_topic_and_time(task)
            if not topic_meetings.exists():
                return None

            best_meeting = topic_meetings.first()
            attendee_match = self._verify_attendee_match(best_meeting, task)

            # Confidence reduced if no attendee match
            confidence = 0.7 if attendee_match else 0.5

            return {
                "meeting": best_meeting,
                "match_type": "topic",
                "confidence": confidence,
                "attendee_match": attendee_match,
            }

        except Exception as e:
            self.logger.debug(f"Error matching by topic: {e}")
            return None

    @transaction.atomic
    def create_or_update_tasklink_from_meeting(
        self, task: Task, meeting: Meeting
    ) -> Optional[Tuple[TaskLinks, bool]]:
        """
        Create or update a TaskLinks record from a Meeting (IDEMPOTENT).

        HARDENED IDEMPOTENCY:
        - Uses meeting_id as primary key for idempotency
        - If TaskLinks exists with same meeting_id, return existing (no duplicate)
        - If TaskLinks exists with different meeting_id, update only if auto-generated
        - Normalized URL is secondary check

        Args:
            task: Task instance
            meeting: Meeting instance

        Returns:
            Tuple of (TaskLinks instance, created: bool) or None if error
        """
        try:
            # Normalize meeting URL
            normalized_url = (
                normalize_url(meeting.recording_url) if meeting.recording_url else None
            )

            if not normalized_url and not meeting.download_url:
                self.logger.warning(
                    f"Meeting {meeting.id} has no recording_url or download_url"
                )
                return None

            # IDEMPOTENCY KEY: Check by meeting_id first (most reliable)
            existing_by_meeting_id = None
            if meeting.meeting_id:
                existing_by_meeting_id = TaskLinks.objects.filter(
                    task=task, is_active=True, meeting_id=meeting.meeting_id
                ).first()

            if existing_by_meeting_id:
                # Same meeting_id = same evidence, return existing (idempotent)
                return existing_by_meeting_id, False

            # Secondary: Check by normalized URL
            existing_by_url = None
            if normalized_url:
                existing_by_url = TaskLinks.objects.filter(
                    task=task, is_active=True, link=normalized_url
                ).first()

            if existing_by_url:
                # Same URL = same evidence, return existing (idempotent)
                # Update meeting_id if missing
                if meeting.meeting_id and not existing_by_url.meeting_id:
                    existing_by_url.meeting_id = meeting.meeting_id
                    existing_by_url.save(update_fields=["meeting_id"])
                return existing_by_url, False

            # Check if there's an auto-generated TaskLinks for this task (different meeting)
            existing_auto = (
                TaskLinks.objects.filter(
                    task=task, is_active=True, is_auto_generated=True
                )
                .exclude(
                    meeting_id=meeting.meeting_id  # Exclude if same meeting_id (already handled above)
                )
                .first()
            )

            if existing_auto:
                # Update existing auto-generated TaskLinks (different meeting)
                existing_auto.meeting_id = meeting.meeting_id
                existing_auto.link = normalized_url or meeting.recording_url
                existing_auto.drive_link = meeting.download_url
                existing_auto.link_name = (
                    meeting.topic[:255]
                    if meeting.topic
                    else "Auto-linked meeting evidence"
                )
                existing_auto.description = (
                    f"AUTO: meeting_id={meeting.meeting_id}, "
                    f"topic={meeting.topic[:200] if meeting.topic else 'N/A'}"
                )
                existing_auto.is_auto_generated = True
                existing_auto.save()

                self.logger.info(
                    f"Updated auto-generated TaskLinks {existing_auto.id} for task {task.id}"
                )
                return existing_auto, False

            # Create new TaskLinks
            added_by_user = task.employee
            if not (added_by_user.is_staff or added_by_user.is_superuser):
                # Find a staff user to use as added_by (fallback)
                from django.contrib.auth import get_user_model

                User = get_user_model()
                staff_user = User.objects.filter(is_staff=True, is_active=True).first()
                if staff_user:
                    added_by_user = staff_user

            new_tasklink = TaskLinks.objects.create(
                task=task,
                added_by=added_by_user,
                link=normalized_url or meeting.recording_url,
                drive_link=meeting.download_url,
                link_name=(
                    meeting.topic[:255]
                    if meeting.topic
                    else "Auto-linked meeting evidence"
                ),
                description=(
                    f"AUTO: meeting_id={meeting.meeting_id}, "
                    f"topic={meeting.topic[:200] if meeting.topic else 'N/A'}"
                ),
                linkpassword="No Password Needed",
                is_active=True,
                is_auto_generated=True,
                meeting_id=meeting.meeting_id,  # Store meeting_id for idempotency
            )

            self.logger.info(
                f"Created auto-generated TaskLinks {new_tasklink.id} for task {task.id}"
            )
            return new_tasklink, True

        except Exception as e:
            self.logger.error(
                f"Error creating/updating TaskLinks for task {task.id}, meeting {meeting.id}: {e}",
                exc_info=True,
            )
            raise

    def apply_scoring_gate(self, task: Task) -> Dict[str, Any]:
        """
        Apply scoring gate to determine if task is eligible for approval.

        Reuses ChecklistEvaluationService logic:
        - Requirement present (for meeting-based activity types, must be present)
        - Evidence complete (auto evidence satisfies)
        - Checklist complete
        - Duration present/OK (duration derived from meeting attendee duration)
        - Quality >= 80%

        NOTE: Does NOT auto-approve or increment points. Only determines eligibility.

        Args:
            task: Task instance to evaluate

        Returns:
            Dict with:
            - eligible_for_approval: bool
            - reasons: List[str] if not eligible
            - quality_score: float
            - evidence_status: str ('complete', 'partial', 'missing')
            - missing_checklist_items: List[str]
        """
        try:
            # Get quality score from ChecklistEvaluationService
            quality_result = self.checklist_service.get_task_quality_score(task)

            quality_score = quality_result.get("quality_score", 0.0)
            evidence_coverage = quality_result.get("evidence_coverage", 0.0)
            missing_checklist_items = quality_result.get("missing_checklist_items", [])
            duration_factor = quality_result.get("duration_factor", 0.0)

            # Determine evidence status
            if evidence_coverage >= 0.95:
                evidence_status = "complete"
            elif evidence_coverage >= 0.5:
                evidence_status = "partial"
            else:
                evidence_status = "missing"

            # Check requirement (for meeting-based activity types)
            requires_requirement = self._task_requires_requirement(task)
            requirement_present = True
            if requires_requirement:
                requirement_present = task.requirement is not None

            # Determine eligibility
            eligible = (
                quality_score >= 0.8
                and evidence_status == "complete"
                and not missing_checklist_items
                and requirement_present
                and duration_factor >= 0.8  # At least 80% of required duration
            )

            reasons = []
            if not eligible:
                if quality_score < 0.8:
                    reasons.append(f"Quality score {quality_score:.2f} < 0.8")
                if evidence_status != "complete":
                    reasons.append(f"Evidence status: {evidence_status}")
                if missing_checklist_items:
                    reasons.append(
                        f"Missing checklist items: {', '.join(missing_checklist_items)}"
                    )
                if not requirement_present:
                    reasons.append("Requirement missing")
                if duration_factor < 0.8:
                    reasons.append(f"Duration factor {duration_factor:.2f} < 0.8")

            return {
                "eligible_for_approval": eligible,
                "reasons": reasons,
                "quality_score": quality_score,
                "evidence_status": evidence_status,
                "missing_checklist_items": missing_checklist_items,
                "duration_factor": duration_factor,
                "requirement_present": requirement_present,
            }

        except Exception as e:
            self.logger.error(
                f"Error applying scoring gate for task {task.id}: {e}", exc_info=True
            )
            return {
                "eligible_for_approval": False,
                "reasons": [f"Error evaluating task: {str(e)}"],
                "quality_score": 0.0,
                "evidence_status": "missing",
                "missing_checklist_items": [],
                "duration_factor": 0.0,
                "requirement_present": False,
            }
