# Budget System - Implementation

**Last Updated:** October 16, 2025  
**Version:** Phase 2 Complete (Data-Driven Tier System) ✅

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

### Budget Model (Core Budget Planning)
**Location:** `coda/finance/models/budget.py`

```python
class Budget(models.Model):
    """
    Core budget planning model
    
    Represents individual budget line items with quantity, unit price, and cases multiplier.
    Critical: Uses proper total_amount calculation to avoid aggregation bugs.
    """
    company = models.ForeignKey('main.Company', on_delete=models.CASCADE)
    department = models.ForeignKey('main.Department', on_delete=models.CASCADE)
    category = models.ForeignKey('BudgetCategory', on_delete=models.PROTECT)
    subcategory = models.ForeignKey('BudgetSubcategory', on_delete=models.SET_NULL, null=True)
    
    item_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    cases = models.DecimalField(max_digits=10, decimal_places=2, default=1)  # Multiplier
    
    budget_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_from = models.DateField()
    date_to = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_amount(self):
        """
        Calculate total amount for this budget item
        
        Formula: unit_price * quantity * cases
        Example: $100/item * 5 items * 2 cases = $1,000
        """
        return (self.unit_price or 0) * (self.quantity or 0) * (self.cases or 1)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['department', 'is_active']),
        ]
```

**Current Data (Oct 2025):**
- **Active Budgets:** 266 records
- **Total Budget:** $837K
- **Categories:** 14 active

---

### BudgetEstimateProjection Model (AI-Generated Forecasts)
**Location:** `coda/finance/models/budget.py`

```python
class BudgetEstimateProjection(models.Model):
    """
    AI-generated budget projections based on transaction data analysis
    
    Created by: management/commands/generate_budget_projections.py
    Uses: Historical transaction data to forecast future budgets
    """
    company = models.ForeignKey('main.Company', on_delete=models.CASCADE)
    department = models.ForeignKey('main.Department', on_delete=models.CASCADE, null=True)
    
    method = models.CharField(
        max_length=50,
        choices=[
            ('transaction_analysis', 'Transaction Data Analysis'),
            ('historical_avg', 'Historical Average'),
            ('trend_forecast', 'Trend-Based Forecast'),
        ],
        help_text="Method used to generate projection"
    )
    
    horizon = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        help_text="Time horizon for projection"
    )
    
    estimates = models.JSONField(
        help_text="Category-wise estimates: {category_id: {monthly_avg, total_projection, confidence}}"
    )
    
    total_estimate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total projected budget"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
        ],
        default='draft'
    )
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

**Current Data (Oct 2025):**
- **Projections:** 13 AI-generated forecasts
- **Recommended Annual Budget:** $722K (vs current $65K)
- **Key Finding:** IT category needs $57K (currently $0)

**Generate New Projection:**
```bash
python manage.py generate_budget_projections --months 12 --save
```

---

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

### Main Budget Dashboard
**URL:** `/finance/budget-dashboard/{company_slug}/`  
**View:** `coda/finance/views_unified_budget.py::unified_budget_dashboard`  
**Template:** `coda/finance/templates/finance/budgets/unified_budget_dashboard.html`

**Purpose:** Main hub for all budget management

**Features:**
- **5 Tabs:**
  1. **Overview** - Budget summary, totals by category
  2. **Estimation** - AI-generated projections
  3. **Planning** - Create/edit budgets
  4. **Approvals** - Approve/reject requests
  5. **Analytics** - Spending trends, variance analysis

- **Category Drill-Down:** Click categories to see all items
- **Filtering:** By department, category, date range
- **Search:** Find specific budget items
- **Theme Switcher:** Navy/Gold or Purple themes

**Critical Implementation Note:**
Uses correct aggregation formula to avoid 177x inflation bug:
```python
total = Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1))
```

---

### Approval Dashboard
**URL:** `/finance/budget/{company_slug}/approvals/`  
**View:** `coda/finance/views/budget/approvals.py::budget_approval_dashboard`  
**Template:** `coda/finance/templates/finance/budgets/budget_approvals.html`

**Purpose:** Dedicated interface for viewing and managing budget approvals

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

## Management Commands

### Budget Analysis:
```bash
# Generate budget projections from transaction data
python manage.py generate_budget_projections --months 12 --save

# Analyze budget vs actual spending
python manage.py analyze_budget_variance

# Verify dashboard calculation fix
python manage.py verify_dashboard_fix
```

### Budget Maintenance:
```bash
# Fix duplicate CodaBudget entries (if any)
python manage.py cleanup_duplicate_codabudgets

# Recalculate all budget totals
python manage.py recalculate_budget_totals

# Archive old budgets
python manage.py archive_old_budgets --older-than 2024-01-01
```

### Budget Projections:
```bash
# Generate projections with different methods
python manage.py generate_budget_projections --method transaction_analysis
python manage.py generate_budget_projections --method historical_avg
python manage.py generate_budget_projections --method trend_forecast

# View current projections
python manage.py list_budget_projections
```

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

## Critical Bug Fixes

### Dashboard Aggregation Bug (Oct 1, 2025) ⚠️ CRITICAL

**Problem:** Budget totals inflated by 177x  
**Example:** $837K actual → displayed as $148M

**Root Cause:**
```python
# WRONG (what we had)
total = Sum('quantity') * Sum('unit_price')
# This does: (2+3) * (100+50) = 750 ❌
# Multiplies sum of ALL quantities by sum of ALL prices
```

**Correct Solution:**
```python
# CORRECT (what we fixed)
total = Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), 
            output_field=DecimalField())
# This does: (2*100) + (3*50) = 350 ✅
# Multiplies EACH item's quantity by ITS price, then sums
```

**Impact:**
- Dashboard now shows accurate totals
- Budget calculations correct
- Reporting reliable

**File:** `views_unified_budget.py` lines 164-174  
**Deployed:** October 1, 2025  
**Regression Test:** Added to `test_regressions.py`

**⚠️ IMPORTANT:** Always use `F()` expressions for row-level calculations before aggregation!

**Source:** MASTER_REFERENCE.md Section: Critical Fixes

---

## Phase 2: Data-Driven Tier System (October 16, 2025) ✅

### Implementation Summary

**Completed:** October 16, 2025  
**Status:** ✅ Deployed to UAT, tested, ready for production  
**Completion:** 95% (integration complete, Finance Manager UI complete)

### New Features Implemented:

#### 1. BudgetCategory Tier Fields
**File:** `coda/finance/models/budget.py`  
**Migration:** `0002_budgetcategory_tier_fields.py`

**Fields Added:**
- `approval_tier` - A/B/C classification from data analysis
- `auto_approve_enabled` - Finance Manager toggle
- `typical_monthly_amount` - Calculated from $1.49M transaction data
- `variance_threshold` - Data-driven anomaly detection threshold
- `is_recurring` - Pattern detection from transaction frequency
- `last_pattern_analysis` - Timestamp of last analysis

**Methods Added:**
- `should_auto_approve(amount)` - Auto-approval logic
- `is_within_variance(amount)` - Variance checking
- `needs_pattern_analysis()` - Check if re-analysis needed

---

#### 2. Tier Classification Command
**File:** `coda/finance/management/commands/classify_budget_category_tiers.py`

**Analyzes:**
- $1,458,482 in transaction data over 27 months
- 366 transactions across 25 categories
- Transaction frequency, amount variance, business criticality

**Classifies into:**
- **Tier A**: Known/Recurring (high frequency, low variance, essential)
- **Tier B**: Variable/Operational (medium frequency, operational)
- **Tier C**: Strategic/Discretionary (low frequency or high variance)

**Usage:**
```bash
python manage.py classify_budget_category_tiers --analyze
python manage.py classify_budget_category_tiers --analyze --save
python manage.py classify_budget_category_tiers --export tiers.csv
```

**Results (Ran Oct 16, 2025):**
- Tier A: 1 category (Rent - $2,000/mo)
- Tier B: 5 categories (Salaries $33k/mo, IT, Utilities, Travel, Office)
- Tier C: 19 categories (Strategic + dormant)

---

#### 3. Smart Approval Service (Phase 2)
**File:** `coda/finance/services/smart_approval_service.py`

**Rewritten to use tier data instead of hardcoded rules:**

**Old (Phase 1):** Hardcoded thresholds (Utilities: 50k, IT: 15k, Salaries: 15k)  
**New (Phase 2):** Data-driven using BudgetCategory tier fields

**Methods:**
- `should_auto_approve(budget_request)` - Uses category.should_auto_approve()
- `get_recommended_approver(budget_request)` - Tier-based routing
- `get_approval_routing(budget_request)` - Complete routing info
- `process_budget_request(budget_request)` - Auto-approve or route

**Routing Logic:**
- **Tier A**: Auto-approve if within variance, else Finance Manager
- **Tier B**: High=Auto, Medium=Dept Manager, Low=Finance Manager
- **Tier C**: High=Senior Manager, Other=Executive

---

#### 4. BudgetRequestService Integration
**File:** `coda/finance/services/automation_service.py`

**Updated `submit_for_approval()` method:**
1. Checks SmartApprovalService first
2. Auto-approves if eligible
3. Routes to policy system if manual approval needed
4. Logs all actions

**Auto-Approval Flow:**
```
Budget Request Submitted
        ↓
SmartApprovalService.should_auto_approve()
        ↓
    ┌───┴───┐
    YES     NO
    ↓       ↓
Auto-    Route to
Approve  Policy
```

---

#### 5. Finance Manager Tier Control Interface
**Files:**
- View: `coda/finance/views/budget/views_tier_management.py`
- Template: `coda/finance/templates/finance/budgets/tier_management_dashboard.html`
- Template: `coda/finance/templates/finance/budgets/auto_approval_log.html`

**URL:** `/finance/tier-management/{company_slug}/`

**Features:**
- View all 25 categories grouped by tier (A/B/C)
- Toggle auto-approval per category (Tier A only)
- Adjust variance thresholds inline
- View tier statistics
- Re-run tier classification analysis
- Auto-approval log with filters

**API Endpoints:**
- `POST /finance/api/tier/toggle-auto-approval/{category_id}/`
- `POST /finance/api/tier/update-variance-threshold/{category_id}/`
- `POST /finance/api/tier/run-reclassification/{company}/`

---

#### 6. Auto-Approval Log Viewer
**URL:** `/finance/tier/auto-approval-log/{company_slug}/`

**Features:**
- View all auto-approved requests
- Filter by date range (7/30/90/365 days)
- Filter by tier (A/B/C)
- Shows variance vs typical amount
- Tier breakdown statistics
- Total amounts auto-approved

---

### Tier Classification Results (Oct 16, 2025)

**Dataset Analyzed:** $1,458,482.32 over 27 months

| Tier | Categories | Total Spending | % of Total |
|------|-----------|----------------|------------|
| **A** | 1 (Rent) | $2,000 | 0.1% |
| **B** | 5 (Salaries, IT, Utilities, Travel, Office) | $1,130,091 | 77.5% |
| **C** | 19 (Strategic + dormant) | $326,390 | 22.4% |

**Key Finding:** 77.5% of spending is in Tier B (operational expenses)

**Auto-Approval Potential:**
- Current: 1 category eligible (Rent)
- Future: Could enable for Tier B high-priority requests (~30-40% automation)

---

### URLs Added (Phase 2)

```python
# Finance Manager Tier Controls
path('tier-management/<str:company_slug>/', ..., name='tier-management-dashboard'),
path('tier/auto-approval-log/<str:company_slug>/', ..., name='auto-approval-log'),

# API Endpoints
path('api/tier/toggle-auto-approval/<int:category_id>/', ...),
path('api/tier/update-variance-threshold/<int:category_id>/', ...),
path('api/tier/run-reclassification/<str:company_slug>/', ...),
```

---

### Configuration

**Tier Classification:** Run on production data Oct 16, 2025  
**Default Settings:**
- Variance threshold: 15-50% (data-driven)
- Auto-approval: Disabled by default (Finance Manager must enable)
- Tier assignment: Based on transaction patterns

**Re-run Analysis:** Finance Manager can trigger via UI or command line

---

## Change History

| Date | Change | Developer | Reason | Reference |
|------|--------|-----------|--------|-----------|
| Oct 16, 2025 | **Phase 2: Tier System COMPLETE** | CM | Data-driven approval automation | This session |
| Oct 16, 2025 | Added 6 tier fields to BudgetCategory | CM | Enable data-driven auto-approval | Migration 0002 |
| Oct 16, 2025 | Created tier classification command | CM | Analyze $1.49M dataset | classify_budget_category_tiers.py |
| Oct 16, 2025 | Ran tier analysis on production data | CM | Classify 25 categories | Results saved to DB |
| Oct 16, 2025 | Integrated SmartApprovalService (Phase 2) | CM | Use tier data, not hardcoded rules | smart_approval_service.py |
| Oct 16, 2025 | Updated BudgetRequestService | CM | Auto-approve before routing | automation_service.py |
| Oct 16, 2025 | Created Finance Manager UI | CM | Tier control interface | views_tier_management.py |
| Oct 16, 2025 | Lean production deployment | CM | 87% size reduction (venv removed) | Production v1738 |
| Oct 13, 2025 | Added approval fields (Migration 0099) | CM | Support Phase 1 workflow | This session |
| Oct 13, 2025 | Fixed permission logic (simple staff approval) | CM | Unblock development | This session |
| Oct 2, 2025 | Dashboard bug fix (aggregation formula) | CM | Fix 177x inflation error | MASTER_REFERENCE.md |
| Oct 1, 2025 | Created BudgetRequest model | CM | Initial implementation | Phase 3 start |
| Sept 30, 2025 | Data quality analysis | CM | Foundation for improvements | DATA_QUALITY_ANALYSIS.md |

---

**Maintained by:** Cursor AI Assistant  
**Last Major Update:** October 16, 2025 (Phase 2 Complete)  
**Questions?** Check REQUIREMENTS.md for business logic, TESTING.md for verification

