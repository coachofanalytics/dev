# View Details: Modal to Inline Revert

## Summary
Reverted "View Details" from Bootstrap modal to inline expand/collapse to eliminate hover flicker issues. This is a minimal, safe change focused only on the DAF v2 UI template.

## Changes Made

### 1. Button Markup Changed ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~356)

**Before:**
```html
<button type="button" 
        class="btn btn-sm btn-outline-secondary js-view-details"
        data-modal-target="#taskDetailsModal{{ task.id }}"
        aria-label="View Details">
  View Details
</button>
```

**After:**
```html
<button type="button" 
        class="btn btn-sm btn-outline-primary js-toggle-details"
        data-target="#taskDetailsInline{{ task.id }}"
        aria-expanded="false"
        aria-label="View Details">
  View Details
</button>
```

**Changes:**
- Changed class from `js-view-details` to `js-toggle-details`
- Changed `data-modal-target` to `data-target`
- Added `aria-expanded="false"`
- Changed button style from `btn-outline-secondary` to `btn-outline-primary`

### 2. Modal Replaced with Inline Container ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~365)

**Before:**
```html
<!-- View Details Modal -->
<div class="modal fade" id="taskDetailsModal{{ task.id }}" ...>
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">...</div>
      <div class="modal-body">...</div>
      <div class="modal-footer">...</div>
    </div>
  </div>
</div>
```

**After:**
```html
<!-- View Details Inline (Collapsible) -->
<div id="taskDetailsInline{{ task.id }}" class="task-details-inline d-none mt-2">
  <div class="card-body border-top pt-3">
    <!-- Same content sections as before -->
  </div>
</div>
```

**Changes:**
- Removed all modal markup (`modal fade`, `modal-dialog`, `modal-content`, `modal-header`, `modal-footer`)
- Created inline container with `task-details-inline` class
- Added `d-none` class to hide by default
- Removed modal footer (Close button and Upload Evidence button)
- Content sections remain the same (Issues Breakdown, Checklist, Evidence, Meetings, Manager Audit)

### 3. JavaScript Handler Replaced ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~847)

**Before:**
```javascript
// FIXED: Explicit modal handler for View Details buttons (prevents flicker)
$(document).on('click', '.js-view-details', function () {
  var target = $(this).data('modal-target');
  if (!target) return;
  $(target).modal('show');
});
```

**After:**
```javascript
// REVERTED: Inline expander handler (vanilla JS, no Bootstrap dependency)
(function() {
  'use strict';
  
  function toggleDetails(button) {
    var targetId = button.getAttribute('data-target');
    if (!targetId) return;
    
    var target = document.querySelector(targetId);
    if (!target) return;
    
    var isVisible = !target.classList.contains('d-none');
    
    // Close other open panels (optional: allow only one open at a time)
    document.querySelectorAll('.task-details-inline:not(.d-none)').forEach(function(panel) {
      if (panel !== target) {
        panel.classList.add('d-none');
        var otherButton = document.querySelector('[data-target="#' + panel.id + '"]');
        if (otherButton) {
          otherButton.setAttribute('aria-expanded', 'false');
        }
      }
    });
    
    // Toggle current panel
    if (isVisible) {
      target.classList.add('d-none');
      button.setAttribute('aria-expanded', 'false');
    } else {
      target.classList.remove('d-none');
      button.setAttribute('aria-expanded', 'true');
    }
  }
  
  // Use event delegation for dynamically added buttons
  document.addEventListener('click', function(e) {
    if (e.target.closest('.js-toggle-details')) {
      e.preventDefault();
      toggleDetails(e.target.closest('.js-toggle-details'));
    }
  });
})();
```

**Changes:**
- Removed jQuery/Bootstrap modal dependency
- Added vanilla JS toggle function
- Implements "only one open at a time" behavior
- Updates `aria-expanded` attribute for accessibility
- Uses event delegation for dynamically added buttons

### 4. CSS Cleanup ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~680)

**Removed:**
- All `.js-view-details` specific CSS (z-index, pointer-events, hover styles)
- Modal-related CSS (`.modal-backdrop`, `.modal`, `.modal-body`, `.modal-header`, `.modal-footer`)
- Overlay protection CSS (stretched-link, card-overlay rules)
- Tooltip exclusion for `.js-view-details`

**Added:**
```css
/* View Details inline expander styles */
.task-details-inline {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
  margin-top: 0.5rem;
}

.task-details-inline.d-none {
  display: none !important;
}
```

### 5. Tooltip Initialization Updated ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~825)

**Before:**
```javascript
$('[data-toggle="tooltip"]')
  .not('.daf-task-grid *')
  .not('.js-view-details')
  .not('.js-view-details *')
  .not('.modal, .modal *')
  .not('[data-toggle="modal"]')
  .tooltip({...});
```

**After:**
```javascript
$('[data-toggle="tooltip"]')
  .not('.daf-task-grid *')  // Exclude entire DAF task grid
  .not('.js-toggle-details')
  .not('.js-toggle-details *')
  .tooltip({...});
```

**Changes:**
- Removed `.js-view-details` exclusion (no longer needed)
- Removed `.modal` exclusion (no longer needed)
- Added `.js-toggle-details` exclusion (prevent tooltips on toggle button)

### 6. Debug Instrumentation Updated ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~883)

**Changed:**
- Updated references from `.js-view-details` to `.js-toggle-details` in debug code

### 7. Tests Updated ✅
**File:** `coda/management/tests/test_daf_v2_template_rendering.py`

**Removed:**
- `test_view_details_modal_exists()` - No longer testing for modal

**Added:**
- `test_view_details_button_exists()` - Tests button exists with correct attributes
- `test_view_details_inline_container_exists()` - Tests inline container exists
- `test_view_details_inline_contains_five_sections()` - Tests all 5 sections present

**Updated:**
- `test_view_details_modal_contains_five_sections()` → `test_view_details_inline_contains_five_sections()`

## Content Sections Preserved

All 5 sections from the modal are preserved in the inline container:

1. ✅ **Issues Breakdown** - Attention reasons list
2. ✅ **Checklist** - Activity checklist items with completion status
3. ✅ **Evidence** - Evidence list with links and upload button
4. ✅ **Meetings** - Meeting progress and match info
5. ✅ **Manager Audit** - Staff-only section with Meeting Config and audit details

## Benefits

1. **No Flicker** - No modal/tooltip/overlay interactions to cause hover loops
2. **Simpler** - Vanilla JS, no Bootstrap modal dependency
3. **Faster** - No modal backdrop/overlay rendering
4. **Better UX** - Inline expansion keeps context visible
5. **Accessible** - Proper `aria-expanded` attributes

## Files Changed

1. `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`
   - Button markup (line ~356)
   - Modal → Inline container (line ~365)
   - JavaScript handler (line ~847)
   - CSS cleanup (line ~680)
   - Tooltip initialization (line ~825)
   - Debug instrumentation (line ~883)

2. `coda/management/tests/test_daf_v2_template_rendering.py`
   - Updated tests for inline container instead of modal

## Verification

### Manual Testing
1. Navigate to `/management/daf/v2/?user_id=2908`
2. Click "View Details" button
3. ✅ Inline content expands below the card
4. ✅ Click again to collapse
5. ✅ Only one panel open at a time
6. ✅ Hover over button - no flicker
7. ✅ All 5 sections visible when expanded

### Automated Testing
```bash
poetry run python coda/manage.py test management.tests.test_daf_v2_template_rendering -v 2
```

**Expected:**
- ✅ All tests pass
- ✅ Button exists with correct attributes
- ✅ Inline container exists
- ✅ All 5 sections present

## Notes

- **No backend changes** - Only template/JS/CSS changes
- **No new dependencies** - Uses vanilla JS
- **Minimal risk** - Changes scoped to DAF v2 template only
- **Backward compatible** - Same content, different presentation

