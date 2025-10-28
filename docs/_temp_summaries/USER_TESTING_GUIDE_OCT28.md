# User Testing Guide - Managed Options Trading
**Date:** October 28, 2025  
**Purpose:** Step-by-step browser testing from user perspective

---

## **🎯 TESTING APPROACH**

**Test as a real user would use the system:**
1. ✅ Click buttons (don't type URLs)
2. ✅ Follow natural workflow
3. ✅ Verify data displays correctly
4. ✅ Check all buttons work
5. ✅ Test forms submit properly

---

## **📋 STEP-BY-STEP TESTING**

### **SCENARIO 1: New User Registration → First Account**

#### **Step 1: Register as New User**

1. Go to: http://localhost:8000/accounts/register/
2. Fill in registration form:
   - **Main Category:** "Investor - Financial, strategic, KCC members"
   - **Sub Category:** "Individual - Personal investors, KCC/loans"
   - **Username:** `demo_investor_1`
   - **Password:** `Demo123!`
   - **Email:** `demo1@test.com`
   - **First Name:** `Demo`
   - **Last Name:** `Investor`
   - Fill other fields as needed
3. Click **"Register"** button
4. ✅ **Expected:** Registration successful, redirected to login

#### **Step 2: Login**

1. Go to: http://localhost:8000/accounts/login/
2. Login with:
   - **Username:** `demo_investor_1`
   - **Password:** `Demo123!`
3. Click **"Login"** button
4. ✅ **Expected:** Logged in, redirected to dashboard

#### **Step 3: Navigate to Investment Dashboard**

1. Should auto-redirect OR click "Investing" in menu
2. Go to: http://localhost:8000/investing/dashboard/
3. ✅ **Expected:** See dashboard with summary cards
4. ✅ **Check:** "Start Managed Options Trading" green card appears
5. ✅ **Check:** Card shows:
   - Benefits list (6 items)
   - "3 Simple Steps"
   - **"Start Now"** button (green, large)

#### **Step 4: Start Onboarding - Risk Assessment**

1. Click **"Start Now"** button (in green card)
2. ✅ **Expected:** Redirected to `/investing/managed/onboarding/risk-assessment/`
3. ✅ **Check Page Shows:**
   - Title: "Risk Tolerance Questionnaire"
   - 10 questions (Question 1-10)
   - Each question has 5 radio button options
   - Submit button at bottom

#### **Step 5: Complete Risk Assessment**

1. Answer all 10 questions (select any options)
2. For testing, select middle option (5 points) for all questions
3. Click **"Submit Assessment"** button
4. ✅ **Expected:** 
   - Form submits successfully
   - See message: "Risk assessment complete! Score: 50/100 (moderate)"
   - Redirected to application page

#### **Step 6: Submit Application**

1. Should be on: `/investing/managed/onboarding/apply/`
2. ✅ **Check Page Shows:**
   - Your risk profile (Score 50, Moderate)
   - Recommended tiers highlighted
   - Form fields:
     - Initial Capital (number input)
     - Fee Tier (dropdown - filtered by risk)
     - Preferred Manager (dropdown - optional)
     - Funding Method (dropdown)

3. Fill in application:
   - **Initial Capital:** `30000` ($30,000)
   - **Fee Tier:** Select "Professional" (matches moderate risk)
   - **Funding Method:** Select "Wire Transfer"
   - Leave Preferred Manager blank

4. Click **"Submit Application"** button
5. ✅ **Expected:**
   - Form validates (capital meets minimum)
   - Redirected to contract review page

#### **Step 7: Review and Sign Contracts**

1. Should be on: `/investing/managed/onboarding/application/<id>/contracts/`
2. ✅ **Check Page Shows:**
   - 4 contracts listed:
     1. Investment Management Agreement (IMA)
     2. Options Trading Risk Disclosure
     3. Fee Schedule Agreement
     4. Terms of Service
   - Each contract has:
     - Contract text (scrollable)
     - Checkbox to acknowledge
     - Signature canvas

3. For each contract:
   - Read contract text
   - Check acknowledgment box
   - Draw signature in canvas
   - Click **"Sign Contract"** button

4. After signing all 4 contracts:
   - ✅ **Expected:** Auto-approval triggers
   - ✅ **Check:** See success message with account number
   - ✅ **Check:** Redirected to client portal

#### **Step 8: View Dashboard After Approval**

1. Go back to: http://localhost:8000/investing/dashboard/
2. ✅ **Expected:** Dashboard now shows:
   - **"Your Managed Options Trading Accounts"** card (blue)
   - Account number (e.g., CODA-OPT-006)
   - Balance: $30,000.00
   - P&L: $0.00
   - Open Positions: 0
   - **"View Account"** button

3. ✅ **Check:** "Get Started" card is GONE (you now have an account)

---

### **SCENARIO 2: Existing User with Account**

#### **Step 1: Login as Test User**

1. Go to: http://localhost:8000/accounts/login/
2. Login with existing test user:
   - **Username:** `test_client_opt`
   - **Password:** `test123`
3. ✅ **Expected:** Logged in successfully

#### **Step 2: View Dashboard**

1. Go to: http://localhost:8000/investing/dashboard/
2. ✅ **Check Dashboard Shows:**
   - Summary cards (4 cards at top)
   - **PENDING BATCH APPROVAL** (red card) - IF batch exists
     - Batch number: BATCH-2025-W44
     - Positions: 3
     - Capital: $23,000
     - Time remaining: XX hours
     - **"APPROVE NOW"** button (large, red)
   
   - **Your Managed Accounts** (blue card)
     - Account: CODA-OPT-006
     - Balance: $30,000.00
     - P&L: Shows current P&L
     - Open Positions: 3
     - **"View Account"** button

#### **Step 3: Click "APPROVE NOW" (Batch Approval)**

1. Click **"APPROVE NOW"** button in red pending batch card
2. ✅ **Expected:** Redirected to `/investing/managed/portal/approvals/batch/1/`
3. ✅ **Check Batch Approval Page Shows:**
   - Batch number and deadline
   - Time remaining (countdown)
   - List of 3 positions:
     - AAPL Bull Put Spread ($500 capital)
     - TSLA Short Put ($22,000 capital)
     - MSFT Bull Put Spread ($500 capital)
   - Each position shows:
     - Symbol, strategy
     - Strike prices
     - Premium
     - Max profit/loss
     - Capital required
   - Total capital: $23,000
   - Three buttons:
     - **"Approve All"** (green)
     - **"Reject All"** (red)
     - **"Review Individually"** (yellow)
   - Signature canvas
   
#### **Step 4: Approve the Batch**

1. Review all positions
2. Draw signature in canvas
3. Click **"Approve All"** button
4. ✅ **Expected:**
   - Success message: "Approved 3 positions!"
   - Positions now show as "Open"
   - Redirected to client portal or dashboard

#### **Step 5: View Client Portal**

1. Click **"View All Managed Accounts"** button on dashboard
   OR go to: http://localhost:8000/investing/managed/portal/
2. ✅ **Check Portal Shows:**
   - Account card(s) with summary
   - List of all open positions (3 positions)
   - Performance metrics
   - **"View Details"** button for each account

#### **Step 6: View Account Details**

1. Click **"View Account"** button
2. ✅ **Expected:** Redirected to `/investing/managed/portal/accounts/<id>/`
3. ✅ **Check Account Detail Page Shows:**
   - Account number: CODA-OPT-006
   - Fee tier: Professional
   - Balance: $30,000.00
   - Total P&L: Current P&L value
   - Win rate: XX%
   
   - **Open Positions Section:**
     - 3 positions listed
     - Each shows: Symbol, Strategy, Capital, P&L, Status
   
   - **Account Activity:**
     - Recent activities logged
   
   - **Performance Chart** (if any closed positions)

---

### **SCENARIO 3: Staff User Testing**

#### **Step 1: Login as Staff**

1. Logout current user
2. Go to: http://localhost:8000/accounts/login/
3. Login as:
   - **Username:** `test_manager`
   - **Password:** `test123`

#### **Step 2: View Dashboard**

1. Go to: http://localhost:8000/investing/dashboard/
2. ✅ **Check:** "Staff Management Tools" section appears (yellow card)
3. ✅ **Check 8 Staff Buttons:**
   - Manage Accounts
   - Create Position
   - Quick Add Position
   - Monitor Positions
   - View Applications
   - View Batches
   - View Sessions
   - Staff Reports

#### **Step 3: Test Each Staff Button**

**Button 1: Manage Accounts**
1. Click **"Manage Accounts"** button
2. ✅ **Expected:** `/investing/managed/accounts/`
3. ✅ **Check:**
   - List of all managed accounts
   - CODA-OPT-005, CODA-OPT-006 appear
   - Each row shows: Account #, Client, Balance, P&L, Status
   - **"Create New Account"** button at top
   - Click account number to view details

**Button 2: Create Position**
1. Back to dashboard, click **"Create Position"**
2. ✅ **Expected:** `/investing/managed/positions/create/`
3. ✅ **Check:**
   - Form loads
   - Account dropdown shows accounts
   - All position fields present

**Button 3: Quick Add Position (Enhanced)**
1. Back to dashboard, click **"Quick Add Position"**
2. ✅ **Expected:** `/investing/managed/positions/create/enhanced/`
3. ✅ **Check:**
   - Multi-tab interface loads
   - Tab 1: Multi-Leg Strategy
   - Tab 2: AI Recommendations
   - Tab 3: Quick Entry
   - Real-time risk calculator on right
   - All fields functional

**Button 4: Monitor Positions**
1. Click **"Monitor Positions"**
2. ✅ **Expected:** `/investing/managed/monitor/`
3. ✅ **Check:**
   - All positions listed
   - Filter by account
   - Alerts shown
   - Exit criteria displayed

**Button 5: View Applications**
1. Click **"View Applications"**
2. ✅ **Expected:** `/investing/managed/staff/applications/pending/`
3. ✅ **Check:**
   - Pending applications listed (if any)
   - Each shows: Client name, capital, tier, status
   - **"Review"** button for each

**Button 6: View Batches**
1. Click **"View Batches"**
2. ✅ **Expected:** `/investing/managed/staff/batches/`
3. ✅ **Check:**
   - All batches listed
   - Batch numbers, accounts, status
   - Pending count shown
   - **"Create Batch"** button (if needed)

---

## **✅ COMPLETE TESTING CHECKLIST**

### **Dashboard Testing:**
- [ ] Summary cards display correct values
- [ ] All buttons are clickable
- [ ] Correct sections show based on user state:
  - [ ] New user → "Start Managed Trading" card
  - [ ] Application pending → "Application In Progress" card
  - [ ] Has account → "Your Managed Accounts" card
  - [ ] Pending batch → "ACTION REQUIRED" red banner
- [ ] Staff users see "Staff Management Tools"
- [ ] Client users don't see staff tools

### **Onboarding Flow:**
- [ ] Risk assessment form displays 10 questions
- [ ] All radio buttons work
- [ ] Form submits and calculates score
- [ ] Application form pre-fills risk data
- [ ] Capital validation works (min $5,000)
- [ ] Tier/capital mismatch shows error
- [ ] Contract page shows all 4 contracts
- [ ] Signature canvas works
- [ ] Auto-approval triggers on last signature
- [ ] Welcome message shows account number

### **Batch Approval:**
- [ ] Pending batch shows on dashboard
- [ ] "APPROVE NOW" button prominent and clickable
- [ ] Batch page shows all positions
- [ ] Position details accurate
- [ ] Total capital correct
- [ ] Time remaining displays
- [ ] Signature canvas works
- [ ] "Approve All" button works
- [ ] Success message shows
- [ ] Dashboard updates (batch disappears)

### **Client Portal:**
- [ ] Account cards display
- [ ] Balance accurate
- [ ] P&L displays correctly
- [ ] Position count accurate
- [ ] "View Account" button works
- [ ] Account detail page shows all data
- [ ] Positions list complete
- [ ] Performance metrics accurate

### **Staff Tools:**
- [ ] All 8 buttons clickable
- [ ] Each view loads without errors
- [ ] Data displays correctly
- [ ] Forms submit successfully
- [ ] Create position works
- [ ] Enhanced form calculations work
- [ ] Monitor dashboard shows alerts
- [ ] Application queue functional

---

## **🔧 TESTING CREDENTIALS**

**Client User:**
- Username: `test_client_opt`
- Password: `test123`
- Has: Account CODA-OPT-006, 3 positions, 1 batch

**Staff User:**
- Username: `test_manager`
- Password: `test123`
- Can: Manage all accounts, create positions, review applications

**New User (Create Your Own):**
- Register with category: "Investor" → "Individual"
- Complete onboarding flow
- Test from scratch

---

## **🌐 KEY URLs TO TEST**

**Registration & Login:**
- http://localhost:8000/accounts/register/
- http://localhost:8000/accounts/login/

**Main Dashboard:**
- http://localhost:8000/investing/dashboard/

**Client Onboarding (Click "Start Now" button):**
- Risk Assessment → Application → Contracts → Auto-Approval

**Client Portal (Click "View All Managed Accounts"):**
- Account list → Account detail → Position details

**Batch Approval (Click "APPROVE NOW" button):**
- Review positions → Sign → Approve All → Confirmation

**Staff Tools (Click any of 8 buttons):**
- Manage Accounts, Create Position, Monitor, Applications, Batches, etc.

---

## **🐛 WHAT TO LOOK FOR**

### **Errors to Report:**
- [ ] 404 errors (page not found)
- [ ] 500 errors (server error)
- [ ] Template errors (AttributeError, etc.)
- [ ] JavaScript errors (F12 console)
- [ ] Missing data
- [ ] Incorrect calculations
- [ ] Buttons that don't work
- [ ] Forms that don't submit

### **Data Verification:**
- [ ] Account numbers correct format (CODA-OPT-XXX)
- [ ] Balances match expected ($30,000 initial)
- [ ] Position capital calculations accurate
- [ ] Batch totals correct (sum of positions)
- [ ] Time remaining calculation correct
- [ ] Performance metrics accurate

### **UI/UX Issues:**
- [ ] Buttons hard to find
- [ ] Unclear navigation
- [ ] Confusing workflow
- [ ] Missing instructions
- [ ] Poor mobile responsiveness

---

## **📝 TESTING LOG**

As you test, note:
1. **URL tested**
2. **What you clicked**
3. **What happened**
4. **Was it correct?**
5. **Any errors?**

**Example:**
```
URL: http://localhost:8000/investing/dashboard/
Clicked: "Start Now" button
Expected: Go to risk assessment
Actual: ✅ Worked perfectly
Errors: None
```

---

**HAPPY TESTING! 🚀**

Report any issues and we'll fix them immediately!
