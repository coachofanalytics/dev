"""
Management command to generate task↔meeting link suggestions (AI-3).

Usage:
    poetry run python coda/manage.py generate_task_meeting_suggestions
    poetry run python coda/manage.py generate_task_meeting_suggestions --days 30 --top-n 5
    poetry run python coda/manage.py generate_task_meeting_suggestions --service external --user-id 5
    poetry run python coda/manage.py generate_task_meeting_suggestions --min-review-confidence 0.45 --auto-confidence 0.85 --dry-run
"""

import hashlib
import logging

from ai_services.models import (AIRequirementMatch, Meeting,
                                MeetingActivityTagSuggestion,
                                TaskMeetingLinkSuggestion)
from ai_services.services.meeting_task_autolink_service import \
    MeetingTaskAutolinkService
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from management.models import Task, TaskLinks

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Generate task↔meeting link suggestions for manager review (AI-3)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back for tasks (default: 30)",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="all",
            help="Service filter: internal, external, or all (default: all)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Process tasks for a specific user only",
        )
        parser.add_argument(
            "--limit-tasks",
            type=int,
            help="Maximum number of tasks to process (default: no limit)",
        )
        parser.add_argument(
            "--top-n",
            type=int,
            default=3,
            help="Number of top suggestions to persist per task (default: 3)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--min-review-confidence",
            type=float,
            default=0.45,
            help="Minimum confidence for review queue (default: 0.45)",
        )
        parser.add_argument(
            "--auto-confidence",
            type=float,
            default=0.85,
            help="Minimum confidence for auto-linking (default: 0.85)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output for each task",
        )
        parser.add_argument(
            "--task-id",
            type=int,
            help="Process exactly one task by ID (bypasses cohort filters)",
        )
        parser.add_argument(
            "--task-ids",
            type=str,
            help='Process multiple tasks by IDs (comma-separated, e.g., "230,231,232") (bypasses cohort filters)',
        )
        parser.add_argument(
            "--fallback-services",
            action="store_true",
            default=True,
            help="Enable service fallback: if primary service has no candidates, try other service (default: True)",
        )
        parser.add_argument(
            "--no-fallback-services",
            dest="fallback_services",
            action="store_false",
            help="Disable service fallback",
        )

    def handle(self, *args, **options):
        days = options.get("days", 30)
        service_option = options.get("service", "all")
        user_id = options.get("user_id")
        limit_tasks = options.get("limit_tasks")
        top_n = options.get("top_n", 3)
        dry_run = options.get("dry_run", False)
        min_review_confidence = options.get("min_review_confidence", 0.45)
        auto_confidence = options.get("auto_confidence", 0.85)
        verbose = options.get("verbose", False)

        # Map service option to service_name
        service_name = None
        if service_option == "external":
            service_name = "gotomeeting_external"
        elif service_option == "internal":
            service_name = "gotomeeting_internal"

        self.stdout.write(
            self.style.SUCCESS("\n🤖 Task↔Meeting Link Suggestions (AI-3) 🤖\n")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made\n")
            )

        # Handle task-id and task-ids options (bypass cohort filters)
        task_id = options.get("task_id")
        task_ids_str = options.get("task_ids")

        if task_id:
            # Process exactly one task
            tasks = Task.objects.filter(id=task_id, is_active=True)
            if not tasks.exists():
                raise CommandError(f"Task {task_id} not found or not active.")
        elif task_ids_str:
            # Process multiple specific tasks
            try:
                task_id_list = [int(tid.strip()) for tid in task_ids_str.split(",")]
                tasks = Task.objects.filter(id__in=task_id_list, is_active=True)
                if tasks.count() != len(task_id_list):
                    found_ids = set(tasks.values_list("id", flat=True))
                    missing = set(task_id_list) - found_ids
                    self.stdout.write(
                        self.style.WARNING(
                            f"Warning: Some task IDs not found: {missing}"
                        )
                    )
            except ValueError as e:
                raise CommandError(
                    f"Invalid task-ids format: {task_ids_str}. Expected comma-separated integers."
                )
        else:
            # Initialize autolink service for scoring
            autolink_service = MeetingTaskAutolinkService(
                time_window_days=days,
                service_name=service_name,
            )

            # Discover candidate tasks
            tasks = autolink_service.discover_candidate_tasks(
                days=days,
                user_id=user_id,
            )

            if limit_tasks:
                tasks = tasks[:limit_tasks]

        task_count = tasks.count()
        self.stdout.write(f"Found {task_count} candidate tasks\n")

        stats = {
            "tasks_scanned": 0,
            "suggestions_created": 0,
            "suggestions_auto_linked": 0,
            "suggestions_queued": 0,
            "suggestions_skipped": 0,
            "errors": 0,
        }

        for task in tasks:
            try:
                stats["tasks_scanned"] += 1

                # Check if task already has sufficient TaskLinks
                existing_links = TaskLinks.objects.filter(
                    task=task,
                    is_active=True,
                    is_auto_generated=True,
                    meeting_id__isnull=False,
                ).count()

                # Get sessions_required and window_mode from activity policy
                sessions_required = 1
                activity_type_slug = None
                policy = None
                window_mode = "submission_window"

                if task.activity_type:
                    activity_type_slug = (
                        task.activity_type.slug or task.activity_type.name
                    )
                elif task.activity_name:
                    activity_type_slug = task.activity_name.upper().replace(" ", "_")

                if activity_type_slug:
                    try:
                        from coda.config.activity_definitions import \
                            get_activity_policy

                        policy = get_activity_policy(activity_type_slug)
                        if policy:
                            sessions_required = policy.sessions_required or 1
                            window_mode = policy.window_mode or "submission_window"
                    except Exception:
                        pass

                if existing_links >= sessions_required:
                    if verbose:
                        self.stdout.write(
                            f"  Task {task.id}: Already has {existing_links} links (required: {sessions_required}), skipping"
                        )
                    continue

                # Get task date for time window calculation
                from datetime import timedelta

                task_date = None
                if task.submission:
                    task_date = task.submission
                elif hasattr(task, "created_at") and task.created_at:
                    task_date = task.created_at

                if not task_date:
                    if verbose:
                        self.stdout.write(
                            f"  Task {task.id}: No submission date, skipping"
                        )
                    continue

                # Determine time window based on window_mode (anchor around task.submission)
                if window_mode == "recent_window":
                    # Ongoing meetings: use NOW()-days..NOW() window
                    end_date = timezone.now()
                    start_date = end_date - timedelta(days=days)
                else:
                    # Cycle-based: use submission anchor ±days
                    start_date = task_date - timedelta(days=days)
                    end_date = task_date + timedelta(days=days)

                # Service fallback logic: try primary service, fallback to other if no candidates
                all_scored_candidates = []
                fallback_used = False
                service_scope_used = []

                services_to_try = []
                if service_option == "all":
                    # Score both services and merge
                    services_to_try = ["gotomeeting_internal", "gotomeeting_external"]
                    service_scope_used = ["both"]
                elif service_option == "internal":
                    services_to_try = ["gotomeeting_internal"]
                    service_scope_used = ["internal"]
                elif service_option == "external":
                    services_to_try = ["gotomeeting_external"]
                    service_scope_used = ["external"]

                # Try each service
                for service_to_try in services_to_try:
                    # Build query for this service
                    query = Q(
                        start_time__date__gte=start_date.date(),
                        start_time__date__lte=end_date.date(),
                        service_name=service_to_try,
                    )

                    meetings_in_window_qs = Meeting.objects.filter(query)

                    # Initialize autolink service for this service
                    autolink_service = MeetingTaskAutolinkService(
                        time_window_days=days,
                        service_name=service_to_try,
                    )

                    # Score candidates for this service
                    scored = autolink_service.score_candidate_meetings(
                        meetings_in_window_qs[:100], task
                    )

                    # Mark which service each candidate came from
                    for candidate in scored:
                        candidate["service_source"] = service_to_try

                    all_scored_candidates.extend(scored)

                    if verbose and scored:
                        self.stdout.write(
                            f"  Task {task.id}: Found {len(scored)} candidates from {service_to_try}"
                        )

                # If primary service had no candidates above threshold, try fallback
                valid_from_primary = [
                    c
                    for c in all_scored_candidates
                    if c.get("score", 0.0) >= min_review_confidence
                    and c.get("service_source") in services_to_try
                ]

                if (
                    fallback_services
                    and service_option != "all"
                    and not valid_from_primary
                ):
                    fallback_service = (
                        "gotomeeting_external"
                        if service_option == "internal"
                        else "gotomeeting_internal"
                    )
                    fallback_used = True
                    service_scope_used.append(
                        fallback_service.replace("gotomeeting_", "")
                    )

                    if verbose:
                        self.stdout.write(
                            f"  Task {task.id}: No candidates above threshold from {service_option}, trying fallback {fallback_service}"
                        )

                    query = Q(
                        start_time__date__gte=start_date.date(),
                        start_time__date__lte=end_date.date(),
                        service_name=fallback_service,
                    )

                    meetings_in_window_qs = Meeting.objects.filter(query)

                    autolink_service = MeetingTaskAutolinkService(
                        time_window_days=days,
                        service_name=fallback_service,
                    )

                    fallback_scored = autolink_service.score_candidate_meetings(
                        meetings_in_window_qs[:100], task
                    )

                    # Mark fallback candidates
                    for candidate in fallback_scored:
                        candidate["service_source"] = fallback_service
                        candidate["fallback_used"] = True

                    all_scored_candidates.extend(fallback_scored)

                    if verbose and fallback_scored:
                        self.stdout.write(
                            f"  Task {task.id}: Found {len(fallback_scored)} candidates from fallback {fallback_service}"
                        )

                    # If still no candidates, try both services combined (optional but recommended)
                    if not fallback_scored and verbose:
                        self.stdout.write(
                            f"  Task {task.id}: No candidates from fallback either. Both services already tried."
                        )

                # Add requirement/topic boost signal
                # Get all meetings from all services for boost check
                all_meetings_qs = Meeting.objects.filter(
                    Q(start_time__date__gte=start_date.date())
                    & Q(start_time__date__lte=end_date.date())
                    & Q(
                        service_name__in=[
                            "gotomeeting_internal",
                            "gotomeeting_external",
                        ]
                    )
                )
                all_scored_candidates = self._apply_requirement_topic_boost(
                    task, all_scored_candidates, all_meetings_qs
                )

                # Add service scope and fallback info to signals_json
                for candidate in all_scored_candidates:
                    signals_hit = candidate.get("signals_hit", [])
                    service_source = candidate.get("service_source", "unknown")
                    service_scope = (
                        "both"
                        if service_option == "all"
                        else service_source.replace("gotomeeting_", "")
                    )

                    # Add service scope info
                    if "service_scope" not in signals_hit:
                        signals_hit.append(f"service_scope:{service_scope}")

                    # Add fallback info if used
                    if candidate.get("fallback_used") or fallback_used:
                        if "fallback_used" not in signals_hit:
                            signals_hit.append("fallback_used")

                    candidate["signals_hit"] = signals_hit

                # Sort all candidates by score (highest first)
                all_scored_candidates.sort(
                    key=lambda x: x.get("score", 0.0), reverse=True
                )

                scored_candidates = all_scored_candidates

                # Filter by minimum threshold and take top-N
                valid_candidates = [
                    c for c in scored_candidates if c["score"] >= min_review_confidence
                ][:top_n]

                if not valid_candidates:
                    if verbose:
                        self.stdout.write(
                            f"  Task {task.id}: No candidates above threshold {min_review_confidence}"
                        )
                    continue

                # Process each candidate
                best_score = valid_candidates[0]["score"] if valid_candidates else 0.0
                second_best_score = (
                    valid_candidates[1]["score"] if len(valid_candidates) > 1 else 0.0
                )
                score_delta = best_score - second_best_score

                # Collect meeting_ids from candidates to fetch in one query
                candidate_meeting_ids = [
                    c["meeting_id"] for c in valid_candidates if c.get("meeting_id")
                ]

                # Fetch meetings by meeting_id (using all meetings QuerySet)
                meetings_by_id = {
                    m.meeting_id: m
                    for m in all_meetings_qs.filter(
                        meeting_id__in=candidate_meeting_ids
                    )
                }

                for candidate in valid_candidates:
                    meeting_id = candidate.get("meeting_id")
                    if not meeting_id:
                        continue

                    meeting = meetings_by_id.get(meeting_id)
                    if not meeting:
                        continue

                    # Generate input hash for deduplication
                    input_hash = self._generate_input_hash(task, meeting, candidate)

                    # Check for existing suggestion with same hash
                    existing = TaskMeetingLinkSuggestion.objects.filter(
                        task=task,
                        meeting=meeting,
                        input_hash=input_hash,
                        is_active=True,
                    ).first()

                    if existing:
                        if verbose:
                            self.stdout.write(
                                f"  Task {task.id} → Meeting {meeting.id}: Duplicate suggestion (hash={input_hash[:8]}), skipping"
                            )
                        continue

                    # Build explanation
                    explanation = self._build_explanation(task, meeting, candidate)

                    # Determine status
                    status = TaskMeetingLinkSuggestion.SuggestionStatus.PROPOSED
                    should_auto_link = False

                    if candidate["score"] >= auto_confidence:
                        # Check if best candidate is clearly above second-best
                        if candidate == valid_candidates[0] and score_delta >= 0.10:
                            status = (
                                TaskMeetingLinkSuggestion.SuggestionStatus.AUTO_LINKED
                            )
                            should_auto_link = True
                        else:
                            status = (
                                TaskMeetingLinkSuggestion.SuggestionStatus.QUEUED_FOR_REVIEW
                            )
                    elif candidate["score"] >= min_review_confidence:
                        status = (
                            TaskMeetingLinkSuggestion.SuggestionStatus.QUEUED_FOR_REVIEW
                        )

                    if not dry_run:
                        with transaction.atomic():
                            # Create suggestion
                            suggestion = TaskMeetingLinkSuggestion.objects.create(
                                task=task,
                                meeting=meeting,
                                confidence=candidate["score"],
                                signals_json=candidate.get("signals_hit", []),
                                explanation=explanation,
                                status=status,
                                provider="rule_based",
                                model="autolink_v3",
                                input_hash=input_hash,
                                is_active=True,
                            )

                            stats["suggestions_created"] += 1

                            if (
                                status
                                == TaskMeetingLinkSuggestion.SuggestionStatus.AUTO_LINKED
                            ):
                                stats["suggestions_auto_linked"] += 1

                                # Create TaskLink
                                TaskLinks.objects.get_or_create(
                                    task=task,
                                    meeting_id=meeting.meeting_id,
                                    is_auto_generated=True,
                                    defaults={
                                        "added_by": task.employee,
                                        "link_name": f"Meeting: {meeting.topic or 'Untitled'}",
                                        "description": explanation,
                                        "link": meeting.recording_url
                                        or meeting.download_url
                                        or "",
                                        "is_active": True,
                                    },
                                )
                            elif (
                                status
                                == TaskMeetingLinkSuggestion.SuggestionStatus.QUEUED_FOR_REVIEW
                            ):
                                stats["suggestions_queued"] += 1

                            if verbose:
                                self.stdout.write(
                                    f"  Task {task.id} → Meeting {meeting.id}: "
                                    f"{status} (confidence={candidate['score']:.2f})"
                                )
                    else:
                        # Dry run: just count
                        if (
                            status
                            == TaskMeetingLinkSuggestion.SuggestionStatus.AUTO_LINKED
                        ):
                            stats["suggestions_auto_linked"] += 1
                        elif (
                            status
                            == TaskMeetingLinkSuggestion.SuggestionStatus.QUEUED_FOR_REVIEW
                        ):
                            stats["suggestions_queued"] += 1
                        stats["suggestions_created"] += 1

                        if verbose:
                            self.stdout.write(
                                f"  [DRY RUN] Task {task.id} → Meeting {meeting.id}: "
                                f"{status} (confidence={candidate['score']:.2f})"
                            )

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error processing task {task.id}: {e}", exc_info=True)
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f"  Task {task.id}: Error - {e}")
                    )

        # Print summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  Tasks scanned: {stats['tasks_scanned']}")
        self.stdout.write(f"  Suggestions created: {stats['suggestions_created']}")
        self.stdout.write(f"  Auto-linked: {stats['suggestions_auto_linked']}")
        self.stdout.write(f"  Queued for review: {stats['suggestions_queued']}")
        self.stdout.write(f"  Errors: {stats['errors']}")
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

    def _generate_input_hash(self, task, meeting, candidate) -> str:
        """Generate hash for deduplication"""
        key_parts = [
            str(task.id),
            str(meeting.id),
            str(candidate.get("score", 0)),
            ",".join(sorted(candidate.get("signals_hit", []))),
            str(meeting.meeting_id or ""),
            str(meeting.start_time.isoformat() if meeting.start_time else ""),
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _build_explanation(self, task, meeting, candidate) -> str:
        """Build human-readable explanation"""
        signals = candidate.get("signals_hit", [])
        score = candidate.get("score", 0.0)

        parts = []

        if "launch_intent" in signals:
            parts.append("Launch intent match")
        if "meeting_room_id" in signals:
            parts.append("Meeting room match")
        if "requirement_code" in signals:
            parts.append("Requirement code match")
        if "attendee_email" in signals:
            parts.append("Attendee email match")
        if "topic_keyword" in signals:
            parts.append("Topic keyword match")
        if "requirement_topic_boost" in signals:
            parts.append("Requirement code in topic")

        # Include service scope and fallback info
        service_scope = None
        for signal in signals:
            if signal.startswith("service_scope:"):
                service_scope = signal.replace("service_scope:", "")
                break

        if service_scope:
            parts.append(f"Service: {service_scope}")

        if "fallback_used" in signals:
            parts.append("Fallback service used")

        # Include meeting activity tag if available
        try:
            tag_suggestion = (
                MeetingActivityTagSuggestion.objects.filter(
                    meeting=meeting, is_active=True
                )
                .order_by("-created_at")
                .first()
            )

            if tag_suggestion:
                parts.append(f"Meeting type: {tag_suggestion.suggested_activity_type}")
        except Exception:
            pass

        # Include requirement match if available
        try:
            req_match = (
                AIRequirementMatch.objects.filter(
                    task=task,
                    meeting=meeting,
                )
                .order_by("-created_at")
                .first()
            )

            if req_match:
                parts.append(
                    f"Requirement match: {req_match.ai_match_label} ({req_match.ai_confidence:.2f})"
                )
        except Exception:
            pass

        explanation = (
            f"Confidence: {score:.2f}. Signals: {', '.join(parts) if parts else 'None'}"
        )
        return explanation

    def _apply_requirement_topic_boost(
        self, task, scored_candidates, meetings_qs
    ) -> list:
        """
        Apply requirement/topic boost signal to candidates.

        If task has a requirement code/id or activity implies requirement,
        boost meetings whose topic_normalized contains requirement codes.
        """
        # Check if task has requirement or activity requires it
        has_requirement = False
        requirement_code = None

        if task.requirement:
            has_requirement = True
            requirement_code = f"REQ-{task.requirement.id}"
        else:
            # Check if activity type requires requirement
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            if activity_type_slug:
                try:
                    from coda.config.activity_definitions import \
                        get_activity_policy

                    policy = get_activity_policy(activity_type_slug)
                    if policy and policy.requirement_required:
                        has_requirement = True
                        # Try to infer requirement code from task if available
                        if task.requirement:
                            requirement_code = f"REQ-{task.requirement.id}"
                except Exception:
                    pass

        if not has_requirement or not requirement_code:
            return scored_candidates

        # Extract requirement number (e.g., "REQ-508" -> "508")
        req_number = requirement_code.replace("REQ-", "").replace("req-", "").strip()

        # Boost candidates whose meeting topic contains requirement code
        for candidate in scored_candidates:
            meeting_id = candidate.get("meeting_id")
            if not meeting_id:
                continue

            # Get meeting from queryset
            meeting = meetings_qs.filter(meeting_id=meeting_id).first()
            if not meeting:
                continue

            # Check topic_normalized for requirement code patterns
            topic_normalized = (meeting.topic_normalized or meeting.topic or "").lower()

            boost_applied = False
            if f"requirement-{req_number}" in topic_normalized:
                candidate["score"] = min(1.0, candidate.get("score", 0.0) + 0.15)
                if "requirement_topic_boost" not in candidate.get("signals_hit", []):
                    candidate.setdefault("signals_hit", []).append(
                        "requirement_topic_boost"
                    )
                boost_applied = True
            elif f"req-{req_number}" in topic_normalized:
                candidate["score"] = min(1.0, candidate.get("score", 0.0) + 0.15)
                if "requirement_topic_boost" not in candidate.get("signals_hit", []):
                    candidate.setdefault("signals_hit", []).append(
                        "requirement_topic_boost"
                    )
                boost_applied = True
            elif req_number in topic_normalized and "requirement" in topic_normalized:
                # Partial match: requirement mentioned with number nearby
                candidate["score"] = min(1.0, candidate.get("score", 0.0) + 0.10)
                if "requirement_topic_boost" not in candidate.get("signals_hit", []):
                    candidate.setdefault("signals_hit", []).append(
                        "requirement_topic_boost"
                    )
                boost_applied = True

        return scored_candidates
