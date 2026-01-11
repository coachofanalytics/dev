"""
Meeting Host Inference Utility

Deterministic inference of probable meeting host from attendee names.
No AI calls - uses name normalization and matching heuristics.

Usage:
    from ai_services.utils.meeting_host_inference import infer_probable_host
    
    result = infer_probable_host(meeting, employees_queryset)
    if result[0]:
        employee_id, confidence, reasons = result
        print(f"Probable host: {employee_id} (confidence: {confidence:.2f})")
"""

import logging
from typing import List, Optional, Tuple

from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
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


def calculate_name_match_score(
    attendee_name: str, employee_first_name: str, employee_last_name: str
) -> Tuple[float, str]:
    """
    Calculate name match score between attendee name and employee name.

    Returns:
        Tuple of (score: float, reason: str)
    """
    if not attendee_name or not employee_first_name:
        return (0.0, "missing_name")

    # Normalize names
    attendee_normalized = normalize_name(attendee_name)
    employee_first_normalized = normalize_name(employee_first_name)
    employee_last_normalized = (
        normalize_name(employee_last_name) if employee_last_name else ""
    )
    employee_full_normalized = (
        f"{employee_first_normalized} {employee_last_normalized}".strip()
    )

    # Split attendee name into tokens
    attendee_tokens = set(attendee_normalized.split())
    if not attendee_tokens:
        return (0.0, "empty_attendee_name")

    # Check full name match (0.95)
    if attendee_normalized == employee_full_normalized:
        return (0.95, "exact_full_name_match")

    # Check if attendee name contains both first and last
    has_first = employee_first_normalized in attendee_tokens
    has_last = (
        employee_last_normalized in attendee_tokens
        if employee_last_normalized
        else False
    )

    if has_first and has_last:
        return (0.95, "full_name_tokens_match")

    # Check first name + last initial (0.85)
    if has_first and employee_last_normalized:
        last_initial = (
            employee_last_normalized[0] if len(employee_last_normalized) > 0 else ""
        )
        for token in attendee_tokens:
            if token.startswith(last_initial) and len(token) > 1:
                return (0.85, "first_name_last_initial_match")

    # Check first name only (0.70) - but uniqueness will be checked separately
    if has_first:
        return (0.70, "first_name_only_match")

    return (0.0, "no_match")


def is_first_name_unique(
    first_name: str,
    employees_queryset: QuerySet,
    exclude_employee_id: Optional[int] = None,
) -> bool:
    """
    Check if first name is unique among employees in queryset.

    Args:
        first_name: First name to check
        employees_queryset: QuerySet of employees to check against
        exclude_employee_id: Optional employee ID to exclude from check

    Returns:
        True if only one employee has this first name
    """
    if not first_name:
        return False

    first_name_normalized = normalize_name(first_name)
    matching_employees = employees_queryset.filter(
        first_name__iexact=first_name_normalized
    )

    if exclude_employee_id:
        matching_employees = matching_employees.exclude(id=exclude_employee_id)

    count = matching_employees.count()
    return count == 1


def infer_probable_host(
    meeting, employees_queryset: QuerySet
) -> Tuple[Optional[int], float, List[str]]:
    """
    Infer probable meeting host from attendee names.

    Deterministic inference using name normalization and matching heuristics.
    No AI calls.

    Confidence heuristics:
    - exact full-name match: 0.95
    - unique first-name match among employees: 0.85
    - partial/approx match: 0.70

    Args:
        meeting: Meeting instance (must have attendees relationship or attendee fields)
        employees_queryset: QuerySet of employees to match against

    Returns:
        Tuple of:
        - employee_id (int or None): ID of probable host, or None if no match
        - confidence (float): Confidence score 0.0-1.0
        - reasons (list[str]): List of explanation strings
    """
    try:
        # Get attendee names from MeetingAttendee records
        attendee_names = []

        if hasattr(meeting, "attendees"):
            # Use MeetingAttendee relationship
            attendees = meeting.attendees.all()
            for attendee in attendees:
                if attendee.attendee_name:
                    attendee_names.append(attendee.attendee_name)
        elif hasattr(meeting, "attendeeNames"):
            # Fallback: check if meeting has attendeeNames field (legacy)
            attendee_names_raw = meeting.attendeeNames
            if isinstance(attendee_names_raw, list):
                attendee_names = [name for name in attendee_names_raw if name]
            elif isinstance(attendee_names_raw, str):
                # Try to parse if it's a JSON string
                try:
                    import json

                    attendee_names = json.loads(attendee_names_raw)
                except:
                    attendee_names = [attendee_names_raw] if attendee_names_raw else []

        if not attendee_names:
            return (None, 0.0, ["No attendee names found"])

        # Score each employee against attendee names
        best_match = None
        best_score = 0.0
        best_reasons = []

        for employee in employees_queryset:
            employee_first_name = employee.first_name or ""
            employee_last_name = employee.last_name or ""

            if not employee_first_name:
                continue

            # Score against all attendee names
            for attendee_name in attendee_names:
                score, reason = calculate_name_match_score(
                    attendee_name, employee_first_name, employee_last_name
                )

                # Adjust score based on uniqueness for first-name-only matches
                if score == 0.70 and reason == "first_name_only_match":
                    # Check if first name is unique
                    is_unique = is_first_name_unique(
                        employee_first_name,
                        employees_queryset,
                        exclude_employee_id=employee.id,
                    )
                    if is_unique:
                        score = 0.85
                        reason = "unique_first_name_match"
                    else:
                        # Not unique - lower confidence
                        score = 0.60
                        reason = "ambiguous_first_name_match"

                if score > best_score:
                    best_score = score
                    best_match = employee.id
                    best_reasons = [f"{reason} (attendee: {attendee_name})"]
                elif score == best_score and best_match != employee.id:
                    # Multiple employees with same score - ambiguous
                    best_match = None
                    best_score = 0.0
                    best_reasons = [
                        "Ambiguous: multiple employees match with same score"
                    ]

        if best_match and best_score >= 0.70:
            return (best_match, best_score, best_reasons)
        else:
            return (
                None,
                best_score,
                best_reasons if best_reasons else ["No confident match found"],
            )

    except Exception as e:
        logger.error(
            f"Error inferring probable host for meeting {meeting.id}: {e}",
            exc_info=True,
        )
        return (None, 0.0, [f"Error: {str(e)}"])
