# DAF v2 Runtime Fixes - Implementation Summary

## Changes Made

### A) DAF v2 Header Metrics: Rename + Correct Semantics

**Files Modified:**
- `coda/management/legacy_views.py` (lines ~2143-2270)
- `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (lines ~65-70)

**Changes:**
1. **Renamed "Pending" to "Remaining"**: 
   - `remaining_amount = target_amount - earned_amount_provisional` (amount not yet earned)
   - Clamped at `max(x, 0)` to prevent negative values

2. **Added "Pending Approval"**:
   - `pending_approval_amount = earned_amount_provisional - approved_earned` (amount pending approval)
   - Clamped at `max(x, 0)` to prevent negative values

3. **Updated template labels**:
   - Changed "Pending:" to "Remaining:"
   - Added "Pending Approval:" with warning color (text-warning)

4. **Reconciliation comments/logging**:
   - Added explicit reconciliation checks for both metrics
   - Logs warnings if reconciliation fails

**Context Variables Added:**
- `remaining_amount`: Decimal (Target - Earned Provisional)
- `pending_approval_amount`: Decimal (Earned Provisional - Approved Earned)
- `pending_amount`: Legacy (deprecated, equals remaining_amount for backward compatibility)

### B) Evidence Topic/Title: Canonical + Immutable for Non-Staff

**Files Modified:**
- `coda/management/forms.py` (lines ~246-410)
- `coda/management/legacy_views.py` (lines ~4195-4217)

**Changes:**
1. **Canonical title generation**:
   - Format: `"{activity_type.name} — REQ-{requirement.id}"` if requirement exists
   - Format: `"{activity_type.name}"` if no requirement
   - Fallback: `task.activity_name` or `"Evidence"`

2. **Form-level enforcement**:
   - `clean_link_name()` method added to `EvidenceForm`
   - For non-staff: ALWAYS returns canonical title (prevents POST tampering)
   - For staff: Allows override but uses canonical if blank
   - Logs warning if non-staff attempts to override

3. **View-level enforcement**:
   - In `newevidence()` view, enforces canonical for non-staff before saving
   - For staff: Uses canonical if blank, otherwise allows override

4. **Template updates**:
   - Non-staff: Field is readonly with visual styling
   - Staff: Field is editable with help text showing default

**Server-Side Protection:**
- Form `clean_link_name()` enforces canonical for non-staff
- View enforces canonical for non-staff before TaskLinks creation
- Both layers prevent POST tampering

### C) Evidence Link Validation + "Open Link" Button Correctness

**Files Created:**
- `coda/management/templatetags/url_validation.py` (NEW)

**Files Modified:**
- `coda/management/utils.py` (added `is_valid_evidence_url()` and `get_url_domain()` functions)

**Files Modified:**
- `coda/management/legacy_views.py` (lines ~3692-3715)
- `coda/management/templates/management/daf/evidence_form.html` (lines ~1-3, ~505-515)

**Changes:**
1. **Centralized URL validation**:
   - `is_valid_evidence_url()` function in `management/utils/url_validation.py`
   - Validates: must start with `http://` or `https://`
   - Rejects placeholder URLs: `"https://..."`, `"http://..."`, `"https://www."`, `"http://www."`
   - Validates URL structure (must have domain)

2. **Template filter**:
   - `is_valid_evidence_url_filter` template tag
   - Usage: `{{ ev.link|is_valid_evidence_url_filter }}`

3. **View validation**:
   - Uses centralized validation utility
   - Shows error message if URL is invalid

4. **Template "Open Link" button**:
   - Only renders when URL passes validation
   - Shows disabled button with "Link (Invalid URL)" if invalid

### D) Evidence Scoping (Privacy Correct)

**Files Modified:**
- `coda/management/legacy_views.py` (lines ~3519-3546)
- `coda/management/templates/management/daf/evidence_form.html` (lines ~488-500)

**Changes:**
1. **Evidence query scoping**:
   - **Non-staff**: Only evidence uploaded by `current user` OR `task owner`
   - **Staff**: All evidence for the task (no restriction)
   - Removed duplicate query logic

2. **Template display**:
   - **Staff**: Shows "Uploaded by: <name>" for each evidence item
   - **Non-staff**: Does not show uploader identity (privacy)

3. **Privacy enforcement**:
   - Non-staff never see other employees' evidence
   - Staff see all evidence with uploader identity for audit

### E) Migrations: EmployeeCareerState

**Status**: ✅ Already exists
- Migration file: `coda/management/migrations/0002_auto_20251229_1714.py`
- Model: `EmployeeCareerState` with all required fields
- No new migration needed

## Verification Commands

```bash
# Generate migrations (if any new models/fields)
poetry run python coda/manage.py makemigrations

# Apply migrations
poetry run python coda/manage.py migrate

# System check
poetry run python coda/manage.py check

# Run server
poetry run python coda/manage.py runserver
```

## Manual Verification Steps

### 1. DAF v2 Header Metrics
1. Navigate to `/management/daf/v2/`
2. **Verify**:
   - Header shows "Remaining:" (not "Pending:")
   - Header shows "Pending Approval:" with warning color
   - Values make sense: `Remaining = Target - Earned (Provisional)`
   - Values make sense: `Pending Approval = Earned (Provisional) - Approved Earned`
   - No negative values displayed

### 2. Evidence Topic/Title Canonical + Immutable
1. As **non-staff user**, navigate to `/management/newevidence/<task_id>/`
2. **Verify**:
   - Topic/Title field is readonly (grayed out)
   - Field shows canonical format: `"{Activity Name} — REQ-{id}"` or `"{Activity Name}"`
   - Cannot edit the field (readonly)
3. **Test POST tampering** (using browser dev tools or curl):
   - Try to POST with different `link_name` value
   - **Verify**: Server enforces canonical title (check saved TaskLinks.link_name)
4. As **staff user**, navigate to same page:
   - **Verify**: Field is editable
   - **Verify**: Help text shows default canonical title
   - **Verify**: Can override canonical title

### 3. Evidence Link Validation
1. Navigate to `/management/newevidence/<task_id>/`
2. **Test invalid URLs**:
   - Try `"invalid-url"` (no http/https) → Should show error
   - Try `"https://..."` (placeholder) → Should show error
   - Try `"http://www."` (incomplete) → Should show error
3. **Test valid URLs**:
   - Try `"https://example.com/recording"` → Should accept
   - Try `"http://gotomeeting.com/recording"` → Should accept
4. **Verify "Open Link" button**:
   - In existing evidence list, valid URLs show "Open Link" button
   - Invalid URLs show disabled "Link (Invalid URL)" button

### 4. Evidence Scoping (Privacy)
1. **As non-staff user**:
   - Navigate to `/management/newevidence/<task_id>/`
   - **Verify**: Only see evidence uploaded by you OR task owner
   - **Verify**: Do NOT see other employees' evidence
   - **Verify**: Do NOT see "Uploaded by:" labels
2. **As staff user**:
   - Navigate to same page
   - **Verify**: See all evidence for the task
   - **Verify**: See "Uploaded by: <name>" for each evidence item

### 5. EmployeeCareerState Migration
1. Run: `poetry run python coda/manage.py migrate`
2. **Verify**: No errors, migration `0002_auto_20251229_1714` is applied
3. **Verify**: `EmployeeCareerState` table exists in database

## Files Changed Summary

1. **`coda/management/legacy_views.py`**:
   - DAF v2 metrics computation (Remaining, Pending Approval)
   - Evidence canonical title enforcement
   - Evidence link validation
   - Evidence scoping logic

2. **`coda/management/forms.py`**:
   - `clean_link_name()` method for server-side enforcement
   - Canonical title initialization and readonly for non-staff

3. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**:
   - Updated header labels (Remaining, Pending Approval)

4. **`coda/management/templates/management/daf/evidence_form.html`**:
   - Readonly field styling for non-staff
   - "Uploaded by:" display for staff
   - "Open Link" button validation

5. **`coda/management/utils.py`** (MODIFIED):
   - Added `is_valid_evidence_url()` function for centralized URL validation
   - Added `get_url_domain()` helper function

6. **`coda/management/templatetags/url_validation.py`** (NEW):
   - Template filter for URL validation

## Notes

- All changes are minimal and backward compatible
- No breaking changes to existing functionality
- EmployeeCareerState migration already exists (no action needed)
- Server-side enforcement prevents POST tampering for non-staff
- Privacy is enforced at query level (non-staff cannot see other employees' evidence)

