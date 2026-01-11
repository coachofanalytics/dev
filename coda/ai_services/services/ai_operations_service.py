"""
AI Operations Service (AI-4)

Orchestrates daily AI operations runs for:
- AI-1: Meeting activity tagging
- AI-2: Requirement match verification (shadow mode)
- AI-3: Manager review suggestions

Feature Flags:
- AI_ENABLED: Master flag (must be True for AI calls)
- AI_OPS_ENABLED: Enable this service
"""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from ai_services.models import AIOperationsRun, Meeting
from django.conf import settings
from django.utils import timezone
from management.models import (RequirementMatchCheck, Task,
                               TaskAIReviewSuggestion)

logger = logging.getLogger(__name__)


class AIOperationsService:
    """
    Service for orchestrating daily AI operations runs.

    Runs AI-1, AI-2, and AI-3 in batch mode, collecting metrics
    and storing results in AIOperationsRun for observability.
    """

    def __init__(self):
        self.ai_enabled = getattr(settings, "AI_ENABLED", False)
        self.ops_enabled = getattr(settings, "AI_OPS_ENABLED", False)

        if not self.ops_enabled:
            logger.debug("AI operations service disabled")

    def run_daily_ops(
        self,
        days: int = 1,
        limit: Optional[int] = None,
        service: Optional[str] = None,
        dry_run: bool = False,
        created_by=None,
    ) -> Dict[str, Any]:
        """
        Run daily AI operations for meetings and tasks.

        Args:
            days: Number of days to look back
            limit: Optional limit on number of items to process
            service: Optional service filter (e.g., 'gotomeeting_external')
            dry_run: If True, don't actually create suggestions (just count)
            created_by: Optional user who triggered the run

        Returns:
            Dictionary with run results and counts
        """
        # Create run record
        run = AIOperationsRun.objects.create(
            days=days,
            limit=limit,
            service_name=service,
            dry_run=dry_run,
            created_by=created_by,
            status=AIOperationsRun.RunStatus.SUCCESS,
        )

        try:
            # Check if ops are enabled
            if not self.ops_enabled:
                run.status = AIOperationsRun.RunStatus.SKIPPED
                run.finished_at = timezone.now()
                run.save()
                return {
                    "status": "skipped",
                    "reason": "AI_OPS_ENABLED is False",
                    "run_id": run.id,
                }

            # Step 1: Run AI-1 meeting tagging
            ai1_results = self._run_ai1_meeting_tagging(
                days=days, limit=limit, service=service, dry_run=dry_run
            )

            # Step 2: Run AI-3 review suggestions for tasks in review queue
            ai3_results = self._run_ai3_review_suggestions(
                days=days, limit=limit, dry_run=dry_run
            )

            # Step 3: Run AI-2 requirement match checks (shadow mode only)
            ai2_results = self._run_ai2_requirement_checks(
                days=days, limit=limit, dry_run=dry_run
            )

            # Update run record with counts
            run.meetings_scanned = ai1_results.get("scanned", 0)
            run.meetings_tagged_created = ai1_results.get("created", 0)
            run.meetings_tagged_cached = ai1_results.get("cached", 0)
            run.meetings_tagged_fallback = ai1_results.get("fallback", 0)

            run.tasks_scanned = ai3_results.get("scanned", 0)
            run.tasks_review_queue = ai3_results.get("review_queue_count", 0)
            run.ai_reviews_created = ai3_results.get("created", 0)
            run.ai_reviews_cached = ai3_results.get("cached", 0)
            run.ai_reviews_fallback = ai3_results.get("fallback", 0)

            run.requirement_checks_created = ai2_results.get("created", 0)
            run.requirement_checks_cached = ai2_results.get("cached", 0)
            run.requirement_checks_fallback = ai2_results.get("fallback", 0)

            run.errors_count = (
                ai1_results.get("errors", 0)
                + ai3_results.get("errors", 0)
                + ai2_results.get("errors", 0)
            )

            # Collect error samples (capped at 10)
            error_samples = []
            error_samples.extend(ai1_results.get("error_samples", [])[:5])
            error_samples.extend(ai3_results.get("error_samples", [])[:3])
            error_samples.extend(ai2_results.get("error_samples", [])[:2])
            run.error_samples = error_samples[:10]

            # Determine status
            if run.errors_count > 0 and run.errors_count < (
                run.meetings_scanned + run.tasks_scanned
            ):
                run.status = AIOperationsRun.RunStatus.PARTIAL
            elif run.errors_count >= (run.meetings_scanned + run.tasks_scanned):
                run.status = AIOperationsRun.RunStatus.FAILED
            else:
                run.status = AIOperationsRun.RunStatus.SUCCESS

            run.finished_at = timezone.now()
            run.save()

            return {
                "status": "success",
                "run_id": run.id,
                "ai1": ai1_results,
                "ai2": ai2_results,
                "ai3": ai3_results,
            }

        except Exception as e:
            logger.error(f"Error in AI operations run: {e}", exc_info=True)
            run.status = AIOperationsRun.RunStatus.FAILED
            run.errors_count += 1
            run.error_samples = [str(e)[:200]]  # Cap error message length
            run.finished_at = timezone.now()
            run.save()

            return {"status": "failed", "run_id": run.id, "error": str(e)}

    def _run_ai1_meeting_tagging(
        self, days: int, limit: Optional[int], service: Optional[str], dry_run: bool
    ) -> Dict[str, Any]:
        """Run AI-1 meeting activity tagging"""
        try:
            from ai_services.services.meeting_activity_tagging_service import \
                MeetingActivityTaggingService

            cutoff_date = timezone.now() - timedelta(days=days)
            meetings_qs = Meeting.objects.filter(start_time__gte=cutoff_date).order_by(
                "-start_time"
            )

            if service:
                service_name = (
                    f"gotomeeting_{service}"
                    if not service.startswith("gotomeeting_")
                    else service
                )
                meetings_qs = meetings_qs.filter(service_name=service_name)

            if limit:
                meetings_qs = meetings_qs[:limit]

            meetings = list(meetings_qs)
            scanned = len(meetings)

            tagging_service = MeetingActivityTaggingService()
            created = 0
            cached = 0
            fallback = 0
            errors = 0
            error_samples = []

            for meeting in meetings:
                try:
                    if dry_run:
                        # Just check if suggestion exists
                        from ai_services.models import \
                            MeetingActivityTagSuggestion

                        existing = MeetingActivityTagSuggestion.objects.filter(
                            meeting=meeting, is_active=True
                        ).first()
                        if existing:
                            cached += 1
                        else:
                            created += 1
                    else:
                        suggestion = tagging_service.suggest_activity_type(
                            meeting, force=False
                        )
                        if suggestion:
                            if suggestion.provider == "fallback":
                                fallback += 1
                            elif suggestion.created_at == suggestion.updated_at:
                                created += 1
                            else:
                                cached += 1
                except Exception as e:
                    errors += 1
                    if len(error_samples) < 5:
                        error_samples.append(f"Meeting {meeting.id}: {str(e)[:100]}")
                    logger.warning(f"Error tagging meeting {meeting.id}: {e}")

            return {
                "scanned": scanned,
                "created": created,
                "cached": cached,
                "fallback": fallback,
                "errors": errors,
                "error_samples": error_samples,
            }

        except Exception as e:
            logger.error(f"Error in AI-1 meeting tagging: {e}", exc_info=True)
            return {
                "scanned": 0,
                "created": 0,
                "cached": 0,
                "fallback": 0,
                "errors": 1,
                "error_samples": [str(e)[:100]],
            }

    def _run_ai3_review_suggestions(
        self, days: int, limit: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Run AI-3 review suggestions for tasks in review queue"""
        try:
            from management.services.checklist_evaluation_service import \
                ChecklistEvaluationService
            from management.services.task_ai_review_service import \
                TaskAIReviewService

            cutoff_date = timezone.now() - timedelta(days=days)

            # Get tasks that need review (similar to daf_review_view logic)
            tasks_qs = Task.objects.filter(
                is_active=True, created_at__gte=cutoff_date
            ).select_related("employee", "activity_type", "requirement")

            if limit:
                tasks_qs = tasks_qs[:limit]

            tasks = list(tasks_qs)
            scanned = len(tasks)

            # Filter to tasks that need review (quality < 0.8, missing evidence, etc.)
            eval_service = ChecklistEvaluationService()
            review_queue_tasks = []

            for task in tasks:
                try:
                    quality_result = eval_service.get_task_quality_score(task)
                    quality_score = quality_result.get("quality_score", 0.0)
                    evidence_coverage = quality_result.get("evidence_coverage", 0.0)

                    # Task needs review if quality < 0.8 or evidence coverage < 0.7
                    if quality_score < 0.8 or evidence_coverage < 0.7:
                        review_queue_tasks.append(task)
                except Exception:
                    pass

            review_queue_count = len(review_queue_tasks)

            review_service = TaskAIReviewService()
            created = 0
            cached = 0
            fallback = 0
            errors = 0
            error_samples = []

            for task in review_queue_tasks:
                try:
                    if dry_run:
                        # Just check if suggestion exists
                        existing = TaskAIReviewSuggestion.objects.filter(
                            task=task, is_active=True, expires_at__gt=timezone.now()
                        ).first()
                        if existing:
                            cached += 1
                        else:
                            created += 1
                    else:
                        suggestion = review_service.generate_review_suggestion(
                            task, force=False
                        )
                        if suggestion:
                            if suggestion.provider == "fallback":
                                fallback += 1
                            else:
                                # Check if it was cached (created_at == updated_at means new)
                                from django.db.models import F

                                if TaskAIReviewSuggestion.objects.filter(
                                    id=suggestion.id, created_at=F("updated_at")
                                ).exists():
                                    created += 1
                                else:
                                    cached += 1
                except Exception as e:
                    errors += 1
                    if len(error_samples) < 3:
                        error_samples.append(f"Task {task.id}: {str(e)[:100]}")
                    logger.warning(
                        f"Error generating review suggestion for task {task.id}: {e}"
                    )

            # Also count TaskMeetingLinkSuggestion (AI-3 task↔meeting link suggestions)
            from ai_services.models import TaskMeetingLinkSuggestion

            link_suggestions_created = TaskMeetingLinkSuggestion.objects.filter(
                created_at__gte=cutoff_date, is_active=True
            ).count()

            # Count tasks with suggestions in review queue
            tasks_with_review_suggestions = (
                TaskMeetingLinkSuggestion.objects.filter(
                    status=TaskMeetingLinkSuggestion.SuggestionStatus.QUEUED_FOR_REVIEW,
                    is_active=True,
                )
                .values_list("task_id", flat=True)
                .distinct()
                .count()
            )

            # Combine counts: TaskAIReviewSuggestion + TaskMeetingLinkSuggestion
            total_created = created + link_suggestions_created
            total_review_queue = review_queue_count + tasks_with_review_suggestions

            return {
                "scanned": scanned,
                "review_queue_count": total_review_queue,
                "created": total_created,
                "cached": cached,
                "fallback": fallback,
                "errors": errors,
                "error_samples": error_samples,
            }

        except Exception as e:
            logger.error(f"Error in AI-3 review suggestions: {e}", exc_info=True)
            return {
                "scanned": 0,
                "review_queue_count": 0,
                "created": 0,
                "cached": 0,
                "fallback": 0,
                "errors": 1,
                "error_samples": [str(e)[:100]],
            }

    def _run_ai2_requirement_checks(
        self, days: int, limit: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Run AI-2 requirement match checks (shadow mode only)"""
        try:
            from management.services.requirement_match_service import \
                RequirementMatchService

            cutoff_date = timezone.now() - timedelta(days=days)

            # Get tasks with requirements that were recently updated
            tasks_qs = Task.objects.filter(
                is_active=True, requirement__isnull=False, updated_at__gte=cutoff_date
            ).select_related("requirement")

            if limit:
                tasks_qs = tasks_qs[:limit]

            tasks = list(tasks_qs)
            scanned = len(tasks)

            req_service = RequirementMatchService()
            created = 0
            cached = 0
            fallback = 0
            errors = 0
            error_samples = []

            for task in tasks:
                if not task.requirement:
                    continue

                try:
                    if dry_run:
                        # Just check if check exists
                        existing = (
                            RequirementMatchCheck.objects.filter(
                                task=task, requirement=task.requirement
                            )
                            .order_by("-created_at")
                            .first()
                        )
                        if existing:
                            cached += 1
                        else:
                            created += 1
                    else:
                        result = req_service.verify_requirement_match(
                            task, task.requirement
                        )
                        if result:
                            if result.get("fallback_used", False):
                                fallback += 1
                            else:
                                # Check if new check was created
                                latest_check = (
                                    RequirementMatchCheck.objects.filter(
                                        task=task, requirement=task.requirement
                                    )
                                    .order_by("-created_at")
                                    .first()
                                )

                                if (
                                    latest_check
                                    and latest_check.created_at >= cutoff_date
                                ):
                                    created += 1
                                else:
                                    cached += 1
                except Exception as e:
                    errors += 1
                    if len(error_samples) < 2:
                        error_samples.append(f"Task {task.id}: {str(e)[:100]}")
                    logger.warning(
                        f"Error checking requirement match for task {task.id}: {e}"
                    )

            return {
                "scanned": scanned,
                "created": created,
                "cached": cached,
                "fallback": fallback,
                "errors": errors,
                "error_samples": error_samples,
            }

        except Exception as e:
            logger.error(f"Error in AI-2 requirement checks: {e}", exc_info=True)
            return {
                "scanned": 0,
                "created": 0,
                "cached": 0,
                "fallback": 0,
                "errors": 1,
                "error_samples": [str(e)[:100]],
            }
