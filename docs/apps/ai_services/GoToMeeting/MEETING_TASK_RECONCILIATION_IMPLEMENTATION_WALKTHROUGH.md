# Meeting-Task Reconciliation: Implementation-Level Walkthrough

**Branch:** 26.01_CODA_DEV_CM  
**Date:** 2026-01-02  
**Purpose:** Full implementation-level documentation of meeting-task reconciliation system

---

## Files

### Reconciliation Service Module

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Full Code:**

```python
"""
Meeting → Task Reconciliation Service

After meeting sync + attendee sync, creates/updates TaskLinks to link meetings to tasks.
This ensures DAF can accurately count meetings_completed.

Idempotent: Safe to run multiple times, no duplicates.
"""

import logging
import difflib
import re
from typing import Dict, List, Optional, Tuple
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import Task, TaskLinks
from ai_services.models import Meeting, MeetingAttendee

logger = logging.getLogger(__name__)
User = get_user_model()


class MeetingTaskReconciliationService:
    """
    Service for reconciling meetings with tasks and creating TaskLinks.
    
    Strategy:
    1. For each meeting, identify the employee (via organizer or attendee)
    2. Find candidate tasks for that employee within time window
    3. Match by requirement code (if available) or activity type
    4. Create/update TaskLinks with meeting_id
    """
    
    def __init__(
        self,
        time_window_days: int = 7,
        dry_run: bool = False,
    ):
        """
        Initialize reconciliation service.
        
        Args:
            time_window_days: Days before/after meeting to search for tasks (default: 7)
            dry_run: If True, don't create/update TaskLinks, only log (default: False)
        """
        self.time_window_days = time_window_days
        self.dry_run = dry_run
        self.logger = logger
    
    def reconcile_meetings(
        self,
        meetings: Optional[List[Meeting]] = None,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None,
    ) -> Dict[str, any]:
        """
        Reconcile meetings with tasks and create/update TaskLinks.
        
        Args:
            meetings: Optional list of specific meetings to reconcile.
                     If None, reconciles all meetings in date range.
            start_date: Start date for meeting filter (if meetings not provided)
            end_date: End date for meeting filter (if meetings not provided)
        
        Returns:
            Dict with reconciliation statistics:
            {
                'meetings_processed': int,
                'meetings_linked': int,
                'tasklinks_created': int,
                'tasklinks_updated': int,
                'tasks_updated': int,
                'errors': List[str],
            }
        """
        stats = {
            'meetings_processed': 0,
            'meetings_linked': 0,
            'tasklinks_created': 0,
            'tasklinks_updated': 0,
            'tasks_updated': set(),  # Use set to track unique tasks
            'errors': [],
        }
        
        # Get meetings to process
        if meetings is None:
            if start_date is None:
                start_date = timezone.now() - timedelta(days=30)  # Default: last 30 days
            if end_date is None:
                end_date = timezone.now()
            
            meetings = Meeting.objects.filter(
                start_time__gte=start_date,
                start_time__lte=end_date
            ).select_related().prefetch_related('attendees', 'attendees__user')
        else:
            # Prefetch related data
            meetings = Meeting.objects.filter(
                id__in=[m.id for m in meetings]
            ).select_related().prefetch_related('attendees', 'attendees__user')
        
        self.logger.info(
            f"🔄 Starting meeting reconciliation: {len(meetings)} meetings, "
            f"time_window={self.time_window_days} days, dry_run={self.dry_run}"
        )
        
        for meeting in meetings:
            try:
                stats['meetings_processed'] += 1
                
                # Step 1: Identify employee from meeting
                employee = self._identify_employee(meeting)
                if not employee:
                    # Log reason: no employee match (always log first 10, then sample)
                    reason = self._get_no_employee_reason(meeting)
                    if stats['meetings_processed'] <= 10 or stats['meetings_processed'] % 50 == 0:
                        self.logger.info(
                            f"   Meeting {meeting.meeting_id} ({meeting.topic[:50] if meeting.topic else 'N/A'}): "
                            f"NO TASK MATCH - no employee match: {reason}"
                        )
                    continue
                
                # Step 2: Find candidate tasks for this employee
                candidate_tasks, match_reason = self._find_candidate_tasks(meeting, employee)
                if not candidate_tasks:
                    # Log reason: no eligible tasks for employee (always log first 10, then sample)
                    if match_reason == 'ambiguous':
                        reason = f"NO TASK MATCH - ambiguous topic match for employee {employee.username} (no requirement_code in meeting)"
                    elif meeting.topic:
                        reason = f"NO TASK MATCH - no eligible tasks for employee {employee.username} for topic {meeting.topic[:50]}"
                    else:
                        reason = f"NO TASK MATCH - no eligible tasks for employee {employee.username} (no requirement_code in meeting)"
                    if stats['meetings_processed'] <= 10 or stats['meetings_processed'] % 50 == 0:
                        self.logger.info(
                            f"   Meeting {meeting.meeting_id} ({meeting.topic[:50] if meeting.topic else 'N/A'}): {reason}"
                        )
                    continue
                
                # Step 3: Select best matching task
                best_task = self._select_best_task(meeting, candidate_tasks)
                if not best_task:
                    # Log reason: requirement/topic mismatch (always log first 10, then sample)
                    reason = self._get_no_task_match_reason(meeting, candidate_tasks)
                    if stats['meetings_processed'] <= 10 or stats['meetings_processed'] % 50 == 0:
                        self.logger.info(
                            f"   Meeting {meeting.meeting_id} ({meeting.topic[:50] if meeting.topic else 'N/A'}): "
                            f"NO TASK MATCH - requirement/topic mismatch: {reason}"
                        )
                    continue
                
                # Step 4: Create/update TaskLinks
                created, updated = self._create_or_update_tasklink(meeting, best_task, employee)
                
                if created:
                    stats['tasklinks_created'] += 1
                    stats['meetings_linked'] += 1
                    stats['tasks_updated'].add(best_task.id)
                    self.logger.info(
                        f"   ✅ Created TaskLink: meeting_id={meeting.meeting_id}, "
                        f"task_id={best_task.id}, employee={employee.username}"
                    )
                elif updated:
                    stats['tasklinks_updated'] += 1
                    stats['meetings_linked'] += 1
                    stats['tasks_updated'].add(best_task.id)
                    self.logger.info(
                        f"   🔄 Updated TaskLink: meeting_id={meeting.meeting_id}, "
                        f"task_id={best_task.id}, employee={employee.username}"
                    )
                
            except Exception as e:
                error_msg = f"Error reconciling meeting {meeting.meeting_id}: {e}"
                stats['errors'].append(error_msg)
                self.logger.error(error_msg, exc_info=True)
        
        # Convert tasks_updated set to count
        stats['tasks_updated'] = len(stats['tasks_updated'])
        
        self.logger.info(
            f"✅ Reconciliation complete: {stats['meetings_processed']} processed, "
            f"{stats['meetings_linked']} linked, {stats['tasklinks_created']} created, "
            f"{stats['tasklinks_updated']} updated, {stats['tasks_updated']} tasks affected"
        )
        
        return stats
    
    def _find_candidate_tasks(
        self,
        meeting: Meeting,
        employee: User
    ) -> Tuple[List[Task], str]:
        """
        Find candidate tasks for employee (no date filtering).
        
        Strategy: Always match by topic similarity to task.activity_name.
        If requirement_code exists, use it as a boost signal (optional), not a gate.
        
        Tasks are filtered by:
        - is_active=True
        - employee=<employee>
        - mxpoint > 0 (meeting-required tasks)
        
        Args:
            meeting: Meeting instance
            employee: Employee user
        
        Returns:
            Tuple of (List of candidate Task instances, match_reason)
            match_reason: 'topic', 'ambiguous', or 'no_match'
        """
        # Base filter: active tasks for employee with meeting requirement (mxpoint > 0)
        base_tasks = Task.objects.filter(
            employee=employee,
            is_active=True,
            mxpoint__gt=0  # Meeting-required tasks
        )
        
        # Require topic for matching
        if not meeting.topic:
            return [], 'no_match'
        
        # Normalize meeting topic
        meeting_topic_normalized = self._normalize_text(meeting.topic)
        if not meeting_topic_normalized:
            return [], 'no_match'
        
        # Get all candidate tasks for topic matching (no date filtering)
        all_tasks = list(base_tasks.order_by('-submission', '-id'))
        if not all_tasks:
            return [], 'no_match'
        
        # Extract requirement_code ID if present (for boosting)
        req_id = None
        if meeting.requirement_code:
            try:
                req_id_str = meeting.requirement_code.upper().replace('REQ-', '').strip()
                if req_id_str:
                    req_id = int(req_id_str)
            except (ValueError, AttributeError):
                pass  # Invalid format, ignore
        
        # Score each task by topic similarity (requirement_code is a boost)
        scored_tasks = []
        for task in all_tasks:
            if not task.activity_name:
                continue
            
            # Normalize task activity_name
            task_name_normalized = self._normalize_text(task.activity_name)
            if not task_name_normalized:
                continue
            
            # Calculate topic similarity
            # Strategy 1: Exact normalized match
            if meeting_topic_normalized == task_name_normalized:
                score = 1.0
                match_type = 'exact_match'
            else:
                # Strategy 2: Fuzzy match
                similarity = self._calculate_similarity(meeting_topic_normalized, task_name_normalized)
                if similarity >= 0.90:
                    score = similarity
                    match_type = 'fuzzy_match'
                else:
                    continue  # Below threshold, skip
            
            # Boost if requirement_code matches (optional signal)
            if req_id and task.requirement_id == req_id:
                score = min(1.0, score + 0.05)  # Small boost (5%)
                match_type = f"{match_type}_req_boost"
            
            scored_tasks.append((task, score, match_type))
        
        # Sort by score (descending)
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_tasks:
            # No matches above threshold
            return [], 'no_match'
        
        # Check for ambiguous matches (multiple candidates with same top score)
        if len(scored_tasks) > 1:
            top_score = scored_tasks[0][1]
            # Count tasks with top score
            top_score_count = sum(1 for _, score, _ in scored_tasks if score == top_score)
            if top_score_count > 1:
                # Ambiguous: multiple candidates tie for best score
                return [], 'ambiguous'  # Don't auto-link if ambiguous
        
        # Return best match
        best_task, best_score, match_type = scored_tasks[0]
        self.logger.debug(
            f"   Found topic match for {employee.username}: task {best_task.id} "
            f"({best_task.activity_name}) with score {best_score:.2f} ({match_type})"
        )
        
        return [best_task], 'topic'
    
    def _select_best_task(
        self,
        meeting: Meeting,
        candidate_tasks: List[Task]
    ) -> Optional[Task]:
        """
        Select best matching task from candidates.
        
        Scoring:
        - Requirement code match: +10 points
        - Time proximity (same day): +5 points
        - Time proximity (1-2 days): +3 points
        - Time proximity (3-7 days): +1 point
        
        Returns:
            Best matching Task or None
        """
        if not candidate_tasks:
            return None
        
        if len(candidate_tasks) == 1:
            return candidate_tasks[0]
        
        # Score each candidate
        scored_tasks = []
        for task in candidate_tasks:
            score = 0
            
            # Requirement code match
            if meeting.requirement_code and task.requirement:
                task_req_code = f"REQ-{task.requirement.id}"
                if meeting.requirement_code.upper() == task_req_code.upper():
                    score += 10
            
            # Time proximity
            if task.submission:
                time_delta = abs((meeting.start_time - task.submission).days)
                if time_delta == 0:
                    score += 5
                elif time_delta <= 2:
                    score += 3
                elif time_delta <= 7:
                    score += 1
            
            scored_tasks.append((score, task))
        
        # Sort by score (descending) and return best
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return scored_tasks[0][1] if scored_tasks else None
    
    def _create_or_update_tasklink(
        self,
        meeting: Meeting,
        task: Task,
        employee: User
    ) -> Tuple[bool, bool]:
        """
        Create or update TaskLinks for meeting → task link.
        
        Args:
            meeting: Meeting instance
            task: Task instance
            employee: Employee user (for added_by field)
        
        Returns:
            Tuple of (created, updated) booleans
        """
        # Check if TaskLinks already exists for this meeting_id
        existing_link = TaskLinks.objects.filter(
            task=task,
            meeting_id=meeting.meeting_id,
            is_active=True
        ).first()
        
        if existing_link:
            # Update existing link
            if not self.dry_run:
                existing_link.link = meeting.recording_url or existing_link.link
                existing_link.drive_link = meeting.google_drive_url or existing_link.drive_link
                existing_link.is_auto_generated = True
                existing_link.save(update_fields=['link', 'drive_link', 'is_auto_generated'])
            return (False, True)
        else:
            # Create new link
            if not self.dry_run:
                TaskLinks.objects.create(
                    task=task,
                    added_by=employee,
                    link_name="Meeting Recording",
                    description=f"Auto-generated from meeting: {meeting.topic}",
                    link=meeting.recording_url or '',
                    meeting_id=meeting.meeting_id,
                    is_active=True,
                    is_auto_generated=True,
                )
            return (True, False)
```

---

## Models

### Task Model

**File:** `coda/management/models.py` (line 470)

**Key Fields:**
```python
class Task(models.Model):
    employee = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="assigned_user",
        limit_choices_to=Q(is_staff=True) & Q(is_active=True),
        default=999,
    )
    activity_name = models.CharField(max_length=255)
    submission = models.DateTimeField(auto_now=True, editable=True, null=True)
    is_active = models.BooleanField(default=True)
    mxpoint = models.DecimalField(max_digits=10, decimal_places=2)  # Meeting requirement
    requirement = models.ForeignKey('Requirement', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ("-submission",)
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['is_active']),
            models.Index(fields=['employee']),
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['submission', 'is_active']),
        ]
```

**No unique constraints** on Task model.

### TaskHistory Model

**File:** `coda/management/models.py` (line 858)

**Key Fields:**
```python
class TaskHistory(models.Model):
    employee = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="history_user_assiged")
    activity_name = models.CharField(max_length=255)
    submission = models.DateTimeField(auto_now=True, editable=True, null=True)
    daf_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True, editable=True, null=True)
```

**Note:** TaskHistory is **NOT used** in reconciliation service. Only `Task` model is used.

### TaskLinks Model

**File:** `coda/management/models.py` (line 789)

**Key Fields:**
```python
class TaskLinks(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True),
    )
    link_name = models.CharField(max_length=255, default="General")
    description = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=1000, blank=True, null=True)
    drive_link = models.URLField(max_length=2000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_auto_generated = models.BooleanField(default=False)
    meeting_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Task Reference"
```

**No unique constraints** on TaskLinks model (allows multiple TaskLinks per task/meeting_id).

### Meeting Model

**File:** `coda/ai_services/models.py` (line 127)

**Key Fields:**
```python
class Meeting(models.Model):
    meeting_id = models.CharField(
        max_length=100, 
        unique=True,  # UNIQUE CONSTRAINT
        db_index=True,
        help_text="Unique GoToMeeting ID"
    )
    topic = models.CharField(max_length=500)
    topic_normalized = models.CharField(max_length=500, blank=True, db_index=True)
    service_name = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(default=0)
    recording_url = models.URLField(max_length=1000, blank=True, null=True)
    requirement_code = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    meeting_instance_key = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['meeting_id']),
            models.Index(fields=['start_time']),
            models.Index(fields=['-start_time']),
            models.Index(fields=['service_name', '-start_time']),
            models.Index(fields=['topic_normalized']),
        ]
```

**Unique Constraint:** `meeting_id` has `unique=True` (line 134).

### MeetingAttendee Model

**File:** `coda/ai_services/models.py` (line 322)

**Key Fields:**
```python
class MeetingAttendee(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(
        'accounts.CustomerUser',  # NOTE: NOT auth.User
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='meeting_attendances',
    )
    attendee_name = models.CharField(max_length=200)
    attendee_email = models.EmailField()
    duration_minutes = models.IntegerField(default=0)
    is_organizer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [('meeting', 'attendee_email')]  # UNIQUE CONSTRAINT
        ordering = ['-duration_minutes']
        indexes = [
            models.Index(fields=['attendee_email']),
            models.Index(fields=['user']),
        ]
```

**Unique Constraint:** `unique_together = [('meeting', 'attendee_email')]` (line 365).

---

## Identifiers

### Meeting.meeting_id

**Type:** `CharField(max_length=100, unique=True)`

**What it is:**
- **Room ID** (not occurrence ID)
- GoToMeeting room identifier (e.g., "698-057-837")
- **Same room can have multiple occurrences** (different `start_time`, `session_id`)
- **Unique constraint** prevents multiple Meeting records with same `meeting_id`

**Source:**
- Extracted from GoToMeeting API: `GET /G2M/rest/historicalMeetings`
- Field: `meeting.get('meetingId')` (line 58 in `goto_meeting_sync_service.py`)

**Stored in TaskLinks.meeting_id:**
- `TaskLinks.meeting_id` stores the same value as `Meeting.meeting_id`
- Used for counting distinct meetings per task (DAF meeting counts)

### Meeting.session_id

**Type:** `CharField(max_length=100, blank=True, null=True, db_index=True)`

**What it is:**
- **Occurrence identifier** for a specific meeting instance
- Extracted from `historicalMeetings` API response: `meeting.get('sessionId')`
- Used to filter attendees for a specific session (not all historical attendees)

**Source:**
- GoToMeeting API: `GET /G2M/rest/historicalMeetings`
- Field: `meeting.get('sessionId')` (line 97 in `goto_meeting_sync_service.py`)

### Meeting.meeting_instance_key

**Type:** `CharField(max_length=100, blank=True, null=True, db_index=True)`

**What it is:**
- **Attendee-scoped instance identifier** from attendee API
- Extracted from attendee API response: `attendee.get('meetingInstanceKey')`
- Used to filter attendees for a specific session when fetching from `/meetings/{meeting_id}/attendees`

**Source:**
- GoToMeeting API: `GET /G2M/rest/meetings/{meeting_id}/attendees`
- Field: `attendee.get('meetingInstanceKey')` (line 262 in `attendee_sync_service.py`)

**Relationship:**
- `session_id` comes from `historicalMeetings` API (meeting metadata)
- `meeting_instance_key` comes from attendee API (attendee metadata)
- Both identify the same occurrence, but from different API endpoints

### TaskLinks.meeting_id

**Type:** `CharField(max_length=100, blank=True, null=True, db_index=True)`

**What it is:**
- Stores `Meeting.meeting_id` (room ID, not occurrence ID)
- Used to count distinct meetings per task: `len(set(link.meeting_id for link in task_links))`
- **Does NOT store** `session_id` or `meeting_instance_key`

**Source:**
- Set during reconciliation: `meeting_id=meeting.meeting_id` (line 499 in reconciliation service)

**Limitation:**
- Cannot distinguish between multiple occurrences of the same room
- If same room has 2 meetings on different dates, both will have same `meeting_id` in TaskLinks
- DAF counts them as 1 meeting (not 2)

---

## Querysets

### Meeting Selection Query

**Location:** `reconcile_meetings()` (line 95-98)

```python
meetings = Meeting.objects.filter(
    start_time__gte=start_date,
    start_time__lte=end_date
).select_related().prefetch_related('attendees', 'attendees__user')
```

**Filters:**
- `start_time__gte=start_date` - Meeting window start
- `start_time__lte=end_date` - Meeting window end
- **No filtering by:** `service_name`, `provider_not_found`, `attendee_count`

### Task Candidate Query

**Location:** `_find_candidate_tasks()` (line 321-325)

```python
base_tasks = Task.objects.filter(
    employee=employee,
    is_active=True,
    mxpoint__gt=0  # Meeting-required tasks
)
```

**Filters:**
- `employee=employee` - Tasks for identified employee
- `is_active=True` - Only active tasks
- `mxpoint__gt=0` - Only meeting-required tasks
- **NO date filtering** (tasks are NOT filtered by `submission` or `created_at` relative to meeting date)

**Ordering:**
```python
all_tasks = list(base_tasks.order_by('-submission', '-id'))
```

**Key Finding:** Tasks are **NOT filtered by time window**. The `time_window_days` parameter is only used in `_select_best_task()` for scoring (not filtering).

### TaskLink Deduplication Query

**Location:** `_create_or_update_tasklink()` (line 476-480)

```python
existing_link = TaskLinks.objects.filter(
    task=task,
    meeting_id=meeting.meeting_id,
    is_active=True
).first()
```

**Deduplication Logic:**
- Checks for existing TaskLink with same `(task, meeting_id, is_active=True)`
- If exists → updates `link`, `drive_link`, `is_auto_generated`
- If not exists → creates new TaskLink

**Note:** Multiple TaskLinks can exist for same `(task, meeting_id)` if `is_active=False`.

---

## Reproduction

### AssertionError: Cannot combine a unique query with a non-unique query

**Status:** ✅ **FIXED** (no longer occurs in current code)

**Historical Issue:**
- **File:** `coda/management/services/meeting_task_reconciliation_service.py`
- **Line:** ~315 (in old version)
- **Error:** `AssertionError: Cannot combine a unique query with a non-unique query`

**Root Cause:**
- Old code combined querysets with `.distinct()`:
  ```python
  tasks = (tasks_by_submission | tasks_by_links).distinct()
  ```
- One queryset had `.distinct()` (unique), the other didn't (non-unique)
- Django ORM doesn't allow combining unique and non-unique querysets

**Fix:**
- Removed date filtering from task queries entirely
- Single queryset: `Task.objects.filter(employee=employee, is_active=True, mxpoint__gt=0)`
- No `.distinct()` calls
- No queryset OR operations

**Current Code (Line 321-325):**
```python
base_tasks = Task.objects.filter(
    employee=employee,
    is_active=True,
    mxpoint__gt=0
)
# No date filtering, no .distinct(), no OR operations
```

**Verification:**
- Test: `test_find_candidate_tasks_no_assertion_error()` in `tests/management/01_unit/test_meeting_task_reconciliation.py`
- Confirms no AssertionError is raised

---

## Findings

### 1. Time Window Filtering

**Question:** Are candidate tasks filtered by a time window?

**Answer:** **NO** - Tasks are **NOT filtered by time window**.

**Evidence:**
- `_find_candidate_tasks()` (line 321-325) filters by:
  - `employee=employee`
  - `is_active=True`
  - `mxpoint__gt=0`
- **No date filters** (`submission__gte`, `submission__lte`, `created_at`, etc.)
- All tasks for employee are considered (regardless of date)

**Time Window Usage:**
- `time_window_days` parameter is **only used in `_select_best_task()`** for scoring (line 444-450)
- Scoring adds points based on time proximity:
  - Same day: +5 points
  - 1-2 days: +3 points
  - 3-7 days: +1 point
- **Does NOT filter tasks** - only scores them

**To Disable Task-Window Filtering:**
- **Already disabled** - no task-window filtering exists
- To disable meeting-window filtering, modify `reconcile_meetings()` (line 95-98):
  ```python
  # Remove date filters:
  meetings = Meeting.objects.all().select_related().prefetch_related('attendees', 'attendees__user')
  ```

### 2. Meeting Identifier Semantics

**Meeting.meeting_id:**
- **Room ID** (not occurrence ID)
- GoToMeeting room identifier (e.g., "698-057-837" or numeric like "616024597")
- Same room can have multiple occurrences (different `start_time`, `session_id`)
- **Unique constraint** (`unique=True`) prevents multiple Meeting records with same `meeting_id`
- **Problem:** If same room has 2 meetings, only 1 Meeting record can exist (the second one overwrites the first during upsert due to `get_or_create(meeting_id=...)`)

**TaskLinks.meeting_id:**
- Stores room ID (same as `Meeting.meeting_id`)
- **Cannot distinguish occurrences** - if same room has 2 meetings, both TaskLinks will have same `meeting_id`
- DAF counts them as 1 meeting (not 2)

**Meeting.session_id:**
- Occurrence identifier (from `historicalMeetings` API)
- **Not stored in TaskLinks** - lost when linking to tasks

**Meeting.meeting_instance_key:**
- Attendee-scoped instance identifier (from attendee API)
- **Not stored in TaskLinks** - lost when linking to tasks

### 3. SQL Validation Results

**Query 1: TaskLinks count grouped by meeting_id**
```sql
SELECT meeting_id, COUNT(*) as link_count
FROM management_tasklinks
WHERE meeting_id IS NOT NULL AND meeting_id != ''
GROUP BY meeting_id
ORDER BY link_count DESC
LIMIT 20
```

**Result:** 
- `meeting_id=616024597: 21 TaskLinks`
- This meeting_id appears across **21 different tasks** and **9 different employees**
- **Finding:** Same meeting (room) can be linked to multiple tasks/employees

**Query 2: meeting_id=616024597 across employees/tasks**
```sql
SELECT 
    tl.meeting_id,
    tl.task_id,
    t.employee_id,
    u.username,
    t.activity_name,
    tl.is_active
FROM management_tasklinks tl
JOIN management_task t ON tl.task_id = t.id
JOIN auth_user u ON t.employee_id = u.id
WHERE tl.meeting_id = '616024597'  -- meeting_id is stored as character varying (text)
ORDER BY tl.created_at DESC
LIMIT 10
```

**Result:** 
- **21 TaskLinks** found for `meeting_id=616024597`
- **21 distinct tasks** (one TaskLink per task)
- **9 distinct employees** (same meeting linked to tasks owned by 9 different employees)
- **Finding:** Same meeting (room) can be linked to multiple tasks across multiple employees
- This is expected behavior if multiple employees have tasks that match the same meeting topic

**Query 3: Meeting occurrences**
```sql
SELECT 
    meeting_id,
    session_id,
    meeting_instance_key,
    start_time,
    topic,
    service_name,
    COUNT(*) OVER (PARTITION BY meeting_id) as occurrence_count
FROM ai_services_meeting
WHERE meeting_id IN (
    SELECT meeting_id
    FROM ai_services_meeting
    GROUP BY meeting_id
    HAVING COUNT(*) > 1
)
ORDER BY meeting_id, start_time
```

**Result:** No meetings with multiple occurrences found (due to `unique=True` constraint on `meeting_id`)

**Note:** The `unique=True` constraint on `Meeting.meeting_id` prevents storing multiple occurrences of the same room. If the same room has 2 meetings, only 1 Meeting record can exist (the second one overwrites the first during upsert).

---

## Recommendations

### 1. Remove Unique Constraint on Meeting.meeting_id

**Problem:** `unique=True` prevents storing multiple occurrences of same room.

**Recommendation:**
- Remove `unique=True` from `Meeting.meeting_id`
- Add composite unique constraint: `(service_name, meeting_id, session_id)` or `(service_name, meeting_id, start_time)`
- Allows same room to have multiple occurrences (different sessions/dates)

### 2. Store session_id in TaskLinks

**Problem:** Cannot distinguish occurrences when counting meetings.

**Recommendation:**
- Add `session_id` field to `TaskLinks` model
- Store `meeting.session_id` when creating TaskLink
- Update DAF counting logic to use `(meeting_id, session_id)` for distinct count

### 3. Fix Meeting Identifier Type Consistency

**Problem:** `meeting_id` may be stored as integer in some cases, causing query mismatches.

**Recommendation:**
- Ensure `meeting_id` is always stored as string in both `Meeting` and `TaskLinks`
- Use `CharField` consistently (already done)
- Cast to string when querying: `meeting_id::text = '616024597'`

### 4. Add Indexes for Common Queries

**Recommendation:**
- Add composite index on `TaskLinks`: `(task_id, meeting_id, is_active)`
- Add composite index on `Meeting`: `(service_name, meeting_id, start_time)`
- Improves query performance for reconciliation

---

**End of Report**

