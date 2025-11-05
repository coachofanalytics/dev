# Managed Options Trading - Implementation Guide
**Feature:** CODA Managed Options Trading Service  
**Last Updated:** October 27, 2025  
**Status:** ✅ Phase 1-5 Complete | ⏳ Phase 6-8 Ready to Build

---

## 📊 **CURRENT IMPLEMENTATION STATUS**

### **✅ COMPLETED (Phases 1-5)**

**Phase 1: Database Models** - COMPLETE
- ✅ `ManagedTradingAccount` (5 fee tiers)
- ✅ `OptionsPosition` (multi-leg support)
- ✅ `TradingRule` (risk management)
- ✅ `TradingActivity` (audit trails)
- ✅ `TradingSession` (consultative tier)
- **Files:** `coda/investing/models.py`, `coda/investing/admin.py`

**Phase 2: Service Layer** - COMPLETE
- ✅ `ManagedTradingService` (accounts, positions, fees)
- ✅ `OptionsMonitoringService` (alerts, monitoring)
- ✅ `OptionPlayIntegrationService` (API placeholder)
- **Files:** `coda/investing/services/managed_trading_service.py`, `options_monitoring_service.py`, `optionplay_integration_service.py`

**Phase 3: Views & Forms** - COMPLETE
- ✅ Staff views (accounts, positions, monitoring, sessions)
- ✅ Client views (portal, account detail)
- ✅ Multi-leg options form with real-time calculations
- **Files:** `coda/investing/views/managed_trading/*.py` (6 files), `forms.py`, `forms_enhanced.py`

**Phase 4: Templates** - COMPLETE
- ✅ 14 HTML templates (staff + client)
- ✅ Real-time JavaScript risk calculations
- ✅ Multi-tab position entry interface
- **Files:** `coda/investing/templates/investing/managed/*.html`

**Phase 5: URLs & Integration** - COMPLETE
- ✅ 30+ URL patterns configured
- ✅ Dashboard integration (8 quick-access buttons)
- **Files:** `coda/investing/urls_managed_trading.py`, `urls.py`

**Testing:**
- ✅ Backend tested (models, services, views)
- ✅ UI tested (forms, templates, calculations)
- ✅ Bug fixes complete (Decimal/float types)

**Deployment:**
- ✅ Committed to GitHub
- ⚠️ Heroku deployment pending (after Phase 6-8)

---

### **✅ PHASE 6 COMPLETE: Client Onboarding & Compliance**

**Status:** ✅ Deployed to Heroku v949 (Backend 100% | Templates Pending)

**What's Done:**
- ✅ 3 new models (InvestorRiskProfile, ManagedTradingApplication, ManagedTradingContract)
- ✅ Risk tolerance questionnaire (10 questions, auto-scoring)
- ✅ Application workflow (capital validation, tier matching)
- ✅ Digital contract system (4 contract types)
- ✅ Auto-approval service (6 criteria checks)
- ✅ Staff review queue
- ✅ Email notifications
- ✅ 7 views, 4 forms, 10 URLs
- ⏳ Templates (6 files pending)

**Files:** `models.py`, `admin.py`, `forms_onboarding.py`, `services/application_approval_service.py`, `views/managed_trading/onboarding.py`, `urls_managed_trading.py`

---

### **⏳ UPCOMING (Phases 7-8)**

**Phase 7: Batch Approval System** (~4 days)
- Weekly position batches
- 24-hour timeout mechanism
- Client approval interface
- Digital signatures
- Notification system

**Phase 8: Integration & Polish** (~3 days)
- OptionPlay API (real data)
- GoToMeeting integration
- Performance reporting
- Final testing & deployment

**Estimated Completion:** 7-9 days (Templates + Phases 7-8)

---

## 🚀 Quick Start: Manual Implementation (Week 1)

### **You Can Start Managing the Client TODAY!**

Since 80% of the infrastructure exists, you can begin managing the client's $30,000 account immediately using existing models while building the full system.

#### **Step 1: Create Client Record (5 minutes)**

```python
# In Django shell or admin
from accounts.models import CustomerUser
from investing.models import Investor_Information

# Create or get client user
client = CustomerUser.objects.get(username='client_options_30k')

# Create investment record to track the $30K account
managed_investment = Investor_Information.objects.create(
    investor=client,
    amount_invested=Decimal('30000.00'),
    investment_type='options',
    investment_purpose='Managed Options Trading Account',
    expected_return_rate=Decimal('20.00'),  # Target 20% annual
    risk_tolerance='moderate',
    kyc_status='verified',
    status='active',
    model_type='Options',
    duration=12,  # 12 months initial
    notes='MANAGED ACCOUNT - Options Trading Strategy Mix'
)

print(f"✅ Created managed account tracking: {managed_investment.id}")
```

#### **Step 2: Execute First Position (15 minutes)**

```python
from investing.models import Portfolio

# Example: Cash-secured put on AAPL
position = Portfolio.objects.create(
    user=request.user,  # CODA trader, not client
    symbol='AAPL',
    strategy='short_put',
    short_strike=Decimal('170.00'),  # Strike price
    long_strike=Decimal('0.00'),  # N/A for short put
    amount=Decimal('300.00'),  # Premium collected
    number_of_contract=1,
    expiry='2025-11-22',  # 30 days out
    short_leg_delta=Decimal('0.30'),  # 30 delta
    short_leg_theta=Decimal('0.15'),  # Positive theta
    comment=f'Client: {client.username} | Capital: $17,000 | Max Loss: $16,700',
    is_active=True,
    is_featured=True
)

print(f"✅ Position created: AAPL $170 Put @ $3.00 premium")
```

#### **Step 3: Track in Spreadsheet (Parallel)**

Create Google Sheet with columns:
```
Date | Account | Symbol | Strategy | Strike | Contracts | Premium | Capital | Max Loss | Status | P&L | Notes
```

This allows you to:
- Track all positions across clients
- Calculate total P&L
- Monitor risk exposure
- Generate client reports

**You can now trade the client's account using existing infrastructure!**

---

## 🏗️ Full System Implementation

### **Phase 1: Database Models** (Week 1-2)

#### **File: `coda/investing/models/managed_trading.py`**

```python
"""
Managed Trading Models
New models for professional options account management
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from main.models import TimeStampedModel

User = get_user_model()


class ManagedTradingAccount(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class OptionsPosition(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class TradingRule(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class TradingActivity(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass
```

#### **Update: `coda/investing/models/__init__.py`**

```python
# Add new imports
from .managed_trading import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingActivity
)

__all__ = [
    # ... existing models
    'ManagedTradingAccount',
    'OptionsPosition',
    'TradingRule',
    'TradingActivity',
]
```

#### **Create Migration:**

```bash
cd coda
python manage.py makemigrations investing
python manage.py migrate
```

---

### **Phase 2: Services** (Week 2-3)

#### **File: `coda/investing/services/managed_trading_service.py`**

```python
"""
Managed Trading Service
Core business logic for managing client options accounts
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Tuple, Optional

from ..models import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingActivity
)
from .base_service import BaseInvestingService

logger = logging.getLogger(__name__)


class ManagedTradingService(BaseInvestingService):
    """
    Service for managed options trading operations
    """
    
    def create_managed_account(
        self, 
        client_user, 
        account_data: Dict
    ) -> ManagedTradingAccount:
        """
        Create new managed trading account
        
        Args:
            client_user: User instance (client)
            account_data: Dict with account parameters
        
        Returns:
            ManagedTradingAccount instance
        """
        try:
            with transaction.atomic():
                # Generate account number
                account_number = self._generate_account_number()
                
                # Create account
                account = ManagedTradingAccount.objects.create(
                    client=client_user,
                    account_name=account_data.get('account_name'),
                    account_number=account_number,
                    initial_capital=Decimal(str(account_data['initial_capital'])),
                    current_balance=Decimal(str(account_data['initial_capital'])),
                    cash_available=Decimal(str(account_data['initial_capital'])),
                    cash_reserved=Decimal('0.00'),
                    high_water_mark=Decimal(str(account_data['initial_capital'])),
                    account_manager=account_data.get('account_manager'),
                    management_fee_percentage=account_data.get('management_fee', Decimal('1.50')),
                    performance_fee_percentage=account_data.get('performance_fee', Decimal('20.00')),
                    status='active',
                    activation_date=date.today()
                )
                
                # Create default trading rules
                self._create_default_trading_rules(account)
                
                # Log activity
                TradingActivity.objects.create(
                    managed_account=account,
                    activity_type='account_created',
                    description=f'Managed account created with ${account.initial_capital}',
                    performed_by=account_data.get('account_manager'),
                    data_snapshot={'initial_capital': str(account.initial_capital)}
                )
                
                logger.info(f"Created managed account {account.account_number} for {client_user.username}")
                
                return account
                
        except Exception as e:
            logger.error(f"Error creating managed account: {e}")
            raise ValidationError(f"Failed to create account: {str(e)}")
    
    def _generate_account_number(self) -> str:
        """Generate unique account number"""
        import random
        prefix = 'CODA-OPT'
        
        # Get count of existing accounts
        count = ManagedTradingAccount.objects.count() + 1
        
        # Format: CODA-OPT-001, CODA-OPT-002, etc.
        account_number = f"{prefix}-{count:03d}"
        
        # Ensure uniqueness
        while ManagedTradingAccount.objects.filter(account_number=account_number).exists():
            count += 1
            account_number = f"{prefix}-{count:03d}"
        
        return account_number
    
    def _create_default_trading_rules(self, account):
        """Create standard trading rules for account"""
        default_rules = [
            {
                'name': 'Max Position Size',
                'type': 'position_limit',
                'config': {'max_position_size': 7000, 'max_contracts': 3},
                'priority': 1
            },
            {
                'name': 'Profit Target',
                'type': 'profit_target',
                'config': {'target_percentage': 50, 'recommend_close': True},
                'priority': 2
            },
            {
                'name': 'Stop Loss',
                'type': 'stop_loss',
                'config': {'loss_percentage': 200, 'auto_close': False},
                'priority': 1
            },
            {
                'name': 'Daily Loss Limit',
                'type': 'risk_limit',
                'config': {'max_daily_loss': 2.0},
                'priority': 1
            },
        ]
        
        for rule_data in default_rules:
            TradingRule.objects.create(
                managed_account=account,
                rule_name=rule_data['name'],
                rule_type=rule_data['type'],
                rule_config=rule_data['config'],
                priority=rule_data['priority'],
                is_active=True
            )
```

**Continue in file with additional methods...**
- `create_position()`
- `close_position()`
- `calculate_fees()`
- `get_account_summary()`

---

### **Phase 3: Views** (Week 3-4)

#### **File: `coda/investing/views/managed_trading_views.py`**

```python
"""
Managed Trading Views
Views for managing client options accounts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

from ..models import ManagedTradingAccount, OptionsPosition
from ..services.managed_trading_service import ManagedTradingService
from ..forms import ManagedAccountForm, OptionsPositionForm


@staff_member_required
def managed_accounts_list(request):
    """
    List all managed trading accounts
    """
    accounts = ManagedTradingAccount.objects.filter(
        status__in=['active', 'paused']
    ).select_related('client', 'account_manager').order_by('-created_at')
    
    context = {
        'accounts': accounts,
        'title': 'Managed Trading Accounts'
    }
    
    return render(request, 'investing/managed/accounts_list.html', context)


@staff_member_required
def create_managed_account(request):
    """
    Create new managed trading account
    """
    if request.method == 'POST':
        form = ManagedAccountForm(request.POST)
        if form.is_valid():
            service = ManagedTradingService()
            try:
                account = service.create_managed_account(
                    client_user=form.cleaned_data['client'],
                    account_data=form.cleaned_data
                )
                messages.success(request, f'Account {account.account_number} created successfully')
                return redirect('investing:managed_account_detail', account_id=account.id)
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        form = ManagedAccountForm()
    
    return render(request, 'investing/managed/create_account.html', {'form': form})


@login_required
def managed_account_detail(request, account_id):
    """
    View managed account details
    Permissions: Admin, Account Manager, or Client (owner)
    """
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    # Permission check
    if not (request.user.is_staff or 
            account.account_manager == request.user or 
            account.client == request.user):
        messages.error(request, 'Access denied')
        return redirect('investing:home')
    
    # Get positions
    positions = account.positions.filter(
        status='open'
    ).order_by('expiration_date')
    
    # Get service
    service = ManagedTradingService()
    summary = service.get_account_summary(account)
    
    context = {
        'account': account,
        'positions': positions,
        'summary': summary,
        'is_manager': account.account_manager == request.user,
        'is_client': account.client == request.user,
    }
    
    return render(request, 'investing/managed/account_detail.html', context)
```

**Additional views to implement:**
- `create_position()`
- `close_position()`
- `position_list()`
- `account_performance()`
- `generate_report()`

---

### **Phase 4: Templates** (Week 4-5)

#### **File: `coda/investing/templates/investing/managed/accounts_list.html`**

```django
{% extends "main/base_templates/new_base.html" %}
{% load static %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col">
            <h2><i class="fa fa-briefcase"></i> Managed Trading Accounts</h2>
        </div>
        <div class="col text-end">
            <a href="{% url 'investing:create_managed_account' %}" class="btn btn-primary">
                <i class="fa fa-plus"></i> New Account
            </a>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total Accounts</h6>
                    <h3>{{ accounts.count }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total AUM</h6>
                    <h3>${{ total_aum|floatformat:0 }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total P&L</h6>
                    <h3 class="{% if total_pnl > 0 %}text-success{% else %}text-danger{% endif %}">
                        ${{ total_pnl|floatformat:0 }}
                    </h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Open Positions</h6>
                    <h3>{{ total_positions }}</h3>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Accounts Table -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Account #</th>
                        <th>Client</th>
                        <th>Balance</th>
                        <th>P&L</th>
                        <th>ROI %</th>
                        <th>Positions</th>
                        <th>Manager</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for account in accounts %}
                    <tr>
                        <td><strong>{{ account.account_number }}</strong></td>
                        <td>{{ account.client.get_full_name }}</td>
                        <td>${{ account.current_balance|floatformat:2 }}</td>
                        <td class="{% if account.total_profit_loss > 0 %}text-success{% else %}text-danger{% endif %}">
                            ${{ account.total_profit_loss|floatformat:2 }}
                        </td>
                        <td class="{% if account.return_on_investment > 0 %}text-success{% else %}text-danger{% endif %}">
                            {{ account.return_on_investment|floatformat:2 }}%
                        </td>
                        <td>{{ account.positions.filter(status='open').count }}</td>
                        <td>{{ account.account_manager.get_full_name }}</td>
                        <td>
                            <span class="badge bg-{% if account.status == 'active' %}success{% else %}warning{% endif %}">
                                {{ account.get_status_display }}
                            </span>
                        </td>
                        <td>
                            <a href="{% url 'investing:managed_account_detail' account.id %}" class="btn btn-sm btn-info">
                                <i class="fa fa-eye"></i> View
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="9" class="text-center text-muted">
                            No managed accounts yet. Create one to get started.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

**Additional templates needed:**
- `account_detail.html`
- `create_account.html`
- `position_entry_form.html`
- `client_dashboard.html`
- `performance_report.html`

---

### **Phase 5: URLs** (Week 5)

#### **File: `coda/investing/urls_managed_trading.py`**

```python
"""
URLs for Managed Options Trading
"""

from django.urls import path
from .views import managed_trading_views

urlpatterns = [
    # Account Management
    path('managed/accounts/', 
         managed_trading_views.managed_accounts_list, 
         name='managed_accounts_list'),
    path('managed/accounts/create/', 
         managed_trading_views.create_managed_account, 
         name='create_managed_account'),
    path('managed/accounts/<int:account_id>/', 
         managed_trading_views.managed_account_detail, 
         name='managed_account_detail'),
    
    # Position Management
    path('managed/positions/create/', 
         managed_trading_views.create_position, 
         name='create_managed_position'),
    path('managed/positions/<int:position_id>/close/', 
         managed_trading_views.close_position, 
         name='close_managed_position'),
    path('managed/positions/<int:position_id>/', 
         managed_trading_views.position_detail, 
         name='managed_position_detail'),
    
    # Client Portal
    path('managed/portal/', 
         managed_trading_views.client_portal_dashboard, 
         name='client_portal'),
    
    # Reporting
    path('managed/accounts/<int:account_id>/report/', 
         managed_trading_views.generate_account_report, 
         name='generate_account_report'),
    
    # API
    path('managed/api/accounts/<int:account_id>/summary/', 
         managed_trading_views.account_summary_api, 
         name='account_summary_api'),
    path('managed/api/positions/monitor/', 
         managed_trading_views.monitor_positions_api, 
         name='monitor_positions_api'),
]
```

#### **Update: `coda/investing/urls.py`**

```python
# Add at the end
urlpatterns += [
    # Managed Options Trading
    path('managed/', include('investing.urls_managed_trading')),
]
```

---

### **Phase 6: Admin Interface** (Week 5)

#### **File: `coda/investing/admin.py` (add to existing)**

```python
from .models import (
    ManagedTradingAccount, 
    OptionsPosition, 
    TradingRule, 
    TradingActivity
)

@admin.register(ManagedTradingAccount)
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_number',
        'client',
        'current_balance',
        'total_profit_loss',
        'win_rate',
        'status',
        'account_manager'
    ]
    list_filter = ['status', 'account_manager', 'trading_enabled']
    search_fields = ['account_number', 'client__username', 'client__email']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'client', 'account_name', 'account_manager')
        }),
        ('Financial Details', {
            'fields': (
                'initial_capital', 'current_balance', 
                'cash_available', 'cash_reserved', 'high_water_mark'
            )
        }),
        ('Fee Structure', {
            'fields': (
                'management_fee_percentage', 
                'performance_fee_percentage', 
                'performance_threshold'
            )
        }),
        ('Risk Parameters', {
            'fields': (
                'max_position_risk', 'max_total_risk', 
                'max_daily_loss', 'max_weekly_loss', 'max_monthly_loss',
                'max_positions'
            )
        }),
        ('Status & Permissions', {
            'fields': ('status', 'trading_enabled', 'auto_trading_enabled')
        }),
        ('Performance Tracking', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades',
                'total_profit_loss', 'total_fees_paid'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(OptionsPosition)
class OptionsPositionAdmin(admin.ModelAdmin):
    list_display = [
        'symbol',
        'strategy',
        'managed_account',
        'expiration_date',
        'days_to_expiration',
        'unrealized_pnl',
        'status'
    ]
    list_filter = ['strategy', 'status', 'managed_account']
    search_fields = ['symbol', 'managed_account__account_number']
    readonly_fields = ['entry_date', 'created_at', 'updated_at']
    
    def days_to_expiration(self, obj):
        return obj.days_to_expiration
    days_to_expiration.short_description = 'DTE'
```

---

### **Phase 7: Forms** (Week 5)

#### **File: `coda/investing/forms/managed_trading_forms.py`**

```python
from django import forms
from decimal import Decimal
from datetime import date, timedelta

from ..models import ManagedTradingAccount, OptionsPosition, TradingRule


class ManagedAccountForm(forms.ModelForm):
    """
    Form for creating/editing managed trading accounts
    """
    
    class Meta:
        model = ManagedTradingAccount
        fields = [
            'client',
            'account_name',
            'initial_capital',
            'account_manager',
            'management_fee_percentage',
            'performance_fee_percentage',
            'performance_threshold',
            'max_position_risk',
            'max_total_risk',
            'max_daily_loss',
            'max_weekly_loss',
            'max_monthly_loss',
            'max_positions'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_capital': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'account_manager': forms.Select(attrs={'class': 'form-control'}),
            # ... other widgets
        }
    
    def clean_initial_capital(self):
        capital = self.cleaned_data.get('initial_capital')
        if capital < Decimal('5000.00'):
            raise forms.ValidationError('Minimum account size is $5,000')
        return capital


class OptionsPositionForm(forms.ModelForm):
    """
    Form for creating options positions
    """
    
    class Meta:
        model = OptionsPosition
        fields = [
            'managed_account',
            'symbol',
            'strategy',
            'positions',  # JSONField - need custom widget
            'capital_required',
            'premium_collected',
            'max_profit',
            'max_loss',
            'expiration_date',
            'notes'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('managed_account')
        capital = cleaned_data.get('capital_required')
        
        if account and capital:
            if capital > account.available_buying_power:
                raise forms.ValidationError(
                    f'Insufficient buying power. Available: ${account.available_buying_power}'
                )
        
        return cleaned_data
```

---

## 📊 Database Migrations

### **Create Migrations**

```bash
# In coda directory
python manage.py makemigrations investing --name managed_trading_models

# Review migration file
python manage.py sqlmigrate investing XXXX

# Apply migration
python manage.py migrate investing

# Verify
python manage.py check
```

### **Sample Migration Output**

```python
# Generated migration file
operations = [
    migrations.CreateModel(
        name='ManagedTradingAccount',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True)),
            ('client', models.ForeignKey(...)),
            # ... all fields
        ],
        options={
            'verbose_name': 'Managed Trading Account',
            'ordering': ['-created_at'],
            'indexes': [...]
        },
    ),
    # ... other models
]
```

---

## 🧪 Implementation Checklist

### **Week 1: Database Foundation**
- [ ] Create `models/managed_trading.py`
- [ ] Define `ManagedTradingAccount` model
- [ ] Define `OptionsPosition` model
- [ ] Define `TradingRule` model
- [ ] Define `TradingActivity` model
- [ ] Create migration
- [ ] Apply migration
- [ ] Verify in database
- [ ] Register in admin
- [ ] Test CRUD operations in admin

### **Week 2: Services**
- [ ] Create `services/managed_trading_service.py`
- [ ] Implement `create_managed_account()`
- [ ] Implement `create_position()`
- [ ] Implement `close_position()`
- [ ] Implement `calculate_fees()`
- [ ] Implement `get_account_summary()`
- [ ] Create unit tests for service methods
- [ ] Test with sample data

### **Week 3-4: Views & Forms**
- [ ] Create `views/managed_trading_views.py`
- [ ] Create `forms/managed_trading_forms.py`
- [ ] Implement account list view
- [ ] Implement account detail view
- [ ] Implement create account view
- [ ] Implement position entry view
- [ ] Implement position close view
- [ ] Test all views

### **Week 5: Templates**
- [ ] Create `templates/investing/managed/` directory
- [ ] Create `accounts_list.html`
- [ ] Create `account_detail.html`
- [ ] Create `create_account.html`
- [ ] Create `position_entry_form.html`
- [ ] Create `client_dashboard.html`
- [ ] Test responsive design

### **Week 6: Risk & Monitoring**
- [ ] Implement position monitoring service
- [ ] Create alert generation logic
- [ ] Setup scheduled tasks (cron/celery)
- [ ] Test alert system
- [ ] Verify stop loss triggers

### **Week 7: Reporting**
- [ ] Implement daily summary email
- [ ] Implement weekly report
- [ ] Implement monthly statement
- [ ] Create PDF templates
- [ ] Test email delivery

### **Week 8: Testing & Launch**
- [ ] Full end-to-end testing
- [ ] Client UAT
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation review
- [ ] Go live!

---

## 🔧 Code Snippets & Examples

### **Example: Creating First Position**

```python
# In Django view or management command
from investing.services.managed_trading_service import ManagedTradingService
from investing.models import ManagedTradingAccount
from decimal import Decimal

# Get account
account = ManagedTradingAccount.objects.get(account_number='CODA-OPT-001')

# Create service
service = ManagedTradingService()

# Position data
position_data = {
    'symbol': 'AAPL',
    'strategy': 'short_put',
    'positions': [
        {
            'type': 'short_put',
            'strike': 170.00,
            'contracts': 1,
            'premium': 300.00,
            'delta': -0.30,
            'theta': 0.15
        }
    ],
    'capital_required': Decimal('17000.00'),
    'premium_collected': Decimal('300.00'),
    'max_profit': Decimal('300.00'),
    'max_loss': Decimal('16700.00'),
    'position_delta': Decimal('-0.30'),
    'position_theta': Decimal('0.15'),
    'expiration_date': date(2025, 11, 22),
    'notes': 'Cash-secured put on AAPL, IV Rank: 45'
}

# Create position
position = service.create_position(account, position_data)

print(f"✅ Position created: {position}")
print(f"Account buying power: ${account.available_buying_power}")
```

---

### **Example: Monitoring Positions**

```python
from investing.services.options_monitoring_service import OptionsMonitoringService

service = OptionsMonitoringService()

# Monitor all active accounts
active_accounts = ManagedTradingAccount.objects.filter(status='active')

for account in active_accounts:
    alerts = service.monitor_account(account)
    
    if alerts:
        for alert in alerts:
            print(f"🚨 Alert: {alert['message']}")
            
            # If critical, take action
            if alert['severity'] == 'critical':
                service.handle_critical_alert(account, alert)
```

---

### **Example: Generating Report**

```python
from investing.services.managed_trading_reporting_service import ManagedTradingReportingService

service = ManagedTradingReportingService()

# Generate monthly statement
account = ManagedTradingAccount.objects.get(account_number='CODA-OPT-001')
statement = service.generate_monthly_statement(account)

# Send to client
service.send_monthly_statement(account, statement)

print(f"✅ Monthly statement sent to {account.client.email}")
```

---

## 🎯 Best Practices

### **Code Organization**
```
coda/investing/
├── models/
│   ├── __init__.py
│   ├── core.py (existing)
│   └── managed_trading.py (NEW)
├── services/
│   ├── managed_trading_service.py (NEW)
│   ├── options_monitoring_service.py (NEW)
│   └── managed_trading_reporting_service.py (NEW)
├── views/
│   └── managed_trading_views.py (NEW)
├── forms/
│   └── managed_trading_forms.py (NEW)
├── templates/investing/managed/ (NEW)
└── urls_managed_trading.py (NEW)
```

### **Naming Conventions**
- **Models**: PascalCase (e.g., `ManagedTradingAccount`)
- **Services**: PascalCase with "Service" suffix
- **Views**: snake_case with descriptive names
- **URLs**: Kebab-case in URL patterns
- **Templates**: snake_case.html

### **Error Handling**

```python
try:
    position = service.create_position(account, position_data)
    messages.success(request, 'Position created successfully')
    return redirect('investing:managed_account_detail', account.id)
except ValidationError as e:
    messages.error(request, f'Validation error: {str(e)}')
    return redirect('investing:create_managed_position')
except Exception as e:
    logger.error(f'Unexpected error creating position: {e}')
    messages.error(request, 'An error occurred. Please try again.')
    return redirect('investing:managed_accounts_list')
```

---

## 📚 Development Workflow

### **Step-by-Step Development Process**

1. **Start with Models** (Week 1)
   - Define models in `models/managed_trading.py`
   - Create and run migrations
   - Test in Django admin

2. **Build Services** (Week 2)
   - Implement core business logic
   - Create unit tests
   - Test with sample data

3. **Create Views** (Week 3)
   - Implement view functions
   - Handle permissions
   - Add error handling

4. **Design Templates** (Week 4)
   - Create HTML templates
   - Add JavaScript for interactivity
   - Ensure responsive design

5. **Connect URLs** (Week 5)
   - Map URLs to views
   - Test all endpoints
   - Verify permissions

6. **Add Monitoring** (Week 6)
   - Implement scheduled tasks
   - Create alert system
   - Test notifications

7. **Build Reporting** (Week 7)
   - Create report generators
   - Test PDF generation
   - Verify email delivery

8. **Final Testing** (Week 8)
   - End-to-end testing
   - Load testing
   - Security testing
   - Client UAT

---

## 🎉 Implementation Summary

**Total Implementation Time:** 8 weeks  
**Files to Create:** ~15 new files  
**Lines of Code:** ~3,000 lines (estimated)  
**Leverages Existing Code:** 80%  
**Development Effort:** Medium

**Immediate Option:** Can start managing client account TODAY using existing `Portfolio` models while building full system in parallel.

---

## 🆕 PHASE 9 COMPLETE: Automation & Spread Builder (Nov 3, 2025)

### **Status:** ✅ Fully Implemented - Ready for Testing

### **New Features Added:**

#### 1. **Automatic Spread Builder** ✅
- **File:** `coda/investing/services/spread_builder.py`
- **Purpose:** Auto-converts single-leg positions to multi-leg spreads
- **Conversions:**
  - Short Puts → Bull Put Spreads (90% capital reduction)
  - Covered Calls → Bear Call Spreads (if no stock owned)
  - Credit Spreads → Import as-is
- **Algorithms:** AI-optimized spread width based on IV, DTE, price
- **Result:** $180k capital → $5-10k (97% savings!)

#### 2. **Auto-Approval Pipeline** ✅
- **File:** `coda/investing/services/auto_approval_service.py`
- **Features:**
  - Auto-approves positions with AI score ≥60
  - Smart distribution to accounts with <2 positions
  - Automatic batch creation
  - WhatsApp notifications
- **Time Savings:** 45 minutes → 0 minutes per upload

#### 3. **Manual Unusual Whales Integration** ✅
- **Updated:** `coda/investing/views/managed_trading/csv_upload.py`
- **Features:**
  - Process manually uploaded Whales CSVs (Options Flow, Dark Pool, Lit Flow)
  - Cross-reference symbols for timing signals
  - Score boosts: +10 to +50 points
  - 🟢🟡🔴 Entry signals
- **Value:** Know WHEN to enter (not just WHAT)

#### 4. **Smart Duplicate Ranking** ✅
- **Updated:** `coda/investing/views/managed_trading/csv_upload.py`
- **Features:**
  - Detects duplicate symbols in current upload + database
  - Ranks by AI score (40%), R:R ratio (30%), DTE (20%), Premium (10%)
  - Marks best as 🏆 RECOMMENDED
  - Marks alternatives with ⚠️ ALTERNATIVE warnings
  - Clear action recommendations in position notes
- **Value:** Know which position to approve when same symbol appears multiple times

#### 5. **One-Click Bulk Approval** ✅
- **Files:** `api_bulk_actions.py`, `suggested_positions.html`, `urls_managed_trading.py`
- **Features:**
  - Purple button on Pending Review page
  - Auto-approves all EXCELLENT positions (score ≥95)
  - Distributes top 3-6 to client accounts
  - Creates batches and sends notifications
  - Updates page automatically
- **Time Savings:** 5 minutes → 2 seconds per batch!

#### 6. **Bug Fixes Applied:**
- ✅ Fixed all OptionPlayRawData field name mismatches
- ✅ Updated strategy_type choices to include spreads
- ✅ Fixed approval button (@staff_member_required)
- ✅ Fixed spread converter recognition (Bear Call vs Bull Put)
- ✅ Fixed list modification during iteration
- ✅ Fixed IV Rank percentage display (3200% → 32%)
- ✅ Fixed import error (PositionScoringService)
- ✅ Fixed rating recalculation after score boosts
- ✅ Fixed premium calculation for spreads
- ✅ Added database migrations (0013, 0014)

### **Database Changes:**
- Migration 0013: Added `notes` field to SuggestedPosition
- Migration 0014: Updated `strategy_type` choices and max_length=30

### **Files Modified:**
1. `coda/investing/models.py` - Updated OptionPlayRawData strategy choices
2. `coda/investing/views/managed_trading/csv_upload.py` - Added spread builder + Whales integration
3. `coda/investing/services/optionplay_converter.py` - Handle all spread types
4. `coda/investing/views/managed_trading/position_suggestions.py` - Fixed approval endpoint
5. `coda/investing/templates/investing/managed/csv_upload_step3.html` - Added automation checkboxes

### **New Files Created:**
1. `coda/investing/services/spread_builder.py` (450 lines)
2. `coda/investing/services/auto_approval_service.py` (500 lines)

### **Testing Required:**
- [x] Restart Django server
- [x] Upload Short Puts CSV
- [x] Verify spread conversion: 12/12 ✅
- [x] Verify SuggestedPosition shows "Bull Put Spread" ✅
- [x] Verify SuggestedPosition shows "Bear Call Spread" for Covered Calls ✅
- [ ] Verify auto-approval for scores ≥95 (EXCELLENT only)
- [ ] Verify distribution to accounts with <2 positions
- [ ] Test one-click bulk approval button
- [ ] Upload with Whales CSVs and verify scoring boosts

### **Known Issues (All Fixed):**
1. ✅ AttributeError 'strike' → Fixed to 'sell_strike'
2. ✅ AttributeError 'premium_total' → Fixed to 'premium'
3. ✅ list.remove() error → Fixed with delayed ID updates
4. ✅ PositionBatch field mismatches → Fixed to use correct model fields
5. ✅ Missing strategy_type choices → Added migration

### **Next Steps:**
1. User tests upload with new code
2. Verify all features working
3. Deploy to Heroku UAT
4. Client acceptance testing

---

## 🎯 PHASE 10: PORTFOLIO INTELLIGENCE & OPTIMIZATION
**Status:** 📋 Approved - Ready to Implement (Nov 5, 2025)  
**Timeline:** 4-5 weeks (Phased: 10A → 10B → 10C → 10D)

### **Phase 10A: Smart Position Ranking** (CURRENT - Week 1-2)
**Priority:** 🔴 CRITICAL | **Status:** ⏳ Starting Implementation

#### **New Service:** `PositionRankingService`
**File:** `coda/investing/services/position_ranking_service.py` (NEW - 400 lines est.)

**Purpose:** Multi-factor ranking algorithm to select top 5 positions from 20+ approved positions.

**Core Methods:**
```python
class PositionRankingService:
    """Intelligent position ranking using multi-factor analysis"""
    
    # Ranking weights (configurable)
    WHALES_WEIGHT = Decimal('0.35')  # 35%
    EARNINGS_WEIGHT = Decimal('0.25')  # 25%
    PROFIT_WEIGHT = Decimal('0.20')   # 20%
    DTE_WEIGHT = Decimal('0.20')      # 20%
    
    def rank_positions(self, positions: List[SuggestedPosition]) -> List[Dict]:
        """
        Rank positions using weighted multi-factor algorithm
        
        Returns:
            [{
                'position': SuggestedPosition,
                'total_score': Decimal,
                'breakdown': {
                    'whales_score': Decimal,
                    'earnings_score': Decimal,
                    'profit_score': Decimal,
                    'dte_score': Decimal
                },
                'rank': int,  # 1-N
                'recommendation': str  # "STRONG BUY", "BUY", etc.
            }]
        """
        
    def _score_whales_signal(self, position) -> Decimal:
        """Score: 0-100 based on Unusual Whales alignment"""
        
    def _score_earnings_safety(self, position) -> Decimal:
        """Score: 100 if safe, 0 if earnings before expiry"""
        
    def _score_profit_potential(self, position) -> Decimal:
        """Score: 0-100 based on ROC%"""
        
    def _score_dte_diversity(self, position, all_positions) -> Decimal:
        """Penalize clustering in same expiry week"""
        
    def get_top_n(self, ranked_positions, n=5) -> List[Dict]:
        """Select top N positions with diversity checks"""
```

**Integration Points:**
- **View:** `coda/investing/views/managed_trading/position_suggestions.py`
  - Add "🏆 Top 5 Recommended" section at top
  - Show ranking breakdown table
  - Add "Accept Top 5" button
  
- **Template:** `coda/investing/templates/investing/staff/suggested_positions.html`
  - Display ranked list with scores
  - Color-code by recommendation (green=strong, yellow=moderate)
  - Show why each position ranked high

**Database Changes:**
- No new models needed (uses existing `SuggestedPosition`)
- Add `ranking_score` and `ranking_breakdown` JSON fields (optional, for caching)

---

### **Phase 10B: LEAPS Conversion** (Week 2-3)
**Priority:** 🟡 HIGH | **Status:** 📋 Planned

#### **New Service:** `LEAPSConverterService`
**File:** `coda/investing/services/leaps_converter_service.py` (NEW - 350 lines est.)

**Purpose:** Convert long-dated options (60-365 DTE) to Bull Call Spreads when Whales signal is strong.

**Core Methods:**
```python
class LEAPSConverterService:
    """Convert LEAPS to Bull Call Spreads for capital efficiency"""
    
    MIN_DTE = 60
    MAX_DTE = 365
    MIN_WHALES_SIGNAL = 30  # Require strong bullish signal
    
    def should_convert(self, option_data: Dict) -> bool:
        """Determine if LEAPS should be converted to spread"""
        
    def convert_to_bull_call_spread(self, long_call: Dict) -> Dict:
        """
        Convert long call to Bull Call Spread
        
        Strategy:
        - BUY ATM call (from Whales data)
        - SELL 10-15% OTM call (estimate premium)
        - Net debit = capital required
        
        Returns position data for Bull Call Spread
        """
        
    def calculate_short_strike(self, long_strike, stock_price) -> Decimal:
        """Calculate optimal short call strike (12% OTM)"""
        
    def estimate_short_premium(self, strike, dte, iv) -> Decimal:
        """Estimate premium using Black-Scholes (fallback if no API)"""
```

**Integration:**
- **File:** `coda/investing/views/managed_trading/csv_upload.py`
  - Modify `_parse_unusual_whales_flow()` to detect LEAPS
  - Call `LEAPSConverterService` for DTE > 60
  - Show conversion summary ("15 LEAPS converted to spreads")

**Example Output:**
```
LEAPS Conversion Summary:
✅ Converted: 15 positions
   - NBIS $115 Call (319 DTE) → $115/$130 Bull Call Spread
   - META $650 Call (227 DTE) → $650/$700 Bull Call Spread
   ...
💰 Capital Savings: $42,500 (67% reduction)
```

---

### **Phase 10C: Portfolio Optimizer** (Week 3-4)
**Priority:** 🔴 CRITICAL | **Status:** 📋 Planned

#### **New Models:** `Portfolio` and `PortfolioPosition`

**File:** `coda/investing/models.py` (Add to existing)

```python
class Portfolio(TimeStampedModel):
    """Generated portfolio of 3-5 positions"""
    
    # Identification
    name = models.CharField(max_length=100)  # "Aggressive Growth"
    strategy_type = models.CharField(
        max_length=20,
        choices=[
            ('aggressive', 'Aggressive Growth'),
            ('balanced', 'Balanced Income'),
            ('conservative', 'Conservative Safety')
        ]
    )
    description = models.TextField()
    
    # Metrics
    total_capital = models.DecimalField(max_digits=12, decimal_places=2)
    expected_roc = models.DecimalField(max_digits=6, decimal_places=2)
    avg_pop = models.DecimalField(max_digits=5, decimal_places=2)
    max_profit = models.DecimalField(max_digits=12, decimal_places=2)
    max_loss = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Diversity
    sector_diversity_score = models.IntegerField()  # 0-100
    dte_range = models.JSONField()  # {'min': 28, 'max': 48}
    earnings_conflicts = models.IntegerField(default=0)
    
    # Whales
    whales_alignment_score = models.IntegerField()  # 0-100
    
    # AI Scoring
    ai_score = models.IntegerField()  # 0-100 (overall portfolio score)
    ai_recommendation_rank = models.IntegerField()  # 1, 2, or 3
    is_recommended = models.BooleanField(default=False)  # Winner
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('generated', 'Generated'),
            ('selected', 'Selected by Staff'),
            ('submitted', 'Submitted to Clients'),
            ('rejected', 'Rejected')
        ],
        default='generated'
    )

class PortfolioPosition(TimeStampedModel):
    """Link between Portfolio and SuggestedPosition"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    suggested_position = models.ForeignKey(SuggestedPosition, on_delete=models.CASCADE)
    allocation_pct = models.DecimalField(max_digits=5, decimal_places=2)  # % of portfolio
    selection_reason = models.TextField()  # Why this position was included
```

#### **New Service:** `PortfolioOptimizerService`
**File:** `coda/investing/services/portfolio_optimizer_service.py` (NEW - 600 lines est.)

**Core Methods:**
```python
class PortfolioOptimizerService:
    """Generate and compare 3 optimized portfolios"""
    
    def generate_portfolios(self, approved_positions, account_balance):
        """
        Create 3 distinct portfolios from approved positions
        
        Returns:
            {
                'aggressive': Portfolio,
                'balanced': Portfolio,
                'conservative': Portfolio,
                'comparison': ComparisonTable,
                'recommended': Portfolio  # Highest score
            }
        """
        
    def _build_aggressive_portfolio(self, positions, balance):
        """High ROC, Whales-driven, concentrated"""
        
    def _build_balanced_portfolio(self, positions, balance):
        """Diversified sectors, mixed DTE, moderate risk"""
        
    def _build_conservative_portfolio(self, positions, balance):
        """High PoP, max diversification, safety first"""
        
    def _score_portfolio(self, portfolio):
        """
        Score portfolio on 5 dimensions
        
        Returns:
            {
                'total': Decimal (0-100),
                'breakdown': {
                    'expected_return': Decimal,
                    'sharpe_ratio': Decimal,
                    'diversification': Decimal,
                    'whales_alignment': Decimal,
                    'capital_efficiency': Decimal
                }
            }
        """
```

**New Views:**
- **File:** `coda/investing/views/managed_trading/portfolio_optimizer.py` (NEW)
  - `portfolio_generator_view()` - Generate 3 portfolios
  - `portfolio_comparison_view()` - Side-by-side comparison
  - `portfolio_select_view()` - Submit selected portfolio

**New Templates:**
- `portfolio_generator.html` - Generate portfolios UI
- `portfolio_comparison.html` - 3-column comparison table
- `portfolio_detail.html` - Single portfolio breakdown

**New URLs:**
```python
# urls_managed_trading.py
path('portfolio/generate/', views.portfolio_generator_view, name='portfolio_generate'),
path('portfolio/compare/<int:batch_id>/', views.portfolio_comparison_view, name='portfolio_compare'),
path('portfolio/select/<int:portfolio_id>/', views.portfolio_select_view, name='portfolio_select'),
```

---

### **Phase 10D: Portfolio Hedging** (Week 4-5)
**Priority:** 🟡 MEDIUM | **Status:** 📋 Planned

#### **New Model:** `PortfolioHedge`

```python
class PortfolioHedge(TimeStampedModel):
    """Insurance positions for portfolio protection"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='hedges')
    
    # Hedge Details
    hedge_type = models.CharField(
        max_length=30,
        choices=[
            ('spy_put_spread', 'SPY Put Spread (Market)'),
            ('vix_call', 'VIX Call (Volatility)'),
            ('qqq_put_spread', 'QQQ Put Spread (Tech Sector)'),
            ('iwm_put_spread', 'IWM Put Spread (Small Cap)')
        ]
    )
    symbol = models.CharField(max_length=10)  # SPY, VIX, QQQ
    
    # Cost/Benefit
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    cost_pct = models.DecimalField(max_digits=5, decimal_places=2)  # % of portfolio
    max_protection = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Position Legs
    positions = models.JSONField()  # Hedge leg details
    
    # Analysis
    scenario_analysis = models.JSONField()  # Market down 5%, 10%, 20%
    recommended = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('recommended', 'Recommended'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('executed', 'Executed')
        ],
        default='recommended'
    )
```

#### **New Service:** `PortfolioHedgingService`
**File:** `coda/investing/services/portfolio_hedging_service.py` (NEW - 450 lines est.)

**Core Methods:**
```python
class PortfolioHedgingService:
    """Calculate and recommend portfolio insurance"""
    
    INSURANCE_BUDGET_MIN = Decimal('0.05')  # 5%
    INSURANCE_BUDGET_MAX = Decimal('0.10')  # 10%
    
    def analyze_portfolio_risk(self, portfolio):
        """Analyze exposure and recommend hedges"""
        
    def recommend_hedges(self, portfolio):
        """
        Returns list of recommended hedges
        
        [{
            'type': 'spy_put_spread',
            'cost': Decimal,
            'protection': Decimal,
            'reason': str,
            'required': bool
        }]
        """
        
    def calculate_spy_put_spread(self, portfolio_value):
        """SPY put spread for market crash protection"""
        
    def calculate_vix_call(self, portfolio_value, current_vix):
        """VIX call for volatility spike"""
        
    def calculate_sector_hedge(self, portfolio, sector):
        """Sector-specific put spread (QQQ, IWM, etc.)"""
        
    def simulate_scenarios(self, portfolio, hedges):
        """
        Simulate market scenarios
        
        Returns:
            {
                'market_down_5pct': {'unhedged': Decimal, 'hedged': Decimal},
                'market_down_10pct': {...},
                'vix_spike_to_60': {...}
            }
        """
```

**New View:**
- **File:** `coda/investing/views/managed_trading/portfolio_hedging.py` (NEW)
  - `portfolio_hedge_view()` - Show hedge recommendations
  - `portfolio_add_hedge_view()` - Add hedge to portfolio

**New Template:**
- `portfolio_hedging.html` - Insurance dashboard

---

## 📊 PHASE 10 IMPLEMENTATION SUMMARY

### **Files to Create (8 New Files):**
1. `coda/investing/services/position_ranking_service.py` (~400 lines)
2. `coda/investing/services/leaps_converter_service.py` (~350 lines)
3. `coda/investing/services/portfolio_optimizer_service.py` (~600 lines)
4. `coda/investing/services/portfolio_hedging_service.py` (~450 lines)
5. `coda/investing/views/managed_trading/portfolio_optimizer.py` (~300 lines)
6. `coda/investing/views/managed_trading/portfolio_hedging.py` (~200 lines)
7. `coda/investing/templates/investing/managed/portfolio_comparison.html` (~250 lines)
8. `coda/investing/templates/investing/managed/portfolio_hedging.html` (~200 lines)

**Total New Code:** ~2,750 lines

### **Files to Modify:**
1. `coda/investing/models.py` - Add Portfolio, PortfolioPosition, PortfolioHedge models
2. `coda/investing/admin.py` - Register new models
3. `coda/investing/views/managed_trading/position_suggestions.py` - Add ranking
4. `coda/investing/views/managed_trading/csv_upload.py` - Add LEAPS detection
5. `coda/investing/templates/investing/staff/suggested_positions.html` - Show rankings
6. `coda/investing/urls_managed_trading.py` - Add 5 new URLs

### **Migrations Needed:**
- **0015_add_portfolio_models.py** - Portfolio, PortfolioPosition, PortfolioHedge

### **Testing Requirements:**
See [05_TESTING.md](05_TESTING.md) for Phase 10 test plans.

### **Deployment Plan:**
See [07_DEPLOYMENT.md](07_DEPLOYMENT.md) for Phase 10 deployment strategy.

---

**Next Phase:** [05_TESTING.md](05_TESTING.md)  
**Previous Phase:** [03_ARCHITECTURE.md](03_ARCHITECTURE.md)  
**Return to:** [README.md](README.md)

