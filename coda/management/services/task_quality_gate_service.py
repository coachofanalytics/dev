"""
Task Quality Gate Service - Single source of truth for evidence/quality consistency.

This service provides unified gate status calculation to ensure:
- Evidence Pass and Quality Pass are logically consistent
- DAF v2 UI shows accurate status
- No mismatches between evidence panel and readiness checks
"""

import logging
import os
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Q
from management.models import Task, TaskLinks

# Optional import - ChecklistEvaluationService may not be available
try:
    from management.services.checklist_evaluation_service import \
        ChecklistEvaluationService
except (ModuleNotFoundError, ImportError):
    # Fallback: create a minimal stub class
    class ChecklistEvaluationService:
        def get_task_quality_score(self, task, tasklinks=None):
            """Fallback implementation returns default score."""
            return 1.0  # Default to passing score

        def evaluate_checklist(self, task, tasklinks=None):
            """Fallback implementation returns empty checklist results."""
            return {"completed": [], "missing": [], "completion_rate": 1.0}


# Optional import - activity_definitions may not be available
try:
    from coda.config.activity_definitions import get_activity_definition

    # Create wrapper function for compatibility
    def get_activity_policy(activity_slug=None, activity_name=None):
        """Wrapper around get_activity_definition to match expected interface."""
        from dataclasses import dataclass, field

        if activity_slug:
            activity_def = get_activity_definition(activity_slug)
            if activity_def:
                # Convert ActivityDefinition to ActivityPolicy-like object
                # Use default_factory for mutable defaults (required by dataclasses)
                @dataclass
                class ActivityPolicy:
                    slug: str = activity_def.slug
                    label: str = activity_def.name
                    meeting_required: bool = True
                    requirement_required: bool = False
                    evidence_requirements: List[str] = field(
                        default_factory=lambda: (
                            list(activity_def.evidence_requirements)
                            if activity_def.evidence_requirements
                            else []
                        )
                    )
                    required_meeting_count: int = 1
                    sessions_required: int = 1

                return ActivityPolicy()

        # Fallback if no slug or definition not found
        @dataclass
        class ActivityPolicy:
            slug: str = activity_slug or "default"
            label: str = activity_name or "Default Activity"
            meeting_required: bool = True
            requirement_required: bool = False
            evidence_requirements: List[str] = field(
                default_factory=lambda: ["doc_or_drive_link", "description"]
            )
            required_meeting_count: int = 1
            sessions_required: int = 1

        return ActivityPolicy()

except (ModuleNotFoundError, ImportError):
    # Fallback: create a minimal stub function
    def get_activity_policy(activity_slug=None, activity_name=None):
        """Fallback implementation returns default policy."""
        from dataclasses import dataclass, field

        @dataclass
        class ActivityPolicy:
            slug: str = activity_slug or "default"
            label: str = activity_name or "Default Activity"
            meeting_required: bool = True
            requirement_required: bool = False
            evidence_requirements: List[str] = field(
                default_factory=lambda: ["doc_or_drive_link", "description"]
            )
            required_meeting_count: int = 1
            sessions_required: int = 1

        return ActivityPolicy()


logger = logging.getLogger(__name__)

# DAF Debug flag - enable via DAF_DEBUG=1 environment variable or Django setting
DAF_DEBUG = getattr(settings, "DAF_DEBUG", False) or (
    os.environ.get("DAF_DEBUG", "").lower() in ("1", "true", "yes")
)


def _daf_debug_log(level, message, *args, **kwargs):
    """Helper to log DAF debug messages only when DAF_DEBUG is enabled."""
    if DAF_DEBUG:
        getattr(logger, level)(message, *args, **kwargs)


def debug_count(label, qs):
    """Log count for a queryset (only when DAF_DEBUG enabled)."""
    if DAF_DEBUG:
        count = qs.count() if hasattr(qs, "count") else len(qs)
        logger.info(f"[DAF_DEBUG] {label}: {count}")
        return count
    return None


def debug_sample(label, qs, fields, limit=5):
    """Log sample rows from queryset (only when DAF_DEBUG enabled)."""
    if DAF_DEBUG:
        items = list(qs[:limit]) if hasattr(qs, "__getitem__") else list(qs)[:limit]
        logger.info(f"[DAF_DEBUG] {label} (sample {len(items)}/{limit}):")
        for i, item in enumerate(items, 1):
            values = {}
            for field in fields:
                try:
                    val = getattr(item, field, None)
                    # Truncate long values
                    if isinstance(val, str) and len(val) > 50:
                        val = val[:47] + "..."
                    values[field] = val
                except Exception:
                    values[field] = "<error>"
            logger.info(f"  [{i}] {values}")


def debug_distinct(label, qs, field, limit=10):
    """Log most common distinct values for a field (only when DAF_DEBUG enabled)."""
    if DAF_DEBUG:
        try:
            from django.db.models import Count

            distinct_qs = (
                qs.values(field).annotate(count=Count("id")).order_by("-count")[:limit]
            )
            logger.info(f"[DAF_DEBUG] {label} (top {limit} distinct {field}):")
            for item in distinct_qs:
                logger.info(f"  {field}={item[field]}: {item['count']}")
        except Exception as e:
            logger.warning(f"[DAF_DEBUG] Error computing distinct {field}: {e}")


class TaskQualityGateService:
    """
    Service for calculating unified task quality gate status.

    Provides consistent evidence/quality checks used across:
    - DAF v2 dashboard
    - Evidence upload page
    - Manager review queue
    """

    def __init__(self):
        self.eval_service = ChecklistEvaluationService()
        self.logger = logger

    def get_task_gate_status(
        self, task: Task, task_links: Optional[Any] = None, user: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get unified gate status for a task.

        Args:
            task: Task instance
            task_links: Optional QuerySet of TaskLinks (for filtered views)
                      If None, queries all active TaskLinks for the task
            user: Optional user for filtering evidence (non-staff see only their own)

        Returns:
            Dict with:
            - has_evidence: bool
            - evidence_count: int
            - evidence_reasons: List[str] (why evidence is missing/partial)
            - requirement_ok: bool
            - meeting_ok: bool (if meeting required)
            - duration_ok: bool
            - quality_score: float
            - quality_pass: bool (>= 0.8 threshold)
            - overall_ready: bool (all gates pass)
            - evidence_status: str ("complete", "partial", "missing")
        """
        # Get activity policy
        activity_slug = self._get_activity_slug(task)
        policy = get_activity_policy(activity_slug) if activity_slug else None

        # Determine requirements from policy or legacy constants
        # DEFAULT: requires_meeting = True unless explicitly set False
        requires_requirement = False
        requires_meeting = True  # Default to True
        if policy:
            requires_requirement = policy.requirement_required
            requires_meeting = (
                policy.meeting_required
            )  # Policy can explicitly set False
        else:
            # Fallback to legacy constants - make import optional
            try:
                from management.legacy_views import (
                    MEETING_REQUIRED_ACTIVITY_TYPES,
                    REQUIREMENT_REQUIRED_ACTIVITY_TYPES)

                if activity_slug:
                    requires_requirement = activity_slug.upper() in [
                        a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
                    ]
                    # If in legacy list, requires_meeting = True; otherwise keep default True
                    # Only set False if explicitly in a "no meeting required" list (if such exists)
                    legacy_requires_meeting = activity_slug.upper() in [
                        a.upper() for a in MEETING_REQUIRED_ACTIVITY_TYPES
                    ]
                    # Keep default True if not in legacy list (backward compatible but defaults to True)
                    if legacy_requires_meeting:
                        requires_meeting = True
                    # else: keep default True (already set above)
            except (ImportError, AttributeError):
                # Legacy constants not available - keep defaults
                requires_requirement = False
                requires_meeting = True  # Keep default

        # Get evidence queryset
        if task_links is not None:
            # Use provided queryset (may be filtered by user)
            evidence_qs = task_links
            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: Using provided task_links queryset",
            )
        else:
            # Query all active evidence for this task
            evidence_qs = TaskLinks.objects.filter(task=task, is_active=True)
            # If user provided and not staff, filter to user's evidence only
            if user and not (user.is_staff or user.is_superuser):
                evidence_qs = evidence_qs.filter(added_by=user)
            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: Queried TaskLinks.filter(task={task.id}, is_active=True)",
            )

        # Focused debug logging for eunice user only
        is_eunice = (
            user and hasattr(user, "username") and user.username.lower() == "eunice"
        )
        if DAF_DEBUG and is_eunice:
            total_count = TaskLinks.objects.filter(task=task).count()
            active_count = TaskLinks.objects.filter(task=task, is_active=True).count()
            null_is_active_count = TaskLinks.objects.filter(
                task=task, is_active__isnull=True
            ).count()
            logger.info(
                f"[DAF_DEBUG] Task {task.id} ({task.activity_name}, mxpoint={task.mxpoint}):"
            )
            logger.info(
                f"  total_tasklinks={total_count}, active={active_count}, null_is_active={null_is_active_count}"
            )

            # Sample TaskLinks
            sample_links = list(TaskLinks.objects.filter(task=task)[:5])
            sample_data = [
                {
                    "id": link.id,
                    "is_active": link.is_active,
                    "meeting_id": getattr(link, "meeting_id", None),
                    "created_at": str(getattr(link, "created_at", None)),
                }
                for link in sample_links
            ]
            logger.info(f"  TaskLinks sample: {sample_data}")

        # Count evidence
        debug_count(
            f"Task {task.id} - Total TaskLinks (before filters)",
            TaskLinks.objects.filter(task=task),
        )
        debug_count(
            f"Task {task.id} - Active TaskLinks",
            TaskLinks.objects.filter(task=task, is_active=True),
        )
        evidence_count = evidence_qs.count()
        has_evidence = evidence_count > 0
        _daf_debug_log(
            "info",
            f"[DAF_DEBUG] Task {task.id}: evidence_count={evidence_count}, has_evidence={has_evidence}",
        )

        # Get evidence details
        evidence_list = list(evidence_qs.select_related("added_by"))
        debug_sample(
            f"Task {task.id} - Evidence list",
            evidence_list,
            ["id", "is_active", "meeting_id", "link"],
            limit=5,
        )
        has_meeting_evidence = False
        has_doc_evidence = False
        has_link_evidence = False

        for link in evidence_list:
            if getattr(link, "is_auto_generated", False) and getattr(
                link, "meeting_id", None
            ):
                has_meeting_evidence = True
            if link.link:
                has_link_evidence = True
                # Check if link matches a meeting
                try:
                    from ai_services.models import Meeting
                    from ai_services.utils.meeting_normalizer import \
                        normalize_url
                    from django.db.models import Q

                    normalized_link = normalize_url(link.link)
                    if normalized_link:
                        meeting_qs = Meeting.objects.filter(
                            Q(recording_url=normalized_link)
                            | Q(download_url=normalized_link)
                        )
                        if meeting_qs.exists():
                            has_meeting_evidence = True
                except Exception:
                    pass
            if link.doc or link.drive_link:
                has_doc_evidence = True

        # Check requirement
        requirement_ok = True
        if requires_requirement:
            requirement_ok = bool(task.requirement)

        # Check meeting requirement
        meeting_ok = True
        meetings_completed_count = 0
        required_meeting_count = 0

        # DAF_DEBUG: Log task details and requires_meeting computation
        if DAF_DEBUG:
            employee_username = (
                user.username
                if user and hasattr(user, "username")
                else (task.employee.username if task.employee else "N/A")
            )
            requirement_id = task.requirement.id if task.requirement else None
            logger.info(
                f"[DAF_DEBUG] Task {task.id}: employee={employee_username}, "
                f"mxpoint={task.mxpoint}, requirement_id={requirement_id}, "
                f"activity_name={task.activity_name}, activity_slug={activity_slug}"
            )
            logger.info(
                f"[DAF_DEBUG] Task {task.id}: requires_meeting={requires_meeting} (from policy={bool(policy)}, policy.meeting_required={policy.meeting_required if policy else 'N/A'})"
            )

        if requires_meeting:
            # Get required meeting count from policy
            if policy:
                if (
                    hasattr(policy, "sessions_required")
                    and policy.sessions_required > 0
                ):
                    required_meeting_count = policy.sessions_required
                    if DAF_DEBUG:
                        logger.info(
                            f"[DAF_DEBUG] Task {task.id}: required_meeting_count={required_meeting_count} (from policy.sessions_required)"
                        )
                elif (
                    hasattr(policy, "required_meeting_count")
                    and policy.required_meeting_count > 0
                ):
                    required_meeting_count = policy.required_meeting_count
                    if DAF_DEBUG:
                        logger.info(
                            f"[DAF_DEBUG] Task {task.id}: required_meeting_count={required_meeting_count} (from policy.required_meeting_count)"
                        )

            # Fallback to task.mxpoint (or point) if policy doesn't specify
            if required_meeting_count == 0 and (task.mxpoint or task.point):
                required_meeting_count = int(task.mxpoint or task.point or 1)
                if DAF_DEBUG:
                    logger.info(
                        f"[DAF_DEBUG] Task {task.id}: required_meeting_count={required_meeting_count} (from task.mxpoint/point)"
                    )
            elif required_meeting_count == 0:
                required_meeting_count = 1  # Default to 1
                if DAF_DEBUG:
                    logger.info(
                        f"[DAF_DEBUG] Task {task.id}: required_meeting_count={required_meeting_count} (default)"
                    )

            # Count distinct completed meetings using transcript_key (primary) or meeting_instance_key (fallback)
            # Apply date filter using Meeting.start_time if date range provided
            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: Counting meetings from {len(evidence_list)} evidence items",
            )

            from django.db.models import Q
            from management.utils.transcript_key_utils import (
                extract_transcript_key, is_transcript_url)

            # Collect transcript_keys and meeting_instance_keys from active TaskLinks
            transcript_keys = set()
            meeting_instance_keys = set()
            meeting_ids = set()

            for link in evidence_list:
                if link.is_active:
                    # Primary: transcript_key from link URL or stored transcript_key field
                    transcript_key = getattr(link, "transcript_key", None)
                    if (
                        not transcript_key
                        and link.link
                        and is_transcript_url(link.link)
                    ):
                        transcript_key = extract_transcript_key(link.link)
                    if transcript_key:
                        transcript_keys.add(transcript_key)

                    # Fallback: meeting_instance_key
                    meeting_instance_key = getattr(link, "meeting_instance_key", None)
                    if meeting_instance_key:
                        meeting_instance_keys.add(meeting_instance_key)

                    # Legacy: meeting_id (only count if no transcript_key or meeting_instance_key)
                    meeting_id = getattr(link, "meeting_id", None)
                    if meeting_id and not transcript_key and not meeting_instance_key:
                        meeting_ids.add(meeting_id)

            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: transcript_keys={list(transcript_keys)}, "
                f"meeting_instance_keys={list(meeting_instance_keys)}, meeting_ids={list(meeting_ids)}",
            )

            # Count distinct meetings using single Q() query (no union+distinct)
            distinct_meeting_count = 0
            try:
                from ai_services.models import Meeting
                from django.db.models import Q

                # Build single query with OR conditions for all join keys
                # Priority: transcript_key > meeting_instance_key > meeting_id
                # distinct() by Meeting.id handles double-counting automatically
                meeting_filter = Q()

                if transcript_keys:
                    meeting_filter |= Q(transcript_key__in=transcript_keys)
                if meeting_instance_keys:
                    meeting_filter |= Q(meeting_instance_key__in=meeting_instance_keys)
                if meeting_ids:
                    meeting_filter |= Q(meeting_id__in=meeting_ids)

                if meeting_filter:
                    # Apply date range filter if provided (from task context or user request)
                    meetings_qs = Meeting.objects.filter(meeting_filter)

                    # Count distinct meetings by id (handles any overlap automatically)
                    distinct_meeting_count = meetings_qs.values("id").distinct().count()

                    if DAF_DEBUG:
                        logger.info(
                            f"[DAF_DEBUG] Task {task.id}: transcript_keys={len(transcript_keys)}, "
                            f"meeting_instance_keys={len(meeting_instance_keys)}, meeting_ids={len(meeting_ids)}"
                        )
                        logger.info(
                            f"[DAF_DEBUG] Task {task.id}: Found {distinct_meeting_count} distinct meetings"
                        )
                else:
                    distinct_meeting_count = 0
                    if DAF_DEBUG:
                        logger.info(
                            f"[DAF_DEBUG] Task {task.id}: No join keys available, meeting_count=0"
                        )

            except Exception as e:
                logger.warning(
                    f"[DAF_DEBUG] Task {task.id}: Error counting meetings: {e}",
                    exc_info=True,
                )
                # Fallback to simple count if join fails
                distinct_meeting_count = (
                    len(transcript_keys) + len(meeting_instance_keys) + len(meeting_ids)
                )

            meetings_completed_count = distinct_meeting_count
            if DAF_DEBUG:
                logger.info(
                    f"[DAF_DEBUG] Task {task.id}: meetings_completed_count={meetings_completed_count}, required_meeting_count={required_meeting_count}"
                )
                logger.info(
                    f"[DAF_DEBUG] Task {task.id}: transcript_keys count={len(transcript_keys)}, "
                    f"meeting_instance_keys count={len(meeting_instance_keys)}, meeting_ids count={len(meeting_ids)}"
                )
            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: meetings_completed_count={meetings_completed_count}, required_meeting_count={required_meeting_count}",
            )

            # Verify meetings exist in Meeting table (for debugging) - using single Q() query
            if DAF_DEBUG and (transcript_keys or meeting_instance_keys or meeting_ids):
                try:
                    from ai_services.models import Meeting
                    from django.db.models import Q

                    # Use same single Q() query approach (no union)
                    verify_filter = Q()
                    if transcript_keys:
                        verify_filter |= Q(transcript_key__in=transcript_keys)
                    if meeting_instance_keys:
                        verify_filter |= Q(
                            meeting_instance_key__in=meeting_instance_keys
                        )
                    if meeting_ids:
                        verify_filter |= Q(meeting_id__in=meeting_ids)

                    if verify_filter:
                        all_meetings = Meeting.objects.filter(verify_filter)
                        found_count = all_meetings.values("id").distinct().count()
                        expected_count = (
                            len(transcript_keys)
                            + len(meeting_instance_keys)
                            + len(meeting_ids)
                        )

                        if found_count < expected_count:
                            logger.warning(
                                f"[DAF_DEBUG] Task {task.id}: Found {found_count}/{expected_count} meetings in Meeting table"
                            )
                        else:
                            logger.info(
                                f"[DAF_DEBUG] Task {task.id}: All {found_count} meetings exist in Meeting table"
                            )

                        # Log meeting details for debugging
                        if all_meetings.exists():
                            meeting_details = list(
                                all_meetings.distinct().values(
                                    "meeting_id",
                                    "start_time",
                                    "topic",
                                    "transcript_key",
                                )[:5]
                            )
                            logger.info(
                                f"[DAF_DEBUG] Task {task.id}: Sample meetings: {meeting_details}"
                            )
                except Exception as e:
                    logger.warning(
                        f"[DAF_DEBUG] Task {task.id}: Error verifying meetings: {e}",
                        exc_info=True,
                    )

            # Meeting requirement is met if meetings_completed >= required
            meeting_ok = meetings_completed_count >= required_meeting_count
            _daf_debug_log(
                "info",
                f"[DAF_DEBUG] Task {task.id}: meeting_ok={meeting_ok} ({meetings_completed_count} >= {required_meeting_count})",
            )

            # Log if requirement not met
            if not meeting_ok:
                self.logger.debug(
                    f"Task {task.id}: Meeting requirement not met: "
                    f"{meetings_completed_count}/{required_meeting_count} meetings completed"
                )

        # Get quality metrics (use same evidence queryset for consistency)
        try:
            quality_result = self.eval_service.get_task_quality_score(
                task, task_links=evidence_qs
            )
            quality_score = quality_result.get("quality_score", 0.0)
            evidence_coverage = quality_result.get("evidence_coverage", 0.0)
            duration_factor = quality_result.get("duration_factor", 0.0)
            missing_checklist_items = quality_result.get("missing_checklist_items", [])
        except Exception as e:
            self.logger.warning(f"Error getting quality score for task {task.id}: {e}")
            quality_score = 0.0
            evidence_coverage = 0.0
            duration_factor = 0.0
            missing_checklist_items = []

        # Determine evidence status
        if evidence_coverage >= 0.95 and (not requires_meeting or meeting_ok):
            evidence_status = "complete"
        elif evidence_coverage >= 0.5 or (has_evidence and not requires_meeting):
            evidence_status = "partial"
        else:
            evidence_status = "missing"

        # Build evidence reasons
        evidence_reasons = []
        if not has_evidence:
            evidence_reasons.append("No evidence uploaded")
        elif requires_meeting and not meeting_ok:
            if meetings_completed_count == 0:
                evidence_reasons.append("Meeting evidence required but not found")
            else:
                evidence_reasons.append(
                    f"Meeting requirement not met: {meetings_completed_count}/{required_meeting_count} "
                    f"(need {required_meeting_count - meetings_completed_count} more)"
                )
        elif evidence_coverage < 0.95:
            evidence_reasons.append(
                f"Evidence coverage insufficient ({evidence_coverage:.0%})"
            )

        # Quality pass (must have evidence to pass)
        quality_pass = quality_score >= 0.8 and has_evidence

        # Duration check
        duration_ok = duration_factor >= 0.8 or (not requires_meeting and has_evidence)

        # Overall ready: all gates pass
        overall_ready = (
            requirement_ok
            and has_evidence
            and (not requires_meeting or meeting_ok)
            and duration_ok
            and quality_pass
        )

        return {
            "has_evidence": has_evidence,
            "evidence_count": evidence_count,
            "evidence_reasons": evidence_reasons,
            "requirement_ok": requirement_ok,
            "meeting_ok": meeting_ok,
            "meetings_completed_count": meetings_completed_count,
            "required_meeting_count": required_meeting_count,
            "duration_ok": duration_ok,
            "quality_score": quality_score,
            "quality_pass": quality_pass,
            "overall_ready": overall_ready,
            "evidence_status": evidence_status,
            "evidence_coverage": evidence_coverage,
            "duration_factor": duration_factor,
            "missing_checklist_items": missing_checklist_items,
            "requires_requirement": requires_requirement,
            "requires_meeting": requires_meeting,
            "policy": policy,
        }

    def _get_activity_slug(self, task: Task) -> Optional[str]:
        """Get activity slug from task."""
        if task.activity_type:
            return (task.activity_type.slug or task.activity_type.name or "").upper()
        elif task.activity_name:
            return task.activity_name.upper().replace(" ", "_")
        return None

    def get_next_steps(self, task: Task, gate_status: Dict[str, Any]) -> List[str]:
        """
        Get actionable next steps to fix task issues.

        Args:
            task: Task instance
            gate_status: Result from get_task_gate_status()

        Returns:
            List of actionable next step messages
        """
        steps = []
        policy = gate_status.get("policy")

        if not gate_status["has_evidence"]:
            if policy and policy.evidence_requirements:
                steps.append(
                    f"Upload evidence: {', '.join(policy.evidence_requirements)}"
                )
            else:
                steps.append("Upload evidence (link, document, or meeting recording)")

        if gate_status["requires_requirement"] and not gate_status["requirement_ok"]:
            steps.append("Select a requirement for this activity type")

        if gate_status["requires_meeting"] and not gate_status["meeting_ok"]:
            steps.append(
                "Provide meeting evidence (GoToMeeting link with REQ-#### in topic)"
            )

        if not gate_status["duration_ok"]:
            steps.append("Ensure meeting duration meets minimum requirements")

        if not gate_status["quality_pass"]:
            missing_items = gate_status.get("missing_checklist_items", [])
            if missing_items:
                steps.append(
                    f"Complete checklist items: {', '.join(missing_items[:3])}"
                )
            else:
                steps.append(
                    "Improve evidence quality (add description, complete checklist)"
                )

        return steps
