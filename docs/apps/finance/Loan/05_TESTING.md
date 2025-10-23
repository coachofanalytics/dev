# Loan System - Testing

**Last Updated:** October 22, 2025

---

## 🧪 TEST SCENARIOS

### Test 1: Apply for Staff Loan
**Steps:**
1. Login as staff member
2. Navigate to `/finance/loans/apply/`
3. Select loan product
4. Enter requested amount
5. Submit application

**Expected:**
- ✅ Application created
- ✅ Eligibility checked automatically
- ✅ Status: Pending

---

### Test 2: Check KCC Eligibility
**Steps:**
1. Login as KCC member
2. Navigate to eligibility checker
3. Select KCC loan product

**Expected:**
- ✅ Eligibility result shown
- ✅ Reasons displayed if not eligible
- ✅ Alternative products suggested

---

## 📊 TEST RESULTS LOG

| Date | Tests | Pass | Fail |
|------|-------|------|------|
| Oct 13, 2025 | 10 | 10 | 0 |
| Sept 2025 | 8 | 8 | 0 |

---

**See:** 02_REQUIREMENTS.md for acceptance criteria


