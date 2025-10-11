# CODA Investing App - Quick Start Testing Guide

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Create Investor User via Admin**

1. **Start Server** (if not already running):
   ```bash
   cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda
   python3 manage.py runserver 8000
   ```

2. **Login to Admin**:
   - URL: http://localhost:8000/admin/
   - Use your superuser credentials

3. **Create Investor User**:
   - Navigate to: **Accounts > Customer Users**
   - Click **Add Customer User**
   - Fill in:
     ```
     Username: investor_test
     Email: investor@codaplatform.com
     First name: John
     Last name: Investor
     Category: INVESTOR
     Password: Test@1234
     Active: ✓ (checked)
     Staff: ☐ (unchecked)
     Superuser: ☐ (unchecked)
     ```
   - Click **Save**

### **Step 2: Login as Investor**

1. **Logout from Admin**
2. **Navigate to Login**: http://localhost:8000/accounts/login/
3. **Enter Credentials**:
   - Username: `investor_test`
   - Password: `Test@1234`
4. **Click Login**

---

## 🧪 **Quick Test Checklist** (Critical Buttons Only)

### ✅ **Phase 1: Navigation & Access** (5 min)
- [ ] Login works → Dashboard loads
- [ ] Main navigation visible
- [ ] User name displayed in header
- [ ] All menu items clickable

### ✅ **Phase 2: Investing Home** (3 min)
- **URL**: http://localhost:8000/investing/
- [ ] Click "Investing" in menu
- [ ] Page loads without errors
- [ ] All feature cards visible
- [ ] "View Plans" button works
- [ ] "Apply Now" button works

### ✅ **Phase 3: Investment Dashboard** (5 min)
- **URL**: http://localhost:8000/investing/dashboard/
- [ ] Click "Dashboard" link
- [ ] 4 summary cards display (Total Invested, Current Value, Returns, Return %)
- [ ] Investment table loads
- [ ] "View Details" buttons work
- [ ] "Create Investment" button works

### ✅ **Phase 4: Individual Investments** (5 min)
- **URL**: http://localhost:8000/investing/individual-investments/
- [ ] Click "My Investments" link
- [ ] Summary cards display correctly
- [ ] Investment list/table loads
- [ ] "Create New Investment" button works
- [ ] "View Dashboard" button works
- [ ] "Back to Investing Home" button works

### ✅ **Phase 5: Investment Application** (7 min)
- **URL**: http://localhost:8000/investing/apply/
- [ ] Click "Apply for Investment" button
- [ ] Form loads completely
- [ ] Investment plan cards display
- [ ] Can select different plans
- [ ] Amount input field works
- [ ] Duration dropdown works
- [ ] "Submit Application" button works
- [ ] Form validation works (try submitting with $500 - should fail)

### ✅ **Phase 6: Risk Management** (5 min)
- **URL**: http://localhost:8000/investing/risk/risk-dashboard/
- [ ] Click "Risk Management" (if available in menu)
- [ ] Risk dashboard loads
- [ ] 4 summary cards display (Total, High Risk, Alerts, Compliance)
- [ ] Risk distribution chart renders
- [ ] Risk trend chart renders
- [ ] Active alerts panel loads
- [ ] Recent assessments panel loads
- [ ] Compliance status table loads
- [ ] All quick action buttons work

### ✅ **Phase 7: Portfolio** (3 min)
- **URL**: http://localhost:8000/investing/myportfolio/
- [ ] Click "Portfolio" link
- [ ] Portfolio list loads
- [ ] "Create Portfolio Entry" button works
- [ ] Table displays correctly (if has data)

### ✅ **Phase 8: Create Individual Investment** (7 min)
- **URL**: http://localhost:8000/investing/create-individual-investment/
- [ ] Navigate to create investment page
- [ ] Form displays all fields
- [ ] Fill in test data:
  ```
  Investment Type: Equity Investment
  Amount: $10,000
  Duration: 12 months
  Purpose: Test investment for portfolio growth
  Expected Return: 8%
  ```
- [ ] Submit button works
- [ ] Success message displays
- [ ] Redirects to appropriate page

### ✅ **Phase 9: Investment Plans** (3 min)
- **URL**: http://localhost:8000/investing/investmentplans/
- [ ] Click "Investment Plans" link
- [ ] Plans list loads
- [ ] All tiers display (Tier 1, 2, 3)
- [ ] Plan details visible
- [ ] "Apply" buttons work

### ✅ **Phase 10: Logout** (1 min)
- [ ] Click "Logout" button
- [ ] Successfully logged out
- [ ] Redirected to login page
- [ ] Can't access protected pages

---

## 🎯 **Critical Test Results**

**Total Tests**: 10 Phases × ~5 tests each = **~50 critical tests**

### **Pass/Fail Tracking**:
```
Phase 1: Navigation & Access      [ ] PASS  [ ] FAIL  Notes: ______________
Phase 2: Investing Home          [ ] PASS  [ ] FAIL  Notes: ______________
Phase 3: Investment Dashboard     [ ] PASS  [ ] FAIL  Notes: ______________
Phase 4: Individual Investments   [ ] PASS  [ ] FAIL  Notes: ______________
Phase 5: Investment Application   [ ] PASS  [ ] FAIL  Notes: ______________
Phase 6: Risk Management         [ ] PASS  [ ] FAIL  Notes: ______________
Phase 7: Portfolio               [ ] PASS  [ ] FAIL  Notes: ______________
Phase 8: Create Investment       [ ] PASS  [ ] FAIL  Notes: ______________
Phase 9: Investment Plans        [ ] PASS  [ ] FAIL  Notes: ______________
Phase 10: Logout                 [ ] PASS  [ ] FAIL  Notes: ______________
```

---

## 🐛 **Quick Bug Report Template**

If you find issues:

```markdown
### Bug #1
- **Page**: _____________________
- **Button/Link**: _____________________
- **Expected**: _____________________
- **Actual**: _____________________
- **Error Message**: _____________________
- **Screenshot**: _____________________
```

---

## 📊 **Key URLs for Testing**

| Feature | URL |
|---------|-----|
| **Login** | http://localhost:8000/accounts/login/ |
| **Investing Home** | http://localhost:8000/investing/ |
| **Dashboard** | http://localhost:8000/investing/dashboard/ |
| **Individual Investments** | http://localhost:8000/investing/individual-investments/ |
| **Create Investment** | http://localhost:8000/investing/create-individual-investment/ |
| **Apply for Investment** | http://localhost:8000/investing/apply/ |
| **Risk Dashboard** | http://localhost:8000/investing/risk/risk-dashboard/ |
| **Portfolio** | http://localhost:8000/investing/myportfolio/ |
| **Investment Plans** | http://localhost:8000/investing/investmentplans/ |
| **Admin** | http://localhost:8000/admin/ |

---

## 💡 **Pro Testing Tips**

1. **Keep Browser Console Open** (F12):
   - Watch for JavaScript errors
   - Check network requests
   - Monitor API calls

2. **Test in Multiple Browsers**:
   - Chrome
   - Firefox
   - Safari (if on Mac)

3. **Test Responsiveness**:
   - Resize browser window
   - Test on mobile device
   - Use Chrome DevTools device emulation

4. **Take Screenshots**:
   - Capture any errors
   - Document successful flows
   - Record UI issues

5. **Test Data Persistence**:
   - Create investment → Logout → Login → Verify data still there
   - Update investment → Refresh page → Verify update persisted

---

## ✅ **Success Criteria**

The app passes testing if:
- [ ] All 10 phases complete without critical errors
- [ ] All buttons and links are clickable and functional
- [ ] No 500 errors occur
- [ ] Forms submit successfully
- [ ] Data displays correctly
- [ ] Navigation works smoothly
- [ ] User can complete full investment workflow
- [ ] Logout works properly

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: Can't Login**
- **Solution**: Verify user created correctly in admin
- **Check**: User is active, password is correct

### **Issue 2: Page Shows 404**
- **Solution**: Check URL spelling
- **Check**: Server is running on correct port

### **Issue 3: Blank Dashboard**
- **Solution**: May need sample data
- **Check**: Create test investment in admin

### **Issue 4: Forms Don't Submit**
- **Solution**: Check browser console for errors
- **Check**: Verify CSRF token present

### **Issue 5: Charts Don't Load**
- **Solution**: Check if Chart.js library loaded
- **Check**: Browser console for JavaScript errors

---

## 📋 **Final Checklist**

Before marking as complete:
- [ ] Server running successfully
- [ ] Test user created and active
- [ ] All 10 test phases attempted
- [ ] Critical bugs documented
- [ ] Screenshots captured (if issues found)
- [ ] Test results recorded
- [ ] Summary report created

---

**Test Conducted**: __________________  
**Date**: __________________  
**Overall Result**: [ ] PASS  [ ] FAIL  
**Notes**: _________________________________

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**Estimated Time**: 30-45 minutes
