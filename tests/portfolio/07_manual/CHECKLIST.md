# Portfolio App - Manual Testing Checklist

**Quick checklist for manual testing**  
**Last Updated:** November 5, 2025

## Pre-Flight Check
- [ ] Environment: UAT / Production
- [ ] User account: Active with appropriate permissions
- [ ] Test data: Created/available
- [ ] Browser: Chrome/Safari/Firefox

---

## Critical Paths

### 1. User Interface
- [ ] All pages load without errors
- [ ] Forms render properly
- [ ] Buttons are clickable and functional
- [ ] Links navigate to correct pages
- [ ] Images/assets load correctly
- [ ] No console errors in browser
- [ ] No 404/500 errors

### 2. Core Functionality
- [ ] Create operations work (C in CRUD)
- [ ] Read/view operations work (R in CRUD)
- [ ] Update operations work (U in CRUD)
- [ ] Delete operations work (D in CRUD)
- [ ] Search/filter functionality works
- [ ] Pagination works (if applicable)
- [ ] Sorting works (if applicable)

### 3. Form Validation
- [ ] Required fields are enforced
- [ ] Invalid data is rejected
- [ ] Error messages are clear and helpful
- [ ] Valid data is accepted
- [ ] Success messages appear
- [ ] Form resets after successful submission

### 4. User Experience
- [ ] Error messages are user-friendly
- [ ] Success confirmations appear
- [ ] Loading states show for async operations
- [ ] Tooltips/help text are helpful
- [ ] Navigation is intuitive
- [ ] UI is visually consistent

### 5. Responsive Design
- [ ] Works on desktop (1920x1080)
- [ ] Works on laptop (1366x768)
- [ ] Works on tablet (iPad)
- [ ] Works on mobile (iPhone/Android)
- [ ] No horizontal scrolling on mobile
- [ ] Touch targets are appropriately sized

### 6. Cross-Browser Compatibility
- [ ] Works in Chrome (latest)
- [ ] Works in Safari (latest)
- [ ] Works in Firefox (latest)
- [ ] Works in Edge (if applicable)
- [ ] No JavaScript errors
- [ ] CSS renders correctly

### 7. Security
- [ ] Login required for protected pages
- [ ] Unauthorized access is blocked (403)
- [ ] Users can only see/edit their own data
- [ ] Staff can see all data (if appropriate)
- [ ] CSRF protection works
- [ ] Session timeout works
- [ ] Logout works correctly

### 8. Performance
- [ ] Page loads in < 2 seconds (desktop)
- [ ] Page loads in < 5 seconds (mobile)
- [ ] Forms submit quickly (< 1 second)
- [ ] No visible lag or freezing
- [ ] Images are optimized
- [ ] Database queries are efficient

### 9. Data Integrity
- [ ] Data saves correctly to database
- [ ] Data displays correctly after save
- [ ] Relationships are maintained
- [ ] Deletes cascade appropriately (or are prevented)
- [ ] No orphaned records

### 10. Edge Cases
- [ ] Handles empty states gracefully
- [ ] Handles very long text input
- [ ] Handles special characters
- [ ] Handles concurrent edits
- [ ] Handles network failures

---

## Dropdown/Selection Filtering Tests

### User Selection Fields
- [ ] Dropdowns show only relevant users (not all 100+)
- [ ] Active users only (no inactive)
- [ ] Correct categories (investors, staff, students, etc.)
- [ ] Count: 10-20 users (not 100+)
- [ ] Clear labels ("Select Client (Investor)")

### Category-Specific Tests (portfolio)
- [ ] [Add app-specific filtering checks here]

---

## Issues Found

| # | Severity | Component | Description | Status |
|---|----------|-----------|-------------|--------|
| 1 | High/Med/Low | | | Open/Fixed |
| 2 | | | | |
| 3 | | | | |

---

## Test Summary

**Date:** ___________  
**Tester:** ___________  
**Environment:** ___________  
**Browser:** ___________  

**Tests Passed:** _____ / _____  
**Critical Issues:** _____  
**Overall Status:** PASS / FAIL  

**Approved for Production:** YES / NO  

---
*Quick reference for manual testing*  
*See: [Full Manual Test Plan](MANUAL_TEST_PLAN.md) for detailed test cases*
