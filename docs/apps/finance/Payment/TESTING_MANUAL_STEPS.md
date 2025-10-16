# Payment System - Manual Testing Steps

**Date:** October 16, 2025  
**Branch:** 25_UAT_FIX  
**Server:** Running at http://localhost:8000  
**Status:** Ready for Manual Testing

---

## ✅ WHAT'S COMPLETED

### Code Integration:
- ✅ Payment system copied from 25.09_CODA_DEV_CM
- ✅ Persona-based routing implemented
- ✅ Database schema issues fixed
- ✅ Django check passes (no errors)
- ✅ Server starts successfully
- ✅ All commits complete (5 commits)

### Commits Made:
1. `264dee9ef` - Payment system analysis documentation
2. `44b7dbde5` - Add unified payment system with 6 methods
3. `b93442040` - Persona-based fallback redirects
4. `45fa3a133` - Cleanup debug logs
5. `d4215f335` - Complete payment documentation
6. `d0351a2b5` - Fix database schema mismatch

---

## 🧪 MANUAL TESTING GUIDE

### Prerequisites:
✅ Server running: `cd coda && python manage.py runserver`  
✅ Browser open  
✅ Dev tools open (F12)  

---

### TEST 1: Payment Method Selection Page (With Context)

**Objective:** Verify unified payment page loads correctly

**Steps:**
1. **Login** to http://localhost:8000/admin
2. **Create Payment_Information** for your user:
   ```sql
   -- In Django shell or admin:
   from finance.models import Payment_Information
   from django.contrib.auth import get_user_model
   User = get_user_model()
   
   user = User.objects.first()  # Or get specific user
   
   Payment_Information.objects.create(
       customer_id=user,
       payment_fees=10000,
       down_payment=3000,
       student_bonus=0,
       plan=1,
       client_signature="test"
   )
   ```

3. **Navigate** to: `http://localhost:8000/finance/unified/methods/`

**Expected Result:**
- ✅ Page loads (HTTP 200)
- ✅ See 6 payment methods (M-Pesa, PayPal, CashApp, Zelle, Venmo, Stripe)
- ✅ Each method shows: icon, description, processing time, fees
- ✅ Total amount displayed: $10,000
- ✅ Down payment displayed: $3,000
- ✅ No console errors (F12 → Console tab)

**If Fails:**
- Check server logs for errors
- Verify Payment_Information record exists
- Check template path: `coda/finance/templates/finance/payments/method_selection.html`

---

### TEST 2: Student Persona Routing (No Context)

**Objective:** Verify students without payment context redirect to services

**Steps:**
1. **Create student user** in Django admin or shell:
   ```python
   from django.contrib.auth import get_user_model
   from django.contrib.auth.models import Group
   
   User = get_user_model()
   
   student = User.objects.create_user(
       username='test_student',
       email='student@test.com',
       password='Test123!',
       category=1  # Student category
   )
   
   # OR add to student group
   student_group, _ = Group.objects.get_or_create(name='student')
   student.groups.add(student_group)
   ```

2. **Login** as `test_student`
3. **Navigate** to: `http://localhost:8000/finance/pay/`

**Expected Result:**
- ✅ Redirect (HTTP 302)
- ✅ URL changes to: `/professional_services/`
- ✅ Services page loads

**If Fails:**
- Check persona detection in shell:
  ```python
  from finance.utilities.payment_utils import PaymentUtils
  persona = PaymentUtils.get_user_persona(student)
  print(persona)  # Should be 'student'
  ```

---

### TEST 3: Investor Persona Routing (No Context)

**Objective:** Verify investors redirect to investing dashboard

**Steps:**
1. **Create investor user**:
   ```python
   investor = User.objects.create_user(
       username='test_investor',
       email='investor@test.com',
       password='Test123!'
   )
   
   investor_group, _ = Group.objects.get_or_create(name='investor')
   investor.groups.add(investor_group)
   
   # OR set flag
   investor.is_investor = True
   investor.save()
   ```

2. **Login** as `test_investor`
3. **Navigate** to: `http://localhost:8000/finance/pay/`

**Expected Result:**
- ✅ Redirect (HTTP 302)
- ✅ URL changes to: `/investing/dashboard/`
- ✅ Investing dashboard loads

---

### TEST 4: Staff Persona Routing (No Context)

**Objective:** Verify staff redirect to unified methods or services

**Steps:**
1. **Create staff user**:
   ```python
   staff = User.objects.create_user(
       username='test_staff',
       email='staff@test.com',
       password='Test123!',
       is_staff=True,
       category=2
   )
   ```

2. **Login** as `test_staff`
3. **Navigate** to: `http://localhost:8000/finance/pay/`

**Expected Result:**
- ✅ Redirect (HTTP 302)
- ✅ URL changes to: `/finance/unified/methods/` OR `/professional_services/`

---

### TEST 5: M-Pesa Payment Flow

**Objective:** Test complete M-Pesa payment with OTP

**Steps:**
1. **Ensure user has Payment_Information** (from Test 1)
2. **Navigate** to: `http://localhost:8000/finance/unified/methods/`
3. **Click** "M-Pesa" button
4. **Expected:** Redirect to M-Pesa form (or show form on same page)
5. **Enter:**
   - Phone: `254712345678`
   - Amount: `50`
6. **Submit** form
7. **Expected:** Redirect to OTP confirmation page
8. **Check email** for OTP code
9. **Enter OTP** on confirmation page
10. **Submit**

**Expected Result:**
- ✅ OTP email received
- ✅ OTP verification successful
- ✅ Redirect to `/finance/unified/success/`
- ✅ Success page shows:
  - Reference number
  - Amount paid
  - Payment method
  - Payment date
- ✅ Payment_History record created in database

**Verify in Database:**
```python
from finance.models import Payment_History
latest = Payment_History.objects.latest('id')
print(f"Method: {latest.payment_method}")
print(f"Amount: {latest.payment_fees}")
print(f"User: {latest.customer.username}")
```

---

### TEST 6: PayPal Payment Flow

**Steps:**
1. From payment methods, **click** "PayPal"
2. **Enter:**
   - Email: `test@example.com`
   - Amount: `100`
3. **Submit**

**Expected Result:**
- ✅ Redirect to `/finance/unified/success/`
- ✅ Success message displayed
- ✅ Payment_History record created

---

### TEST 7: Priority Order (Loan Takes Priority)

**Objective:** Verify active loan shows before persona routing

**Steps:**
1. **Create loan** for student user:
   ```python
   from finance.models import LoanApplication
   
   loan = LoanApplication.objects.create(
       borrower=student,
       amount_requested=5000,
       status='active'
   )
   ```

2. **Login** as student (who has active loan)
3. **Navigate** to: `http://localhost:8000/finance/pay/`

**Expected Result:**
- ✅ Shows legacy payment page (NOT redirected to services)
- ✅ Context shows loan repayment
- ✅ Amount shows loan total

---

### TEST 8: Error Handling

**Objective:** Verify graceful error handling

**Steps:**
1. Navigate to: `http://localhost:8000/finance/unified/failed/`
2. **Expected:** Failure page loads with error message

3. Try invalid payment method: `http://localhost:8000/finance/unified/process/invalid_method/`
4. **Expected:** Error message, redirect to method selection

---

## 🐛 TROUBLESHOOTING

### Issue 1: Server Won't Start
**Symptom:** `python manage.py runserver` fails

**Check:**
```bash
python manage.py check
# Should show: System check identified no issues
```

**Fix:**
- Check imports in unified_payment.py
- Verify all files committed
- Check Python path

---

### Issue 2: Payment Page Shows 404
**Symptom:** `/finance/unified/methods/` returns 404

**Check:**
```bash
python manage.py show_urls | grep unified
# Should show unified payment URLs
```

**Fix:**
- Verify URLs configured in finance/urls.py
- Check imports in urls.py
- Restart server

---

### Issue 3: Database Errors
**Symptom:** `ProgrammingError: column does not exist`

**Check:**
```python
# In shell:
from finance.models import Payment_Information
Payment_Information._meta.get_fields()
# Shows model fields

# Check actual database table:
# psql or pgAdmin to see actual columns
```

**Fix:**
- Use .order_by('-id') instead of default ordering
- Don't query non-existent fields
- Consider migration (but test in UAT first)

---

### Issue 4: Redirects in Loop
**Symptom:** Maximum redirects exceeded

**Check:**
- Persona detection returning correct value
- Redirect URLs exist
- No circular redirects

**Fix:**
- Test persona detection in shell
- Verify destination URLs load
- Check redirect logic

---

## 📊 VALIDATION CHECKLIST

### Code Quality:
- [x] No lint errors
- [x] Django check passes
- [x] Imports all resolve
- [x] URLs configured correctly
- [x] No syntax errors

### Database:
- [x] Schema mismatch handled gracefully
- [ ] Payment_Information query works
- [ ] Payment_History creation works
- [ ] No data corruption

### User Experience:
- [ ] Payment page loads
- [ ] Methods displayed correctly
- [ ] Redirects work smoothly
- [ ] Error messages clear
- [ ] Success page informative

### Business Logic:
- [ ] Priority order correct (loan > info > history > persona)
- [ ] Persona detection accurate
- [ ] Amount validation works
- [ ] Payment records saved
- [ ] Email notifications sent (M-Pesa OTP)

---

## 📝 TEST RESULTS LOG

### Date: October 16, 2025

| Test | Status | Notes |
|------|--------|-------|
| Django Check | ✅ PASS | No issues found |
| Server Start | ✅ PASS | Runs on port 8000 |
| Payment Methods Page | ⚠️ PENDING | Requires login + Payment_Information |
| Student Redirect | ⚠️ PENDING | Need to create test user |
| Investor Redirect | ⚠️ PENDING | Need to create test user |
| Staff Redirect | ⚠️ PENDING | Need to create test user |
| M-Pesa Flow | ⚠️ PENDING | Needs Payment_Information |
| PayPal Flow | ⚠️ PENDING | Needs Payment_Information |
| Database Fix | ✅ PASS | order_by('-id') works |
| Linter | ✅ PASS | No errors |

**Next Action:** Create test users and manually test each scenario

---

## 🚀 QUICK TEST SCRIPT

Copy this into Django shell to quickly setup test users:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from finance.models import Payment_Information

User = get_user_model()

# 1. Create student
student, _ = User.objects.get_or_create(
    username='test_student',
    defaults={
        'email': 'student@test.com',
        'category': 1
    }
)
student.set_password('Test123!')
student.save()
student_group, _ = Group.objects.get_or_create(name='student')
student.groups.add(student_group)
print("✅ Student created")

# 2. Create investor
investor, _ = User.objects.get_or_create(
    username='test_investor',
    defaults={'email': 'investor@test.com'}
)
investor.set_password('Test123!')
investor.save()
investor_group, _ = Group.objects.get_or_create(name='investor')
investor.groups.add(investor_group)
print("✅ Investor created")

# 3. Create staff
staff, _ = User.objects.get_or_create(
    username='test_staff',
    defaults={
        'email': 'staff@test.com',
        'is_staff': True,
        'category': 2
    }
)
staff.set_password('Test123!')
staff.save()
print("✅ Staff created")

# 4. Create Payment_Information for one user
payment_info, _ = Payment_Information.objects.get_or_create(
    customer_id=staff,
    defaults={
        'payment_fees': 10000,
        'down_payment': 3000,
        'plan': 1,
        'client_signature': 'test'
    }
)
print("✅ Payment info created for staff")

print("\n🎉 Test users created!")
print("Login credentials (all): password = 'Test123!'")
print("\nTest URLs:")
print("- http://localhost:8000/finance/pay/ (as student → redirects to services)")
print("- http://localhost:8000/finance/pay/ (as investor → redirects to investing)")
print("- http://localhost:8000/finance/unified/methods/ (as staff with payment info)")
```

---

## 📋 TESTING SEQUENCE

### Sequence 1: Test Persona Redirects (5 minutes)

1. **Login** as `test_student` (password: `Test123!`)
2. **Go to:** `http://localhost:8000/finance/pay/`
3. **Check:** URL redirects to `/professional_services/`
4. **✅ PASS** if redirects correctly

5. **Logout**, **Login** as `test_investor`
6. **Go to:** `http://localhost:8000/finance/pay/`
7. **Check:** URL redirects to `/investing/dashboard/`
8. **✅ PASS** if redirects correctly

### Sequence 2: Test Payment Methods Page (5 minutes)

1. **Login** as `test_staff` (has Payment_Information)
2. **Go to:** `http://localhost:8000/finance/unified/methods/`
3. **Check:**
   - ✅ Page loads (no 404 or 500)
   - ✅ 6 payment methods visible
   - ✅ Icons displayed
   - ✅ Amount shows: $10,000 total, $3,000 down payment
   - ✅ No console errors

### Sequence 3: Test M-Pesa Flow (10 minutes)

1. From payment methods page, **click** "M-Pesa" button
2. **Expected:** Form or redirect to `/finance/unified/process/mpesa/`
3. **Enter:**
   - Phone: `254712345678`
   - Amount: `50`
4. **Submit**
5. **Check:** Redirect to OTP page `/finance/unified/mpesa-otp/`
6. **Check email** for OTP (check spam if needed)
7. **Enter OTP**, **submit**
8. **Check:** Redirect to success page
9. **Verify** Payment_History created

### Sequence 4: Test Other Payment Methods (5 minutes each)

**PayPal:**
1. Click PayPal method
2. Enter email + amount
3. Submit → Should redirect to success

**CashApp:**
1. Click CashApp method
2. Enter CashApp ID + amount
3. Submit → Should redirect to success

**Zelle:**
1. Click Zelle method
2. Enter email + amount
3. Submit → Should redirect to success

**Venmo:**
1. Click Venmo method
2. Enter username + amount
3. Submit → Should redirect to success

**Stripe:**
1. Click Stripe method
2. Enter amount
3. Submit → Should redirect to success

---

## 🔍 WHAT TO LOOK FOR

### Success Indicators:
- ✅ No 500 errors in server logs
- ✅ Pages load quickly (< 2 seconds)
- ✅ Redirects work smoothly
- ✅ Forms submit successfully
- ✅ Database records created
- ✅ Success messages displayed
- ✅ No console errors (F12)

### Red Flags:
- ❌ 500 Internal Server Error
- ❌ Template not found errors
- ❌ Database constraint errors
- ❌ Circular redirects
- ❌ Payment not saved to database
- ❌ Emails not sent (M-Pesa OTP)

---

## 📊 CURRENT SERVER STATUS

### Based on Terminal Logs:

**Server:**
- ✅ Running at http://127.0.0.1:8000/
- ✅ Django 3.2.6
- ✅ Auto-reload enabled

**Initial Access Attempt:**
- ✅ `/finance/unified/methods/` responded with 302 (redirect)
- ✅ User redirected to dashboard (no payment context)
- ✅ No server crash

**Known Working URLs:**
- ✅ `/dashboard/` - Main dashboard
- ✅ `/finance/loan-home/` - Loan homepage
- ✅ `/finance/user-loans/` - User loans list

**Database Issue Fixed:**
- ✅ `created_at` column error handled
- ✅ Query uses `order_by('-id')` instead
- ✅ Fallback query implemented

---

## 🎯 NEXT STEPS

### Immediate (Now):
1. **Create test users** using shell script above
2. **Test each persona** redirect
3. **Create Payment_Information** for one user
4. **Test payment methods page** loading
5. **Test M-Pesa flow** (if time permits)

### After Manual Testing (Today/Tomorrow):
1. **Document results** in TESTING.md
2. **Fix any issues** found
3. **Commit fixes**
4. **Deploy to UAT**
5. **Test in UAT** environment

### Before Production (Week):
1. **UAT testing** complete
2. **User acceptance** received
3. **No critical bugs**
4. **Get user approval**
5. **Deploy to production**

---

## 📝 TEST REPORT TEMPLATE

After testing, fill this out:

```
## Payment System Manual Test Report
Date: [DATE]
Tester: [NAME]
Environment: Local Development
Branch: 25_UAT_FIX

### Test 1: Student Persona Redirect
- Status: [ ] PASS [ ] FAIL
- Notes:

### Test 2: Investor Persona Redirect
- Status: [ ] PASS [ ] FAIL
- Notes:

### Test 3: Staff Persona Redirect
- Status: [ ] PASS [ ] FAIL
- Notes:

### Test 4: Payment Methods Page
- Status: [ ] PASS [ ] FAIL
- Notes:

### Test 5: M-Pesa Flow
- Status: [ ] PASS [ ] FAIL
- Notes:

### Test 6: PayPal Flow
- Status: [ ] PASS [ ] FAIL
- Notes:

### Issues Found:
1.
2.
3.

### Overall Status: [ ] READY FOR UAT [ ] NEEDS FIXES

### Recommendations:
-
```

---

## ✅ SUMMARY

### What's Working:
✅ Server starts successfully  
✅ No import errors  
✅ No configuration errors  
✅ Database query fixed  
✅ URLs configured  
✅ Persona routing implemented  
✅ All code committed  

### Ready to Test:
- Payment method selection page
- Persona-based redirects
- M-Pesa OTP flow
- Other payment methods
- Success/failure pages

### Time Estimate:
- Setup test users: 5 minutes
- Test persona redirects: 10 minutes
- Test payment methods: 15 minutes
- Test M-Pesa flow: 10 minutes
- **Total:** 40 minutes

---

**Server is running! Ready for you to test! 🚀**

**Start with:** Create test users using the shell script above, then follow the testing sequence.


