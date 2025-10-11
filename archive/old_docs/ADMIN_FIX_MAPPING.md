# Admin Configuration Fix Mapping

## Field Mapping for Admin Fixes

### Transaction Model
**Actual Fields:** `['id', 'user', 'amount', 'currency', 'transaction_type', 'status', 'description', 'category', 'subcategory', 'vendor', 'location', 'transaction_date', 'processed_date', 'reference_number', 'notes', 'created_at', 'updated_at']`

**Admin Errors:**
- `list_display[0]` uses `receiver` ❌ → should use `vendor` or `description`
- `list_display[4]` uses `type` ❌ → should use `transaction_type` ✅
- `list_filter[1]` uses `type` ❌ → should use `transaction_type` ✅

**Fix:**
```python
list_display = ['vendor', 'amount', 'currency', 'category', 'transaction_type', 'status', 'transaction_date', 'created_at']
list_filter = ['category', 'transaction_type', 'status', 'currency', 'transaction_date']
```

---

### BudgetCategory Model
**Actual Fields:** `['subcategories', 'items', 'category_type', 'budgetrequest', 'approvalpolicy', 'budgetalert', 'id', 'name', 'description']`

**Admin Errors:**
- `readonly_fields[0]` - unknown field ❌
- `readonly_fields[1]` - unknown field ❌
- `list_display[2]` uses `created_at` ❌ (doesn't exist)
- `list_filter[0]` uses `created_at` ❌ (doesn't exist)

**Fix:**
```python
list_display = ['name', 'description', 'category_type']
list_filter = ['category_type']
readonly_fields = []  # No timestamp fields in this model
```

---

### BudgetSubCategory Model
**Actual Fields:** `['items', 'sub_category_type', 'id', 'category', 'name']`

**Admin Errors:**
- `readonly_fields[0]` - unknown field ❌
- `readonly_fields[1]` - unknown field ❌
- `list_display[2]` uses `description` ❌ (doesn't exist)
- `list_display[3]` uses `created_at` ❌ (doesn't exist)
- `list_filter[1]` uses `created_at` ❌ (doesn't exist)

**Fix:**
```python
list_display = ['name', 'category', 'sub_category_type']
list_filter = ['category', 'sub_category_type']
readonly_fields = []  # No timestamp fields
```

---

### BudgetRequest Model
**Actual Fields:** `['disbursement_requests', 'audit_logs', 'id', 'created_at', 'updated_at', 'is_active', 'is_featured', 'modification_reason', 'requester', 'amount', 'currency', 'purpose', 'department', 'request_date', 'required_date', 'priority', 'approval_policy', 'current_approver', 'approval_chain', 'status', 'rejection_reason', 'budget_category', 'cost_center', 'attachments', 'created_by', 'last_modified_by']`

**Admin Errors:**
- `readonly_fields[2]` uses `submitted_at` ❌ (doesn't exist) → use `request_date`
- `list_display[0]` uses `title` ❌ (doesn't exist) → use `purpose`
- `list_display[1]` uses `category` ❌ → use `budget_category` ✅
- `list_display[2]` uses `requested_amount` ❌ → use `amount` ✅
- `list_display[5]` uses `requested_by` ❌ → use `requester` ✅
- `list_filter[2]` uses `category` ❌ → use `budget_category` ✅

**Fix:**
```python
list_display = ['purpose', 'budget_category', 'amount', 'status', 'priority', 'requester', 'created_at']
list_filter = ['status', 'priority', 'budget_category', 'created_at']
readonly_fields = ['created_at', 'updated_at', 'request_date']
```

---

### BudgetEstimateProjection Model
**Actual Fields:** `['id', 'budget', 'projection_date', 'projected_amount', 'confidence_score', 'projection_method', 'notes', 'created_at']`

**Admin Errors:**
- `readonly_fields[1]` uses `updated_at` ❌ (doesn't exist)
- `list_display[0]` uses `projection_name` ❌ (doesn't exist) → use `id` or `budget`
- `list_display[1]` uses `estimation_method` ❌ → use `projection_method` ✅
- `list_display[2]` uses `total_estimated_amount` ❌ → use `projected_amount` ✅
- `list_display[3]` uses `estimation_confidence` ❌ → use `confidence_score` ✅
- `list_display[4]` uses `status` ❌ (doesn't exist)
- `list_filter[0]` uses `status` ❌ (doesn't exist)
- `list_filter[1]` uses `estimation_method` ❌ → use `projection_method` ✅

**Fix:**
```python
list_display = ['budget', 'projection_method', 'projected_amount', 'confidence_score', 'projection_date', 'created_at']
list_filter = ['projection_method', 'projection_date', 'created_at']
readonly_fields = ['created_at']
```

---

### ApprovalPolicy Model
**Actual Fields:** `['budget', 'budgetrequest', 'id', 'created_at', 'updated_at', 'is_featured', 'name', 'description', 'is_active', 'min_amount', 'max_amount', 'approver_roles', 'approval_chain', 'auto_approve', 'requires_otp', 'applicable_user_types', 'max_approval_days', 'escalation_days', 'applicable_departments', 'applicable_categories']`

**Admin Errors:**
- `list_display[1]` uses `policy_type` ❌ (doesn't exist)
- `list_display[2]` uses `approval_level` ❌ (doesn't exist)
- `list_filter[0]` uses `policy_type` ❌ (doesn't exist)
- `list_filter[1]` uses `approval_level` ❌ (doesn't exist)

**Fix:**
```python
list_display = ['name', 'min_amount', 'max_amount', 'auto_approve', 'requires_otp', 'is_active']
list_filter = ['is_active', 'auto_approve', 'requires_otp']
```

---

### LoanApplication Model
**Actual Fields:** `['loan_payments', 'loan_collateral', 'rollovers', 'decision_audits', 'performance_records', 'payments', 'notifications', 'id', 'application_number', 'loan_product', 'loan_plan_id', 'borrower', 'guarantor', 'guarantor_relationship', 'guarantor_consent_date', 'guarantor_eligibility_score', 'guarantor_approval_status', 'amount_requested', 'purpose', 'collateral', 'duration', 'interest_rate', 'total_payable', 'monthly_payment', 'status', 'submitted_at', 'approved_at', 'approved_by', 'credit_score', 'employment_status', 'monthly_income', 'is_eligible', 'is_active', 'is_featured', 'created_at', 'updated_at']`

**Admin Errors:**
- `readonly_fields[0]` uses `application_id` ❌ → use `application_number` ✅
- `list_display[0]` uses `application_id` ❌ → use `application_number` ✅
- `list_display[1]` uses `applicant` ❌ → use `borrower` ✅
- `list_display[3]` uses `requested_amount` ❌ → use `amount_requested` ✅
- `list_display[5]` uses `priority` ❌ (doesn't exist)
- `list_filter[1]` uses `priority` ❌ (doesn't exist)

**Fix:**
```python
list_display = ['application_number', 'borrower', 'loan_product', 'amount_requested', 'status', 'created_at']
list_filter = ['status', 'loan_product', 'created_at']
readonly_fields = ['application_number', 'created_at', 'updated_at', 'submitted_at']
```

---

### LoanProduct Model
**Actual Fields:** `['loanapplication', 'id', 'name', 'description', 'min_amount', 'max_amount', 'interest_rate', 'min_term_months', 'max_term_months', 'fees', 'is_active', 'min_credit_score', 'product_type', 'requirements']`

**Admin Errors:**
- `readonly_fields[0]` uses `created_at` ❌ (doesn't exist)
- `readonly_fields[1]` uses `updated_at` ❌ (doesn't exist)
- `list_filter[1]` uses `status` ❌ (doesn't exist)
- `list_filter[2]` uses `requires_collateral` ❌ (doesn't exist)
- `list_filter[3]` uses `auto_approve` ❌ (doesn't exist)

**Fix:**
```python
list_filter = ['product_type', 'is_active']
readonly_fields = []  # No timestamp fields
```

---

## Summary of Changes Needed

1. **Transaction**: 3 field name changes
2. **BudgetCategory**: Remove non-existent timestamp fields
3. **BudgetSubCategory**: Remove non-existent fields
4. **BudgetRequest**: 5 field name changes
5. **BudgetEstimateProjection**: 7 field name changes
6. **ApprovalPolicy**: Remove non-existent fields
7. **LoanApplication**: 5 field name changes
8. **LoanProduct**: Remove non-existent fields

**Total Fixes: 41 errors → All corrected**

