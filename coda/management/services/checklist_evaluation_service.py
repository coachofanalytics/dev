"""
Checklist Evaluation Service

Evaluates task quality and checklist completion.
Used by DAF v2 view and quality gate service.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Q, Sum
from management.models import Task, TaskLinks

logger = logging.getLogger(__name__)


class ChecklistEvaluationService:
    """
    Service for evaluating task quality and checklist completion.

    Provides quality metrics including:
    - Evidence coverage (documents, links, meeting recordings)
    - Checklist completion
    - Duration validation
    - Overall quality score
    """

    def __init__(self):
        self.logger = logger

    def get_task_quality_score(
        self, task: Task, task_links: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get quality score for a task.

        Args:
            task: Task instance
            task_links: Optional QuerySet or list of TaskLinks.
                      If None, queries all active TaskLinks for the task.
                      Can be a QuerySet or list of TaskLink instances.

        Returns:
            Dict with:
            - quality_score: float (0.0 to 1.0, >= 0.8 is pass)
            - evidence_coverage: float (0.0 to 1.0, >= 0.95 is complete)
            - duration_factor: float (0.0 to 1.0+, >= 0.8 is ok)
            - total_duration_minutes: int
            - missing_checklist_items: List[str]
            - checklist_completion: float (0.0 to 1.0)
        """
        try:
            # Get evidence links
            if task_links is None:
                evidence_qs = TaskLinks.objects.filter(task=task, is_active=True)
                evidence_list = list(evidence_qs)
            elif hasattr(task_links, "__iter__") and not isinstance(
                task_links, (str, bytes)
            ):
                # Handle both QuerySet and list
                if hasattr(task_links, "exists"):
                    evidence_list = list(task_links)
                else:
                    evidence_list = list(task_links)
            else:
                evidence_list = []

            # Count evidence items
            evidence_count = len(evidence_list)

            # Calculate evidence coverage
            # Complete if: has link OR has doc OR has drive_link
            has_link = any(link.link for link in evidence_list)
            has_doc = any(
                link.doc and link.doc.name != "None" for link in evidence_list
            )
            has_drive = any(link.drive_link for link in evidence_list)

            has_usable_evidence = has_link or has_doc or has_drive

            # Evidence coverage: 1.0 if has usable evidence, 0.5 if partial, 0.0 if none
            if has_usable_evidence:
                # Check if evidence is "complete" (has multiple items or comprehensive)
                if (
                    evidence_count >= 2
                    or (has_link and has_doc)
                    or (has_link and has_drive)
                ):
                    evidence_coverage = 1.0
                elif evidence_count == 1:
                    evidence_coverage = 0.7  # Single evidence item
                else:
                    evidence_coverage = 0.5  # Has evidence but minimal
            else:
                evidence_coverage = 0.0

            # Calculate duration factor
            # For meeting-based tasks, check if meeting duration meets requirements
            total_duration_minutes = 0
            for link in evidence_list:
                # Try to get duration from meeting if linked
                # For now, assume each evidence item contributes some duration
                if link.link and "gotomeeting" in link.link.lower():
                    # If it's a meeting link, assume minimum meeting duration
                    total_duration_minutes += 30  # Default: 30 minutes per meeting
                elif link.drive_link:
                    # Drive link might have recorded meeting
                    total_duration_minutes += 15  # Default: 15 minutes
                else:
                    # Other evidence (documents, etc.)
                    total_duration_minutes += 5  # Default: 5 minutes

            # Duration factor: 1.0 if >= 30 minutes, proportional otherwise
            # For meeting-based activities, need at least 30 minutes total
            if total_duration_minutes >= 30:
                duration_factor = 1.0
            elif total_duration_minutes > 0:
                duration_factor = float(total_duration_minutes) / 30.0
            else:
                duration_factor = 0.0

            # Evaluate checklist items
            missing_checklist_items = []
            checklist_completion = 0.0

            # Basic checklist: evidence + description + meeting (if required)
            checklist_total = 3  # link/doc, description, meeting
            checklist_completed = 0

            # 1. Evidence (link or doc)
            if has_usable_evidence:
                checklist_completed += 1
            else:
                missing_checklist_items.append("Evidence (document or link) required")

            # 2. Description
            has_description = any(
                link.description and link.description.strip() for link in evidence_list
            )
            if has_description or task.description:
                checklist_completed += 1
            else:
                missing_checklist_items.append("Description required")

            # 3. Meeting evidence (if task requires meeting)
            requires_meeting = getattr(task, "requires_meeting", True)
            has_meeting_evidence = any(
                link.link
                and (
                    "gotomeeting" in link.link.lower() or "meeting" in link.link.lower()
                )
                for link in evidence_list
            )

            if not requires_meeting:
                # Meeting not required, always pass this item
                checklist_completed += 1
            elif has_meeting_evidence:
                checklist_completed += 1
            else:
                missing_checklist_items.append("Meeting recording required")

            checklist_completion = (
                float(checklist_completed) / float(checklist_total)
                if checklist_total > 0
                else 0.0
            )

            # Calculate overall quality score
            # Weighted average: evidence (40%), checklist (30%), duration (30%)
            quality_score = (
                evidence_coverage * 0.4
                + checklist_completion * 0.3
                + min(1.0, duration_factor) * 0.3
            )

            # Ensure quality score is in [0.0, 1.0]
            quality_score = max(0.0, min(1.0, quality_score))

            return {
                "quality_score": quality_score,
                "evidence_coverage": evidence_coverage,
                "duration_factor": duration_factor,
                "total_duration_minutes": total_duration_minutes,
                "missing_checklist_items": missing_checklist_items,
                "checklist_completion": checklist_completion,
                "evidence_count": evidence_count,
            }

        except Exception as e:
            self.logger.error(
                f"Error evaluating quality for task {task.id}: {e}", exc_info=True
            )
            # Return safe defaults
            return {
                "quality_score": 0.0,
                "evidence_coverage": 0.0,
                "duration_factor": 0.0,
                "total_duration_minutes": 0,
                "missing_checklist_items": ["Error evaluating quality"],
                "checklist_completion": 0.0,
                "evidence_count": 0,
            }

    def evaluate_checklist(
        self, task: Task, task_links: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate checklist completion for a task.

        Args:
            task: Task instance
            task_links: Optional QuerySet or list of TaskLinks

        Returns:
            Dict with:
            - completed: List[str] (completed items)
            - missing: List[str] (missing items)
            - completion_rate: float (0.0 to 1.0)
        """
        quality_result = self.get_task_quality_score(task, task_links)

        # Get all checklist items
        all_items = [
            "Evidence (document or link)",
            "Description",
            "Meeting recording" if getattr(task, "requires_meeting", True) else None,
        ]
        all_items = [item for item in all_items if item]  # Remove None

        missing_items = quality_result.get("missing_checklist_items", [])
        completed_items = [item for item in all_items if item not in missing_items]

        completion_rate = quality_result.get("checklist_completion", 0.0)

        return {
            "completed": completed_items,
            "missing": missing_items,
            "completion_rate": completion_rate,
        }
