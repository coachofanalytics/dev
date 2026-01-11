"""
Management command to automatically link Meeting records to Tasks and create evidence.

Usage:
    poetry run python coda/manage.py autolink_meeting_evidence
    poetry run python coda/manage.py autolink_meeting_evidence --days 1 --user-id 5
    poetry run python coda/manage.py autolink_meeting_evidence --service external --dry-run
    poetry run python coda/manage.py autolink_meeting_evidence --limit 10 --verbose

Phase 3: Automation pipeline for meeting-based tasks (HARDENED).
"""

import logging

from ai_services.models import AutolinkRun
from ai_services.services.meeting_task_autolink_service import \
    MeetingTaskAutolinkService
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from management.models import Task, TaskReviewComment

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Automatically link Meeting records to Tasks and create evidence (Phase 3 - HARDENED)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Meeting lookback window in days (not task recency). Used for meeting search time window (default: 1)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Process tasks for a specific user only",
        )
        parser.add_argument(
            "--service",
            type=str,
            choices=["external", "internal", "all"],
            default="all",
            help="Service name filter: external (gotomeeting_external), internal (gotomeeting_internal), or all (default: all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of tasks to process (default: no limit)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output for each task",
        )
        parser.add_argument(
            "--diagnose",
            action="store_true",
            help="Diagnose mode: show matching analysis without creating/updating TaskLinks (read-only)",
        )
        parser.add_argument(
            "--task-id",
            type=int,
            help="Process a specific task ID only (useful with --diagnose)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results as JSON lines (useful with --diagnose for analysis)",
        )

    def handle(self, *args, **options):
        days = options.get("days", 1)
        user_id = options.get("user_id")
        service_option = options.get("service", "all")
        dry_run = options.get("dry_run", False)
        limit = options.get("limit", 25 if options.get("diagnose", False) else None)
        verbose = options.get("verbose", False)
        diagnose = options.get("diagnose", False)
        task_id = options.get("task_id")
        json_output = options.get("json", False)

        # Map service option to service_name
        service_name = None
        if service_option == "external":
            service_name = "gotomeeting_external"
        elif service_option == "internal":
            service_name = "gotomeeting_internal"

        self.stdout.write(
            self.style.SUCCESS(
                "\n🔗 Meeting Evidence Auto-Link (Phase 3 - HARDENED) 🔗\n"
            )
        )

        if diagnose:
            self.stdout.write(
                self.style.WARNING(
                    "🔍 DIAGNOSE MODE - Read-only analysis, no TaskLinks created/updated\n"
                )
            )
        elif dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made\n")
            )

        # Create AutolinkRun for observability (always create, even in diagnose mode for stats tracking)
        autolink_run = AutolinkRun.objects.create(
            days=days,
            user_id=user_id,
            service_name=service_name,
            dry_run=dry_run or diagnose,  # Mark as dry_run if diagnose mode
            status="in_progress",
        )

        try:
            # Initialize service with meeting lookback window from --days parameter
            # time_window_days controls the meeting search window, not task filtering
            autolink_service = MeetingTaskAutolinkService(
                time_window_days=days,  # Use --days as meeting lookback window
                service_name=service_name,
            )

            # Discover candidate tasks
            if task_id:
                # Process specific task only
                tasks = Task.objects.filter(id=task_id, is_active=True)
                if not tasks.exists():
                    self.stdout.write(
                        self.style.ERROR(f"Task {task_id} not found or not active.")
                    )
                    autolink_run.status = "failed"
                    autolink_run.finished_at = timezone.now()
                    autolink_run.error_message = f"Task {task_id} not found"
                    autolink_run.save()
                    return
            else:
                # Discover candidate tasks (days param not used for task filtering, only for meeting window)
                tasks = autolink_service.discover_candidate_tasks(
                    days=days,  # Passed for compatibility, but not used for task filtering
                    user_id=user_id,
                )

                # Output candidate selection summary in diagnose mode
                if diagnose:
                    from management.services.policy_resolver import \
                        PolicyResolver

                    from coda.config.activity_definitions import \
                        ACTIVITY_POLICIES

                    task_count = tasks.count()
                    employees_included = tasks.values_list(
                        "employee__username", flat=True
                    ).distinct()
                    activity_types = tasks.values_list(
                        "activity_name", flat=True
                    ).distinct()

                    # Get meeting-required activity types from ActivityPolicy
                    meeting_required_slugs = [
                        slug
                        for slug, policy in ACTIVITY_POLICIES.items()
                        if policy.meeting_required
                    ]

                    # Get user group if user_id specified
                    user_group = None
                    if user_id:
                        try:
                            from django.contrib.auth import get_user_model

                            User = get_user_model()
                            user = User.objects.get(id=user_id)
                            policy_config = PolicyResolver.for_user(user)
                            user_group = policy_config.group_name
                        except Exception:
                            pass

                    self.stdout.write(f"\n📊 Candidate Selection Summary:")
                    self.stdout.write(f"   Tasks found: {task_count}")
                    if user_group:
                        self.stdout.write(f"   User group: {user_group}")
                    self.stdout.write(
                        f"   Employees included: {len(employees_included)} ({', '.join(employees_included[:5])}{'...' if len(employees_included) > 5 else ''})"
                    )
                    self.stdout.write(
                        f"   Activity types found: {', '.join(activity_types[:5])}{'...' if len(activity_types) > 5 else ''}"
                    )
                    self.stdout.write(
                        f"   Meeting-required activity types (from ActivityPolicy): {', '.join(meeting_required_slugs)}"
                    )
                    self.stdout.write(
                        f"   Exclusion rule: Tasks with existing auto-generated TaskLinks (meeting_id present) excluded"
                    )

                    # Show exclusion reasons for tasks that should be included but aren't
                    if user_id and task_count < 10:  # Only if we expect more tasks
                        try:
                            from django.contrib.auth import get_user_model
                            from management.models import TaskLinks

                            User = get_user_model()
                            user = User.objects.get(id=user_id)

                            # Get all meeting-required tasks for this user
                            all_meeting_tasks = Task.objects.filter(
                                employee_id=user_id, is_active=True
                            )

                            # Check which ones are excluded and why
                            excluded_with_auto_evidence = (
                                TaskLinks.objects.filter(
                                    task__employee_id=user_id,
                                    is_active=True,
                                    is_auto_generated=True,
                                    meeting_id__isnull=False,
                                )
                                .values_list("task_id", flat=True)
                                .distinct()
                            )

                            excluded_count = len(excluded_with_auto_evidence)
                            if excluded_count > 0:
                                self.stdout.write(
                                    f"   Excluded tasks (already auto-linked): {excluded_count}"
                                )
                        except Exception as e:
                            self.stdout.write(
                                f"   (Could not compute exclusion details: {e})"
                            )

                    self.stdout.write("")

            if limit:
                tasks = tasks[:limit]

            total_tasks_scanned = tasks.count()
            autolink_run.tasks_scanned = total_tasks_scanned
            autolink_run.save(update_fields=["tasks_scanned"])

            self.stdout.write(f"📋 Found {total_tasks_scanned} candidate task(s)\n")

            if total_tasks_scanned == 0:
                self.stdout.write(
                    self.style.WARNING("No candidate tasks found. Exiting.")
                )
                autolink_run.status = "success"
                autolink_run.finished_at = timezone.now()
                autolink_run.save()
                return

            # Statistics
            matched_tasks = 0
            tasklinks_created = 0
            tasklinks_updated = 0
            tasks_skipped = 0
            tasks_mismatched = 0
            eligible_ready_for_review = 0
            tasks_failed = 0
            not_eligible_by_reason = {}
            unmatched_patterns = {}

            # Sample task IDs (max 10 each)
            sample_matched = []
            sample_mismatched = []
            sample_failed = []

            # Dry-run preview table header
            if dry_run:
                self.stdout.write("\n" + "=" * 120)
                self.stdout.write(
                    f"{'Task ID':<10} {'User':<15} {'Activity':<25} {'Req Code':<12} "
                    f"{'Meeting ID':<15} {'Match':<15} {'Conf':<6} {'Action':<15}"
                )
                self.stdout.write("=" * 120)

            # Process each task
            for task in tasks:
                task_id = task.id
                user_name = task.employee.username if task.employee else "N/A"
                activity_type = (
                    (
                        task.activity_type.slug
                        if task.activity_type
                        else task.activity_name
                    )[:25]
                    if task.activity_type or task.activity_name
                    else "N/A"
                )
                requirement_code = (
                    f"REQ-{task.requirement.id}" if task.requirement else "None"
                )

                if verbose:
                    self.stdout.write(
                        f"\n📝 Processing Task {task_id}: {task.activity_name}"
                    )
                    if task.employee:
                        self.stdout.write(f"   Employee: {user_name}")
                    if task.requirement:
                        self.stdout.write(f"   Requirement: {requirement_code}")

                # Find matching meeting
                match_result = autolink_service.find_meeting_for_task(task)

                if not match_result:
                    if diagnose:
                        # In diagnose mode, get detailed diagnostic information
                        diagnostic_info = autolink_service.diagnose_meeting_search(task)

                        # Get top 3 meeting candidates with scoring
                        from datetime import timedelta

                        from ai_services.models import Meeting
                        from django.db.models import Q

                        task_date = (
                            task.submission
                            if task.submission
                            else task.created_at.date()
                        )
                        start_date = task_date - timedelta(
                            days=autolink_service.time_window_days
                        )
                        end_date = task_date + timedelta(
                            days=autolink_service.time_window_days
                        )

                        candidate_meetings_query = Meeting.objects.filter(
                            Q(start_time__date__gte=start_date)
                            & Q(start_time__date__lte=end_date)
                        )
                        if service_name:
                            candidate_meetings_query = candidate_meetings_query.filter(
                                service_name=service_name
                            )

                        # Get more candidates to score, then take top 3
                        candidate_meetings = candidate_meetings_query.order_by(
                            "-start_time"
                        )[:10]

                        # Score all candidates
                        scored_candidates = autolink_service.score_candidate_meetings(
                            candidate_meetings, task
                        )
                        meeting_candidates = scored_candidates[:3]  # Top 3

                        diagnosis = {
                            "task_id": task_id,
                            "employee": user_name,
                            "activity_type": activity_type,
                            "requirement_code": (
                                requirement_code if task.requirement else None
                            ),
                            "meeting_candidates": meeting_candidates,
                            "final_decision": "NO LINK",
                            "decision_reason": "No match found",
                            "diagnostic_info": diagnostic_info,
                        }

                        if json_output:
                            import json

                            self.stdout.write(json.dumps(diagnosis))
                        else:
                            self.stdout.write(f"\n{'='*80}")
                            self.stdout.write(f"Task {task_id}: {activity_type}")
                            self.stdout.write(f"Employee: {user_name}")

                            # Show policy info
                            if diagnostic_info.get("policy"):
                                policy = diagnostic_info["policy"]
                                self.stdout.write(f"\nPolicy:")
                                self.stdout.write(
                                    f"  meeting_required: {policy.get('meeting_required')}"
                                )
                                self.stdout.write(
                                    f"  meeting_room_id expected: {policy.get('meeting_room_id')}"
                                )
                                self.stdout.write(
                                    f"  sessions_required: {policy.get('sessions_required')}"
                                )
                                self.stdout.write(
                                    f"  requirement_required: {policy.get('requirement_required')}"
                                )

                            # Show query parameters
                            query_params = diagnostic_info.get("query_parameters", {})
                            self.stdout.write(f"\nCandidate Meeting Query Parameters:")
                            self.stdout.write(
                                f"  service filter: {query_params.get('service_filter', 'N/A')}"
                            )
                            self.stdout.write(
                                f"  date window: {query_params.get('date_window_days', 'N/A')} days"
                            )
                            self.stdout.write(
                                f"  start_date: {query_params.get('start_date', 'N/A')}"
                            )
                            self.stdout.write(
                                f"  end_date: {query_params.get('end_date', 'N/A')}"
                            )
                            self.stdout.write(
                                f"  meeting_room_id filter: {query_params.get('meeting_room_id_filter', 'None')}"
                            )

                            # Show candidate counts
                            candidate_counts = diagnostic_info.get(
                                "candidate_counts", {}
                            )
                            self.stdout.write(f"\nCandidate Meeting Counts:")
                            for stage, count in candidate_counts.items():
                                self.stdout.write(f"  {stage}: {count}")

                            # Show zero candidate reasons
                            zero_reasons = diagnostic_info.get(
                                "zero_candidate_reasons", []
                            )
                            if zero_reasons:
                                self.stdout.write(f"\nZero Candidate Reasons:")
                                for reason in zero_reasons:
                                    self.stdout.write(f"  - {reason}")

                            # Show top candidates with full details
                            self.stdout.write(f"\nTop 3 Meeting Candidates:")
                            if meeting_candidates:
                                for i, candidate in enumerate(meeting_candidates, 1):
                                    self.stdout.write(
                                        f"  {i}. Meeting ID: {candidate.get('meeting_id', 'N/A')}"
                                    )
                                    self.stdout.write(
                                        f"     Service: {candidate.get('service_name', 'N/A')}"
                                    )
                                    self.stdout.write(
                                        f"     Start: {candidate.get('start_time', 'N/A')}"
                                    )
                                    self.stdout.write(
                                        f"     Duration: {candidate.get('duration_minutes', 0)} minutes"
                                    )
                                    self.stdout.write(
                                        f"     Signals Hit: {', '.join(candidate.get('signals_hit', [])) or 'None'}"
                                    )
                                    self.stdout.write(
                                        f"     Score: {candidate.get('score', 0.0):.2f}"
                                    )
                                    if candidate.get("rejection_reason"):
                                        self.stdout.write(
                                            f"     Rejection Reason: {candidate['rejection_reason']}"
                                        )
                            else:
                                self.stdout.write(f"  (No candidates found)")

                            self.stdout.write(
                                f"\nFinal Decision: {diagnosis['final_decision']}"
                            )
                            self.stdout.write(f"Reason: {diagnosis['decision_reason']}")
                            self.stdout.write(f"{'='*80}\n")
                        continue

                    if verbose:
                        self.stdout.write(
                            self.style.WARNING("   ❌ No meeting match found")
                        )
                    unmatched_patterns["no_match"] = (
                        unmatched_patterns.get("no_match", 0) + 1
                    )
                    continue

                # Check for requirement mismatch
                if match_result.get("requirement_mismatch"):
                    tasks_mismatched += 1
                    mismatch_reason = match_result.get(
                        "mismatch_reason", "Requirement mismatch"
                    )

                    if len(sample_mismatched) < 10:
                        sample_mismatched.append(task_id)

                    if dry_run:
                        self.stdout.write(
                            f"{task_id:<10} {user_name:<15} {activity_type:<25} {requirement_code:<12} "
                            f"{'N/A':<15} {'MISMATCH':<15} {'0.0':<6} {'SKIP':<15}"
                        )
                        if verbose:
                            self.stdout.write(f"   ⚠️  {mismatch_reason}")

                    # Create review comment for mismatch (skip in diagnose mode)
                    if diagnose:
                        # In diagnose mode, show mismatch analysis
                        diagnosis = {
                            "task_id": task_id,
                            "employee": user_name,
                            "activity_type": activity_type,
                            "requirement_code": (
                                requirement_code if task.requirement else None
                            ),
                            "meeting_candidates": [],
                            "final_decision": "NO LINK",
                            "decision_reason": f"Requirement mismatch: {mismatch_reason}",
                        }
                        if json_output:
                            import json

                            self.stdout.write(json.dumps(diagnosis))
                        else:
                            self.stdout.write(f"\n{'='*80}")
                            self.stdout.write(f"Task {task_id}: {activity_type}")
                            self.stdout.write(f"Employee: {user_name}")
                            self.stdout.write(f"Requirement: {requirement_code}")
                            self.stdout.write(
                                f"\nFinal Decision: {diagnosis['final_decision']}"
                            )
                            self.stdout.write(f"Reason: {diagnosis['decision_reason']}")
                            self.stdout.write(f"{'='*80}\n")
                        continue

                    # Create review comment for mismatch
                    if not dry_run:
                        comment_text = (
                            f"Auto-link prevented: {mismatch_reason}. "
                            f"Task requires {requirement_code} but meeting has different requirement code. "
                            f"Please verify meeting requirement code matches task requirement."
                        )

                        existing_comment = TaskReviewComment.objects.filter(
                            task=task, comment__icontains="Auto-link prevented"
                        ).first()

                        if not existing_comment:
                            TaskReviewComment.objects.create(
                                task=task,
                                employee=task.employee,
                                reviewer=task.employee,
                                comment=comment_text,
                                status="NEEDS_FIX",
                            )
                    continue

                meeting = match_result["meeting"]
                match_type = match_result["match_type"]
                confidence = match_result.get("confidence", 0.0)
                attendee_match = match_result.get("attendee_match", False)
                meeting_id = meeting.meeting_id[:15] if meeting.meeting_id else "N/A"

                if verbose:
                    self.stdout.write(
                        f"   ✅ Matched Meeting {meeting.id}: {meeting.topic[:60]} "
                        f"(type: {match_type}, confidence: {confidence:.2f})"
                    )

                matched_tasks += 1
                if len(sample_matched) < 10:
                    sample_matched.append(task_id)

                if dry_run:
                    # Determine action
                    action = "CREATE"
                    # Check if would update existing
                    if meeting.meeting_id:
                        from management.models import TaskLinks

                        existing = TaskLinks.objects.filter(
                            task=task, meeting_id=meeting.meeting_id, is_active=True
                        ).exists()
                        if existing:
                            action = "UPDATE"

                    self.stdout.write(
                        f"{task_id:<10} {user_name:<15} {activity_type:<25} {requirement_code:<12} "
                        f"{meeting_id:<15} {match_type:<15} {confidence:.2f} {action:<15}"
                    )
                    continue

                # Diagnose mode: output matching analysis without creating TaskLinks (read-only)
                if diagnose:
                    # Get detailed diagnostic information
                    diagnostic_info = autolink_service.diagnose_meeting_search(task)

                    # Get top 3 meeting candidates with scoring (even if matched, show alternatives)
                    from datetime import timedelta

                    from ai_services.models import Meeting
                    from django.db.models import Q

                    task_date = (
                        task.submission if task.submission else task.created_at.date()
                    )
                    start_date = task_date - timedelta(
                        days=autolink_service.time_window_days
                    )
                    end_date = task_date + timedelta(
                        days=autolink_service.time_window_days
                    )

                    candidate_meetings = Meeting.objects.filter(
                        Q(start_time__date__gte=start_date)
                        & Q(start_time__date__lte=end_date)
                    )
                    if service_name:
                        candidate_meetings = candidate_meetings.filter(
                            service_name=service_name
                        )

                    # Get more candidates to score, then take top 3
                    candidate_meetings_list = candidate_meetings.order_by(
                        "-start_time"
                    )[:10]

                    # Score all candidates
                    scored_candidates = autolink_service.score_candidate_meetings(
                        candidate_meetings_list, task
                    )
                    meeting_candidates = scored_candidates[:3]  # Top 3

                    diagnosis = {
                        "task_id": task_id,
                        "employee": user_name,
                        "activity_type": activity_type,
                        "requirement_code": (
                            requirement_code if task.requirement else None
                        ),
                        "meeting_candidates": meeting_candidates,
                        "final_decision": "WOULD LINK",
                        "decision_reason": f"Match found: {match_type}, confidence: {confidence:.2f}",
                        "matched_meeting": {
                            "meeting_id": meeting.meeting_id,
                            "start_time": (
                                meeting.start_time.isoformat()
                                if meeting.start_time
                                else None
                            ),
                            "requirement_code": meeting.requirement_code,
                            "has_recording": bool(
                                meeting.recording_url or meeting.download_url
                            ),
                        },
                        "diagnostic_info": diagnostic_info,
                    }

                    if json_output:
                        import json

                        self.stdout.write(json.dumps(diagnosis))
                    else:
                        self.stdout.write(f"\n{'='*80}")
                        self.stdout.write(f"Task {task_id}: {activity_type}")
                        self.stdout.write(f"Employee: {user_name}")

                        # Show policy info
                        if diagnostic_info.get("policy"):
                            policy = diagnostic_info["policy"]
                            self.stdout.write(f"\nPolicy:")
                            self.stdout.write(
                                f"  meeting_required: {policy.get('meeting_required')}"
                            )
                            self.stdout.write(
                                f"  meeting_room_id expected: {policy.get('meeting_room_id')}"
                            )
                            self.stdout.write(
                                f"  sessions_required: {policy.get('sessions_required')}"
                            )
                            self.stdout.write(
                                f"  requirement_required: {policy.get('requirement_required')}"
                            )

                        # Show query parameters
                        query_params = diagnostic_info.get("query_parameters", {})
                        self.stdout.write(f"\nCandidate Meeting Query Parameters:")
                        self.stdout.write(
                            f"  service filter: {query_params.get('service_filter', 'N/A')}"
                        )
                        self.stdout.write(
                            f"  date window: {query_params.get('date_window_days', 'N/A')} days"
                        )
                        self.stdout.write(
                            f"  start_date: {query_params.get('start_date', 'N/A')}"
                        )
                        self.stdout.write(
                            f"  end_date: {query_params.get('end_date', 'N/A')}"
                        )
                        self.stdout.write(
                            f"  meeting_room_id filter: {query_params.get('meeting_room_id_filter', 'None')}"
                        )

                        # Show candidate counts
                        candidate_counts = diagnostic_info.get("candidate_counts", {})
                        self.stdout.write(f"\nCandidate Meeting Counts:")
                        for stage, count in candidate_counts.items():
                            self.stdout.write(f"  {stage}: {count}")

                        # Show top candidates with full details
                        self.stdout.write(f"\nTop 3 Meeting Candidates:")
                        for i, candidate in enumerate(meeting_candidates, 1):
                            self.stdout.write(
                                f"  {i}. Meeting ID: {candidate.get('meeting_id', 'N/A')}"
                            )
                            self.stdout.write(
                                f"     Service: {candidate.get('service_name', 'N/A')}"
                            )
                            self.stdout.write(
                                f"     Start: {candidate.get('start_time', 'N/A')}"
                            )
                            self.stdout.write(
                                f"     Duration: {candidate.get('duration_minutes', 0)} minutes"
                            )
                            self.stdout.write(
                                f"     Signals Hit: {', '.join(candidate.get('signals_hit', [])) or 'None'}"
                            )
                            self.stdout.write(
                                f"     Score: {candidate.get('score', 0.0):.2f}"
                            )
                            if candidate.get("rejection_reason"):
                                self.stdout.write(
                                    f"     Rejection Reason: {candidate['rejection_reason']}"
                                )

                        self.stdout.write(
                            f"\nFinal Decision: {diagnosis['final_decision']}"
                        )
                        self.stdout.write(f"Reason: {diagnosis['decision_reason']}")
                        self.stdout.write(f"Match Type: {match_type}")
                        self.stdout.write(
                            f"Matched Meeting: {diagnosis['matched_meeting']}"
                        )
                        self.stdout.write(f"{'='*80}\n")

                    continue  # Skip TaskLinks creation in diagnose mode

                # Create or update TaskLinks
                try:
                    with transaction.atomic():
                        result = (
                            autolink_service.create_or_update_tasklink_from_meeting(
                                task, meeting
                            )
                        )

                        if result is None or result[0] is None:
                            tasks_skipped += 1
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(
                                        "   ⚠️  Could not create TaskLinks (missing URL)"
                                    )
                                )
                            continue

                        tasklink, created = result

                        if created:
                            tasklinks_created += 1
                            if verbose:
                                self.stdout.write(
                                    f"   ✅ Created TaskLinks {tasklink.id}"
                                )
                        else:
                            tasklinks_updated += 1
                            if verbose:
                                self.stdout.write(
                                    f"   🔄 Updated TaskLinks {tasklink.id}"
                                )

                        # Apply scoring gate
                        gate_result = autolink_service.apply_scoring_gate(task)

                        if gate_result["eligible_for_approval"]:
                            eligible_ready_for_review += 1

                            # Create review comment with match details
                            comment_text = (
                                f"Auto-linked meeting evidence found. "
                                f"Meeting: {meeting.meeting_id or meeting.id}, "
                                f"Match method: {match_type}, "
                                f"Confidence: {confidence:.2f}, "
                                f"Attendee match: {'Yes' if attendee_match else 'No'}, "
                                f"Requirement code: {meeting.requirement_code or 'None'}. "
                                f"Task is ready for review. Quality score: {gate_result['quality_score']:.2f}"
                            )

                            existing_comment = TaskReviewComment.objects.filter(
                                task=task,
                                comment__icontains="Auto-linked meeting evidence",
                            ).first()

                            if not existing_comment:
                                TaskReviewComment.objects.create(
                                    task=task,
                                    employee=task.employee,
                                    reviewer=task.employee,
                                    comment=comment_text,
                                    status="INFO",
                                )
                                if verbose:
                                    self.stdout.write(
                                        "   📝 Created review comment (ready for review)"
                                    )
                        else:
                            # Not eligible - track reasons
                            reasons = gate_result.get("reasons", [])
                            for reason in reasons:
                                reason_key = (
                                    reason.split(":")[0] if ":" in reason else reason
                                )
                                not_eligible_by_reason[reason_key] = (
                                    not_eligible_by_reason.get(reason_key, 0) + 1
                                )

                            # Create review comment with match details
                            comment_text = (
                                f"Auto-linked meeting evidence found. "
                                f"Meeting: {meeting.meeting_id or meeting.id}, "
                                f"Match method: {match_type}, "
                                f"Confidence: {confidence:.2f}, "
                                f"Attendee match: {'Yes' if attendee_match else 'No'}, "
                                f"Requirement code: {meeting.requirement_code or 'None'}. "
                                f"Task needs attention: {', '.join(reasons)}"
                            )

                            existing_comment = TaskReviewComment.objects.filter(
                                task=task,
                                comment__icontains="Auto-linked meeting evidence",
                            ).first()

                            if not existing_comment:
                                TaskReviewComment.objects.create(
                                    task=task,
                                    employee=task.employee,
                                    reviewer=task.employee,
                                    comment=comment_text,
                                    status="NEEDS_FIX",
                                )
                                if verbose:
                                    self.stdout.write(
                                        f"   ⚠️  Created review comment: {', '.join(reasons)}"
                                    )

                except Exception as e:
                    tasks_failed += 1
                    if len(sample_failed) < 10:
                        sample_failed.append(task_id)
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error processing task {task_id}: {e}")
                    )
                    logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
                    continue

            # Update AutolinkRun with statistics
            autolink_run.tasks_matched = matched_tasks
            autolink_run.tasklinks_created = tasklinks_created
            autolink_run.tasklinks_updated = tasklinks_updated
            autolink_run.tasks_skipped = tasks_skipped
            autolink_run.tasks_mismatched = tasks_mismatched
            autolink_run.tasks_eligible = eligible_ready_for_review
            autolink_run.tasks_failed = tasks_failed
            autolink_run.sample_matched_task_ids = sample_matched
            autolink_run.sample_mismatched_task_ids = sample_mismatched
            autolink_run.sample_failed_task_ids = sample_failed
            autolink_run.status = "success"
            autolink_run.finished_at = timezone.now()
            autolink_run.save()

            # Summary output
            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("📊 SUMMARY"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f"Total tasks scanned: {total_tasks_scanned}")
            self.stdout.write(f"Matched tasks: {matched_tasks}")
            self.stdout.write(f"TaskLinks created: {tasklinks_created}")
            self.stdout.write(f"TaskLinks updated: {tasklinks_updated}")
            self.stdout.write(f"Tasks skipped: {tasks_skipped}")
            self.stdout.write(f"Tasks mismatched: {tasks_mismatched}")
            self.stdout.write(
                f"Eligible (ready for review): {eligible_ready_for_review}"
            )
            self.stdout.write(f"Tasks failed: {tasks_failed}")

            if not_eligible_by_reason:
                self.stdout.write("\nNot eligible breakdown:")
                for reason, count in sorted(not_eligible_by_reason.items()):
                    self.stdout.write(f"  - {reason}: {count}")

            if unmatched_patterns:
                self.stdout.write("\nUnmatched patterns:")
                for pattern, count in sorted(unmatched_patterns.items()):
                    self.stdout.write(f"  - {pattern}: {count}")

            self.stdout.write(f"\nAutolinkRun ID: {autolink_run.id}")
            if diagnose:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✅ Diagnosis complete (no TaskLinks created/updated)\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ Auto-link process completed!\n")
                )

        except Exception as e:
            autolink_run.status = "failed"
            autolink_run.finished_at = timezone.now()
            autolink_run.error_message = str(e)
            autolink_run.save()

            self.stdout.write(self.style.ERROR(f"\n❌ Autolink process failed: {e}\n"))
            logger.error(f"Autolink process failed: {e}", exc_info=True)
            raise CommandError(f"Autolink failed: {e}")
