# Manual Testing Checklist - Budget System UAT

**Environment:** https://codamakutano.herokuapp.com  
**Date:** October 1, 2025  
**Version:** v791+  
**Tester:** _______________

---

## 🔐 **Pre-Testing Setup**

- [ ] **Login URL:** https://codamakutano.herokuapp.com/social_accounts/login/
- [ ] **Test User Created:** Yes / No
- [ ] **Browser:** Chrome / Firefox / Safari / Edge
- [ ] **Clear Cache:** Ctrl+Shift+Del (clear browser cache)
- [ ] **Open DevTools:** F12 (to watch for console errors)

---

## ✅ **Test 1: Login & Navigation**

**Time:** 5 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Navigate to https://codamakutano.herokuapp.com
2. [ ] Click "Login" or navigate to login page
3. [ ] Enter credentials and login
4. [ ] Verify successful login (redirected to homepage)
5. [ ] Navigate to Main Menu → **Finance**
6. [ ] Look for **Budget Dashboard** link
7. [ ] Click on Budget Dashboard

### Expected Results:
- [ ] Login successful (no errors)
- [ ] Homepage loads
- [ ] Finance menu visible
- [ ] Budget Dashboard link present
- [ ] Can navigate to budget section

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 2: Dashboard Overview Tab**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Navigate to `/finance/budget-dashboard/<your-slug>/`
2. [ ] Verify "Overview" tab is active/visible
3. [ ] Check budget summary displays
4. [ ] Check budget list/table displays
5. [ ] Verify data shows (259 budgets or filtered set)
6. [ ] Test department filter dropdown
7. [ ] Select different department
8. [ ] Verify filtering works
9. [ ] Check page load time (<3 seconds)
10. [ ] Open browser console (F12) - check for errors

### Expected Results:
- [ ] Overview tab loads successfully
- [ ] Budget summary shows totals
- [ ] Budget list displays correctly
- [ ] 259 budgets visible (or filtered count)
- [ ] Department filter works
- [ ] No console errors
- [ ] Page loads in <3 seconds

### Screenshots:
- [ ] Take screenshot of overview tab

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 3: Dashboard Estimation Tab**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Click "Estimation" tab
2. [ ] Verify tab content loads
3. [ ] Check for AI estimation interface
4. [ ] Look for estimation method selector
5. [ ] Try to input test budget parameters (if form present)
6. [ ] Check for "Generate Estimate" button
7. [ ] Verify no errors in console
8. [ ] Check page responsiveness

### Expected Results:
- [ ] Estimation tab loads
- [ ] Estimation interface displays
- [ ] Forms/inputs work
- [ ] No console errors
- [ ] Page responsive

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 4: Dashboard Planning Tab**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Click "Planning" tab
2. [ ] Verify planning interface loads
3. [ ] Check for data quality indicators
4. [ ] Look for planning tools
5. [ ] Test any input fields
6. [ ] Verify no console errors

### Expected Results:
- [ ] Planning tab loads
- [ ] Interface displays correctly
- [ ] Data quality scores visible (91%)
- [ ] Tools functional
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 5: Dashboard Approvals Tab**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Click "Approvals" tab
2. [ ] Check if pending approvals list displays
3. [ ] Verify approval workflow interface
4. [ ] Check approval history (if any)
5. [ ] Verify no console errors

### Expected Results:
- [ ] Approvals tab loads
- [ ] Approval list displays (may be empty)
- [ ] Workflow interface visible
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 6: Dashboard Analytics Tab**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Click "Analytics" tab
2. [ ] Check if charts/graphs display
3. [ ] Verify data visualizations load
4. [ ] Test time period filters (if present)
5. [ ] Check for export functionality
6. [ ] Verify no console errors

### Expected Results:
- [ ] Analytics tab loads
- [ ] Charts display correctly
- [ ] Data visualizations work
- [ ] Filters functional
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 7: Planning - Weekly Timeframe**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Navigate to `/finance/budget-planning/<slug>/?timeframe=weekly`
2. [ ] Verify weekly planning interface loads
3. [ ] Check weekly breakdown displays
4. [ ] Test week selector (if present)
5. [ ] Verify calculations correct
6. [ ] Test save functionality (if applicable)
7. [ ] Check for console errors

### Expected Results:
- [ ] Weekly planning loads (<3 seconds)
- [ ] Weekly breakdown visible
- [ ] Week selector works
- [ ] Data displays correctly
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 8: Planning - Monthly Timeframe**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Navigate to `/finance/budget-planning/<slug>/?timeframe=monthly`
2. [ ] Verify monthly planning loads
3. [ ] Check monthly breakdown
4. [ ] Test month selector
5. [ ] Verify month-to-month comparisons
6. [ ] Check calculations
7. [ ] Verify no errors

### Expected Results:
- [ ] Monthly planning loads
- [ ] Monthly data displays
- [ ] Comparisons work
- [ ] Calculations correct
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 9: Planning - Yearly Timeframe**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Navigate to `/finance/budget-planning/<slug>/?timeframe=yearly`
2. [ ] Verify yearly planning loads
3. [ ] Check annual breakdown
4. [ ] Test year selector
5. [ ] Verify year-over-year comparisons
6. [ ] Check calculations
7. [ ] Verify no errors

### Expected Results:
- [ ] Yearly planning loads
- [ ] Annual data displays
- [ ] Comparisons work
- [ ] Calculations correct
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 10: Planning - Multi-Year Timeframe**

**Time:** 10 minutes  
**Priority:** 🟢 MEDIUM

### Steps:
1. [ ] Navigate to `/finance/budget-planning/<slug>/?timeframe=multi_year`
2. [ ] Verify multi-year planning loads
3. [ ] Check long-term projections
4. [ ] Test date range selector
5. [ ] Verify trend analysis
6. [ ] Check calculations
7. [ ] Verify no errors

### Expected Results:
- [ ] Multi-year planning loads
- [ ] Projections display
- [ ] Trend analysis works
- [ ] Calculations correct
- [ ] No errors

### Actual Results:
```
[Record what happened]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 11: URL Redirects (Old URLs)**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Test old URL: `/finance/automated-budget-estimation/`
   - Should redirect to: `/finance/budget-dashboard/<slug>/?tab=estimation`
2. [ ] Test old URL: `/finance/enhanced-budget-dashboard/<slug>/`
   - Should redirect to: `/finance/budget-dashboard/<slug>/?tab=planning`
3. [ ] Test old URL: `/finance/weekly-planning/<slug>/`
   - Should redirect to: `/finance/budget-planning/<slug>/?timeframe=weekly`
4. [ ] Test old URL: `/finance/monthly-planning/<slug>/`
   - Should redirect to: `/finance/budget-planning/<slug>/?timeframe=monthly`
5. [ ] Test old URL: `/finance/yearly-planning/<slug>/`
   - Should redirect to: `/finance/budget-planning/<slug>/?timeframe=yearly`

### Expected Results:
- [ ] All old URLs redirect automatically (<1 second)
- [ ] Correct tab/timeframe set
- [ ] No 404 errors
- [ ] Data displays correctly
- [ ] Bookmarks still work

### Actual Results:
```
Old URL 1: [Result]
Old URL 2: [Result]
Old URL 3: [Result]
Old URL 4: [Result]
Old URL 5: [Result]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 12: Mobile Responsiveness**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Open browser DevTools (F12)
2. [ ] Toggle device toolbar (Ctrl+Shift+M)
3. [ ] Test on iPhone size (375x667)
4. [ ] Test on iPad size (768x1024)
5. [ ] Verify layout adapts
6. [ ] Check tabs are clickable
7. [ ] Verify no horizontal scrolling
8. [ ] Test forms on touch screen simulation
9. [ ] Check navigation menu

### Expected Results:
- [ ] Layout responsive on mobile
- [ ] Tabs accessible and functional
- [ ] Text readable (no tiny font)
- [ ] No horizontal scroll
- [ ] Forms work on touch
- [ ] Navigation responsive

### Actual Results:
```
iPhone: [Result]
iPad: [Result]
```

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 13: Performance Testing**

**Time:** 10 minutes  
**Priority:** 🟡 HIGH

### Steps:
1. [ ] Open browser DevTools → Network tab
2. [ ] Reload dashboard page
3. [ ] Record page load time
4. [ ] Check number of requests
5. [ ] Verify no failed requests (red)
6. [ ] Test with slow 3G (DevTools → Network → Throttling)
7. [ ] Check console for warnings

### Expected Results:
- [ ] Dashboard loads in <3 seconds
- [ ] Reasonable request count (<50)
- [ ] No failed requests
- [ ] Works on slow connection
- [ ] No console warnings/errors

### Performance Metrics:
- Load Time: _______ seconds
- Total Requests: _______
- Failed Requests: _______
- Page Size: _______ MB

### Issues Found:
```
[List any problems]
```

---

## ✅ **Test 14: Data Integrity**

**Time:** 10 minutes  
**Priority:** 🔴 CRITICAL

### Steps:
1. [ ] Navigate to overview tab
2. [ ] Count visible budgets
3. [ ] Check budget amounts display correctly
4. [ ] Verify dates show properly
5. [ ] Check department names correct
6. [ ] Verify no "undefined" or "null" displayed
7. [ ] Test sorting (if available)
8. [ ] Test search/filter

### Expected Results:
- [ ] Budget count: 259 (or correct filtered amount)
- [ ] All amounts display correctly
- [ ] All dates formatted properly
- [ ] All text displays (no undefined/null)
- [ ] Sorting works (if present)
- [ ] Search/filter works (if present)

### Data Sample:
```
Budget 1: [Name, Amount, Date]
Budget 2: [Name, Amount, Date]
Budget 3: [Name, Amount, Date]
```

### Issues Found:
```
[List any problems]
```

---

## 📊 **Testing Summary**

### Overall Results:

| Test Category | Tests Passed | Tests Failed | Pass Rate |
|---------------|--------------|--------------|-----------|
| Critical      | ___/7        | ___/7        | ___%      |
| High          | ___/5        | ___/5        | ___%      |
| Medium        | ___/2        | ___/2        | ___%      |
| **TOTAL**     | **___/14**   | **___/14**   | **___%**  |

### Critical Bugs Found:
```
1. [Bug description]
2. [Bug description]
3. [Bug description]
```

### High Priority Issues:
```
1. [Issue description]
2. [Issue description]
```

### Medium/Low Issues:
```
1. [Issue description]
2. [Issue description]
```

### Recommendation:
- [ ] ✅ **APPROVE** - Ready for production (0 critical, 0-2 high issues)
- [ ] ⚠️ **APPROVE WITH FIXES** - Minor issues need fixing (0 critical, 3-5 high issues)
- [ ] ❌ **REJECT** - Critical issues found (1+ critical or 6+ high issues)

### Comments:
```
[Your overall feedback and recommendations]
```

---

## 📝 **Sign-Off**

**Tester Name:** _______________  
**Date:** _______________  
**Time Spent:** _______ hours  
**Signature:** _______________

---

**Next Steps:**
1. Submit this checklist to project lead
2. Create bug tickets for all critical/high issues
3. Retest after fixes deployed
4. Schedule production deployment after approval

---

**For Support:**
- **Technical Issues:** [IT Support Email]
- **Questions:** [Project Lead Contact]
- **Documentation:** `/coda/docs/apps/finance/Budgeting/`



