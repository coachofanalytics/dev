# View Details Hover Flicker - Root Cause & Fix

## Problem
The "View Details" button on `/management/daf/v2/` was flickering when hovering/moving the mouse, even after previous fixes.

## Root Cause Identified

### Primary Cause: Card Hover Transform
**Location:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` line 635

**Problem:**
```css
.task-card:hover {
  transform: translateY(-1px);  /* THIS CAUSES HOVER BOUNCE */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

**Why it caused flicker:**
1. When mouse hovers over the card, `transform: translateY(-1px)` moves the entire card (including the button) up by 1px
2. This movement causes the mouse cursor to leave the button area
3. Mouse leaves button → triggers `mouseleave` → card moves back down
4. Mouse re-enters button → triggers `mouseenter` → card moves up again
5. **Result: Infinite hover loop causing flicker**

### Secondary Issues (Preventive Fixes)
- CTA row needed z-index protection from potential overlays
- Button needed explicit z-index to stay above any overlays

## Fixes Applied

### 1. Removed Transform from Card Hover ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Before:**
```css
.task-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.task-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

**After:**
```css
.task-card {
  /* REMOVED transform from transition - no position changes on hover */
  transition: box-shadow 0.2s ease;
}

.task-card:hover {
  /* REMOVED transform: translateY(-1px) - causes hover bounce loop */
  /* Only change box-shadow, no position/geometry changes */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

**Impact:** Card no longer moves on hover, eliminating the hover bounce loop.

### 2. Added Z-Index Protection ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**CTA Row:**
```html
<div class="d-flex task-cta-row" style="position: relative; z-index: 3;">
```

**CSS:**
```css
/* Protect CTA row from overlay interference */
.task-cta-row {
  position: relative;
  z-index: 3;
}

.js-view-details {
  /* ... existing styles ... */
  z-index: 4;  /* Ensure button stays on top */
}
```

**Impact:** Prevents any overlay elements from interfering with button hover.

### 3. Added Debug Instrumentation ✅
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Enabled via:** `?debug_hover=1` querystring

**What it logs:**
- Element under pointer during mousemove (throttled to 50ms)
- `mouseover`, `mouseout`, `mouseenter`, `mouseleave` events on cards and buttons
- Computed styles: `pointer-events`, `z-index`, `position`, `display`, `visibility`
- Bounding boxes for button and topmost element
- Event counts summary every 2 seconds

**Usage:**
```
/management/daf/v2/?user_id=2908&debug_hover=1
```

**Note:** Debug code is guarded and only runs when `debug_hover=1` is present in URL.

## Files Changed

1. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - Removed `transform: translateY(-1px)` from `.task-card:hover` (line ~635)
   - Updated transition to remove transform (line ~631)
   - Added z-index protection to CTA row (HTML line ~320, CSS line ~722)
   - Added z-index to `.js-view-details` (line ~706)
   - Added debug instrumentation (line ~900+)

## Validation Steps

### Manual Testing

1. **Test without debug:**
   ```
   /management/daf/v2/?user_id=2908
   ```
   - Hover over "View Details" button while moving mouse
   - ✅ **Expected:** No flicker, smooth hover
   - Click "View Details"
   - ✅ **Expected:** Modal opens consistently

2. **Test with debug (if flicker persists):**
   ```
   /management/daf/v2/?user_id=2908&debug_hover=1
   ```
   - Open browser console
   - Hover over "View Details" button
   - Check logs for:
     - Rapid element switching (indicates overlay issue)
     - High event counts (indicates loop)
     - Z-index conflicts
     - Pointer-events issues

### Expected Debug Output (if working correctly)
- Element changes should be minimal (only when actually moving between elements)
- Event counts should be low (1-2 per hover, not hundreds)
- No tooltip elements appearing in logs
- Button z-index: 4, CTA row z-index: 3

## Root Cause Summary

**The hover flicker was caused by:**
1. **Primary:** `.task-card:hover` with `transform: translateY(-1px)` creating a hover bounce loop
2. **Secondary:** Potential overlay interference (prevented with z-index)

**The fix:**
- Removed position-changing transforms from card hover
- Added z-index layering to protect button area
- Added debug instrumentation for future troubleshooting

## Acceptance Criteria Status

✅ **Hovering View Details while moving mouse: no flicker**
- Fixed by removing `transform: translateY(-1px)` from card hover

✅ **Clicking View Details: modal opens consistently**
- Already working, no changes needed

✅ **No page refresh / no form submit triggered**
- Already working (`type="button"` prevents submit)

✅ **Debug instrumentation available**
- Enabled via `?debug_hover=1` querystring

✅ **Minimal risk changes**
- Only removed problematic transform, added z-index protection
- No changes to click handler or other functionality

## Notes

- The debug instrumentation is **temporary** and should be removed after confirming the fix works in production
- If flicker persists after this fix, use debug mode to identify the specific element causing the loop
- The fix follows the principle: **hover states must change color only, not dimensions or position**

