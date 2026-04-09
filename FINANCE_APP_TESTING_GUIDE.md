# Finance App - Comprehensive Testing Guide

## Overview
The Finance App is a comprehensive financial management system for handling payments, contracts, budgets, transactions, and investment opportunities. It manages customer payments, financial records, budget tracking, and an investment directory platform.

---

## 1. Core Models & Data Structure

### 1.1 Payment Management Models

#### **Payment_Information**
- **Purpose**: Store client contract payment details
- **Key Fields**:
  - `customer_id` (ForeignKey: CustomerUser) - Client reference
  - `payment_method` (CharField) - Payment type (Cash, Mpesa, Check, etc.)
  - `plan` (IntegerField) - Payment plan duration
  - `contract_submitted_date` (DateTimeField) - Contract date
  - `client_signature`, `company_rep` - Contract signatories
  - `client_date`, `rep_date` - Signature dates
- **Calculated Properties**:
  - `student_balance` - Calculates remaining balance: `payment_fees - (down_payment + student_bonus)`
  - `jobsupport_balance` - Calculates support balance: `payment_fees - down_payment`
- **Testing Considerations**:
  - Verify balance calculations are accurate
  - Test with missing/null values
  - Ensure date tracking works properly

#### **Payment_History**
- **Purpose**: Audit trail of all payment transactions
- **Key Fields**: Mirrors Payment_Information with additional tracking
  - `payment_fees`, `down_payment`, `student_bonus`, `fee_balance`
  - Historical record of signed contracts
- **Testing Considerations**:
  - Verify historical records are created on payment
  - Test data integrity (duplicate fields observation: `down_payment` and `student_bonus` defined twice)
  - Ensure archive completeness

#### **Default_Payment_Fees**
- **Purpose**: System-wide default payment configuration
- **Key Fields**:
  - `job_down_payment_per_month` (default: 500)
  - `job_plan_hours_per_month` (default: 40)
  - `student_down_payment_per_month` (default: 500)
  - `student_bonus_payment_per_month` (default: 250)
- **Testing Considerations**:
  - Test updating default fees affects new payments
  - Verify only superusers can modify these values
  - Test system behavior with edge case fee values

### 1.2 Transaction Management Model

#### **Transaction**
- **Purpose**: Track all financial inflows/outflows
- **Key Fields**:
  - `clients_category` (Choices: DYC, Other)
  - `category` (Choices: Registration Fee, Contributions, Donations, GC Application, Business, Tourism, Stocks, Other)
  - `method` (Choices: Cash, Mpesa, Check, Cashapp, Zelle, Venmo, Paypal, Other)
  - `period` (Choices: Weekly, Bi-Weekly, Monthly, Yearly)
  - `sender` (ForeignKey: CustomerUser)
  - `receiver`, `phone`, `sender_phone` - Contact info
  - `qty`, `amount`, `transaction_cost` (Decimal fields)
  - `receipt_link` - URL to transaction receipt
  - `is_active`, `has_paid` (Boolean flags)
  - `transaction_date` (default: timezone.now)
- **Calculated Properties**:
  - `total_payment` - Rounds amount to 2 decimals
  - `total_paid` - Returns amount if `has_paid=True`, else 0
  - `end` - Derives time from login_date (potential bug: `login_date` not defined)
  - `receipturl` - Returns receipt link or redirects to main:layout
- **Testing Considerations**:
  - **CRITICAL BUG**: `end` property uses undefined `login_date` field
  - Test decimal precision (10,2 max_digits)
  - Verify receipt URL handling
  - Test transaction filtering by category/method/period
  - Validate amount and cost calculations

### 1.3 Budget Management Models

#### **BudgetCategory**
- **Purpose**: Parent categories for budgets (e.g., Operations)
- **Key Fields**: `name`, `description`
- **Testing**: CRUD operations, cascading deletes

#### **BudgetSubCategory**
- **Purpose**: Hierarchical budget classification
- **Key Fields**: 
  - `category` (ForeignKey: BudgetCategory)
  - `name`
- **String Representation**: `"category_name-subcategory_name"`
- **Testing**: Verify subcategory constraints, cascading, ordering

#### **Budget**
- **Purpose**: Individual budget item tracking
- **Key Fields**:
  - `budget_lead` (ForeignKey: CustomerUser, staff-only limit)
  - `category`, `subcategory` (ForeignKey/CharField)
  - `start_date`, `end_date`
  - `item` (CharField), `cases`, `qty`, `unit_price` (Decimal)
  - `description`, `receipt_link`
  - `is_active` (Boolean)
- **Calculated Properties**:
  - `days` - Difference between end_date and start_date
  - `amount` - `unit_price * cases * qty` (rounded to 2 decimals)
  - `receipturl` - Returns receipt URL or redirects to main:layout
- **Testing Considerations**:
  - Verify amount calculations with various unit_price/qty/cases combinations
  - Test date range calculations
  - Validate staff-only access controls
  - Test budget lead filtering (is_staff=True, is_active=True, category=2)

#### **CodaBudget** (TimeStampedModel)
- **Purpose**: Department-specific budget tracking with timestamps
- **Key Fields**:
  - `budget_lead` (ForeignKey: User, staff-only)
  - `department` (ForeignKey: Department)
  - `category`, `subcategory` (ForeignKey: BudgetCategory/BudgetSubCategory)
  - `item`, `cases`, `qty`, `unit_price` (Decimal)
  - `description`, `receipt_link`
  - `created_at`, `updated_at` (auto-managed), `is_active`, `is_featured`
- **Calculated Properties**:
  - `amount` - `unit_price * qty` (returns Decimal('0.00') if missing)
- **Ordering**: By department, created_at, category, subcategory
- **Testing Considerations**:
  - Test timestamp auto-management
  - Verify department relationships
  - Test cascading department deletes
  - Validate amount calculation with null values

### 1.4 Investment Directory Models

#### **Opportunity**
- **Purpose**: Community-submitted investment opportunities
- **Status Choices**: PENDING, APPROVED, REJECTED
- **Key Fields**:
  - `title`, `description` - Opportunity details
  - `contact` - Submitter email
  - `type` - Opportunity type
  - `status` (default: PENDING)
  - `rejection_reason` (optional - when rejected)
  - `is_suspicious` (Boolean - spam detection flag)
  - `last_notified_at` (DateTimeField - notification tracking)
  - `created_at` (auto_now_add)
- **Custom Manager**: `ApprovedManager` - Filters by status='APPROVED'
- **Signal Automation**:
  - **pre_save**: Stores original status for comparison
  - **post_save**: Sends email notifications when status changes:
    - APPROVED: Approval confirmation email
    - REJECTED: Rejection notification with reason
- **Testing Considerations**:
  - Test status change email notifications
  - Verify spam detection (banned keywords: 'crypto', 'guaranteed', 'whatsapp me', 'bitcoin')
  - Test `is_suspicious` flag marking
  - Validate description length check (min 20 characters)
  - Test approved manager filtering
  - Mock email sending

#### **NewsLetterSubscriber**
- **Purpose**: Newsletter subscription management
- **Key Fields**:
  - `email` (EmailField, unique)
  - `is_verified` (Boolean, default: False)
  - `subscribed_at` (auto_now_add)
  - `verification_token` (UUIDField, auto-generated)
- **Signal Automation**:
  - **post_save (created=True)**: Sends welcome email on new subscription
- **Testing Considerations**:
  - Test email uniqueness constraint
  - Verify welcome email on subscription
  - Test verification token generation
  - Validate email verification flow
  - Mock email sending

### 1.5 Supporting Models

#### **Company** (TimeStampedModel)
- Associated with CODA analytics
- Fields: `name`, `slug` (unique), `sector`, `mission`, `website`, `user` (ForeignKey), `description`

---

## 2. Views & Endpoints

### 2.1 Payment/Contract Management Views

#### **homepage** (GET)
- Route: `/finance/`
- Renders homepage

#### **contract_form_submission** (GET/POST)
- Route: `/finance/contract_form/`
- **GET**: Display contract form
- **POST**: 
  - Parse user student data
  - Create or update Payment_Information
  - Calculate fees: `payment_fees = duration * 1000`
  - Calculate balance: `fee_balance = payment_fees - down_payment`
  - If student contract: `fee_balance -= student_bonus`
  - Create Payment_History record
  - Save Payment_Information
- **Testing**:
  - Test form submission with valid data
  - Test missing form data error handling
  - Verify fee calculation accuracy
  - Test student vs. job support handling
  - Test redirect behavior

#### **pay** (GET)
- Route: `/finance/pay/` or `/finance/payment/<int:service>/`
- **Logic**:
  - Fetch user's Membership record
  - Get Membership fee (in USD)
  - Convert to KES using exchange rate API
  - Display payment information
- **Testing**:
  - Test authentication requirement
  - Test exchange rate API failure handling
  - Test missing Membership error handling
  - Verify KES conversion accuracy

#### **payment** (GET)
- Route: `/finance/payment_method/<str:method>/`
- **Supported Methods**: 'mpesa' (account: 0100008710952)
- Display payment method details with contact information
- **Testing**: Test all payment method rendering, verify account numbers

#### **process_payment** (POST)
- Route: `/finance/process-payment/`
- **Logic**:
  - Get user's Membership
  - Accept entered amount from form
  - Update `membership.fee = entered_amount`
  - Set `membership.status = 'PAID'`
  - Redirect to success page
- **Testing**:
  - Test valid amount input
  - Test invalid (non-numeric) input handling
  - Test ValueError exception handling
  - Verify membership fee update
  - Test redirect behavior

#### **payment_success** (GET)
- Route: `/finance/payment-success/`
- Display success page after payment

#### **payments** (GET)
- Route: `/finance/payments/`
- Fetch user's last Payment_Information record
- Display payment details
- **Testing**: Test with no payment history

#### **mycontract** (GET)
- Route: `/finance/mycontract/<str:username>/`
- Fetch contract for specific user
- **Testing**: Test with non-existent user (should 404), verify contract display

#### **PaymentInformationUpdateView** (UpdateView)
- Route: `/finance/pay/<int:pk>/`
- Model: Payment_Information
- Editable fields: `customer_id`, `down_payment`
- Requires authentication (not superuser-only)
- **Testing**: Test update functionality, permission checks

#### **PaymentCreateView** (CreateView)
- Route: `/finance/newpayment/`
- Model: Payment_Information
- Fields: `customer_id`, `down_payment`, `payment_method`
- Success URL: `/finance/pay/`
- **Testing**: Test creation with various field combinations

### 2.2 Default Payment Management

#### **DefaultPaymentListView** (GET)
- Route: `/finance/defaultpayments/`
- Lists all Default_Payment_Fees records
- **Testing**: Test listing, pagination if applicable

#### **DefaultPaymentUpdateView** (UpdateView)
- Route: `/finance/payment/<int:pk>/update/`
- Model: Default_Payment_Fees
- Editable fields: job/student down payments, job hours, student bonus, loan_amount
- **Access Control**: Superuser-only validation
- Success URL: `/finance/payments`
- **Testing**: 
  - Test superuser access
  - Test non-superuser rejection
  - Verify fee update persistence

### 2.3 Transaction Management

#### **transact** (GET/POST)
- Route: `/finance/transact/`
- **GET**: Display InflowForm
- **POST**:
  - Validate form
  - Set `instance.sender = request.user`
  - Save Transaction
  - Redirect to transaction list
- **Testing**: Test form validation, user assignment, save functionality

#### **TransactionListView** (ListView)
- Route: `/finance/transaction/`
- Model: Transaction
- Template: finance/payments/transactions.html
- Context: `transactions`
- **Testing**: Test listing, ordering, pagination

#### **TransanctionDetailView** (DetailView) [NOTE: Typo in view name]
- Route: `/finance/transaction/<int:pk>/`
- Model: Transaction
- Template: finance/payments/transaction_detail.html
- Requires login
- **Testing**: Test detail display, 404 for non-existent

#### **TransactionUpdateView** (UpdateView)
- Route: `/finance/transaction/<int:pk>/update/`
- Model: Transaction
- Requires login + user must be transaction sender
- Editable fields: sender, receiver, phone, sender_phone, department, category, type, payment_method, qty, amount, transaction_cost, description, receipt_link
- Success URL: `/finance/transaction-list` (via reverse)
- **Access Control**: `test_func()` - Only transaction sender can update
- **Testing**:
  - Test sender-only access
  - Test unauthorized access rejection
  - Verify all fields update correctly
  - Test redirect to transaction list

### 2.4 Budget Views

#### **finance_report** (GET)
- Route: `/finance/` (different from homepage?)
- Render: finance/reports/finance.html
- **Testing**: Test rendering, context data

#### **solutions** (GET)
- Route: `/finance/solutions/`
- Display banking and investment solutions

#### **budget_dashboard** (GET)
- Route: `/finance/budgets/dashboard/`
- Aggregate budget data by company and calculate totals
- Returns: summary with total budget amount
- **Testing**: Test aggregation logic, calculation accuracy

#### **budget_projection** (GET/POST)
- Routes: `/finance/budgets/` or `/finance/budgets/summary/` or `/finance/budgets/detailed/`
- **Parameters**: `duration` (month 1-12 or year > 12)
- **POST**: Filter by department using DepartmentFilterForm
- **Logic**:
  - Filter CodaBudget by date range and optionally department
  - Aggregate by category and subcategory
  - Calculate totals: `sum(item.amount * item.qty)`
  - Group by month/category
- **Template Selection**: 'detailed' suffix → detailed_budget.html, else → summary_budget.html
- **Testing**:
  - Test month filtering (1-12)
  - Test year filtering (> 12)
  - Test department filter
  - Verify aggregation accuracy
  - Test both budget views (summary vs. detailed)

### 2.5 Investment Directory & Newsletter

#### **finance_directory** (GET/POST)
- Route: `/finance/directory/`
- **GET**: Display approved opportunities and submission form
- **POST**:
  - **Rate Limiting**: 60-second cooldown per IP address (using Django cache)
  - **Spam Detection**:
    - Check for banned keywords: 'crypto', 'guaranteed', 'whatsapp me', 'bitcoin'
    - Check description length (min 20 characters)
    - Set `is_suspicious = True` if triggered
  - Set status to PENDING
  - Display success message, redirect to directory
- **Template**: finance/investment/directory.html
- **Context**: opportunities (approved), count, form
- **Testing**:
  - Test rate limiting (submit, wait, submit within 60s should fail)
  - Test spam detection (banned keywords)
  - Test description length validation
  - Test PENDING status on creation
  - Test successful submission
  - Test malicious input handling

#### **moderation_queue** (GET)
- Route: `/finance/moderation/`
- **Access**: Staff-only (`@staff_member_required`)
- Fetch: All opportunities ordered by `-created_at`, verified subscriber count
- **Testing**: Test staff-only access, data fetching

#### **approve_opportunity** (GET)
- Route: `/finance/approve/<int:pk>/`
- **Access**: Staff-only
- Set opportunity status to APPROVED
- **Signal Trigger**: Sends approval email to `opportunity.contact`
- Redirect: `/finance/moderation/`
- **Testing**: 
  - Test approval status update
  - Test email sending
  - Test 404 for non-existent opportunity

#### **reject_opportunity** (GET)
- Route: `/finance/reject_opportunity/<int:pk>/`
- **Access**: Staff-only
- Set opportunity status to REJECTED
- **Signal Trigger**: Sends rejection email
- Redirect: `/finance/moderation/`
- **Testing**: 
  - Test rejection status update
  - Test email sending
  - Test 404 for non-existent opportunity

#### **delete_opportunity** (GET/POST)
- Route: `/finance/opportunity/delete/<int:pk>/`
- **Access**: Staff-only
- **POST**: Delete opportunity, show success message
- Redirect: `/finance/moderation/`
- **Testing**: Test delete functionality, success message

#### **subscribe_newsletter** (POST - AJAX)
- Route: `/finance/subscribe/`
- **Input**: email (POST parameter)
- **Logic**:
  - Strip and lowercase email
  - Get or create NewsLetterSubscriber
  - If already verified subscriber: return "already subscribed"
  - Build verification URL: `reverse('finance:verify_email', args=[subscriber.id])`
  - Send verification email
- **Response**: JSON with success/error messages
- **Testing**:
  - Test valid email submission
  - Test empty email handling
  - Test duplicate subscription
  - Test verification email sending
  - Test JSON response format

#### **verify_email** (GET)
- Route: `/finance/verify/<int:subscriber_id>/`
- **Logic**:
  - Get subscriber by ID
  - If not verified: set `is_verified = True` and save
  - Display success template
- **Testing**: 
  - Test verification flag update
  - Test 404 for non-existent subscriber
  - Test double-verification (idempotent)

#### **admin_send_newsletter** (POST)
- Route: `/finance/admin/send-newsletter/`
- **Access**: Staff-only
- **Input**: subject, message (POST parameters)
- **Logic**:
  - Get all verified subscribers
  - Send bulk email
  - Display success/error message
- **Testing**:
  - Test staff-only access
  - Test email sending to multiple recipients
  - Test with no verified subscribers
  - Test error handling

#### **Payment_Review** (GET)
- Route: `/finance/Payment_Review/`
- Simulated payment amount: 3500
- Calculate divided amount:
  - 1000 < amount ≤ 3000: divide by 3
  - amount > 3000: divide by 4
  - else: keep as-is
- **Testing**: Test all division logic paths

---

## 3. Forms

### **InflowForm**
- **Model**: Transaction
- **Fields**: All fields
- **Widgets**: description → Textarea (30 cols, 1 row)
- **Labels**: Custom labels for all fields
- **Testing**: Test field rendering, validation

### **BudgetForm**
- **Model**: Budget
- **Fields**: budget_lead, category, subcategory, item, qty, unit_price, description, is_active, receipt_link
- **Testing**: Test field validation, required fields

### **DepartmentFilterForm**
- For filtering by department name
- **Testing**: Test department filtering logic

### **OpportunityForm**
- **Model**: Opportunity
- Requires validation of description length
- **Testing**: Test form validation with short descriptions

---

## 4. Utility Functions

### **category_subcategory(user_categories)**
- Extracts category and sub_category from user category objects
- **Testing**: Test with empty/single/multiple categories

### **check_default_fee(Default_Payment_Fees, username)**
- Retrieves or creates default fee record
- **Testing**: Test creation of missing defaults, retrieval of existing

### **get_exchange_rate(base, target)**
- Fetches exchange rate from openexchangerates.org API
- **Fallback**: 139.00 (USD to KES)
- **Testing**: 
  - Test successful API call
  - Test API timeout/failure (should use fallback)
  - Verify decimal rounding (2 places)

### **compute_amt(VisaService, transactions, rate, user_categories)**
- **Calculates**: total_price, total_amt, balance, receipt_url
- **Logic**:
  - Extract category/subcategory
  - Get VisaService price or use registration fee (19.99)
  - Apply exchange rate
  - Aggregate transaction totals
  - Calculate balance: `total_price - total_amt`
- **Testing**: Test with various service types, missing data

### **DYCDefaultPayments()**
- Returns default payment info for different user types
- **Hardcoded Values**:
  - Student: 5000 total, 500 down, 100 bonus
  - Business: 10000 total, 500 down, 100 bonus
  - Greencard: 20000 total, 500 down, 100 bonus
- **Testing**: Test return values, only first dict is used (unusual logic)

---

## 5. Signals & Automation

### **Payment_Information Signals**
- None defined, but Payment_History created in view on form submission

### **Opportunity Signals**
- **pre_save**: Store original status
- **post_save**: 
  - Skip if newly created
  - Compare `previous_status` vs current `status`
  - APPROVED → Send approval email
  - REJECTED → Send rejection email
- **Testing**: 
  - Mock signal execution
  - Test email content accuracy
  - Test status comparison logic
  - Verify email field handling

### **NewsLetterSubscriber Signals**
- **post_save (created=True)**: Send welcome email
- **Testing**: 
  - Test email sending on creation
  - Ensure not sent on updates
  - Mock email service

---

## 6. Admin Interface

All registered models in admin:
- Transaction
- Payment_History (custom admin with list_display)
- Payment_Information
- Default_Payment_Fees
- CodaBudget
- Budget
- BudgetCategory
- BudgetSubCategory
- Opportunity
- NewsLetterSubscriber

**Testing**:
- Test CRUD operations in admin
- Verify list_display for Payment_History
- Test filters (if defined)
- Test admin permissions

---

## 7. Critical Bugs & Issues Found

### **HIGH PRIORITY**
1. **Transaction.end property** (Line ~170)
   - Uses undefined `login_date` field
   - Should probably use `transaction_date`
   - Will raise AttributeError if accessed

2. **Payment_History model** (Line ~65)
   - Fields `down_payment` and `student_bonus` defined twice
   - Second definition overrides first
   - Data inconsistency risk

3. **Transaction model**
   - `receipt_link` redirects if None (redirects in property)
   - Should return None or empty string instead

### **MEDIUM PRIORITY**
1. **TransactionUpdateView** (Line 342)
   - Misspelled view name: `TransanctionDetailView`
   - Affects code readability and potential issues

2. **Budget amount calculation** (Line ~253)
   - Commented-out calculation using `days`
   - Currently multiplies by `cases`: `unit_price * cases * qty`
   - Documentation needed on which is correct

3. **budget_projection filter logic**
   - Assumes year is 2024 (hardcoded)
   - Will fail for future years
   - Should use timezone.now().year

4. **permission checks**
   - DefaultPaymentUpdateView manual permission check instead of UserPassesTestMixin
   - Inconsistent with other views

### **LOW PRIORITY**
1. **OpportunityForm**
   - Used in directory but not defined in forms.py
   - May be missing validation

2. **Email configuration**
   - Hardcoded email addresses in some views
   - Should use settings

3. **Logging**
   - Logger initialized but minimally used
   - More logging needed for debugging

4. **Type hints**
   - No type hints in functions
   - Makes testing and maintenance harder

---

## 8. Testing Strategy by Component

### **Unit Testing**
- Model properties: balance calculations, amount calculations
- Utility functions with various inputs
- Signal logic with mocked email
- Form validation

### **Integration Testing**
- Payment workflow (form → model → history creation)
- Opportunity submission → approval → email notification
- Newsletter subscription → verification → bulk email
- Budget aggregation logic

### **API/View Testing**
- All GET/POST endpoints
- Authentication requirements
- Permission checks
- Redirect behavior
- Form error handling
- Exchange rate API fallback

### **Edge Cases**
- Missing/null fields
- Boundary values (amounts, dates)
- Concurrent submissions (rate limiting)
- Invalid user data
- API failures

### **Performance Testing**
- Bulk transaction listing
- Large budget aggregations
- Newsletter sending to many subscribers
- Exchange rate API timeouts

---

## 9. URL Routing Reference

```
/finance/                              → homepage
/finance/solutions/                    → solutions  
/finance/directory/                    → finance_directory (GET/POST)
/finance/moderation/                   → moderation_queue (staff-only)
/finance/approve/<pk>/                 → approve_opportunity (staff-only)
/finance/reject_opportunity/<pk>/      → reject_opportunity (staff-only)
/finance/opportunity/delete/<pk>/      → delete_opportunity (staff-only)
/finance/subscribe/                    → subscribe_newsletter (AJAX POST)
/finance/verify/<subscriber_id>/       → verify_email
/finance/admin/send-newsletter/        → admin_send_newsletter (staff-only POST)
/finance/transact/                     → transact
/finance/transaction/                  → TransactionListView
/finance/transaction/<pk>/             → TransanctionDetailView
/finance/transaction/<pk>/update/      → TransactionUpdateView
/finance/contract_form/                → contract_form_submission
/finance/mycontract/<username>/        → mycontract
/finance/Payment_Review/               → Payment_Review
/finance/pay/                          → pay
/finance/payment/<service>/            → pay (with service param)
/finance/payment_method/<method>/      → payment
/finance/process-payment/              → process_payment (POST)
/finance/payment-success/              → payment_success
/finance/payments/                     → payments
/finance/pay/<pk>/                     → PaymentInformationUpdateView
/finance/defaultpayments/              → DefaultPaymentListView
/finance/newpayment/                   → PaymentCreateView
/finance/payment/<pk>/update/          → DefaultPaymentUpdateView
```

---

## 10. Dependencies & External Services

1. **Django Cache** - For rate limiting newsletter signups
2. **Exchange Rate API** - (openexchangerates.org) - For USD/KES conversion
3. **Email Service** - For notifications and newsletters
4. **CustomerUser Model** - From accounts app
5. **Membership Model** - From accounts app (assuming)
6. **Department Model** - From accounts app (assuming)

---

## 11. Recommended Test Cases

### **Critical Path**
1. Complete payment flow: contract form → payment → success
2. Investment opportunity submission → moderation → approval → email
3. Newsletter subscription → verification → bulk email

### **Boundary Testing**
1. Payment with various amounts and currencies
2. Budget with extreme dates (same day, 1-year range)
3. Transaction with max/min decimal precision
4. Long descriptions with banned keywords

### **Security Testing**
1. Non-authenticated access to protected views
2. Non-staff access to staff-only views
3. SQL injection in search/filter fields
4. CSRF on POST endpoints
5. XSS in form inputs

### **Performance Testing**
1. Bulk transaction creation
2. Large budget aggregations
3. Newsletter sending to 10k+ subscribers
4. Concurrent payment submissions

---

## Summary for QA
- **Total Models**: 11 (Payment_Information, Payment_History, Default_Payment_Fees, Transaction, Budget, BudgetCategory, BudgetSubCategory, CodaBudget, Opportunity, NewsLetterSubscriber, Company)
- **Total Views/Endpoints**: 20+
- **Key Features**: Payment management, Budget tracking, Investment directory, Newsletter
- **Critical Issues**: 3 high-priority bugs identified
- **External Dependencies**: Exchange rate API, Email service, Django Cache
- **Access Controls**: Login required for most, staff-only for moderation
- **Automation**: Email notifications on opportunity status changes and newsletter send-outs
