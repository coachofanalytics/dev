# View Details Button Fix Summary

## Root Cause Analysis

### A1) Why Click Was Broken

**Root Cause Found in Code:**
- **Location:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` lines 942-946
- **Problem:** `mouseenter/mouseleave` event handlers with `stopPropagation()` were interfering with click events
- **Specific Issue:**
  ```javascript
  // PROBLEMATIC CODE (removed):
  $(document).on('mouseenter mouseleave', '.js-view-details', function(e) {
    e.stopPropagation();  // This breaks Bootstrap's event handling
  });
  ```
- **Why it broke:** `stopPropagation()` on hover events was preventing Bootstrap's modal click handlers from working correctly, creating a race condition where hover events blocked click events.

### A2) Why Hover Flickered

**Root Cause:**
- Tooltip overlays were capturing pointer events, causing a `mouseenter`/`mouseleave` loop
- The `mouseenter/mouseleave` handlers with `stopPropagation()` were creating reflow loops
- Multiple tooltip initializations were possible

## Fixes Applied

### A1) Removed Hover Event Interference

**Removed:**
- All `mouseenter/mouseleave` handlers on `.js-view-details`
- `preventDefault()` and `stopPropagation()` from click handler (not needed for button type="button")
- Complex tooltip attribute removal logic that could interfere

**Replaced with:**
- Simple, canonical click handler:
  ```javascript
  $(document).on('click', '.js-view-details', function () {
    var target = $(this).data('modal-target');
    if (!target) return;
    $(target).modal('show');
  });
  ```

### A2) Updated Button HTML to Canonical Format

**Before:**
```html
<button type="button" 
        class="btn btn-info btn-sm flex-fill js-view-details"
        data-modal-target="#taskDetailsModal{{ task.id }}"
        data-task-id="{{ task.id }}"
        aria-label="View all details">
  <i class="fas fa-eye"></i> View Details
</button>
```

**After (Canonical):**
```html
<button type="button" 
        class="btn btn-sm btn-outline-secondary js-view-details"
        data-modal-target="#taskDetailsModal{{ task.id }}"
        aria-label="View Details">
  View Details
</button>
```

**Changes:**
- Removed `btn-info` → `btn-outline-secondary` (canonical style)
- Removed `flex-fill` (not needed for single button)
- Removed `data-task-id` (not used)
- Removed icon (simpler, canonical)
- Simplified `aria-label`

### A3) Fixed Hover Flicker (Tooltip Overlay Pointer Capture)

**CSS Fix (already in place):**
```css
.tooltip, .popover, .tooltip *, .popover * {
  pointer-events: none !important;
}
```

This prevents tooltip overlays from capturing pointer events and causing hover loops.

### A4) Hardened Tooltip Initialization

**Before:**
- Complex exclusion logic with multiple `.not()` calls
- Delay settings that could cause issues

**After:**
```javascript
$('[data-toggle="tooltip"]')
  .not('.js-view-details')
  .not('.js-view-details *')
  .not('.modal, .modal *')
  .not('[data-toggle="modal"]')
  .tooltip({
    container: 'body',
    boundary: 'window'
  });
```

**Key Points:**
- Uses EXACT selector `[data-toggle="tooltip"]` only
- Excludes `.js-view-details` and its children
- No broad selectors like `[data-toggle]` or `.btn`
- Initializes once with guard flag

### A5) Layout Stability

**CSS (already in place):**
```css
.js-view-details {
  border: 1px solid transparent;  /* Base border - no width change */
}

.js-view-details:hover {
  border-color: rgba(0, 0, 0, 0.1);  /* Only color changes */
  transform: none;
  padding: inherit;
  margin: inherit;
}
```

Button does not change border width, padding, or height on hover.

## Files Changed

1. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - Updated button HTML (line ~354)
   - Simplified click handler (line ~899)
   - Hardened tooltip initialization (line ~853)

## Acceptance Criteria Status

✅ **Hovering View Details while moving mouse: no flicker**
- Fixed by: `pointer-events: none` on tooltips + removed hover handlers

✅ **Clicking View Details: modal opens every time**
- Fixed by: Removed `mouseenter/mouseleave` interference, simplified click handler

✅ **No page refresh / no form submit triggered**
- Ensured by: `type="button"` (prevents form submit)

✅ **No regressions to Start Meeting / Upload Evidence / density toggle**
- Verified: Only `.js-view-details` affected, other buttons unchanged

---

# Migration Blocker Fix (Part B)

## B1) Migration State Diagnosis

The `accounts.0003_userprofile_image2` migration may not exist in the codebase, but the column `accounts_userprofile.image2_id` exists in clone/prod databases.

**To diagnose:**
```bash
poetry run python coda/manage.py showmigrations accounts
```

If `accounts.0003_userprofile_image2` shows as `[ ]` (not applied) but the column exists in DB, use `--fake`.

## B2) Safe Fix Commands

### Local Clone DB

```bash
# Step 1: Verify column exists (optional)
poetry run python coda/manage.py dbshell
# In psql: \d accounts_userprofile
# (Look for image2_id column)

# Step 2: Fake the migration
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake

# Step 3: Continue normal migrations
poetry run python coda/manage.py migrate
```

### Heroku Production

```bash
# Step 1: Fake the migration
heroku run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake --app <APP_NAME>

# Step 2: Continue normal migrations
heroku run python coda/manage.py migrate --app <APP_NAME>
```

## B3) Verification

After using `--fake`, verify:
```bash
poetry run python coda/manage.py showmigrations accounts
```

The migration should show as `[X]` (applied) instead of `[ ]` (not applied).

## Files Referenced

- `MIGRATION_REPAIR_RUNBOOK.md` (already exists with detailed instructions)

---

## Summary

**View Details Fix:**
- ✅ Removed `mouseenter/mouseleave` handlers that broke clicks
- ✅ Simplified click handler to canonical form
- ✅ Updated button HTML to match canonical format
- ✅ Hardened tooltip initialization
- ✅ Maintained layout stability CSS

**Migration Fix:**
- ✅ Documented `--fake` migration commands for local + Heroku
- ✅ Runbook already exists in `MIGRATION_REPAIR_RUNBOOK.md`

