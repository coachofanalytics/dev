# 🧪 **LOCAL TESTING GUIDE - Budget Request & Approval Workflow**

**Date:** October 12, 2025  
**Server:** http://127.0.0.1:8000  
**Status:** ✅ Server Running & All URLs Responding

---

## **🎯 TESTING OVERVIEW**

We'll test the complete budget workflow in this order:
1. ✅ Login and access dashboard
2. ✅ Create budget request
3. ✅ View "My Requests" list
4. ✅ Edit draft request
5. ✅ Submit for approval
6. ✅ Approve as staff user
7. ✅ View approval dashboard
8. ✅ Test budget comparison

---

## **📝 TEST 1: Login & Dashboard Access**

### **Steps:**
1. Open browser: http://127.0.0.1:8000
2. Login with your credentials
3. Navigate to: http://127.0.0.1:8000/finance/budget-dashboard/coda/

### **Expected Results:**
- ✅ Login successful
- ✅ Budget dashboard loads
- ✅ Overview tab visible
- ✅ Three new buttons visible:
  - 🔵 **"Create Budget Request"** (Blue/Primary)
  - ⚪ **"My Requests"** (Gray/Secondary)
  - 🟡 **"Approvals"** (Yellow/Warning - staff only)

### **What to Check:**
- [ ] All buttons are clickable
- [ ] Button styling is correct
- [ ] Staff-only "Approvals" button appears for staff users
- [ ] Budget categories display correctly
- [ ] Recent budgets show up

---

## **📝 TEST 2: Create Budget Request**

### **Steps:**
1. Click **"Create Budget Request"** button
2. URL should be: http://127.0.0.1:8000/finance/budget-requests/create/
3. Fill out the form:
   - **Amount:** 50000
   - **Currency:** KES
   - **Purpose:** "Test budget request for Q4 2025 marketing campaign"
   - **Department:** Select any
   - **Budget Category:** Select any
   - **Required Date:** Pick a future date
   - **Priority:** High
   - **Cost Center:** TEST-2025-Q4 (optional)
   - **Attachments:** marketing-proposal.pdf (optional)
4. **Leave "Submit for approval" UNCHECKED** (save as draft first)
5. Click **"Create Request"**

### **Expected Results:**
- ✅ Form validation works (try submitting with empty fields first)
- ✅ Date validation prevents past dates
- ✅ Amount validation requires positive number
- ✅ Success message: "Budget request #X created and saved as draft."
- ✅ Redirect to budget request detail page
- ✅ Status badge shows "Draft" (gray)

### **What to Check:**
- [ ] All form fields display correctly
- [ ] Department dropdown populated
- [ ] Budget category dropdown populated
- [ ] Date picker works
- [ ] Form validates before submitting
- [ ] Success message appears
- [ ] Request ID is generated
- [ ] Detail page loads correctly

### **Screenshots to Take:**
1. Empty form
2. Filled form
3. Success message
4. Request detail page

---

## **📝 TEST 3: View "My Requests" List**

### **Steps:**
1. Click **"My Requests"** button on overview tab
2. URL should be: http://127.0.0.1:8000/finance/budget-requests/
3. You should see your draft request

### **Expected Results:**
- ✅ Request list displays
- ✅ Your draft request appears
- ✅ Status badge shows "Draft"
- ✅ Priority badge shows "High"
- ✅ Action buttons visible:
  - 👁️ **View** (eye icon)
  - ✏️ **Edit** (pencil icon)
  - ✈️ **Submit for Approval** (paper plane icon)

### **Test Filters:**
1. **Status Filter:** Select "Draft" → should show only drafts
2. **Department Filter:** Select a department → should filter
3. **Search:** Type "marketing" → should find your request
4. **Clear Filters:** Should reset to show all

### **What to Check:**
- [ ] Request appears in list
- [ ] All fields display correctly (ID, purpose, amount, status, priority)
- [ ] Filters work properly
- [ ] Search works
- [ ] Pagination works (if you have >20 requests)
- [ ] Action buttons are clickable
- [ ] Amount shows correct currency

---

## **📝 TEST 4: Edit Draft Request**

### **Steps:**
1. In "My Requests" list, click **Edit** button (pencil icon)
2. Modify the request:
   - Change **Amount** to 75000
   - Update **Purpose** to add "Updated: includes digital advertising budget"
   - Change **Priority** to "Urgent"
3. **Still leave "Submit for approval" UNCHECKED**
4. Click **"Update Request"**

### **Expected Results:**
- ✅ Edit form loads with existing data
- ✅ All fields are editable
- ✅ Success message: "Budget request #X updated successfully."
- ✅ Redirect back to detail page
- ✅ Updated values display
- ✅ Status still shows "Draft"

### **What to Check:**
- [ ] Form pre-populated with existing data
- [ ] Can modify all fields
- [ ] Validation still works
- [ ] Changes saved correctly
- [ ] Updated timestamp changes
- [ ] Still in draft status

---

## **📝 TEST 5: Submit for Approval**

### **Option A: Submit from Edit Form**
1. Click Edit again
2. This time **CHECK** "Submit for approval immediately"
3. Click **"Update Request"**

### **Option B: Submit from List**
1. Go to "My Requests"
2. Click **Submit for Approval** button (paper plane icon)
3. Confirm in popup

### **Expected Results:**
- ✅ Confirmation dialog appears
- ✅ Success message: "Request submitted for approval!"
- ✅ Status changes from "Draft" to "Submitted" or "Under Review"
- ✅ Status badge color changes (yellow/blue)
- ✅ Edit button disappears (can't edit submitted requests)
- ✅ Email sent to first approver (check logs if configured)

### **What to Check:**
- [ ] Status updates correctly
- [ ] Can no longer edit
- [ ] Approval chain created
- [ ] Current approver assigned
- [ ] Timeline shows submission
- [ ] Email notification sent (if email configured)

### **Check in Detail Page:**
- [ ] Status badge updated
- [ ] "Current Approver" box shows approver
- [ ] "Approval Chain" box shows chain
- [ ] Timeline shows "Submitted" event
- [ ] Edit button removed

---

## **📝 TEST 6: View Approval Dashboard (Staff Only)**

### **Steps:**
1. **If you're staff:** Click **"Approvals"** button on overview tab
2. **If you're not staff:** Login with a staff account
3. URL should be: http://127.0.0.1:8000/finance/budget/coda/approvals/

### **Expected Results:**
- ✅ Approval dashboard loads
- ✅ Statistics cards show:
  - Pending Approval count
  - Approved count
  - Rejected count
  - Total Requests count
- ✅ "Pending Approvals" table shows your submitted request
- ✅ "Recent Approvals" table shows history

### **What to Check:**
- [ ] Statistics are accurate
- [ ] Your request appears in pending table
- [ ] Request shows all details (ID, requester, purpose, amount)
- [ ] Priority badge displays correctly
- [ ] Action buttons visible:
  - 👁️ View
  - ✅ Approve
  - ❌ Reject
- [ ] Recent approvals table shows history

---

## **📝 TEST 7: Approve Request**

### **Option A: From Approval Dashboard**
1. On approval dashboard, click **Approve** button (green checkmark)
2. Confirm approval
3. Watch for success notification

### **Option B: From Detail Page**
1. Click **View** button to see request detail
2. In "Approval Action Required" box
3. Optionally add comments
4. Click **"Approve Request"** button
5. Confirm

### **Expected Results:**
- ✅ Confirmation dialog appears
- ✅ Success message: "Budget request approved successfully!"
- ✅ Page reloads automatically
- ✅ Status changes to "Approved"
- ✅ Status badge turns green
- ✅ Request moves to "Recent Approvals" table
- ✅ Email sent to requester (if configured)

### **What to Check:**
- [ ] Approval processes successfully
- [ ] Status updates to "Approved"
- [ ] Badge color changes to green
- [ ] Request removed from pending
- [ ] Approval timestamp recorded
- [ ] Approver name recorded
- [ ] Email sent to requester

### **View Request as Original User:**
1. Logout staff account
2. Login as original requester
3. Go to "My Requests"
4. Find your request
5. Click to view details

### **Should See:**
- [ ] Status = "Approved" (green badge)
- [ ] Approval chain shows checkmark
- [ ] Timeline shows approval event
- [ ] Approver name visible
- [ ] Approval comments visible (if added)

---

## **📝 TEST 8: Test Rejection (Create Another Request)**

### **Steps:**
1. Create a new budget request (follow TEST 2)
2. Submit it for approval (follow TEST 5)
3. As staff, go to approval dashboard
4. Click **Reject** button (red X)
5. In popup, enter rejection reason: "Budget exceeds department allocation for Q4"
6. Confirm rejection

### **Expected Results:**
- ✅ Rejection reason prompt appears
- ✅ Success message: "Budget request rejected."
- ✅ Status changes to "Rejected"
- ✅ Status badge turns red
- ✅ Email sent to requester with reason

### **View as Requester:**
- [ ] Status = "Rejected" (red badge)
- [ ] Rejection reason visible in red alert box
- [ ] Timeline shows rejection event
- [ ] Rejection timestamp recorded

---

## **📝 TEST 9: Budget Comparison View**

### **Steps:**
1. Go to Budget Dashboard → Overview Tab
2. Click **"View Details"** on any budget category
3. On category detail page, look for **"Compare"** or comparison options
4. If available, test budget vs actual comparison

### **Expected Results:**
- ✅ Category detail page loads
- ✅ Budget breakdown shows
- ✅ If comparison view exists:
  - Chart displays budget vs actual
  - Table shows variance analysis
  - Can select different timeframes

### **What to Check:**
- [ ] Category statistics correct
- [ ] Subcategory breakdown displays
- [ ] Recent transactions show
- [ ] Budget item edit buttons work
- [ ] Comparison features functional

---

## **📝 TEST 10: End-to-End Workflow**

### **Complete Journey:**
1. **Create** budget request (Draft)
2. **Edit** to modify details
3. **Submit** for approval
4. **View** in "My Requests" (status = Under Review)
5. **Login as staff**
6. **See** in approval dashboard
7. **View details** and review
8. **Approve** the request
9. **Logout staff**
10. **Login as requester**
11. **See** approved status
12. **Check** email notifications

### **Success Criteria:**
- [ ] All steps complete without errors
- [ ] Status changes at each stage
- [ ] Emails sent at key points
- [ ] Audit trail complete
- [ ] No broken links or buttons
- [ ] All data persists correctly

---

## **🐛 COMMON ISSUES & SOLUTIONS**

### **Issue 1: "Create Budget Request" button doesn't appear**
**Solution:** Refresh page, check if you're logged in

### **Issue 2: Form validation errors**
**Solution:** Ensure all required fields filled, amount > 0, date in future

### **Issue 3: Can't edit submitted request**
**Solution:** This is correct behavior - only drafts can be edited

### **Issue 4: Approval button doesn't appear**
**Solution:** Check if you're logged in as staff user, check if you're the current approver

### **Issue 5: Email not received**
**Solution:** Email might not be configured in local dev - check console logs instead

### **Issue 6: 500 error on any page**
**Solution:** 
- Check server console for errors
- Verify database is accessible
- Check all model fields match database schema

---

## **✅ TESTING CHECKLIST**

### **Core Functionality**
- [ ] Budget request creation works
- [ ] Draft saving works
- [ ] Request editing works
- [ ] Submission for approval works
- [ ] Approval process works
- [ ] Rejection process works
- [ ] Status transitions correct
- [ ] Email notifications sent

### **UI/UX**
- [ ] All buttons visible and styled
- [ ] Forms are user-friendly
- [ ] Validation messages clear
- [ ] Success/error notifications appear
- [ ] Navigation intuitive
- [ ] Mobile responsive (bonus)

### **Data Integrity**
- [ ] Amounts save correctly
- [ ] Dates persist properly
- [ ] User associations correct
- [ ] Approval chain accurate
- [ ] Audit trail complete
- [ ] No data loss on edit

### **Permissions**
- [ ] Regular users can create requests
- [ ] Users can only see their own requests
- [ ] Staff can see all requests
- [ ] Only staff can approve/reject
- [ ] Only draft requests can be edited
- [ ] Approved requests are read-only

---

## **📸 SCREENSHOTS TO CAPTURE**

For documentation and UAT handoff:
1. Budget Dashboard with new buttons
2. Create Budget Request form
3. My Requests list with filters
4. Budget Request detail page (draft)
5. Budget Request detail page (submitted)
6. Approval Dashboard (staff view)
7. Approval Action in progress
8. Budget Request detail page (approved)
9. Budget Request detail page (rejected with reason)
10. Budget comparison view (if testing)

---

## **🚀 NEXT STEPS AFTER LOCAL TESTING**

### **If All Tests Pass:**
1. ✅ Mark all tests as complete
2. ✅ Commit any bug fixes
3. ✅ Push to Heroku UAT
4. ✅ Repeat key tests on UAT
5. ✅ Get user acceptance
6. ✅ Deploy to production

### **If Issues Found:**
1. ❌ Document the issue
2. 🔧 Fix the bug
3. ✅ Retest locally
4. ✅ Then proceed to UAT

---

## **📞 SUPPORT COMMANDS**

### **Check Server Logs:**
```bash
# Watch logs in real-time
tail -f logs/django.log

# Check for errors
grep ERROR logs/django.log
```

### **Database Queries (if needed):**
```bash
python manage.py shell

# In shell:
from finance.models import BudgetRequest
BudgetRequest.objects.all()  # See all requests
BudgetRequest.objects.filter(status='draft')  # See drafts
```

### **Restart Server:**
```bash
# If server crashes
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver
```

---

## **🎯 TESTING STATUS**

Track your progress:

- [ ] TEST 1: Login & Dashboard Access
- [ ] TEST 2: Create Budget Request
- [ ] TEST 3: View "My Requests" List
- [ ] TEST 4: Edit Draft Request
- [ ] TEST 5: Submit for Approval
- [ ] TEST 6: View Approval Dashboard
- [ ] TEST 7: Approve Request
- [ ] TEST 8: Test Rejection
- [ ] TEST 9: Budget Comparison View
- [ ] TEST 10: End-to-End Workflow

**Total Tests:** 10  
**Completed:** ___  
**Failed:** ___  
**Issues Found:** ___

---

*Happy Testing! 🧪*  
*Report any issues and I'll help fix them immediately.*

