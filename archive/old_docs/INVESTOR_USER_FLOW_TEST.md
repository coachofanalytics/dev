# CODA Investing App - Investor User Flow Test Plan

## 🎯 **Test Overview**

**Date**: October 25, 2025  
**User Type**: Investor (User Category: INVESTOR)  
**Scope**: Complete end-to-end user flow testing  
**Environment**: Local Development (localhost:8000)

---

## 📋 **Pre-Test Setup**

### **1. Create/Verify Investor User**
```python
# Run in Django shell: python3 manage.py shell

from accounts.models import CustomerUser
from accounts.choices import UserCategory

# Create test investor user
investor = CustomerUser.objects.create_user(
    username='investor_test',
    email='investor@codaplatform.com',
    password='Test@1234',
    first_name='John',
    last_name='Investor',
    category=UserCategory.INVESTOR,
    is_active=True
)

print(f"✅ Created investor user: {investor.username}")
print(f"📧 Email: {investor.email}")
print(f"🔑 Password: Test@1234")
print(f"👤 Category: {investor.get_category_display()}")
```

### **2. Verify Server is Running**
- URL: http://localhost:8000
- Admin: http://localhost:8000/admin
- Investing Home: http://localhost:8000/investing/

---

## 🧪 **Complete User Flow Test**

### **Phase 1: Login & Authentication** ✅

#### **Test 1.1: Login Page**
- **URL**: http://localhost:8000/accounts/login/
- **Actions**:
  - [ ] Navigate to login page
  - [ ] Verify login form displays correctly
  - [ ] Check "Remember Me" checkbox exists
  - [ ] Verify "Forgot Password" link exists
  
#### **Test 1.2: Login Process**
- **Credentials**:
  - Username: `investor_test`
  - Password: `Test@1234`
- **Actions**:
  - [ ] Enter credentials
  - [ ] Click "Login" button
  - [ ] Verify successful redirect
  - [ ] Check user is authenticated
  
#### **Test 1.3: Post-Login Dashboard**
- **Expected**: Redirect to appropriate dashboard
- **Actions**:
  - [ ] Verify investor sees investing dashboard
  - [ ] Check user name displays in header
  - [ ] Verify logout button is visible

---

### **Phase 2: Investing Platform Overview** 🏠

#### **Test 2.1: Platform Home**
- **URL**: http://localhost:8000/investing/
- **Actions**:
  - [ ] Click "Investing" in main navigation
  - [ ] Verify platform overview page loads
  - [ ] Check all feature cards display
  - [ ] Verify investment plans section

#### **Test 2.2: Investment Plans**
- **URL**: http://localhost:8000/investing/investmentplans/
- **Actions**:
  - [ ] Click "View Investment Plans" button
  - [ ] Verify all investment tiers display (Tier 1, 2, 3)
  - [ ] Check plan details (rates, amounts, durations)
  - [ ] Verify "Apply Now" buttons work

#### **Test 2.3: Investment Content**
- **Actions**:
  - [ ] Read investment descriptions
  - [ ] Check advantages/features sections
  - [ ] Verify all links and buttons functional

---

### **Phase 3: Investment Application** 📝

#### **Test 3.1: Application Form Access**
- **URL**: http://localhost:8000/investing/apply/
- **Actions**:
  - [ ] Click "Apply for Investment" button
  - [ ] Verify form loads correctly
  - [ ] Check all form fields display
  - [ ] Verify plan selection cards

#### **Test 3.2: Plan Selection**
- **Actions**:
  - [ ] Click on Tier 1 plan card
  - [ ] Verify card highlights/selects
  - [ ] Check minimum amount updates
  - [ ] Try selecting different tiers

#### **Test 3.3: Form Completion**
- **Test Data**:
  ```json
  {
    "investment_plan": "Tier 1",
    "amount_invested": "5000.00",
    "duration": "12",
    "investment_purpose": "Long-term growth and portfolio diversification",
    "model_type": "Installment",
    "expected_return_rate": "8.00"
  }
  ```
- **Actions**:
  - [ ] Fill in investment amount ($5,000)
  - [ ] Select duration (12 months)
  - [ ] Enter investment purpose
  - [ ] Select model type
  - [ ] Set expected return rate
  - [ ] Click "Submit Application"

#### **Test 3.4: Form Validation**
- **Actions**:
  - [ ] Try submitting with amount < $1,000 (should fail)
  - [ ] Try submitting with empty fields (should fail)
  - [ ] Verify error messages display correctly
  - [ ] Test successful submission

---

### **Phase 4: Investment Dashboard** 📊

#### **Test 4.1: Dashboard Access**
- **URL**: http://localhost:8000/investing/dashboard/
- **Actions**:
  - [ ] Click "Dashboard" in navigation
  - [ ] Verify dashboard loads completely
  - [ ] Check all summary cards display
  - [ ] Verify charts render correctly

#### **Test 4.2: Summary Cards**
- **Cards to Verify**:
  - [ ] Total Invested (displays amount)
  - [ ] Current Value (shows valuation)
  - [ ] Total Returns (displays returns)
  - [ ] Return % (shows percentage)

#### **Test 4.3: Investment List**
- **Actions**:
  - [ ] Verify investment table displays
  - [ ] Check all columns visible
  - [ ] Verify "View Details" buttons
  - [ ] Test pagination (if applicable)

#### **Test 4.4: Performance Charts**
- **Actions**:
  - [ ] Verify performance chart renders
  - [ ] Check chart displays data correctly
  - [ ] Test chart interactivity (if applicable)

---

### **Phase 5: Individual Investments** 💼

#### **Test 5.1: Investments List**
- **URL**: http://localhost:8000/investing/individual-investments/
- **Actions**:
  - [ ] Click "My Investments" link
  - [ ] Verify investments list loads
  - [ ] Check summary cards display
  - [ ] Verify investment table

#### **Test 5.2: Investment Details**
- **URL**: http://localhost:8000/investing/individual-investment/1/
- **Actions**:
  - [ ] Click "View Details" on an investment
  - [ ] Verify detail page loads
  - [ ] Check all investment information displays
  - [ ] Verify performance metrics
  - [ ] Check document section

#### **Test 5.3: Create New Investment**
- **URL**: http://localhost:8000/investing/create-individual-investment/
- **Actions**:
  - [ ] Click "Create New Investment" button
  - [ ] Verify form displays
  - [ ] Fill in all required fields
  - [ ] Submit form
  - [ ] Verify investment created successfully

---

### **Phase 6: Risk Management** 🛡️

#### **Test 6.1: Risk Dashboard Access**
- **URL**: http://localhost:8000/investing/risk/risk-dashboard/
- **Actions**:
  - [ ] Click "Risk Management" link
  - [ ] Verify risk dashboard loads
  - [ ] Check risk summary cards display
  - [ ] Verify risk distribution chart

#### **Test 6.2: Risk Summary Cards**
- **Cards to Verify**:
  - [ ] Total Investments count
  - [ ] High Risk investments
  - [ ] Active Alerts count
  - [ ] Compliance Issues

#### **Test 6.3: Risk Distribution Chart**
- **Actions**:
  - [ ] Verify doughnut chart renders
  - [ ] Check low/medium/high risk breakdown
  - [ ] Verify chart colors and labels

#### **Test 6.4: Active Alerts**
- **Actions**:
  - [ ] Check active alerts panel
  - [ ] Verify alert severity indicators
  - [ ] Test alert action buttons
  - [ ] Check alert details display

#### **Test 6.5: Recent Risk Assessments**
- **Actions**:
  - [ ] Verify recent assessments list
  - [ ] Check risk rating badges
  - [ ] Verify assessment scores
  - [ ] Test "New Assessment" button

#### **Test 6.6: Compliance Status**
- **Actions**:
  - [ ] Check compliance table displays
  - [ ] Verify requirement types
  - [ ] Check status indicators
  - [ ] Verify due dates
  - [ ] Test progress bars

---

### **Phase 7: Portfolio Management** 📈

#### **Test 7.1: Portfolio Access**
- **URL**: http://localhost:8000/investing/myportfolio/
- **Actions**:
  - [ ] Click "Portfolio" in navigation
  - [ ] Verify portfolio list loads
  - [ ] Check portfolio entries display
  - [ ] Verify filtering options

#### **Test 7.2: Portfolio Details**
- **Actions**:
  - [ ] Click on portfolio entry
  - [ ] Verify details display correctly
  - [ ] Check all metrics visible
  - [ ] Verify options data

#### **Test 7.3: Create Portfolio Entry**
- **URL**: http://localhost:8000/investing/myportfoliocreate/
- **Actions**:
  - [ ] Click "Create Portfolio Entry"
  - [ ] Fill in all required fields
  - [ ] Submit form
  - [ ] Verify entry created

#### **Test 7.4: Update Portfolio**
- **URL**: http://localhost:8000/investing/myportfolioupdate/SYMBOL/
- **Actions**:
  - [ ] Click "Edit" on portfolio entry
  - [ ] Modify returns/comments
  - [ ] Save changes
  - [ ] Verify updates applied

---

### **Phase 8: Options Trading** 📊

#### **Test 8.1: Options List**
- **URL**: http://localhost:8000/investing/options/SYMBOL/
- **Actions**:
  - [ ] Navigate to options section
  - [ ] Verify options list displays
  - [ ] Check all option types
  - [ ] Verify pricing information

#### **Test 8.2: Covered Calls**
- **Actions**:
  - [ ] View covered calls list
  - [ ] Check strike prices
  - [ ] Verify expiry dates
  - [ ] Check returns calculation

#### **Test 8.3: Short Puts**
- **Actions**:
  - [ ] View short puts list
  - [ ] Check option details
  - [ ] Verify implied volatility
  - [ ] Check risk metrics

#### **Test 8.4: Credit Spreads**
- **Actions**:
  - [ ] View credit spreads
  - [ ] Check spread width
  - [ ] Verify premium/width ratio
  - [ ] Check earnings dates

---

### **Phase 9: Investment Strategies** 🎯

#### **Test 9.1: Strategies List**
- **URL**: http://localhost:8000/investing/investstrategy/
- **Actions**:
  - [ ] Click "Investment Strategies"
  - [ ] Verify strategies list loads
  - [ ] Check strategy details
  - [ ] Verify filtering options

#### **Test 9.2: Create Strategy**
- **URL**: http://localhost:8000/investing/investstrategycreate/
- **Actions**:
  - [ ] Click "Create Strategy" button
  - [ ] Fill in strategy details
  - [ ] Submit form
  - [ ] Verify strategy created

#### **Test 9.3: Update Strategy**
- **URL**: http://localhost:8000/investing/investstrategyupdate/1/
- **Actions**:
  - [ ] Click "Edit" on strategy
  - [ ] Modify strategy details
  - [ ] Save changes
  - [ ] Verify updates applied

---

### **Phase 10: Reports & Analytics** 📑

#### **Test 10.1: Performance Reports**
- **Actions**:
  - [ ] Access performance reports section
  - [ ] Verify report data displays
  - [ ] Check monthly/quarterly reports
  - [ ] Verify report accuracy

#### **Test 10.2: Returns Analysis**
- **URL**: http://localhost:8000/investing/companyreturns/SYMBOL/
- **Actions**:
  - [ ] View company returns page
  - [ ] Check returns table
  - [ ] Verify calculations
  - [ ] Check historical data

#### **Test 10.3: Cost Basis**
- **URL**: http://localhost:8000/investing/costbasis/
- **Actions**:
  - [ ] Navigate to cost basis page
  - [ ] Verify cost basis table
  - [ ] Check calculations
  - [ ] Verify date ranges

---

### **Phase 11: Market Analysis** 📉

#### **Test 11.1: Ticker Measures**
- **URL**: http://localhost:8000/investing/measures/
- **Actions**:
  - [ ] Access ticker measures page
  - [ ] Verify financial metrics display
  - [ ] Check risk ratios
  - [ ] Verify data sources

#### **Test 11.2: Overbought/Oversold**
- **URL**: http://localhost:8000/investing/overboughtsold/SYMBOL/
- **Actions**:
  - [ ] View oversold positions
  - [ ] Check RSI indicators
  - [ ] Verify volume data
  - [ ] Check PE ratios

---

### **Phase 12: User Profile & Settings** ⚙️

#### **Test 12.1: Profile Access**
- **Actions**:
  - [ ] Click on user name/avatar
  - [ ] Verify profile page loads
  - [ ] Check personal information
  - [ ] Verify investment preferences

#### **Test 12.2: Notification Preferences**
- **Actions**:
  - [ ] Access notification settings
  - [ ] Verify preference options
  - [ ] Toggle notification types
  - [ ] Save preferences

#### **Test 12.3: Communication History**
- **Actions**:
  - [ ] View communication history
  - [ ] Check email records
  - [ ] Verify report history
  - [ ] Check notification log

---

### **Phase 13: Mobile Responsiveness** 📱

#### **Test 13.1: Mobile View**
- **Actions**:
  - [ ] Resize browser to mobile width
  - [ ] Verify responsive layout
  - [ ] Check navigation menu (hamburger)
  - [ ] Test all buttons/links

#### **Test 13.2: Touch Interactions**
- **Actions**:
  - [ ] Test touch-friendly buttons
  - [ ] Verify form inputs work
  - [ ] Check swipe gestures (if applicable)
  - [ ] Test chart interactions

---

### **Phase 14: Error Handling** ⚠️

#### **Test 14.1: 404 Errors**
- **Actions**:
  - [ ] Navigate to non-existent URL
  - [ ] Verify 404 page displays
  - [ ] Check "Back to Home" link

#### **Test 14.2: Permission Errors**
- **Actions**:
  - [ ] Try accessing admin-only pages
  - [ ] Verify permission denied message
  - [ ] Check proper redirect

#### **Test 14.3: Form Validation Errors**
- **Actions**:
  - [ ] Submit forms with invalid data
  - [ ] Verify error messages display
  - [ ] Check field-level validation
  - [ ] Verify error styling

---

### **Phase 15: Logout & Security** 🔐

#### **Test 15.1: Logout Process**
- **Actions**:
  - [ ] Click "Logout" button
  - [ ] Verify successful logout
  - [ ] Check redirect to login page
  - [ ] Verify session cleared

#### **Test 15.2: Security Checks**
- **Actions**:
  - [ ] Try accessing protected URLs after logout
  - [ ] Verify redirect to login
  - [ ] Check CSRF token presence
  - [ ] Verify secure cookies

---

## 📊 **Test Results Template**

### **Test Execution Summary**

| Phase | Total Tests | Passed | Failed | Blocked | Pass Rate |
|-------|-------------|--------|--------|---------|-----------|
| 1. Login & Authentication | 3 | - | - | - | - |
| 2. Platform Overview | 3 | - | - | - | - |
| 3. Investment Application | 4 | - | - | - | - |
| 4. Investment Dashboard | 4 | - | - | - | - |
| 5. Individual Investments | 3 | - | - | - | - |
| 6. Risk Management | 6 | - | - | - | - |
| 7. Portfolio Management | 4 | - | - | - | - |
| 8. Options Trading | 4 | - | - | - | - |
| 9. Investment Strategies | 3 | - | - | - | - |
| 10. Reports & Analytics | 3 | - | - | - | - |
| 11. Market Analysis | 2 | - | - | - | - |
| 12. User Profile & Settings | 3 | - | - | - | - |
| 13. Mobile Responsiveness | 2 | - | - | - | - |
| 14. Error Handling | 3 | - | - | - | - |
| 15. Logout & Security | 2 | - | - | - | - |
| **TOTAL** | **49** | - | - | - | **-%** |

---

## 🐛 **Bug Tracking Template**

### **Issue Log**

| # | Phase | Test | Severity | Description | Status | Fix |
|---|-------|------|----------|-------------|--------|-----|
| 1 | - | - | - | - | - | - |

---

## ✅ **Sign-Off Checklist**

- [ ] All test phases completed
- [ ] All critical buttons tested
- [ ] All navigation links verified
- [ ] Forms validated and functional
- [ ] Charts and visualizations working
- [ ] Mobile responsiveness confirmed
- [ ] Security checks passed
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Documentation updated

---

**Test Conducted By**: _________________  
**Date**: _________________  
**Signature**: _________________

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**Status**: ⏳ **READY FOR TESTING**
