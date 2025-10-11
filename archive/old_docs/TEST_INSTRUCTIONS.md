# 🧪 Finance App Testing Instructions

**Date:** October 7, 2025  
**Server:** http://127.0.0.1:8000  
**Status:** ✅ READY FOR TESTING

---

## 🎯 QUICK START

### 1. Access the Application
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

### 2. Test Users (All passwords: `test123`)

| Username | Password | Role | Use For |
|----------|----------|------|---------|
| `budget_manager` | `test123` | Manager (Staff) | Approving requests, viewing all budgets |
| `finance_officer` | `test123` | Officer | Creating budget requests |
| `it_manager` | `test123` | Department Head | Department-specific testing |
| `investor_user` | `test123` | Investor | Investment dashboard testing |

---

## 📋 TEST WORKFLOWS

### **Workflow 1: Budget Dashboard** 
**User:** `budget_manager`

1. Login at: http://127.0.0.1:8000/accounts/login/
2. Navigate to: http://127.0.0.1:8000/finance/budget-dashboard/coda/
3. **Verify:**
   - ✅ Dashboard loads without errors
   - ✅ Budget categories display
   - ✅ Totals calculate correctly
   - ✅ Charts/graphs render
4. **Test Buttons:**
   - Click "Add Budget" button
   - Click "Edit" on any budget item
   - Click "Export" button (if present)

---

### **Workflow 2: Create Budget Request**
**User:** `finance_officer`

1. Login at: http://127.0.0.1:8000/accounts/login/
2. Navigate to: http://127.0.0.1:8000/finance/budget-requests/
3. Click "New Budget Request" or "Create Request"
4. **Fill Form:**
   - Purpose: "Test Budget Request"
   - Category: Select any
   - Amount: 10000
   - Currency: KES
   - Priority: Normal
5. Click "Submit"
6. **Verify:**
   - ✅ Success message appears
   - ✅ Request appears in list
   - ✅ Status shows "Pending"

---

### **Workflow 3: Approve Budget Request**
**User:** `budget_manager`

1. Login at: http://127.0.0.1:8000/accounts/login/
2. Navigate to: http://127.0.0.1:8000/finance/budget-approvals/
3. Find the test request created above
4. Click "Approve" button
5. Add approval notes (optional)
6. Confirm approval
7. **Verify:**
   - ✅ Status changes to "Approved"
   - ✅ Approval notification sent
   - ✅ Audit log created

---

### **Workflow 4: Smart Transaction Entry**
**User:** `budget_manager` or `finance_officer`

1. Navigate to: http://127.0.0.1:8000/finance/smart-transaction-entry/
2. **Fill Form:**
   - Amount: 5000
   - Category: Select from dropdown
   - Subcategory: Should auto-populate
   - Description: "Test transaction"
   - Date: Today
3. Click "Save Transaction"
4. **Verify:**
   - ✅ Transaction saved
   - ✅ Cascading dropdowns work
   - ✅ AI predictions work (if enabled)

---

### **Workflow 5: Admin Interface**
**User:** `budget_manager` (staff user)

1. Navigate to: http://127.0.0.1:8000/admin/
2. Login with `budget_manager` / `test123`
3. **Test Admin Sections:**
   - ✅ Finance → Transactions (should list properly)
   - ✅ Finance → Budget Categories (no errors)
   - ✅ Finance → Budget Requests (fields match)
   - ✅ Finance → Loan Applications (fields correct)
4. **Try Editing:**
   - Click on any transaction
   - Verify all fields display correctly
   - Try saving (or cancel)

---

### **Workflow 6: Automation Dashboard**
**User:** `budget_manager`

1. Navigate to: http://127.0.0.1:8000/finance/automation/
2. **Verify:**
   - ✅ Dashboard loads
   - ✅ Approval policies display
   - ✅ Automation rules show
3. **Test:**
   - Click "Add Policy" (if button exists)
   - View existing policies
   - Check audit logs

---

## 🔍 SPECIFIC THINGS TO TEST

### **Buttons to Click:**
- [ ] "Add Budget" button
- [ ] "Edit Budget" button
- [ ] "Delete" button (if present)
- [ ] "Approve" button
- [ ] "Reject" button
- [ ] "Export" button
- [ ] "View Details" link
- [ ] "Save" button
- [ ] "Cancel" button
- [ ] "Submit" button

### **Forms to Fill:**
- [ ] Budget request form
- [ ] Transaction entry form
- [ ] Budget edit form
- [ ] Approval form

### **Data to Verify:**
- [ ] Budget totals calculate correctly
- [ ] Categories display properly
- [ ] Transactions list loads
- [ ] User permissions work
- [ ] Dates format correctly
- [ ] Currency displays properly

---

## 🐛 HOW TO REPORT ISSUES

If you find any issues, note:

1. **URL** where error occurred
2. **User** you were logged in as
3. **Action** you were trying to perform
4. **Error Message** (take screenshot)
5. **Expected** vs **Actual** behavior

### Browser Console (Important!)
Press `F12` in your browser to open Developer Tools and check:
- **Console tab** for JavaScript errors (red text)
- **Network tab** for failed requests (red status codes)

---

## 📊 SUCCESS CRITERIA

### ✅ Core Functionality:
- [ ] Users can login successfully
- [ ] Budget dashboard displays without errors
- [ ] Budget requests can be created
- [ ] Budget requests can be approved/rejected
- [ ] Transactions can be entered
- [ ] Admin interface works for all models
- [ ] All buttons trigger correct actions
- [ ] All forms submit successfully
- [ ] No 500 errors on any page
- [ ] No JavaScript console errors

### ✅ Data Integrity:
- [ ] Budget calculations are correct
- [ ] Approvals update status properly
- [ ] Transactions save with correct data
- [ ] Audit logs are created
- [ ] Timestamps are accurate

### ✅ User Experience:
- [ ] Pages load quickly (<2 seconds)
- [ ] Forms are intuitive
- [ ] Error messages are helpful
- [ ] Success messages appear
- [ ] Navigation is clear

---

## 🚀 NEXT STEPS AFTER TESTING

1. **If everything works:**
   - Document any minor UI improvements needed
   - Prepare for UAT deployment
   - Create deployment checklist

2. **If issues found:**
   - Document each issue clearly
   - Prioritize: Critical → Major → Minor
   - Fix critical issues before UAT
   - Minor issues can be fixed in UAT

---

## 📞 NEED HELP?

Check these files for more info:
- `coda/docs/apps/finance/TESTING_GUIDE.md` - Comprehensive testing guide
- `coda/docs/apps/finance/FINAL_STATUS_REPORT.md` - What was fixed
- `coda/docs/apps/finance/ADMIN_FIX_MAPPING.md` - Admin field mappings

---

## 🎉 TESTING CHECKLIST

Use this quick checklist:

- [ ] Server is running
- [ ] Can access http://127.0.0.1:8000
- [ ] Can login as budget_manager
- [ ] Budget dashboard loads
- [ ] Can create budget request
- [ ] Can approve budget request  
- [ ] Smart transaction entry works
- [ ] Admin interface accessible
- [ ] No console errors
- [ ] All buttons work
- [ ] Forms submit correctly

**When all checked:** ✅ **READY FOR UAT DEPLOYMENT!**

---

**Happy Testing! 🧪**

