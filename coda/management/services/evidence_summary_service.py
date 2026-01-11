"""
Evidence Summary Service - Single source of truth for evidence checks.

This service provides unified API for all evidence checks to prevent contradictions.
Used by DAF v2, compliance calculations, and task quality gates.

Backward compatible: Returns safe defaults if models/fields are missing.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from django.db.models import QuerySet

logger = logging.getLogger(__name__)

try:
    from management.models import Task, TaskLinks
except ImportError:
    logger.warning("Evidence summary service: Could not import Task/TaskLinks models")
    Task = None
    TaskLinks = None


def get_task_evidence_summary(
    task: Task,
    task_links: Optional[Union[QuerySet, List[Any]]] = None,
    meeting_match_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get evidence summary for a task.

    This is the single source of truth for all evidence checks.

    Args:
        task: Task instance
        task_links: Optional QuerySet or list of TaskLinks.
                  If None, queries all active TaskLinks for the task.
                  Can be a QuerySet or list of TaskLink instances.
        meeting_match_info: Optional dict from meeting matching logic

    Returns:
        dict with:
        - count_active: int (number of active TaskLinks)
        - count_usable: int (number of active TaskLinks with usable evidence: link/doc/drive_link)
        - items_qs: QuerySet/list of active TaskLinks
        - has_minimum: bool (True if at least one usable evidence exists)
        - status: 'missing' | 'partial' | 'complete' | 'auto_pending'
        - reasons_if_fail: List[str] (reasons why evidence is missing/partial)
        - has_auto_generated: bool (True if any TaskLink has is_auto_generated=True)
    """
    if Task is None or TaskLinks is None:
        # Backward compatible: return safe defaults if models not available
        return {
            "count_active": 0,
            "count_usable": 0,
            "items_qs": [],
            "has_minimum": False,
            "status": "missing",
            "reasons_if_fail": ["Models not available"],
            "has_auto_generated": False,
        }

    try:
        # Get evidence links
        if task_links is None:
            evidence_qs = TaskLinks.objects.filter(task=task, is_active=True)
            evidence_list = list(evidence_qs)
        elif hasattr(task_links, "__iter__") and not isinstance(
            task_links, (str, bytes)
        ):
            # Handle both QuerySet and list
            if hasattr(task_links, "filter"):
                # It's a QuerySet - ensure it's filtered to active only
                evidence_qs = (
                    task_links.filter(is_active=True)
                    if hasattr(task_links, "filter")
                    else task_links
                )
                evidence_list = (
                    list(evidence_qs) if hasattr(evidence_qs, "__iter__") else []
                )
            else:
                # It's a list - filter to active only
                evidence_list = [
                    link for link in task_links if getattr(link, "is_active", True)
                ]
        else:
            evidence_list = []

        # Count active evidence
        count_active = len(evidence_list)

        # Count usable evidence (has link OR doc OR drive_link)
        count_usable = 0
        has_auto_generated = False
        reasons_if_fail = []

        for link in evidence_list:
            # Check if evidence is usable (has link, doc, or drive_link)
            has_link = bool(getattr(link, "link", None))
            has_doc = (
                bool(getattr(link, "doc", None))
                and getattr(link, "doc", None) != "None"
            )
            has_drive = bool(getattr(link, "drive_link", None))

            if has_link or has_doc or has_drive:
                count_usable += 1

            # Check if auto-generated
            if getattr(link, "is_auto_generated", False):
                has_auto_generated = True

        # Determine status
        has_minimum = count_usable > 0

        if count_active == 0:
            status = "missing"
            reasons_if_fail = ["No evidence uploaded"]
        elif count_usable == 0:
            status = "missing"
            reasons_if_fail = [
                "Evidence exists but none is usable (missing link/doc/drive_link)"
            ]
        elif count_usable == 1:
            status = "partial"
            reasons_if_fail = [
                "Only one evidence item (may need more for complete evidence)"
            ]
        elif has_auto_generated and meeting_match_info:
            # Check if meeting is matched but TaskLinks not yet created (auto_pending)
            if meeting_match_info.get("has_match") and not has_minimum:
                status = "auto_pending"
                reasons_if_fail = ["Meeting matched but evidence not yet created"]
            else:
                status = "complete"
                reasons_if_fail = []
        else:
            status = "complete"
            reasons_if_fail = []

        # Get items_qs (QuerySet if available, otherwise list)
        if task_links is None:
            items_qs = TaskLinks.objects.filter(task=task, is_active=True)
        elif hasattr(task_links, "filter"):
            items_qs = (
                task_links.filter(is_active=True)
                if hasattr(task_links, "filter")
                else evidence_list
            )
        else:
            items_qs = evidence_list

        return {
            "count_active": count_active,
            "count_usable": count_usable,
            "items_qs": items_qs,
            "has_minimum": has_minimum,
            "status": status,
            "reasons_if_fail": reasons_if_fail,
            "has_auto_generated": has_auto_generated,
        }

    except Exception as e:
        logger.error(
            f"Error getting evidence summary for task {task.id if task else 'unknown'}: {e}",
            exc_info=True,
        )
        # Backward compatible: return safe defaults on error
        return {
            "count_active": 0,
            "count_usable": 0,
            "items_qs": [],
            "has_minimum": False,
            "status": "missing",
            "reasons_if_fail": [f"Error: {str(e)}"],
            "has_auto_generated": False,
        }
