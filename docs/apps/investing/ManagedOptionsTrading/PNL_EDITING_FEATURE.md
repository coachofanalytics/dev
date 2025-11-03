# P&L Editing Feature - COMPLETE ✅

## Overview

Staff can now manually adjust position P&L values directly from the position detail page. All adjustments are logged with reasons for full audit trail.

---

## ✅ What Was Implemented

### 1. **Database/Model Layer**
- Added `'pnl_adjusted'` activity type to `TradingActivity.ACTIVITY_TYPE_CHOICES`
- Migration: `0007_add_pnl_adjustment_activity.py` (already run)

### 2. **View Layer**
**File**: `coda/investing/views/managed_trading/positions.py`

- `adjust_position_pnl()` view (lines 388-472)
  - **Permission**: Staff only (`@staff_member_required`)
  - **Method**: POST only (`@require_POST`)
  - **Parameters**:
    - `adjustment_type`: 'premium' (entry) or 'exit' (close)
    - `new_value`: New premium amount
    - `reason`: Required explanation
  - **Logging**: Creates `TradingActivity` record with:
    - Old/new values
    - Old/new P&L
    - Staff member who made change
    - Detailed reason
    - Full data snapshot for audit

### 3. **URL Pattern**
**File**: `coda/investing/urls_managed_trading.py` (line 64-66)

```python
path('managed/positions/<int:position_id>/adjust-pnl/', 
     positions.adjust_position_pnl, 
     name='adjust_position_pnl'),
```

### 4. **Template/UI**
**File**: `coda/investing/templates/investing/managed/position_detail.html`

**Enhanced Position Detail Page**:
- Shows 4 metric cards: Premium, Capital, P&L, Expiration
- **"✏️ Edit P&L" button** on P&L card (staff only)
- Position legs table
- **Activity Log** table (highlights P&L adjustments in yellow)

**P&L Edit Modal**:
- Shows current values (Premium Collected, Exit Premium, Current P&L)
- Dropdown to select what to adjust
- Input for new value
- **Required reason field** (audit trail)
- Warning about logging
- Confirmation dialog

---

## 🎯 How It Works

### User Flow:

1. **Staff** views position detail page
2. Clicks **"✏️ Edit P&L"** button on P&L card
3. Modal opens showing current values
4. Selects what to adjust:
   - **Premium Collected** (if entry price was wrong)
   - **Exit Premium** (if close price was wrong)
5. Enters new value (e.g., $150.00)
6. **Must provide reason** (e.g., "Early exit at better price")
7. Clicks "Save Adjustment"
8. Confirms action
9. P&L updated, adjustment logged

### What Gets Logged:

```
TradingActivity created:
- Type: 'pnl_adjusted'
- Description: "P&L manually adjusted by John Smith. 
               Premium Collected: $100.00 → $150.00. 
               P&L changed: $100.00 → $150.00. 
               Reason: Early exit at better price"
- Performed By: John Smith (staff)
- Data Snapshot: {
    "field_changed": "Premium Collected",
    "old_value": "100.00",
    "new_value": "150.00",
    "old_pnl": "100.00",
    "new_pnl": "150.00",
    "reason": "Early exit at better price",
    "position_status": "open"
  }
```

---

## 🧪 Testing Guide

### Test 1: Adjust Open Position P&L

```bash
# 1. Navigate to position detail
http://localhost:8000/investing/managed/positions/123/

# 2. As staff, click "✏️ Edit P&L" button

# 3. In modal:
   - Select: "Premium Collected (Entry)"
   - New Value: 150.00
   - Reason: "Adjusted for partial fill"
   - Click "Save Adjustment"

# 4. Verify:
   - P&L card updates to $150.00
   - Success message shown
   - Activity log shows adjustment (yellow row)
```

### Test 2: Adjust Closed Position Exit

```bash
# 1. For a CLOSED position
   - Select: "Exit Premium (Close)"
   - New Value: 50.00
   - Reason: "Early exit before expiration"
   - Click "Save Adjustment"

# 2. Verify:
   - Realized P&L recalculates
   - Activity log shows who, when, why
```

### Test 3: Verify Audit Trail

```python
from investing.models import TradingActivity

# Get all P&L adjustments
adjustments = TradingActivity.objects.filter(activity_type='pnl_adjusted')

for adj in adjustments:
    print(f"Position: {adj.position.symbol}")
    print(f"Adjusted by: {adj.performed_by.get_full_name()}")
    print(f"Date: {adj.created_at}")
    print(f"Reason: {adj.data_snapshot['reason']}")
    print(f"Old P&L: ${adj.data_snapshot['old_pnl']}")
    print(f"New P&L: ${adj.data_snapshot['new_pnl']}")
    print("---")
```

---

## 🔐 Security & Compliance

### Who Can Edit:
- ✅ **Staff only** (`@staff_member_required` decorator)
- ❌ Clients cannot edit
- ❌ Account managers cannot edit (unless also staff)

### Audit Trail:
- ✅ Every adjustment logged
- ✅ Who made the change
- ✅ When it was made
- ✅ What was changed (old → new)
- ✅ **Why it was changed** (required reason)
- ✅ Full data snapshot in JSON

### Validation:
- ✅ Reason field required (cannot submit without)
- ✅ New value must be numeric
- ✅ Adjustment type must be valid
- ✅ Confirmation dialog prevents accidental changes

---

## 📊 UI Screenshots (Description)

### Position Detail Page:
```
┌─────────────────────────────────────────────────────────┐
│ AAPL - Bull Put Spread                                  │
│ Account: CODA-OPT-005 | Status: Open                   │
└─────────────────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Premium  │ │ Capital  │ │   P&L    │ │Expiration│
│ $150.00  │ │ $500     │ │ $150.00  │ │Dec 13    │
│          │ │          │ │ ✏️ Edit  │ │ 42 days  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

Position Legs:
┌─────────────┬────────┬──────────┬─────────┐
│    Type     │ Strike │Contracts │ Premium │
├─────────────┼────────┼──────────┼─────────┤
│ Short Put   │  $95   │    1     │ $1.50   │
│ Long Put    │  $90   │    1     │ $0.00   │
└─────────────┴────────┴──────────┴─────────┘

Activity Log:
┌────────────┬──────────────┬─────────────────┬──────┐
│    Date    │     Type     │  Description    │  By  │
├────────────┼──────────────┼─────────────────┼──────┤
│Nov 01 14:30│ P&L Adjusted │ Premium: $100→  │ John │
│            │              │ $150. Reason:   │      │
│            │              │ Early exit      │      │
└────────────┴──────────────┴─────────────────┴──────┘
```

### Edit P&L Modal:
```
┌─────────────────────────────────────────┐
│ ✏️ Edit Position P&L                    │
├─────────────────────────────────────────┤
│ Current Values:                         │
│   Premium Collected: $100.00            │
│   Exit Premium: $0.00                   │
│   Current P&L: $100.00                  │
│                                         │
│ What to Adjust: [Premium Collected ▼]  │
│ New Value: [150.00________]             │
│ Reason*: [Early exit at better price__] │
│                                         │
│ ⚠️  This adjustment will be logged      │
│                                         │
│ [Cancel]        [💾 Save Adjustment]    │
└─────────────────────────────────────────┘
```

---

## 📝 Code Files Modified

| File | Purpose | Lines |
|------|---------|-------|
| `investing/models.py` | Added 'pnl_adjusted' activity type | 1 line |
| `investing/migrations/0007_add_pnl_adjustment_activity.py` | Migration | Auto-generated |
| `investing/views/managed_trading/positions.py` | View logic for adjustment | 85 lines |
| `investing/urls_managed_trading.py` | URL pattern | 3 lines |
| `investing/templates/investing/managed/position_detail.html` | UI/Modal | 217 lines |

**Total**: 5 files, ~306 lines of code

---

## ✅ Requirements Met

| Requirement | Status | Implementation |
|------------|--------|----------------|
| **Where**: Position detail page | ✅ | Button on P&L card |
| **Who**: Staff only | ✅ | `@staff_member_required` |
| **What**: Reason for adjustment | ✅ | Required textarea field |
| **When**: Both open and closed | ✅ | Works for all statuses |
| **Audit Trail**: Full logging | ✅ | `TradingActivity` with data snapshot |

---

## 🚀 Deployment Steps

1. **Migration already run**: `0007_add_pnl_adjustment_activity.py` ✅

2. **Test locally**:
```bash
cd coda
python manage.py runserver 8000
# Navigate to: /investing/managed/positions/<id>/
# Test P&L editing as staff user
```

3. **Deploy to UAT**:
```bash
git add -A
git commit -m "Add P&L editing feature with full audit trail"
git push uat 25.10_CODA_UAT_CM
```

4. **Run migration on UAT**:
```bash
heroku run "cd coda && python manage.py migrate investing" --app codamakutano
```

5. **Verify in UAT**:
- Login as staff
- View any position
- Test P&L adjustment
- Check activity log

---

## 🎉 SUCCESS!

**ALL 6 FEATURES NOW COMPLETE:**

1. ✅ Balance Tracking (Total, Deployed, Available, P&L)
2. ✅ Position Sizing Rules (2% max, 15% total)
3. ✅ OptionPlay Scraper Integration
4. ✅ Fallback Order Fix (API → Scraper → Mock)
5. ✅ P&L Adjustment Activity Type
6. ✅ **P&L Editing UI** (THIS FEATURE)

---

**Implementation Date**: November 1, 2025  
**Status**: COMPLETE & READY FOR DEPLOYMENT 🚀  
**Test Status**: Pending user testing

---

*Part of CODA Managed Trading System - Final Feature*

