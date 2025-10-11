# Template Testing Plan - Buttons and Redirects

**Date:** October 3, 2025  
**Status:** 🚧 **IN PROGRESS**  
**Goal:** Test all buttons and redirects in templates after structure organization

---

## 🎯 **TESTING OBJECTIVES**

### ✅ **Critical Templates to Test**
1. **Budget Dashboard** (`budgets/unified_dashboard.html`)
2. **Smart Transaction Entry** (`payments/smart_transaction_entry.html`)
3. **Budget Category Edit** (`budgets/budget_category_edit.html`)
4. **Budget Requests** (`budgets/budget_requests_list.html`)
5. **Loan Dashboard** (`loans/loan_budget_dashboard.html`)

### ✅ **Key Areas to Test**
- **Navigation Links**: Tab navigation, breadcrumbs
- **Action Buttons**: Save, Edit, Delete, Approve, Reject
- **Form Submissions**: POST requests, AJAX calls
- **API Endpoints**: AJAX calls to organized views
- **Redirects**: After form submissions, after actions

---

## 🧪 **TESTING CHECKLIST**

### **1. Budget Dashboard (`unified_dashboard.html`)**
- [ ] **Tab Navigation**: Overview, Estimation, Planning, Approvals, Analytics, Editing, Loans
- [ ] **Department Filter**: Dropdown selection and form submission
- [ ] **Category Links**: Clickable categories (if implemented)
- [ ] **Action Buttons**: Any edit/create buttons
- [ ] **API Calls**: Dashboard data loading

### **2. Smart Transaction Entry (`smart_transaction_entry.html`)**
- [ ] **Form Submission**: POST to organized view
- [ ] **Auto-fill Button**: `fillFromLast()` function
- [ ] **Cancel Button**: Redirect to cashflows list
- [ ] **API Calls**: 
  - `/finance/api/predict-all/` (line 352)
  - `/finance/api/subcategories/` (line 597)
  - `{% url "finance:api-get-items" %}` (line 651)
  - `{% url "finance:api-suggest-defaults" %}` (line 730)

### **3. Budget Category Edit (`budget_category_edit.html`)**
- [ ] **Form Submission**: POST to organized editing view
- [ ] **Save Button**: Update budget estimates
- [ ] **Cancel Button**: Return to dashboard
- [ ] **Approval Workflow**: Submit for approval button

### **4. Budget Requests (`budget_requests_list.html`)**
- [ ] **Request Links**: Link to request details
- [ ] **Approve/Reject Buttons**: Action buttons
- [ ] **Create Request**: New request button
- [ ] **Filter/Search**: Any filtering functionality

### **5. Loan Dashboard (`loan_budget_dashboard.html`)**
- [ ] **Loan Application**: Create new application
- [ ] **Eligibility Check**: Check eligibility button
- [ ] **Application List**: View applications
- [ ] **Dashboard Navigation**: Tab navigation

---

## 🔍 **SPECIFIC ISSUES TO CHECK**

### **1. URL Name Changes**
After organizing views, some URL names might have changed:
- `views_budget_drilldown` → `views.budget.drilldown`
- `views_smart_transaction` → `views.transaction.smart_entry`
- `views_loan_budget_integration` → `views.loan.budget_integration`

### **2. Import Path Changes**
Templates might reference views that have moved:
- Check all `{% url %}` tags
- Verify API endpoint URLs
- Check form action URLs

### **3. View Function Names**
Some view functions might have been renamed during organization:
- Check function names in templates
- Verify redirect URLs in views
- Check AJAX endpoint references

---

## 🚨 **CRITICAL TESTING AREAS**

### **1. Form Actions**
```html
<!-- Check these form actions work -->
<form method="post" action="{% url 'finance:budget-category-edit' company.slug category.id %}">
<form method="post" action="{% url 'finance:smart-transaction-entry' %}">
```

### **2. AJAX Endpoints**
```javascript
// Check these AJAX calls work
url: '/finance/api/predict-all/',
url: '/finance/api/subcategories/',
url: '{% url "finance:api-get-items" %}',
```

### **3. Navigation Links**
```html
<!-- Check these navigation links work -->
<a href="{% url 'finance:unified-budget-dashboard' company.slug %}">
<a href="{% url 'finance:budget-category-detail' company.slug category.id %}">
```

### **4. Button Actions**
```html
<!-- Check these button actions work -->
<button onclick="fillFromLast()">Quick Fill</button>
<button type="submit">Save Budget</button>
<button onclick="approveRequest({{ request.id }})">Approve</button>
```

---

## 🛠️ **TESTING METHODOLOGY**

### **1. Manual Testing**
- Navigate to each template
- Click all buttons and links
- Submit all forms
- Check redirects work correctly

### **2. URL Testing**
- Test all URL patterns in `urls.py`
- Verify URL names match template references
- Check for 404 errors

### **3. JavaScript Testing**
- Test all AJAX calls
- Check console for JavaScript errors
- Verify API endpoints respond correctly

### **4. Form Testing**
- Submit forms with valid data
- Submit forms with invalid data
- Check form validation works
- Verify success/error messages

---

## 📋 **TESTING RESULTS TRACKER**

### **Budget Dashboard**
- [ ] Tab navigation works
- [ ] Department filter works
- [ ] Category links work (if implemented)
- [ ] No JavaScript errors
- [ ] API calls successful

### **Smart Transaction Entry**
- [ ] Form submission works
- [ ] Auto-fill button works
- [ ] Cancel button redirects correctly
- [ ] All API endpoints respond
- [ ] Form validation works

### **Budget Category Edit**
- [ ] Form submission works
- [ ] Save button updates budget
- [ ] Cancel button redirects
- [ ] Approval workflow works
- [ ] Error handling works

### **Budget Requests**
- [ ] Request list loads
- [ ] Request details work
- [ ] Approve/Reject buttons work
- [ ] Create request works
- [ ] Filtering works

### **Loan Dashboard**
- [ ] Dashboard loads
- [ ] Loan application works
- [ ] Eligibility check works
- [ ] Application list works
- [ ] Navigation works

---

## 🚀 **NEXT STEPS**

1. **Start Manual Testing**: Test each template systematically
2. **Fix Broken Links**: Update any broken URL references
3. **Fix JavaScript Errors**: Resolve any AJAX or JS issues
4. **Update Templates**: Fix any template issues found
5. **Deploy and Test**: Test in UAT environment

---

**Status**: 🚧 **READY TO START TESTING**  
**Priority**: **HIGH** - Critical for user experience  
**Owner**: CODA Development Team



