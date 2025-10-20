# Eunice Payment Flow - Manual Test Guide

**Date:** October 16, 2025  
**User:** eunice  
**Password:** MANAGER2030  
**Server:** http://localhost:8000

---

## 👤 EUNICE'S PROFILE

**User Details:**
- **Username:** eunice
- **Email:** eunicesichangi06@gmail.com
- **Category:** 6
- **Persona:** staff (is_staff=True, is_superuser=True)
- **Groups:** employee, coda-staff-member Group 1

**Current Status:**
- **Existing Loans:** 1 loan (Loan #100, status: under_review, $250)
- **Payment Info:** 0 records
- **Payment History:** 0 records

**Expected Behavior:**
Since eunice is a **staff user** with an existing loan in "under_review" status, the payment flow depends on the loan status:
- If loan status = "active" or "approved" → Payment page shows for loan repayment
- If loan status = "under_review" → No payment context → Redirect to `/finance/unified/methods/`

---

## 🧪 MANUAL TEST SCENARIOS

### SCENARIO 1: Test Existing Loan Payment (If Loan is Active)

**First, check/update loan status:**
1. Go to: http://localhost:8000/admin/finance/loanapplication/100/change/
2. Check loan status
3. If status = "under_review", change to "approved" or "active"
4. Save loan

**Then test payment:**
1. **Logout** (if logged in)
2. **Login** as: `eunice` / `MANAGER2030`
3. **Navigate to:** http://localhost:8000/finance/pay/
4. **Expected:**
   - ✅ Payment page loads
   - ✅ Shows loan repayment context
   - ✅ Amount: $250 (loan amount)
   - ✅ Payment methods visible (PayPal, M-Pesa, etc.)

### SCENARIO 2: Test Persona Redirect (If No Active Loan)

**Setup:**
1. Ensure loan status is NOT "active" or "approved"
   - Or temporarily delete/complete the loan

**Test:**
1. **Login** as: `eunice` / `MANAGER2030`
2. **Navigate to:** http://localhost:8000/finance/pay/
3. **Expected (since eunice is staff):**
   - ✅ Redirect to: `/finance/unified/methods/`
   - OR if no payment context: redirect to `/professional_services/`

### SCENARIO 3: Test Unified Payment Methods

**Setup:**
1. Create Payment_Information for eunice via Django admin or shell:

```python
# In Django shell (python manage.py shell):
from django.contrib.auth import get_user_model
from finance.models import Payment_Information

User = get_user_model()
eunice = User.objects.get(username='eunice')

# Create payment info
payment_info = Payment_Information.objects.create(
    customer_id=eunice,
    payment_fees=100,
    down_payment=30,
    student_bonus=0,
    plan=1,
    client_signature='test'
)
print(f"Created Payment_Information #{payment_info.id}")
```

**Test:**
1. **Login** as eunice
2. **Navigate to:** http://localhost:8000/finance/unified/methods/
3. **Expected:**
   - ✅ Page loads (no redirect)
   - ✅ Shows 6 payment methods with cards/icons
   - ✅ Total amount: $100
   - ✅ Down payment: $30
   - ✅ Each method has:
     - Icon (M-Pesa 📱, PayPal 💳, etc.)
     - Description
     - Processing time
     - Fees

### SCENARIO 4: Test M-Pesa Payment Flow

**Prerequisites:** Complete Scenario 3 first (have Payment_Information)

**Steps:**
1. From unified methods page, **click** "M-Pesa" button
2. **Expected:** Redirect to `/finance/unified/process/mpesa/` or show M-Pesa form
3. **Enter:**
   - Phone: `254712345678` (use 254 prefix for Kenya)
   - Amount: `30` (or your down payment amount)
4. **Submit** form
5. **Expected:** Redirect to `/finance/unified/mpesa-otp/`
6. **Check email:** eunicesichangi06@gmail.com for OTP code
7. **Enter OTP** on page
8. **Submit**
9. **Expected:**
   - ✅ Redirect to `/finance/unified/success/`
   - ✅ Success message displayed
   - ✅ Shows:
     - Reference number (e.g., MPESA-254712345678-30.0)
     - Amount: $30
     - Method: mpesa
     - Payment date

10. **Verify in database:**
```python
# In shell:
from finance.models import Payment_History
latest = Payment_History.objects.latest('id')
print(f"Customer: {latest.customer.username}")  # Should be eunice
print(f"Amount: {latest.payment_fees}")
print(f"Method: {latest.payment_method}")
```

---

## 🐛 TROUBLESHOOTING FOR EUNICE

### Issue 1: "No payment context" Message
**Cause:** No Payment_Information exists for eunice
**Fix:** Create Payment_Information using shell script in Scenario 3

### Issue 2: Loan Payment Not Showing
**Cause:** Loan status is "under_review" not "active"/"approved"  
**Fix:** Update loan status in admin:
```
http://localhost:8000/admin/finance/loanapplication/100/change/
Change status to: approved or active
```

### Issue 3: Page Redirects When It Shouldn't
**Cause:** Payment context exists but not found
**Fix:** Check query in views uses `.order_by('-id')` not default ordering

### Issue 4: M-Pesa OTP Not Received
**Cause:** Email service not configured or email blocked
**Check:** 
- Server logs for email errors
- Spam folder in eunicesichangi06@gmail.com
- Email service configuration in settings

---

## ✅ EXPECTED TEST RESULTS

### With Active Loan (Loan #100 status='approved'):
```
✅ /finance/pay/ → Shows payment page
✅ Context: Loan repayment
✅ Amount: $250
✅ Can select payment method
✅ Legacy payment flow works (PayPal, M-Pesa buttons visible)
```

### With Payment_Information Created:
```
✅ /finance/unified/methods/ → Shows unified payment page
✅ 6 methods visible
✅ Can click M-Pesa → Shows form
✅ Can submit → OTP sent
✅ Can verify OTP → Payment complete
✅ Success page shows details
✅ Payment_History record created
```

### Without Any Context:
```
✅ /finance/pay/ → Redirects to /finance/unified/methods/
✅ (Since eunice is staff persona)
✅ If no Payment_Information → Further redirects or shows message
```

---

## 📝 QUICK TEST COMMANDS

### In Browser:
1. Login: http://localhost:8000/admin/
   - Username: eunice
   - Password: MANAGER2030

2. Test URLs:
   - http://localhost:8000/finance/pay/
   - http://localhost:8000/finance/unified/methods/
   - http://localhost:8000/finance/loan-home/
   - http://localhost:8000/finance/user-loans/

### In Django Shell:
```bash
python manage.py shell

# Check eunice
from django.contrib.auth import get_user_model
User = get_user_model()
eunice = User.objects.get(username='eunice')

# Check loans
from finance.models import LoanApplication
loans = LoanApplication.objects.filter(borrower=eunice)
for loan in loans:
    print(f"Loan #{loan.id}: {loan.status}, ${loan.amount_requested}")

# Approve loan for payment testing
loan = LoanApplication.objects.get(id=100)
loan.status = 'approved'  # or 'active'
loan.save()
print("Loan approved for payment testing!")

# Create payment info
from finance.models import Payment_Information
payment_info = Payment_Information.objects.create(
    customer_id=eunice,
    payment_fees=100,
    down_payment=30,
    plan=1,
    client_signature='test'
)
print(f"Payment info created: #{payment_info.id}")
```

---

## 🎯 SUCCESS CRITERIA FOR EUNICE

### Minimum Viable Test:
- [ ] Can login as eunice
- [ ] Can access `/finance/pay/`
- [ ] If loan active → sees payment page
- [ ] If no context → redirects appropriately (staff persona)

### Full Test:
- [ ] Can see loan repayment page (if loan active)
- [ ] Can access `/finance/unified/methods/` (with Payment_Information)
- [ ] Can see all 6 payment methods
- [ ] Can click M-Pesa and see form
- [ ] Can submit M-Pesa and get OTP
- [ ] Can verify OTP and see success
- [ ] Payment_History record created

---

## 📊 CURRENT STATUS FOR EUNICE

Based on test script output:

**User:** ✅ eunice (found, superuser, staff)  
**Persona:** ✅ staff (detected correctly)  
**Loan:** ✅ #100 (under_review, $250)  
**Payment Info:** ❌ 0 records (needs creation for unified methods test)  
**Payment History:** ❌ 0 records (will be created after payment)

**To Enable Full Test:**
1. **Option A:** Approve Loan #100
   - Then `/finance/pay/` will show loan repayment
   
2. **Option B:** Create Payment_Information
   - Then `/finance/unified/methods/` will work

---

## 🚀 RECOMMENDED TEST SEQUENCE

### Quick Test (5 minutes):
1. Login as eunice in browser
2. Go to http://localhost:8000/finance/pay/
3. See what happens (document result)
4. Go to http://localhost:8000/finance/unified/methods/
5. See what happens (document result)

### Full Test (20 minutes):
1. Approve Loan #100 in admin
2. Login as eunice
3. Test loan payment flow
4. Create Payment_Information
5. Test unified methods page
6. Test M-Pesa flow (if time permits)

---

**Your server is running! You can test now in your browser! 🚀**

**Recommended:** Start with Quick Test to see current behavior, then decide on Full Test.


