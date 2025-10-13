# CODA Budget Category Classification
**Purpose:** Tier categories for automated approval workflow  
**Date:** October 13, 2025

---

## 🔴 TIER A: KNOWN/RECURRING (Auto-Approve)

### Utilities & Infrastructure
- **Utilities** ⚡
- **Rent** 🏢
- **Insurance** 🛡️
- **Security** 🔒

### People Costs
- **Salaries and Wages** 💰
- **Sales Commissions** 💵

### IT & Communications
- **IT and Software** (subscriptions, licenses) 💻

### Regulatory
- **Taxes** 📋
- **Compliance and Regulatory** ⚖️

**Business Rationale:**
- These are budgeted, recurring expenses
- Predictable amounts
- Business cannot operate without them
- Already committed/contracted
- **Auto-approve with Finance Manager oversight**

**Total: 9 categories**

---

## 🟡 TIER B: VARIABLE/OPERATIONAL (Priority-Based)

### Office & Operations
- **Office Supplies** 📎
- **Inventory and Supplies** 📦
- **Facilities and Equipment** (maintenance/small purchases) 🛠️
- **Maintenance and Repairs** 🔧

### People Development
- **Training and Development** 📚
- **Travel and Entertainment** ✈️

### Business Services
- **Professional Services** (consultants, legal, accounting) 👔
- **Customer Service** 📞
- **Logistics and Shipping** 🚚

**Priority Rules:**
- **HIGH/URGENT** → Auto-approve (emergency repairs, urgent travel)
- **MEDIUM** → Department Manager approval
- **LOW** → Requires justification + approval policy

**Total: 9 categories**

---

## 🟢 TIER C: STRATEGIC/DISCRETIONARY (Smart Assessment)

### Growth & Development
- **Research and Development (R&D)** 🔬
- **Marketing and Advertising** 📢

### Strategic Investments
- **Human Resources** (new hires, restructuring) 👥
- **Depreciation and Amortization** (capital assets) 📊
- **Operational Expenses** (new programs) 🎯

### Uncategorized
- **Miscellaneous Expenses** ❓
- **Other** ❓

**Assessment Questions:**
1. Strategic alignment? (0-20 points)
2. ROI/benefit expected? (0-25 points)
3. Time sensitivity? (0-15 points)
4. Risk if not approved? (0-20 points)
5. Alternatives considered? (0-10 points)
6. Long-term impact? (0-10 points)

**Scoring:**
- 80-100 points → Senior Manager approval (fast-track)
- 50-79 points → Standard approval chain
- < 50 points → Executive review required

**Total: 7 categories**

---

## 📊 SUMMARY TABLE

| Tier | Categories | Auto-Approve | Approval Logic |
|------|-----------|--------------|----------------|
| **A - Known** | 9 | ✅ YES | Finance Manager can override |
| **B - Variable** | 9 | ⚠️ DEPENDS | Based on priority (High=Yes, Med/Low=No) |
| **C - Strategic** | 7 | ❌ NO | Based on assessment score |

**Total:** 25 categories classified

---

## 🔧 TECHNICAL IMPLEMENTATION

### Add to BudgetCategory Model:
```python
class BudgetCategory(models.Model):
    name = models.CharField(...)
    
    # NEW FIELDS for approval automation
    approval_tier = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Known/Recurring - Auto-Approve'),
            ('B', 'Variable - Priority-Based'),
            ('C', 'Strategic - Assessment Required'),
        ],
        default='C',
        help_text="Approval tier for automation"
    )
    
    auto_approve_enabled = models.BooleanField(
        default=False,
        help_text="Whether auto-approval is currently enabled for this category"
    )
    
    requires_assessment = models.BooleanField(
        default=False,
        help_text="Whether strategic assessment questions are required"
    )
```

### Approval Logic:
```python
def process_budget_request_approval(budget_request, user=None):
    category = budget_request.budget_category
    
    # TIER A: Auto-approve if enabled
    if category.approval_tier == 'A' and category.auto_approve_enabled:
        budget_request.auto_approve(reason="Known recurring expense")
        notify_finance_manager(budget_request, 'auto_approved')
        return 'auto_approved'
    
    # TIER B: Priority-based
    elif category.approval_tier == 'B':
        if budget_request.priority in ['urgent', 'high']:
            budget_request.auto_approve(reason=f"High priority {category.name}")
            notify_manager(budget_request, 'auto_approved_priority')
            return 'auto_approved'
        elif budget_request.priority == 'medium':
            assign_to_department_manager(budget_request)
            return 'pending_manager'
        else:
            apply_approval_policy(budget_request)
            return 'pending_policy'
    
    # TIER C: Strategic assessment
    elif category.approval_tier == 'C':
        if budget_request.has_assessment():
            score = calculate_assessment_score(budget_request)
            return route_by_score(budget_request, score)
        else:
            # Require assessment first
            return 'assessment_required'
    
    # Default: manual approval
    return 'pending_manual'
```

---

## 🎯 CATEGORY TIER ASSIGNMENTS

### TIER A (Auto-Approve):
```sql
UPDATE finance_budgetcategory 
SET approval_tier = 'A', auto_approve_enabled = TRUE 
WHERE name IN (
    'Utilities',
    'Rent',
    'Insurance',
    'Security',
    'Salaries and Wages',
    'Sales Commissions',
    'IT and Software',
    'Taxes',
    'Compliance and Regulatory'
);
```

### TIER B (Priority-Based):
```sql
UPDATE finance_budgetcategory 
SET approval_tier = 'B' 
WHERE name IN (
    'Office Supplies',
    'Inventory and Supplies',
    'Facilities and Equipment',
    'Maintenance and Repairs',
    'Training and Development',
    'Travel and Entertainment',
    'Professional Services',
    'Customer Service',
    'Logistics and Shipping'
);
```

### TIER C (Strategic):
```sql
UPDATE finance_budgetcategory 
SET approval_tier = 'C', requires_assessment = TRUE 
WHERE name IN (
    'Research and Development (R&D)',
    'Marketing and Advertising',
    'Human Resources',
    'Depreciation and Amortization',
    'Operational Expenses',
    'Miscellaneous Expenses',
    'Other'
);
```

---

## 🔔 NOTIFICATION SYSTEM

### For Auto-Approvals:
- **Daily Digest** to Finance Manager
- **Summary:** "15 requests auto-approved today ($45,000 total)"
- **Ability to review** and flag for investigation

### For Manual Approvals:
- **Immediate notification** to assigned approver
- **Escalation** if not reviewed within X days
- **Reminders** for pending approvals

---

## 🛡️ FINANCE MANAGER CONTROLS

**Dashboard Features:**
```
┌─────────────────────────────────────┐
│ Finance Manager Approval Controls   │
├─────────────────────────────────────┤
│ ✅ Auto-Approve Settings            │
│   ☑ Utilities (enabled)             │
│   ☑ Salaries (enabled)              │
│   ☑ Rent (enabled)                  │
│   ...                                │
│                                      │
│ 📊 Today's Auto-Approvals: 15       │
│   Total: $45,230.50                 │
│   [View Details] [Pause All]        │
│                                      │
│ ⚠️ Flagged for Review: 2            │
│   - Unusual amount detected         │
│   - New vendor                      │
│   [Review Now]                      │
└─────────────────────────────────────┘
```

---

## 🎯 NEXT STEPS

1. **Confirm tier assignments** - Do these make sense for CODA?
2. **Add tier fields** to BudgetCategory model
3. **Update categories** in database with tier assignments
4. **Implement approval routing** logic
5. **Build Finance Manager controls**
6. **Create assessment form** for Tier C

---

## ❓ QUESTIONS FOR REFINEMENT

1. **Who is the "Finance Manager"?**
   - Specific user?
   - Anyone with "Finance Manager" role?
   - Department head of Finance department?

2. **What should happen if Finance Manager pauses auto-approval?**
   - All Tier A go to manual?
   - Just that specific category?
   - Temporary or permanent?

3. **For Tier B medium priority, who is "Department Manager"?**
   - Manager of requester's department?
   - Manager of budget category's owning department?
   - Fixed person per category?

4. **For Tier C assessment, who scores the answers?**
   - Automatic scoring system?
   - Finance team reviews and scores?
   - Requester self-scores?

---

**Let's build this RIGHT!** Tell me if the tier assignments make sense, then we'll implement properly. 🎯

