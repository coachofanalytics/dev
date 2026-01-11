# Evidence Display Fix Summary

## Problem
- DB shows 16 TaskLinks for task_id=265
- UI evidence panel shows "No evidence uploaded yet"
- Step 3 readiness shows "Evidence Complete"
- Mismatch: Evidence panel uses filtered queryset (user's evidence only), but readiness check uses ALL evidence

## Root Cause
1. `get_user_evidence_for_task()` filters evidence by user (non-staff see only their own)
2. `_calculate_approval_readiness()` queries ALL evidence for the task
3. Result: Non-staff users see empty panel but readiness shows complete (because other users' evidence exists)

## Solution
1. Updated `ChecklistEvaluationService.get_task_quality_score()` to accept optional `task_links` queryset
2. Updated `_calculate_approval_readiness()` to accept optional `task_links` parameter
3. Updated `get_user_evidence_for_task()` to return `task_evidence_qs` queryset
4. Updated all `_calculate_approval_readiness()` call sites to pass the filtered queryset

## Files Changed

### 1. `coda/management/services/checklist_evaluation_service.py`
- **Line 40**: Updated `get_task_quality_score()` signature to accept `task_links=None`
- **Line 71**: Use provided `task_links` queryset if available, otherwise query all

### 2. `coda/management/legacy_views.py`
- **Line 2739**: Updated `_calculate_approval_readiness()` signature to accept `task_links=None`
- **Line 2855**: Pass `task_links` to `ChecklistEvaluationService.get_task_quality_score()`
- **Line 2877-2880**: Fallback uses provided queryset if available
- **Line 3340**: `get_user_evidence_for_task()` now returns `task_evidence_qs` in result dict
- **Line 3392**: Return dict includes `'task_evidence_qs'` key
- **Line 3436**: Pass `task_links=evidence_data.get('task_evidence_qs')` to readiness calculation
- **Line 3790**: Pass `task_links=evidence_data.get('task_evidence_qs')` to readiness calculation
- **Line 3830**: Pass `task_links=evidence_data.get('task_evidence_qs')` to readiness calculation

## Template Verification
- Template `coda/management/templates/management/daf/evidence_form.html` uses correct fields:
  - `ev.link_name` (line 485, 542) - ✅ Correct
  - `ev.description` (line 498) - ✅ Correct
  - `ev.link` (line 502) - ✅ Correct
  - `ev.drive_link` (line 506) - ✅ Correct
  - `ev.doc` (line 511) - ✅ Correct
  - No references to `topic_name` - ✅ Correct

## Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check

# 2. Manual test
# Navigate to: http://127.0.0.1:8000/management/newevidence/265/
# Expected:
# - Evidence panel shows user's evidence (or "No evidence" if none)
# - Step 3 readiness shows evidence status matching the panel
# - If user has no evidence but others do: panel shows "No evidence", readiness shows "Incomplete"

# 3. Test with different users
# - Non-staff user: Should see only their own evidence
# - Staff user: Should see all evidence for the task
```

## Test Case

```python
# coda/management/tests/test_evidence_display_fix.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from management.models import Task, TaskLinks

User = get_user_model()

class EvidenceDisplayFixTest(TestCase):
    def test_evidence_panel_matches_readiness(self):
        """Evidence panel and readiness check use same filtered queryset"""
        # Create task
        user1 = User.objects.create_user(username='user1', email='user1@test.com')
        user2 = User.objects.create_user(username='user2', email='user2@test.com')
        task = Task.objects.create(employee=user1, activity_name='Test Activity')
        
        # User1 uploads evidence
        TaskLinks.objects.create(
            task=task,
            added_by=user1,
            link_name='User1 Evidence',
            link='https://example.com/1',
            is_active=True
        )
        
        # User2 uploads evidence
        TaskLinks.objects.create(
            task=task,
            added_by=user2,
            link_name='User2 Evidence',
            link='https://example.com/2',
            is_active=True
        )
        
        # As user1: panel should show only user1's evidence, readiness should match
        from management.legacy_views import get_user_evidence_for_task, _calculate_approval_readiness
        
        evidence_data = get_user_evidence_for_task(task, user1, is_staff=False)
        self.assertEqual(len(evidence_data['task_evidence']), 1)
        self.assertEqual(evidence_data['task_evidence'][0]['link_name'], 'User1 Evidence')
        
        # Readiness should use same filtered queryset
        readiness = _calculate_approval_readiness(
            task, 
            requires_requirement=False,
            task_links=evidence_data['task_evidence_qs']
        )
        # If user1 has evidence, readiness should show complete
        self.assertTrue(readiness['evidence_complete'])
        
        # As staff: panel should show all evidence
        evidence_data_staff = get_user_evidence_for_task(task, user1, is_staff=True)
        self.assertEqual(len(evidence_data_staff['task_evidence']), 2)
```

