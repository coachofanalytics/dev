# Budget System - Implementation

**Last Updated:** October 13, 2025  
**Version:** Phase 1 Complete

---

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐        ┌─────────────┐
│   User/UI   │────────▶│    Views     │───────▶│   Models    │
│  (Template) │◀────────│ (Controllers)│◀───────│ (Database)  │
└─────────────┘         └──────────────┘        └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │   Services   │ (Phase 2)
                        │  (Business   │
                        │    Logic)    │
                        └──────────────┘
```

**Current (Phase 1):** Views contain business logic  
**Future (Phase 2):** Service layer handles approval routing

---

## Data Model

### BudgetRequest Model
**Location:** `coda/finance/models/budget.py`

```python
class BudgetRequest(TimeStampedModel, StatusMixin):
    """
    Represents a budget request that goes through approval workflow
    
    Phase 1: Simple staff approval
    Phase 2: Intelligent tier-based routing
    """
    
    # Core Fields
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budget_requests_created'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    purpose = models.TextField(
        help_text="Justification for budget request"
    )
    
    department = models.ForeignKey(
        'main.Department',
        on_delete=models.CASCADE,
        related_name='budget_requests'
    )
    
    budget_category = models.ForeignKey(
        'finance.BudgetCategory',
        on_delete=models.PROTECT,
        related_name='budget_requests'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    
    # Approval Tracking (Added Oct 13, 2025 - Migration 0099)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budget_requests',
        help_text="User who approved the request"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of approval"
    )
    
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_budget_requests',
        help_text="User who rejected the request"
    )
    
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of rejection"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )
    
    # Approval Chain (Phase 2)
    current_approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_budget_approvals',
        help_text="User currently responsible for approval"
    )
    
    approval_chain = models.JSONField(
        default=list,
        blank=True,
        help_text="History of approval steps"
    )
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['budget_category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.purpose[:50]} - ${self.amount} ({self.get_status_display()})"
```

**Key Methods:**
```python
def can_approve(self, user):
    """Check if user can approve this request (Phase 1 logic)"""
    return user.is_staff or user.is_superuser

def approve(self, user, notes=''):
    """Approve the budget request"""
    self.status = 'approved'
    self.approved_by = user
    self.approved_at = timezone.now()
    self.save()
    # Send notification
    
def reject(self, user, reason):
    """Reject the budget request"""
    self.status = 'rejected'
    self.rejected_by = user
    self.rejected_at = timezone.now()
    self.rejection_reason = reason
    self.save()
    # Send notification
```

---

### ApprovalPolicy Model
**Location:** `coda/finance/models/budget.py`

```python
class ApprovalPolicy(TimeStampedModel):
    """
    Defines approval rules for budget categories
    
    Phase 1: Not actively used (simple staff approval)
    Phase 2: Core of intelligent routing
    """
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Amount thresholds
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Null = no upper limit"
    )
    
    # Approval routing
    approver_roles = models.JSONField(
        default=list,
        help_text="List of role names that can approve"
    )
    
    approval_chain = models.JSONField(
        default=list,
        help_text="Sequential approval chain configuration"
    )
    
    auto_approve = models.BooleanField(
        default=False,
        help_text="Auto-approve if conditions met"
    )
    
    # Applicability
    applicable_departments = models.ManyToManyField(
        'main.Department',
        blank=True
    )
    
    applicable_categories = models.ManyToManyField(
        'finance.BudgetCategory',
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher = checked first")
    
    class Meta:
        ordering = ['-priority', 'name']
        verbose_name_plural = 'Approval Policies'
    
    def __str__(self):
        return f"{self.name} (${self.min_amount} - ${self.max_amount or '∞'})"
```

---

### BudgetCategory Model (Future Enhancement)
**Location:** `coda/finance/models/category.py`

**Phase 2 Fields to Add:**
```python
class BudgetCategory(models.Model):
    # ... existing fields ...
    
    # Approval Automation (Phase 2)
    approval_tier = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Known/Recurring - Auto-Approve'),
            ('B', 'Variable - Priority-Based'),
            ('C', 'Strategic - Assessment Required'),
        ],
        default='C',
        help_text="Approval tier from transaction pattern analysis"
    )
    
    auto_approve_enabled = models.BooleanField(
        default=False,
        help_text="Finance Manager can enable/disable auto-approval"
    )
    
    typical_monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Typical monthly spend (calculated from data)"
    )
    
    variance_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="% variance from typical that triggers review"
    )
    
    is_recurring = models.BooleanField(
        default=False,
        help_text="Detected as recurring based on transaction patterns"
    )
    
    last_pattern_analysis = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When pattern analysis was last run"
    )
```

---

## Views & URLs

### Approval Dashboard
**URL:** `/finance/budget/{company_slug}/approvals/`  
**View:** `coda/finance/views/budget/approvals.py::budget_approval_dashboard`  
**Template:** `coda/finance/templates/finance/budgets/budget_approvals.html`

**Purpose:** Main interface for viewing and managing budget approvals

**Flow:**
1. User navigates to URL
2. View checks permissions (login required)
3. Fetches pending budget requests for company
4. Fetches recent approvals/rejections
5. Calculates statistics
6. Renders template with context

**Key Code:**
```python
@login_required
def budget_approval_dashboard(request, company_slug):
    """Dashboard for budget approvals"""
    
    # Get company
    company = get_object_or_404(Company, slug=company_slug)
    
    # Get pending requests
    pending_requests = BudgetRequest.objects.filter(
        status='pending',
        department__company=company
    ).select_related(
        'requester',
        'budget_category',
        'department'
    ).order_by('-created_at')
    
    # Get recent decisions
    recent_approvals = BudgetRequest.objects.filter(
        status='approved',
        department__company=company
    ).select_related('approved_by').order_by('-approved_at')[:10]
    
    recent_rejections = BudgetRequest.objects.filter(
        status='rejected',
        department__company=company
    ).select_related('rejected_by').order_by('-rejected_at')[:10]
    
    # Statistics
    total_pending = pending_requests.count()
    total_approved_this_month = BudgetRequest.objects.filter(
        status='approved',
        department__company=company,
        approved_at__gte=timezone.now().replace(day=1)
    ).count()
    
    context = {
        'company': company,
        'pending_requests': pending_requests,
        'recent_approvals': recent_approvals,
        'recent_rejections': recent_rejections,
        'total_pending': total_pending,
        'total_approved_this_month': total_approved_this_month,
        'can_approve': _can_approve_any(request.user),
    }
    
    return render(request, 'finance/budgets/budget_approvals.html', context)
```

---

### Approve Budget Request
**URL:** `POST /finance/budget/{company_slug}/approve/{request_id}/`  
**View:** `coda/finance/views/budget/approvals.py::approve_budget_request`

**Flow:**
1. POST request with request_id
2. Validate user has approval permission
3. Fetch budget request
4. Set approved_by, approved_at
5. Update status to 'approved'
6. Send notification
7. Redirect to dashboard with success message

**Key Code:**
```python
@login_required
@require_http_methods(["POST"])
def approve_budget_request(request, company_slug, request_id):
    """Approve a budget request"""
    
    budget_request = get_object_or_404(BudgetRequest, id=request_id)
    
    # Check permission
    if not _can_approve_request(request.user, budget_request):
        messages.error(request, "You don't have permission to approve this request.")
        return redirect('finance:budget_approvals', company_slug=company_slug)
    
    # Check already approved
    if budget_request.status == 'approved':
        messages.warning(request, "This request has already been approved.")
        return redirect('finance:budget_approvals', company_slug=company_slug)
    
    # Approve
    budget_request.status = 'approved'
    budget_request.approved_by = request.user
    budget_request.approved_at = timezone.now()
    budget_request.save()
    
    # Send notification (email)
    send_budget_approval_email(budget_request)
    
    messages.success(
        request,
        f"Budget request '{budget_request.purpose[:50]}' approved successfully."
    )
    
    return redirect('finance:budget_approvals', company_slug=company_slug)
```

---

### Reject Budget Request
**URL:** `POST /finance/budget/{company_slug}/reject/{request_id}/`  
**View:** `coda/finance/views/budget/approvals.py::reject_budget_request`

**Similar to approve, but:**
- Sets `rejected_by`, `rejected_at`
- Requires `rejection_reason` from POST data
- Status = 'rejected'

---

### Permission Check Helper
**Location:** `coda/finance/views/budget/editing.py::_can_approve_request`

```python
def _can_approve_request(user, budget_request):
    """
    Check if user can approve the budget request.

    TEMPORARY SIMPLE LOGIC (Phase 1):
    - Staff and superusers can approve

    TODO Phase 2: Implement proper tier-based approval system
    """
    return user.is_staff or user.is_superuser
```

---

## Templates

### Budget Approvals Dashboard
**Location:** `coda/finance/templates/finance/budgets/budget_approvals.html`

**Key Features:**
- Pending requests table with approve/reject buttons
- Recent approvals/rejections history
- Statistics summary
- Filter controls (future)
- Theme switcher

**Approval Button Example:**
```html
<form method="post" action="{% url 'finance:approve_budget' company.slug request.id %}" style="display:inline;">
    {% csrf_token %}
    <button type="submit" class="btn btn-sm btn-success" title="Approve">
        <i class="fas fa-check"></i>
    </button>
</form>
```

**Reject Button Example:**
```html
<button type="button" class="btn btn-sm btn-danger" 
        onclick="showRejectModal({{ request.id }})" title="Reject">
    <i class="fas fa-times"></i>
</button>

<!-- Reject Modal -->
<div class="modal fade" id="rejectModal{{request.id}}">
    <!-- Form with rejection_reason textarea -->
</div>
```

---

## Services (Phase 2 - Planned)

### Intelligent Approval Engine
**Location (Future):** `coda/finance/services/budget/approval_engine.py`

```python
class IntelligentApprovalEngine:
    """
    Data-driven approval routing based on CODA spending patterns
    
    Routes budget requests automatically based on:
    - Category tier (A/B/C)
    - Amount vs typical spending
    - Priority level
    - Assessment score (Tier C)
    """
    
    def route_budget_request(self, budget_request):
        """
        Main entry point for approval routing
        
        Returns dict with:
        - action: 'auto_approve', 'assign_approval', 'flag_for_review', etc.
        - reason: Why this action
        - assign_to: User/role to assign (if applicable)
        - notify: Users to notify
        """
        category = budget_request.budget_category
        
        if category.approval_tier == 'A':
            return self._handle_tier_a(budget_request, category)
        elif category.approval_tier == 'B':
            return self._handle_tier_b(budget_request, category)
        elif category.approval_tier == 'C':
            return self._handle_tier_c(budget_request, category)
        else:
            return {'action': 'manual_approval', 'reason': 'Unclassified category'}
    
    def _handle_tier_a(self, request, category):
        """Auto-approve known recurring with anomaly detection"""
        # Check if amount is typical
        if category.typical_monthly_amount:
            variance = self._calculate_variance(
                request.amount,
                category.typical_monthly_amount
            )
            
            if variance > category.variance_threshold:
                # Amount is unusual - flag for review
                return {
                    'action': 'flag_for_review',
                    'reason': f'Amount {variance:.1f}% higher than typical ${category.typical_monthly_amount}',
                    'assign_to': 'finance_manager'
                }
        
        # Amount is typical - auto-approve
        if category.auto_approve_enabled:
            return {
                'action': 'auto_approve',
                'reason': 'Known recurring expense within normal range',
                'notify': ['finance_manager']
            }
        else:
            return {
                'action': 'assign_approval',
                'assign_to': 'finance_manager',
                'reason': 'Auto-approval paused for this category'
            }
    
    def _handle_tier_b(self, request, category):
        """Priority-based routing for variable costs"""
        if request.priority in ['urgent', 'high']:
            return {
                'action': 'auto_approve',
                'reason': f'High priority {category.name} request',
                'notify': ['department_manager', 'finance_manager']
            }
        elif request.priority == 'medium':
            return {
                'action': 'assign_approval',
                'assign_to': 'department_manager',
                'reason': 'Medium priority requires manager review'
            }
        else:
            return {
                'action': 'apply_policy',
                'reason': 'Low priority requires justification'
            }
    
    def _handle_tier_c(self, request, category):
        """Strategic assessment-based routing"""
        if request.has_assessment:
            score = request.calculate_assessment_score()
            
            if score >= 80:
                return {
                    'action': 'assign_approval',
                    'assign_to': 'senior_manager',
                    'reason': f'High strategic value (score: {score})'
                }
            elif score >= 50:
                return {
                    'action': 'approval_chain',
                    'chain': ['department_manager', 'finance_manager'],
                    'reason': f'Medium strategic value (score: {score})'
                }
            else:
                return {
                    'action': 'executive_review',
                    'assign_to': 'cfo_or_ceo',
                    'reason': f'Requires executive decision (score: {score})'
                }
        else:
            return {
                'action': 'require_assessment',
                'reason': 'Strategic requests require assessment'
            }
    
    def _calculate_variance(self, actual, typical):
        """Calculate percentage variance"""
        if typical == 0:
            return 100
        return abs(actual - typical) / typical * 100
```

---

## Workflows

### Current Approval Workflow (Phase 1)

```
┌──────────────────────┐
│ User Creates Request │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Status: Pending      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Staff Reviews on     │
│ Approval Dashboard   │
└──────────┬───────────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌────────┐
│Approve │   │Reject  │
└───┬────┘   └───┬────┘
    │            │
    ▼            ▼
Status:      Status:
Approved     Rejected
approved_by  rejected_by
approved_at  rejected_at
             rejection_reason
```

---

### Future Approval Workflow (Phase 2)

```
┌──────────────────────┐
│ User Creates Request │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│ Approval Engine Routes   │
│ Based on Category Tier   │
└──────────┬───────────────┘
           │
      ┌────┴────┬────────────┐
      │         │            │
      ▼         ▼            ▼
  ┌────────┐ ┌──────────┐ ┌──────────┐
  │ Tier A │ │  Tier B  │ │  Tier C  │
  │ Known  │ │Variable  │ │Strategic │
  └───┬────┘ └────┬─────┘ └────┬─────┘
      │           │            │
      ▼           ▼            ▼
  Check     Check        Require
  Variance  Priority     Assessment
      │           │            │
      ▼           ▼            ▼
  Within?    High/Med/Low   Score?
      │           │            │
  ┌───┴───┐   ┌───┴───┐   ┌────┴────┐
  │       │   │   │   │   │    │    │
  ▼       ▼   ▼   ▼   ▼   ▼    ▼    ▼
Auto-   Flag High Med Low High Med  Low
Approve Review Auto Mgr Policy Mgr Chain Exec
```

---

## Database Migrations

### Migration 0099: Add Approval Fields to BudgetRequest
**Created:** October 13, 2025  
**Purpose:** Add approval audit trail fields

**File:** `coda/finance/migrations/0099_add_approval_fields_to_budget_request.py`

```python
class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finance', '0012_merge_20251004_0055'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='budgetrequest',
            name='approved_by',
            field=models.ForeignKey(...),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='approved_at',
            field=models.DateTimeField(...),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='rejected_by',
            field=models.ForeignKey(...),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='rejected_at',
            field=models.DateTimeField(...),
        ),
    ]
```

**Impact:** Enables proper audit trail for all approval decisions

---

## Security & Permissions

### Current Permission Model (Phase 1)

**Login Required:** All budget views require authentication

**Approval Permission:**
```python
def _can_approve_request(user, budget_request):
    return user.is_staff or user.is_superuser
```

**Data Access Control:**
- Users only see budgets for their company
- Filter: `.filter(department__company=request.user.company)`

### Future Permission Model (Phase 2)

**Role-Based:**
- `finance_manager` - Full control, can override
- `department_manager` - Can approve department budgets
- `senior_manager` - Can approve high-value strategic
- `executive` - Can approve all

**Tier-Based:**
- Tier A: Finance Manager oversight
- Tier B: Department Manager (medium), Finance Manager (low)
- Tier C: Based on assessment score

---

## Performance Considerations

### Database Queries
**Optimization applied:**
- `select_related('requester', 'budget_category', 'department')` - Reduce N+1
- `prefetch_related` for M2M when needed
- Indexes on `status`, `created_at`, `budget_category`

### Caching (Phase 2)
- Cache approval policies (1 hour)
- Cache category tier assignments (daily refresh)
- Cache typical monthly amounts (weekly refresh)

### Batch Processing
- Pattern analysis runs overnight (cron job)
- Email notifications queued (Celery - future)

---

## External Dependencies

### Current
- Django 4.x
- PostgreSQL
- Email backend (SMTP or SendGrid)

### Future (Phase 2)
- Pandas (for pattern analysis)
- NumPy (for statistical calculations)
- Celery (for background jobs)
- Redis (for caching)

---

## Configuration

### Settings
**File:** `coda/heroku_settings.py`

```python
# Budget Approval Settings (Phase 2)
BUDGET_AUTO_APPROVE_THRESHOLD = 1000  # Auto-approve below this for Tier A
BUDGET_TIER_A_MAX = 5000  # Max amount for Tier A auto-approval
BUDGET_TIER_B_MAX = 10000  # Max for Tier B without exec review
BUDGET_VARIANCE_THRESHOLD = 20  # Default variance % for anomaly detection
BUDGET_PATTERN_ANALYSIS_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
```

### Environment Variables
- `BUDGET_APPROVAL_EMAIL` - Email for approval notifications
- `ENABLE_AUTO_APPROVAL` - Feature flag (Phase 2)
- `FINANCE_MANAGER_USER_ID` - Default Finance Manager

---

## Code Examples

### Creating a Budget Request
```python
from finance.models import BudgetRequest, BudgetCategory
from main.models import Department

# Create request
request = BudgetRequest.objects.create(
    requester=request.user,
    amount=500.00,
    purpose="Office supplies for Q4",
    department=Department.objects.get(name="Operations"),
    budget_category=BudgetCategory.objects.get(name="Office Supplies"),
    priority='medium',
    status='pending'
)
```

### Approving a Request
```python
from django.utils import timezone

request = BudgetRequest.objects.get(id=123)
request.status = 'approved'
request.approved_by = current_user
request.approved_at = timezone.now()
request.save()

# Send notification
send_budget_approval_email(request)
```

### Checking Permissions
```python
if _can_approve_request(request.user, budget_request):
    # Show approve/reject buttons
else:
    # Show read-only view
```

---

## Known Technical Debt

### Current (Phase 1)
- [ ] Approval logic in views (should be in service layer)
- [ ] No approval notifications (email pending)
- [ ] Template has inline JS (should extract to static file)
- [ ] Policy model not actively used
- [ ] No approval delegation

### Phase 2 Refactoring Needed
- [ ] Move all business logic to service layer
- [ ] Implement proper role-based permissions
- [ ] Add comprehensive test coverage
- [ ] Extract approval engine to separate service
- [ ] Add caching layer

---

## Future Improvements

### Phase 2 (This Month)
- [ ] Data-driven tier classification
- [ ] Intelligent approval routing
- [ ] Auto-approval with anomaly detection
- [ ] Finance Manager control dashboard

### Phase 3 (Q4 2025)
- [ ] Real-time updates (WebSockets)
- [ ] Mobile-optimized interface
- [ ] Batch approval actions
- [ ] Approval delegation
- [ ] Budget vs actuals tracking

### Phase 4 (2026)
- [ ] AI-powered fraud detection
- [ ] Predictive budgeting
- [ ] Integration with accounting systems
- [ ] Advanced analytics dashboard

---

## Change History

| Date | Change | Developer | Reason |
|------|--------|-----------|--------|
| Oct 13, 2025 | Added approval fields (Migration 0099) | CM | Support Phase 1 workflow |
| Oct 13, 2025 | Fixed permission logic (simple staff approval) | CM | Unblock development |
| Oct 2, 2025 | Dashboard bug fix (aggregation formula) | CM | Fix 177x inflation error |
| Oct 1, 2025 | Created BudgetRequest model | CM | Initial implementation |

---

**Maintained by:** Cursor AI Assistant  
**Next Review:** After Phase 2 implementation  
**Questions?** Check REQUIREMENTS.md for business logic, TESTING.md for verification

