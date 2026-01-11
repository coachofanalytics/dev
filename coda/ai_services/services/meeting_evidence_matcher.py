"""
Meeting Evidence Matcher Service.

Matches TaskLinks evidence URLs to Meeting records using normalized URL matching
and optional topic-based heuristics.

Phase 2B: Reliable DB-only matching layer for TaskLinks -> Meeting duration lookup.
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from ai_services.models import Meeting
from ai_services.utils.meeting_normalizer import (
    extract_candidate_activity_tags, extract_requirement_code, normalize_topic,
    normalize_url)
from django.db.models import Q, QuerySet
from django.utils import timezone
from management.models import Task, TaskLinks

logger = logging.getLogger(__name__)


class MeetingEvidenceMatcher:
    """
    Service for matching TaskLinks evidence to Meeting records.

    Primary strategy: URL-based matching using normalized URLs.
    Fallback strategy: Topic + time window matching (optional, guarded, stricter rules).
    """

    def __init__(
        self,
        enable_topic_fallback: bool = True,
        time_window_days: int = 2,
        service_name: str = None,
        require_activity_tag_overlap: bool = True,
        require_employee_match: bool = False,
    ):
        """
        Initialize matcher.

        Args:
            enable_topic_fallback: Whether to attempt topic-based matching if URL match fails
            time_window_days: Days before/after task date to search for meetings (default: 2)
            service_name: Optional service name filter (e.g., 'gotomeeting_external')
            require_activity_tag_overlap: Require candidate activity tags to overlap (default: True, stricter)
            require_employee_match: Require employee name/department match if available (default: False, optional)
        """
        self.enable_topic_fallback = enable_topic_fallback
        self.time_window_days = time_window_days
        self.service_name = service_name
        self.require_activity_tag_overlap = require_activity_tag_overlap
        self.require_employee_match = require_employee_match
        self.logger = logger

    def find_meetings_for_task(self, task: Task) -> QuerySet[Meeting]:
        """
        Find meetings associated with a task based on evidence URLs and optional heuristics.

        Args:
            task: Task instance to find meetings for

        Returns:
            QuerySet of Meeting objects, ordered by start_time desc
        """
        # Primary: URL-based matching (HIGH confidence)
        meetings = self._match_by_urls(task)

        # Fallback: Topic + time window (only if URL match found nothing and enabled)
        # Topic matches have LOW confidence
        if not meetings.exists() and self.enable_topic_fallback:
            meetings = self._match_by_topic_and_time(task)

        return meetings.order_by("-start_time")

    def _match_by_urls(self, task: Task) -> QuerySet[Meeting]:
        """
        Match meetings by normalizing and comparing evidence URLs.

        Strategy:
        1. Collect all evidence URLs from TaskLinks (link + drive_link)
        2. Normalize each URL
        3. Query Meeting where recording_url or download_url matches normalized URLs

        Args:
            task: Task instance

        Returns:
            QuerySet of matched Meeting objects
        """
        try:
            # Collect evidence URLs from TaskLinks
            task_links = TaskLinks.objects.filter(task=task, is_active=True)

            evidence_urls = []
            for task_link in task_links:
                if task_link.link:
                    evidence_urls.append(task_link.link.strip())
                if task_link.drive_link:
                    evidence_urls.append(task_link.drive_link.strip())

            if not evidence_urls:
                return Meeting.objects.none()

            # Normalize all evidence URLs
            normalized_urls = []
            for url in evidence_urls:
                normalized = normalize_url(url)
                if normalized:
                    normalized_urls.append(normalized)

            if not normalized_urls:
                return Meeting.objects.none()

            # Query meetings where recording_url or download_url matches any normalized URL
            # Note: Meeting.recording_url and download_url are already normalized during save
            # Phase 2C+1: Filter by service_name if provided
            query = Q(recording_url__in=normalized_urls) | Q(
                download_url__in=normalized_urls
            )
            if self.service_name:
                query = query & Q(service_name=self.service_name)
            # If service_name not specified, don't filter by service_name (backward compatible)

            meetings = Meeting.objects.filter(query).distinct()

            if meetings.exists():
                self.logger.debug(
                    f"Matched {meetings.count()} meeting(s) for task {task.id} via URL matching"
                )

            return meetings

        except Exception as e:
            self.logger.error(
                f"Error in URL matching for task {task.id}: {e}", exc_info=True
            )
            return Meeting.objects.none()

    def _match_by_topic_and_time(self, task: Task) -> QuerySet[Meeting]:
        """
        Fallback: Match meetings by topic similarity within a time window.

        Strategy:
        1. Determine task date (from submission, duedate, or created_at)
        2. Define time window (task_date ± time_window_days)
        3. Get candidate activity tags from task's activity_type
        4. Query meetings in time window
        5. Filter by topic similarity (normalized topic + candidate tags)

        Args:
            task: Task instance

        Returns:
            QuerySet of matched Meeting objects (limited to top matches)
        """
        try:
            # Determine task date
            task_date = self._get_task_date(task)
            if not task_date:
                return Meeting.objects.none()

            # Define time window
            start_date = task_date - timedelta(days=self.time_window_days)
            end_date = task_date + timedelta(days=self.time_window_days)

            # Query meetings in time window (Phase 2C+1: Filter by service_name if provided)
            query = Q(
                start_time__date__gte=start_date.date(),
                start_time__date__lte=end_date.date(),
            )
            if self.service_name:
                query = query & Q(service_name=self.service_name)
            # If service_name not specified, don't filter by service_name (backward compatible)

            meetings_in_window = Meeting.objects.filter(query)

            if not meetings_in_window.exists():
                return Meeting.objects.none()

            # Get candidate activity tags from task
            activity_tags = self._get_activity_tags_for_task(task)

            # Get requirement code from task if available (for REQ-#### matching)
            task_requirement_code = None
            if hasattr(task, "requirement") and task.requirement:
                # Requirement model uses id as identifier (__str__ returns 'CODA000' + str(id))
                # Extract REQ code format: REQ-{id}
                task_requirement_code = f"REQ-{task.requirement.id}"

            # Filter by topic similarity and requirement code
            # Confidence strategy:
            # - Topic fallback base: LOW (0.3-0.6 from _calculate_topic_confidence)
            # - REQ code match: boost to MEDIUM (0.7)
            # - REQ code mismatch: reduce significantly (0.1-0.2)
            matched_meetings = []
            for meeting in meetings_in_window:
                confidence = self._calculate_topic_confidence(
                    meeting, task, activity_tags
                )

                # Apply requirement code matching logic
                if task_requirement_code and meeting.requirement_code:
                    if (
                        task_requirement_code.upper()
                        == meeting.requirement_code.upper()
                    ):
                        # REQ codes match: boost confidence to MEDIUM
                        confidence = max(
                            confidence, 0.7
                        )  # MEDIUM confidence for topic+REQ match
                        self.logger.debug(
                            f"REQ code match: task {task.id} REQ={task_requirement_code} "
                            f"matches meeting {meeting.id} REQ={meeting.requirement_code} "
                            f"(confidence: {confidence:.2f})"
                        )
                    elif confidence > 0:
                        # REQ code mismatch: significantly reduce confidence
                        confidence = min(
                            confidence * 0.3, 0.2
                        )  # Cap at 0.2 for mismatches
                        self.logger.debug(
                            f"REQ code mismatch: task {task.id} REQ={task_requirement_code} "
                            f"vs meeting {meeting.id} REQ={meeting.requirement_code} "
                            f"(confidence reduced to: {confidence:.2f})"
                        )

                if confidence > 0:
                    matched_meetings.append((meeting, confidence))

            # Sort by confidence and return top matches (limit to 3 for safety)
            matched_meetings.sort(key=lambda x: x[1], reverse=True)
            top_matches = [m[0] for m in matched_meetings[:3]]

            if top_matches:
                self.logger.debug(
                    f"Matched {len(top_matches)} meeting(s) for task {task.id} via topic fallback"
                )
                # Return as QuerySet
                meeting_ids = [m.id for m in top_matches]
                return Meeting.objects.filter(id__in=meeting_ids)

            return Meeting.objects.none()

        except Exception as e:
            self.logger.error(
                f"Error in topic matching for task {task.id}: {e}", exc_info=True
            )
            return Meeting.objects.none()

    def _get_task_date(self, task: Task) -> Optional[timezone.datetime]:
        """
        Get task date from available fields.

        Priority: submission > duedate > created_at
        """
        # Check submission field (DateTimeField)
        if hasattr(task, "submission") and task.submission:
            # submission is a DateTimeField, return as-is
            return task.submission
        # Check duedate field (if it exists)
        if hasattr(task, "duedate") and task.duedate:
            # Convert to datetime if it's a date
            if isinstance(task.duedate, timezone.datetime):
                return task.duedate
            elif isinstance(task.duedate, timezone.date):
                return timezone.make_aware(
                    timezone.datetime.combine(
                        task.duedate, timezone.datetime.min.time()
                    )
                )
        # Check created_at (TimeStampedModel provides this)
        if hasattr(task, "created_at") and task.created_at:
            return task.created_at
        # Fallback: use current date (not ideal, but safe)
        return timezone.now()

    def _get_activity_tags_for_task(self, task: Task) -> List[str]:
        """
        Get candidate activity tags from task's activity_type.

        Returns list of tag strings (e.g., ['pbr', 'client_training'])
        """
        if not task.activity_type:
            return []

        # Use activity_type.name to extract tags
        activity_name = task.activity_type.name if task.activity_type.name else ""
        if activity_name:
            return extract_candidate_activity_tags(activity_name)

        return []

    def _calculate_topic_confidence(
        self, meeting: Meeting, task: Task, activity_tags: List[str]
    ) -> float:
        """
        Calculate confidence score (0.0-1.0) for topic-based matching (Phase 2C+1: Stricter rules).

        Factors:
        - Meeting topic normalized vs task activity tags (REQUIRED if require_activity_tag_overlap=True)
        - Meeting topic normalized vs task title/description (if available)
        - Employee name/department match (OPTIONAL if require_employee_match=True)

        Returns:
            Confidence score (0.0 = no match, 1.0 = perfect match)
        """
        confidence = 0.0

        # Use stored normalized topic if available, otherwise compute
        meeting_topic_normalized = (
            meeting.topic_normalized
            if meeting.topic_normalized
            else normalize_topic(meeting.topic)
        )
        meeting_tags = extract_candidate_activity_tags(meeting.topic)

        # Factor 1: Activity tag overlap (REQUIRED if require_activity_tag_overlap=True)
        if activity_tags and meeting_tags:
            overlap = set(activity_tags) & set(meeting_tags)
            if overlap:
                # Confidence based on overlap ratio
                tag_overlap_score = len(overlap) / max(
                    len(activity_tags), len(meeting_tags)
                )
                confidence += 0.6 * tag_overlap_score
            elif self.require_activity_tag_overlap:
                # Stricter: require overlap, return 0 if no overlap
                return 0.0
        elif self.require_activity_tag_overlap and (
            not activity_tags or not meeting_tags
        ):
            # Stricter: require both tags available and overlap, return 0 if missing
            return 0.0

        # Factor 2: Topic similarity (simple containment check)
        if hasattr(task, "description") and task.description:
            task_desc_normalized = normalize_topic(task.description)
            if task_desc_normalized and meeting_topic_normalized:
                # Check if normalized topics share significant words
                task_words = set(task_desc_normalized.split())
                meeting_words = set(meeting_topic_normalized.split())
                if task_words and meeting_words:
                    overlap_ratio = len(task_words & meeting_words) / max(
                        len(task_words), len(meeting_words)
                    )
                    confidence += 0.3 * overlap_ratio

        # Factor 3: Employee name/department match (OPTIONAL if require_employee_match=True)
        if self.require_employee_match and hasattr(task, "employee") and task.employee:
            employee_name_lower = (
                task.employee.get_full_name().lower()
                if hasattr(task.employee, "get_full_name")
                and task.employee.get_full_name()
                else task.employee.email.lower() if task.employee.email else ""
            )

            # Check if employee name appears in meeting topic or attendees
            if employee_name_lower and meeting_topic_normalized:
                # Simple check: employee first name or last name in topic
                employee_parts = employee_name_lower.split()
                if any(
                    part in meeting_topic_normalized
                    for part in employee_parts
                    if len(part) > 2
                ):
                    confidence += 0.1

            # Check department if available
            if (
                hasattr(task, "department")
                and task.department
                and hasattr(task.department, "name")
            ):
                dept_name_lower = task.department.name.lower()
                if dept_name_lower and dept_name_lower in meeting_topic_normalized:
                    confidence += 0.1
        elif self.require_employee_match:
            # If employee matching is required but no employee info available, reduce confidence
            confidence *= 0.5

        return min(1.0, confidence)

    def _get_match_reason(
        self, meeting: Meeting, task: Task, activity_tags: List[str], confidence: float
    ) -> str:
        """
        Generate human-readable reason for topic-based match (for debug output).

        Phase 2C+1: Debug output for match_tasklinks_to_meetings --verbose
        """
        reasons = []

        # Use stored normalized topic if available, otherwise compute
        meeting_topic_normalized = (
            meeting.topic_normalized
            if meeting.topic_normalized
            else normalize_topic(meeting.topic)
        )
        meeting_tags = extract_candidate_activity_tags(meeting.topic)

        # Tag overlap reason
        if activity_tags and meeting_tags:
            overlap = set(activity_tags) & set(meeting_tags)
            if overlap:
                reasons.append(f"tag overlap: {', '.join(overlap)}")

        # Topic similarity reason
        if hasattr(task, "description") and task.description:
            task_desc_normalized = normalize_topic(task.description)
            if task_desc_normalized and meeting_topic_normalized:
                task_words = set(task_desc_normalized.split())
                meeting_words = set(meeting_topic_normalized.split())
                if task_words and meeting_words:
                    common_words = task_words & meeting_words
                    if common_words:
                        reasons.append(
                            f"common words: {', '.join(list(common_words)[:3])}"
                        )

        # Employee/department match reason
        if hasattr(task, "employee") and task.employee:
            employee_name = (
                task.employee.get_full_name()
                if hasattr(task.employee, "get_full_name")
                and task.employee.get_full_name()
                else task.employee.email
            )
            if employee_name and employee_name.lower() in meeting_topic_normalized:
                reasons.append(f"employee match: {employee_name}")

        if (
            hasattr(task, "department")
            and task.department
            and hasattr(task.department, "name")
        ):
            dept_name = task.department.name
            if dept_name and dept_name.lower() in meeting_topic_normalized:
                reasons.append(f"department match: {dept_name}")

        return "; ".join(reasons) if reasons else f"confidence: {confidence:.2f}"

    def get_detailed_matches(self, task: Task) -> List[Dict[str, Any]]:
        """
        Get detailed match information for debugging/reporting.

        Returns:
            List of dicts with:
            - meeting: Meeting instance
            - match_type: 'url' or 'topic'
            - confidence: float (0.0-1.0)
        """
        matches = []

        # URL matches (HIGH confidence: 0.9-1.0)
        url_matches = self._match_by_urls(task)
        for meeting in url_matches:
            # Base confidence for URL match
            confidence = 0.9

            # Check if REQ codes also match (VERY HIGH confidence)
            task_requirement_code = None
            if hasattr(task, "requirement") and task.requirement:
                task_requirement_code = f"REQ-{task.requirement.id}"

            if task_requirement_code and meeting.requirement_code:
                if task_requirement_code.upper() == meeting.requirement_code.upper():
                    confidence = 1.0  # VERY HIGH: URL + REQ match
                else:
                    # URL matches but REQ mismatch: still high but note the issue
                    confidence = 0.85
                    self.logger.warning(
                        f"URL match but REQ mismatch: task {task.id} REQ={task_requirement_code} "
                        f"vs meeting {meeting.id} REQ={meeting.requirement_code}"
                    )

            matches.append(
                {
                    "meeting": meeting,
                    "match_type": "url",
                    "confidence": confidence,
                    "requirement_code_match": (
                        (
                            task_requirement_code
                            and meeting.requirement_code
                            and task_requirement_code.upper()
                            == meeting.requirement_code.upper()
                        )
                        if task_requirement_code
                        else None
                    ),
                }
            )

        # Topic matches (only if no URL matches)
        if not url_matches.exists() and self.enable_topic_fallback:
            task_date = self._get_task_date(task)
            if task_date:
                start_date = task_date - timedelta(days=self.time_window_days)
                end_date = task_date + timedelta(days=self.time_window_days)

                # Phase 2C+1: Filter by service_name if provided
                query = Q(
                    start_time__date__gte=start_date.date(),
                    start_time__date__lte=end_date.date(),
                )
                if self.service_name:
                    query = query & Q(service_name=self.service_name)
                # If service_name not specified, don't filter by service_name (backward compatible)

                meetings_in_window = Meeting.objects.filter(query)

                activity_tags = self._get_activity_tags_for_task(task)

                # Get requirement code for REQ matching
                task_requirement_code = None
                if hasattr(task, "requirement") and task.requirement:
                    task_requirement_code = f"REQ-{task.requirement.id}"

                for meeting in meetings_in_window:
                    confidence = self._calculate_topic_confidence(
                        meeting, task, activity_tags
                    )

                    # Apply REQ code matching (same logic as _match_by_topic_and_time)
                    req_code_match = None
                    if task_requirement_code and meeting.requirement_code:
                        if (
                            task_requirement_code.upper()
                            == meeting.requirement_code.upper()
                        ):
                            confidence = max(
                                confidence, 0.7
                            )  # MEDIUM for topic+REQ match
                            req_code_match = True
                        elif confidence > 0:
                            confidence = min(
                                confidence * 0.3, 0.2
                            )  # Reduce for mismatch
                            req_code_match = False

                    if confidence > 0:
                        # Phase 2C+1: Include match reason for debug output
                        match_reason = self._get_match_reason(
                            meeting, task, activity_tags, confidence
                        )
                        matches.append(
                            {
                                "meeting": meeting,
                                "match_type": "topic",
                                "confidence": confidence,
                                "match_reason": match_reason,
                                "requirement_code_match": req_code_match,
                            }
                        )

                # Sort by confidence
                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:3]  # Limit to top 3

        return matches
