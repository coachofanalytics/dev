# DAF v2 E2E Verification Checklist

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Purpose:** Verify end-to-end runtime flow for a selected current employee

---

## Prerequisites

1. **Database:** Using cloned production database (`coda_prod_clone`)
2. **Current Employee:** Select a current employee ID (from Employee Groups page, typically 7-10 active employees)
3. **Access:** Staff/superuser account for debug pages

---

## Step 1: Import Legacy Meetings (Seed Canonical Table)

**Goal:** Populate `ai_services_meeting` table from legacy `getdata_gotomeetings` data.

```bash
# Import all legacy meetings
poetry run python coda/manage.py import_legacy_gotomeetings --service gotomeeting_external

# Verify import succeeded
poetry run python coda/manage.py shell
```

In Django shell:
```python
from ai_services.models import Meeting
print(f"Meeting count: {Meeting.objects.count()}")
# Expected: > 0 (should match or exceed legacy GotoMeetings count)
```

**Acceptance:**
- ✅ Command completes without exceptions
- ✅ `Meeting.objects.count() > 0`
- ✅ No `NameError: name 'requirement_code' is not defined`

---

## Step 2: Verify Meeting Count

```bash
poetry run python coda/manage.py shell
```

```python
from ai_services.models import Meeting, GotoMeetings

meeting_count = Meeting.objects.count()
legacy_count = GotoMeetings.objects.count()

print(f"Canonical Meeting count: {meeting_count}")
print(f"Legacy GotoMeetings count: {legacy_count}")

# Expected: meeting_count > 0, ideally meeting_count >= legacy_count (after grouping)
```

**Acceptance:**
- ✅ `Meeting.objects.count() > 0`
- ✅ Meetings have `requirement_code` extracted from topics (check a few: `Meeting.objects.filter(requirement_code__isnull=False).count()`)

---

## Step 3: Run Autolink Diagnose for Current Employee

**Goal:** Verify autolink finds candidate tasks without submission date filtering.

```bash
# Get a current employee ID from Employee Groups page or:
poetry run python coda/manage.py shell
```

```python
from management.services.employee_filter_service import get_filtered_employees_queryset
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
factory = RequestFactory()
request = factory.get('/')
request.user = User.objects.filter(is_staff=True).first()

employees = get_filtered_employees_queryset(request)
current_employee = employees.first()
print(f"Current employee ID: {current_employee.id}, Username: {current_employee.username}")
```

Then run diagnose:
```bash
# Replace <USER_ID> with the ID from above
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id <USER_ID> --days 14 --limit 50
```

**Expected Output:**
```
🔗 Meeting Evidence Auto-Link (Phase 3 - HARDENED) 🔗
🔍 DIAGNOSE MODE - Read-only analysis, no TaskLinks created/updated

📊 Candidate Selection Summary:
   Tasks found: <N>
   Employees included: 1 (<username>)
   Activity types: INTERNAL_TRAINING_SESSION, SELF_TRAINING_SESSION, ...
   Exclusion rule: Tasks with existing auto-generated TaskLinks (meeting_id present) excluded

📋 Found <N> candidate task(s)
...
```

**Acceptance:**
- ✅ No `AttributeError` (autolink_run exists)
- ✅ Candidate tasks found > 0 (even if tasks have old submission dates)
- ✅ Candidate selection summary shows correct employee and activity types
- ✅ No crash even if no matches exist

---

## Step 4: Run Autolink Diagnose for Single Task

```bash
# Replace <TASK_ID> with an actual task ID from the employee
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --task-id <TASK_ID>
```

**Acceptance:**
- ✅ Only that task is analyzed
- ✅ Output shows matching analysis (top 3 candidates, confidence scores)
- ✅ No TaskLinks created/updated

---

## Step 5: Open DAF v2 UI for Current Employee

**URL:** `/management/daf/v2/?user_id=<USER_ID>`

**Verify:**
- ✅ Page loads without errors
- ✅ Task cards show task names (not placeholders)
- ✅ Evidence chips reflect actual evidence status
- ✅ "Needs Attention" tab shows tasks correctly
- ✅ Summary bar shows "Approved Earned" and "Provisional Earned"

---

## Step 6: Open DAF Runtime Debug Page

**URL:** `/management/debug/daf-runtime/`

**Verify (Staff Only):**
- ✅ Page loads without errors
- ✅ Shows meeting count (should match Step 2)
- ✅ Shows autolink run history
- ✅ Shows task compliance statistics
- ✅ All sections populate correctly

---

## Step 7: Verify Dashboard Shortcuts

**URL:** `/dashboard`

**Verify:**
- ✅ User Management card visible
- ✅ "Employee Groups" link present (staff only)
- ✅ "DAF Runtime Debug" link present (staff only)
- ✅ Both links work and navigate correctly
- ✅ Non-staff users do not see debug link

---

## Step 8: Verify Internal Training Policy

**For Group B Employee:**
1. Create/edit an Internal Training task
2. Verify requirement is NOT required (no validation error)
3. Verify topic dropdown appears (if implemented)
4. Verify task can be saved without requirement

**For Group A Employee:**
1. Create/edit an Internal Training task
2. Verify requirement IS required
3. Verify validation error if requirement missing

**Acceptance:**
- ✅ Group B: Internal Training does not require requirement
- ✅ Group A: Internal Training requires requirement (existing behavior)
- ✅ Policy resolver correctly distinguishes groups

---

## Step 9: Run Full Autolink (Non-Diagnose)

**Warning:** This will create TaskLinks. Only run if you want to test the full flow.

```bash
# For specific employee (recommended)
poetry run python coda/manage.py autolink_meeting_evidence --user-id <USER_ID> --days 14 --limit 10 --dry-run

# Check what would be created
# If satisfied, remove --dry-run to actually create TaskLinks
```

**Acceptance:**
- ✅ Autolink finds matches based on meeting time window (--days)
- ✅ TaskLinks created/updated correctly
- ✅ No errors in logs

---

## Troubleshooting

### Issue: Meeting count is 0 after import
- Check logs for parse failures
- Verify `GotoMeetings.objects.count() > 0`
- Check `meeting_id` field is populated in legacy table

### Issue: Autolink finds 0 candidates
- Verify employee has active tasks with meeting-based activity types
- Check task `is_active=True`
- Verify employee is in "current employees" list (Employee Groups page)
- Check exclusion rule: tasks with existing auto-generated TaskLinks are excluded

### Issue: Diagnose mode crashes
- Verify AutolinkRun is always created (check code)
- Check for `AttributeError: 'NoneType' object has no attribute 'tasks_matched'`

### Issue: Dashboard links not showing
- Verify user is staff/superuser
- Check template: `coda/unified_dashboard/templates/unified_dashboard/widgets/user_management.html`
- Verify URLs are correct: `management:employee_groups` and `management:daf_runtime_debug`

---

## Success Criteria

✅ All 9 steps complete without errors  
✅ Meeting table populated from legacy data  
✅ Autolink finds candidates without submission date dependency  
✅ DAF v2 UI shows correct data for current employee  
✅ Debug page accessible and functional  
✅ Dashboard shortcuts work for staff  
✅ Internal Training policy enforced correctly by group  

---

**Status:** Ready for E2E verification

