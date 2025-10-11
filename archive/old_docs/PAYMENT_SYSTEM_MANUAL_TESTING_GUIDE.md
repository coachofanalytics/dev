# 💳 Payment System Manual Testing Guide

## 🎯 **Test User Setup**

### **Test User Credentials**
- **Email**: `teststudent@example.com`
- **Password**: `testpassword123`
- **User Type**: Student (Category 3)
- **Payment Balance**: $1000 total fees, $300 down payment, $650 balance

---

## 🚀 **Step-by-Step Testing Procedure**

### **Step 1: Start the Server**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver
```
**Expected**: Server starts on http://127.0.0.1:8000

---

### **Step 2: Login as Test User**

1. **Open Browser** and go to: `http://127.0.0.1:8000/accounts/login/`

2. **Enter Credentials**:
   - **Username/Email**: `teststudent@example.com`
   - **Password**: `testpassword123`

3. **Click "Login"**

**Expected Result**: ✅ Redirected to dashboard or home page

---

### **Step 3: Navigate to Payment Methods**

1. **Go to Payment Methods Page**: `http://127.0.0.1:8000/finance/unified/methods/`

2. **Verify Page Loads**:
   - Should see "Choose Your Payment Method" heading
   - Should see payment summary showing $1000 total, $300 down payment
   - Should see 6 payment method cards

**Expected Result**: ✅ All 6 payment methods displayed with correct amounts

---

### **Step 4: Test Each Payment Method**

#### **4A: Test PayPal Payment**

1. **Click "Continue with PayPal"** on the PayPal card

2. **Verify PayPal Form Loads**:
   - Should see PayPal payment form
   - Should have fields for amount and email

3. **Fill PayPal Form**:
   - **Amount**: `200` (or any amount ≤ $650)
   - **Email**: `test@example.com`

4. **Click "Submit" or "Pay"**

**Expected Result**: ✅ Redirected to payment success page

---

#### **4B: Test CashApp Payment**

1. **Go back to payment methods**: `http://127.0.0.1:8000/finance/unified/methods/`

2. **Click "Continue with CashApp"**

3. **Fill CashApp Form**:
   - **Amount**: `150`
   - **CashApp ID**: `testcashapp123`

4. **Submit Payment**

**Expected Result**: ✅ Redirected to payment success page

---

#### **4C: Test Zelle Payment**

1. **Go back to payment methods**

2. **Click "Continue with Zelle"**

3. **Fill Zelle Form**:
   - **Amount**: `100`
   - **Email**: `test@example.com`

4. **Submit Payment**

**Expected Result**: ✅ Redirected to payment success page

---

#### **4D: Test Venmo Payment**

1. **Go back to payment methods**

2. **Click "Continue with Venmo"**

3. **Fill Venmo Form**:
   - **Amount**: `75`
   - **Venmo Username**: `testvenmo123`

4. **Submit Payment**

**Expected Result**: ✅ Redirected to payment success page

---

#### **4E: Test Stripe Payment**

1. **Go back to payment methods**

2. **Click "Continue with Credit/Debit Card"**

3. **Fill Stripe Form**:
   - **Amount**: `50`

4. **Submit Payment**

**Expected Result**: ✅ Redirected to payment success page

---

#### **4F: Test MPESA Payment (OTP Flow)**

1. **Go back to payment methods**

2. **Click "Continue with MPESA Mobile Money"**

3. **Fill MPESA Form**:
   - **Amount**: `25`
   - **Phone Number**: `+1234567890`

4. **Submit Payment**

**Expected Result**: ✅ Redirected to OTP confirmation page

5. **On OTP Page**:
   - Should see "Enter OTP" form
   - Check console/email for OTP code
   - Enter the OTP code
   - Click "Verify OTP"

**Expected Result**: ✅ Redirected to payment success page

---

### **Step 5: Test Payment Success Page**

**For each successful payment, verify**:

1. **Success Page Elements**:
   - ✅ "Payment Successful!" heading
   - ✅ Payment details (reference, amount, method, date)
   - ✅ "What Happens Next?" section
   - ✅ Action buttons (View History, Dashboard, Make Another Payment)

2. **Action Buttons**:
   - **"View Payment History"** → Should go to payment history page
   - **"Go to Dashboard"** → Should go to home page
   - **"Make Another Payment"** → Should go back to payment methods

**Expected Result**: ✅ All elements present and functional

---

### **Step 6: Test Payment History**

1. **Navigate to Payment History**: `http://127.0.0.1:8000/finance/payments/history/complete/`

2. **Verify History Page**:
   - Should see "PAYMENT HISTORY" heading
   - Should see your completed payments
   - Should show payment details (amount, method, date)

**Expected Result**: ✅ Payment history displays all completed payments

---

### **Step 7: Test Payment Failed Scenarios**

#### **7A: Test Invalid Amount**

1. **Go to any payment method**

2. **Enter Invalid Amount**:
   - **Amount**: `1000` (more than balance of $650)

3. **Submit Payment**

**Expected Result**: ✅ Redirected to payment failed page with error message

---

#### **7B: Test Missing Required Fields**

1. **Go to PayPal payment**

2. **Leave Email Field Empty**

3. **Submit Payment**

**Expected Result**: ✅ Error message about missing email field

---

### **Step 8: Test Navigation Flow**

1. **From Payment Methods** → **Payment Form** → **Success Page** → **Payment History**
2. **From Success Page** → **Dashboard** → **Back to Payment Methods**
3. **From Payment History** → **Make Another Payment** → **Payment Methods**

**Expected Result**: ✅ Smooth navigation between all pages

---

## 🔍 **What to Look For**

### **✅ Success Indicators**:
- All payment methods load correctly
- Payment forms submit successfully
- Success page displays payment details
- Payment history shows completed payments
- Navigation works smoothly
- Error handling works for invalid inputs

### **❌ Common Issues to Watch For**:
- **Payment methods not loading**: Check server logs
- **Forms not submitting**: Check CSRF token issues
- **Success page not showing**: Check session data
- **History not updating**: Check database records
- **Navigation broken**: Check URL patterns

---

## 🛠️ **Troubleshooting**

### **If Payment Methods Don't Load**:
1. Check if user has payment information in database
2. Verify user is logged in
3. Check server logs for errors

### **If Payment Forms Don't Submit**:
1. Check CSRF token is present
2. Verify form fields are filled correctly
3. Check amount doesn't exceed balance

### **If Success Page Doesn't Show**:
1. Check session data is stored
2. Verify payment was recorded in database
3. Check redirect URLs

### **If History Doesn't Update**:
1. Check Payment_History table in database
2. Verify user is viewing correct history page
3. Check payment status is "completed"

---

## 📊 **Expected Results After Testing**

After completing all tests, you should have:

- **5-6 completed payments** in Payment_History table
- **Payment success page** working for all methods
- **Payment history** showing all transactions
- **Error handling** working for invalid inputs
- **Navigation** working smoothly between pages

---

## 🎯 **Test Checklist**

- [ ] Server starts successfully
- [ ] User login works
- [ ] Payment methods page loads
- [ ] All 6 payment methods visible
- [ ] PayPal payment works
- [ ] CashApp payment works
- [ ] Zelle payment works
- [ ] Venmo payment works
- [ ] Stripe payment works
- [ ] MPESA payment works (with OTP)
- [ ] Success page displays correctly
- [ ] Payment history shows transactions
- [ ] Error handling works
- [ ] Navigation works smoothly

---

## 📝 **Notes**

- **Test User**: `teststudent@example.com` / `testpassword123`
- **Server URL**: `http://127.0.0.1:8000`
- **Database**: SQLite (local development)
- **All payments are simulated** (no real money processed)
- **OTP codes** are displayed in console/email

---

**Happy Testing! 🚀💳**

