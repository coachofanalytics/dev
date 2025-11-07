# Managed Options Trading - Architecture
**Feature:** CODA Managed Options Trading Service  
**Date:** October 22, 2025  
**Status:** 🏗️ Architecture Design

---

## 🏗️ System Architecture Overview

### **High-Level Architecture**

```
┌──────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                                 │
│  ┌────────────────┐              ┌──────────────────┐            │
│  │ Client Portal  │              │  Trader Dashboard │            │
│  │ (Read-Only)    │              │  (Full Access)    │            │
│  └────────┬───────┘              └────────┬──────────┘            │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                               │
            └───────────┬───────────────────┘
                        │
┌───────────────────────▼───────────────────────────────────────────┐
│                   PRESENTATION LAYER                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Django Templates + jQuery + AJAX                           │  │
│  │  - method_selection.html, dashboard.html, reports.html     │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────┬───────────────────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────────────────┐
│                      VIEW LAYER                                    │
│  ┌─────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │ Account Views   │  │ Position Views │  │  Report Views   │   │
│  │ - Create        │  │ - Entry        │  │  - Daily        │   │
│  │ - List          │  │ - Exit         │  │  - Weekly       │   │
│  │ - Update        │  │ - Monitor      │  │  - Monthly      │   │
│  └────────┬────────┘  └────────┬───────┘  └────────┬────────┘   │
└───────────┼──────────────────────┼────────────────────┼───────────┘
            │                      │                     │
┌───────────▼──────────────────────▼─────────────────────▼──────────┐
│                     SERVICE LAYER                                  │
│  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Trading Service  │  │ Risk Mgmt Svc   │  │ Reporting Svc   │ │
│  │ - Entry logic    │  │ - Monitoring    │  │ - Statement gen │ │
│  │ - Exit logic     │  │ - Alert gen     │  │ - Fee calc      │ │
│  │ - Position calc  │  │ - Risk calc     │  │ - Performance   │ │
│  └────────┬─────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼──────────────────────┼────────────────────┼───────────┘
            │                      │                     │
┌───────────▼──────────────────────▼─────────────────────▼──────────┐
│                      MODEL LAYER                                   │
│  ┌──────────────────────┐  ┌────────────────────────────────┐   │
│  │ ManagedTradingAccount│  │     OptionsPosition            │   │
│  │ - Account data       │  │     - Position tracking        │   │
│  │ - Balance tracking   │  │     - P&L calculations         │   │
│  │ - Fee config         │  │     - Greeks                   │   │
│  └──────────────────────┘  └────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌────────────────────────────────┐   │
│  │    TradingRule       │  │    TradingActivity             │   │
│  │ - Risk limits        │  │    - Audit trail               │   │
│  │ - Profit targets     │  │    - Activity log              │   │
│  └──────────────────────┘  └────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  EXISTING MODELS (Reuse)                                  │   │
│  │  - Portfolio, RiskAssessment, RiskAlert                   │   │
│  │  - Options_Returns, InvestmentAnalytics                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────┬────────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────────┐
│                   DATABASE LAYER                                    │
│  PostgreSQL (Production/UAT) | SQLite (Local Development)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ♻️ Cross-App Reuse Inventory (Updated Nov 7, 2025)

| Component / Template | Current Location | Status | Leverage & Dedup Plan |
|----------------------|------------------|--------|-----------------------|
| `NotificationService` | `coda/notifications/services.py` | ✅ Implemented | Extend with scenario digest helpers; keep WhatsApp/email templates under `notifications/managed_income/` to avoid new service clones. |
| `stats_card.html` partial | `templates/shared/components/` | ✅ Implemented | Reuse for client income dashboard + staff heatmap summary; prohibit new bespoke cards in investing templates. |
| `PositionFetcherService` | `investing/services/position_fetcher_service.py` | ✅ Implemented | Wrap in `CapitalAllocationService` instead of duplicating fetch logic in Celery or views. |
| `UnusualWhalesService` | `investing/services/unusual_whales_service.py` | ✅ Implemented | Introduce caching decorator + bulk fetch method; mandate all apps call through service (no direct API calls). |
| `CommunicationLog` model | `communications/models.py` | ✅ Implemented | Log scenario digests + premium alerts here; avoid new per-app log tables. |
| `CapitalAllocationService` (new) | `investing/services/capital_allocation_service.py` | 🚀 Planned | Shared sizing rules for Celery task, dashboard preview, and scenario projections. |
| `audit_shared_templates` mgmt cmd | `core/management/commands/` | 🚀 Planned | Monthly run to detect duplicate templates across apps; feeds maintenance checklist. |

**Action Items:**
- Before adding UI fragments for strategy legs or preview modal, extract/extend partials in `templates/investing/shared/` to avoid duplication with `portfolio` app.
- Document any new helpers in `docs/apps/shared/STYLE_GUIDE.md` (create if missing) after first use.
- Enforce reuse by code review checklist (see 05_TESTING.md integration section for paths).

---

## 📊 Database Schema Design

### **New Models**

#### **Model 1: ManagedTradingAccount**

```python
class ManagedTradingAccount(TimeStampedModel):
    """
    Managed options trading account for clients
    Supports multiple accounts per platform
    """
    
    # ========== CLIENT INFORMATION ==========
    client = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Never delete if account exists
        related_name='managed_trading_accounts',
        help_text="Client who owns this account"
    )
    account_name = models.CharField(
        max_length=255,
        help_text="Friendly account name"
    )
    account_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique account identifier (CODA-OPT-XXX)"
    )
    
    # ========== FINANCIAL DATA ==========
    initial_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('5000.00'))],
        help_text="Starting account balance"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current total account value"
    )
    cash_available = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cash available for new positions"
    )
    cash_reserved = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cash reserved for open positions"
    )
    high_water_mark = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Highest account balance (for performance fees)"
    )
    
    # ========== MANAGEMENT ==========
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_accounts',
        help_text="CODA trader managing this account"
    )
    management_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.50'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Annual management fee percentage"
    )
    performance_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Performance fee percentage on profits"
    )
    performance_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('8.00'),
        help_text="Minimum return before performance fees apply"
    )
    
    # ========== RISK PARAMETERS ==========
    max_position_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Max risk per position (% of capital)"
    )
    max_total_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        help_text="Max total risk across all positions"
    )
    max_daily_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        help_text="Daily loss limit (% of capital)"
    )
    max_weekly_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Weekly loss limit (% of capital)"
    )
    max_monthly_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text="Monthly loss limit (% of capital)"
    )
    max_positions = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum concurrent positions"
    )
    
    # ========== STATUS & PERMISSIONS ==========
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending_setup', 'Pending Setup'),
            ('active', 'Active Trading'),
            ('paused', 'Trading Paused'),
            ('liquidating', 'Liquidating Positions'),
            ('closed', 'Account Closed')
        ],
        default='pending_setup'
    )
    trading_enabled = models.BooleanField(
        default=True,
        help_text="Allow new positions to be opened"
    )
    auto_trading_enabled = models.BooleanField(
        default=False,
        help_text="Enable automated trading decisions"
    )
    
    # ========== PERFORMANCE TRACKING ==========
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    total_profit_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_fees_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # ========== DATES ==========
    activation_date = models.DateField(null=True, blank=True)
    last_trade_date = models.DateField(null=True, blank=True)
    last_fee_calculation = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Managed Trading Account"
        verbose_name_plural = "Managed Trading Accounts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['account_manager', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    # ========== COMPUTED PROPERTIES ==========
    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0
        return round((self.winning_trades / self.total_trades) * 100, 2)
    
    @property
    def return_on_investment(self):
        """Calculate ROI percentage"""
        if self.initial_capital == 0:
            return 0
        return round((self.total_profit_loss / self.initial_capital) * 100, 2)
    
    @property
    def available_buying_power(self):
        """Calculate available buying power"""
        return self.cash_available - self.cash_reserved
    
    @property
    def profit_factor(self):
        """Calculate profit factor (gross profit / gross loss)"""
        # Calculate from TradingActivity records
        # Returns ratio of total profits to total losses
        pass
    
    def __str__(self):
        return f"{self.account_name} ({self.account_number})"
```

**Database Indexes:**
- Primary: `id` (auto)
- Composite: `client + status` (for client queries)
- Composite: `account_manager + status` (for manager queries)
- Composite: `status + created_at` (for listings)

---

#### **Model 2: OptionsPosition**

```python
class OptionsPosition(TimeStampedModel):
    """
    Individual options position within a managed account
    Supports single-leg and multi-leg strategies
    """
    
    # ========== ACCOUNT LINK ==========
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text="Parent managed account"
    )
    
    # ========== POSITION BASICS ==========
    symbol = models.CharField(
        max_length=10,
        help_text="Stock ticker symbol"
    )
    strategy = models.CharField(
        max_length=30,
        choices=[
            ('short_put', 'Cash-Secured Put'),
            ('covered_call', 'Covered Call'),
            ('bull_put_spread', 'Bull Put Spread'),
            ('bear_call_spread', 'Bear Call Spread'),
            ('iron_condor', 'Iron Condor'),
            ('long_call', 'Long Call'),
            ('long_put', 'Long Put'),
            ('short_strangle', 'Short Strangle'),
            ('short_straddle', 'Short Straddle')
        ],
        help_text="Options strategy type"
    )
    
    # ========== POSITION LEGS (JSONFIELD) ==========
    positions = models.JSONField(
        default=list,
        help_text="Array of position legs"
    )
    # Example structure:
    # [
    #   {
    #     'type': 'short_put',
    #     'strike': 170.00,
    #     'contracts': 1,
    #     'premium': 300.00,
    #     'delta': -0.30,
    #     'theta': 0.15
    #   },
    #   {
    #     'type': 'long_put',
    #     'strike': 165.00,
    #     'contracts': 1,
    #     'cost': 150.00,
    #     'delta': -0.20,
    #     'theta': -0.10
    #   }
    # ]
    
    # ========== FINANCIAL METRICS ==========
    capital_required = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total capital required/at risk"
    )
    premium_collected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Net premium collected (credit strategies)"
    )
    premium_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Premium paid (debit strategies)"
    )
    max_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum possible profit"
    )
    max_loss = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum possible loss"
    )
    
    # ========== GREEKS ==========
    position_delta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position delta"
    )
    position_theta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position theta (time decay)"
    )
    position_gamma = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position gamma"
    )
    position_vega = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position vega (volatility sensitivity)"
    )
    
    # ========== DATES ==========
    entry_date = models.DateField(
        auto_now_add=True,
        help_text="Date position was opened"
    )
    expiration_date = models.DateField(
        help_text="Options expiration date"
    )
    exit_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date position was closed"
    )
    
    # ========== STATUS & PERFORMANCE ==========
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('closed', 'Closed'),
            ('assigned', 'Assigned'),
            ('expired_worthless', 'Expired Worthless'),
            ('rolled', 'Rolled to Next Cycle')
        ],
        default='open'
    )
    
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current market value of position"
    )
    realized_pnl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Profit/loss after closing"
    )
    unrealized_pnl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current profit/loss (open positions)"
    )
    
    # ========== EXIT INFORMATION ==========
    exit_reason = models.CharField(
        max_length=30,
        choices=[
            ('profit_target', 'Profit Target Reached'),
            ('stop_loss', 'Stop Loss Hit'),
            ('expiration', 'Natural Expiration'),
            ('assignment', 'Early Assignment'),
            ('manual', 'Manual Close'),
            ('risk_reduction', 'Risk Reduction'),
            ('market_condition', 'Market Condition Change'),
            ('roll', 'Rolled to Next Expiration')
        ],
        null=True,
        blank=True
    )
    exit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price at which position was closed"
    )
    
    # ========== METADATA ==========
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Trading notes and rationale"
    )
    entry_market_conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Market conditions at entry"
    )
    # Example: {
    #   'stock_price': 180.50,
    #   'iv_rank': 45,
    #   'market_trend': 'bullish',
    #   'rsi': 55
    # }
    
    class Meta:
        verbose_name = "Options Position"
        verbose_name_plural = "Options Positions"
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['managed_account', 'status']),
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['expiration_date', 'status']),
            models.Index(fields=['strategy', 'status']),
        ]
    
    # ========== COMPUTED PROPERTIES ==========
    @property
    def days_in_trade(self):
        """Calculate days position has been open"""
        if self.exit_date:
            return (self.exit_date - self.entry_date).days
        return (date.today() - self.entry_date).days
    
    @property
    def days_to_expiration(self):
        """Calculate days until expiration"""
        return (self.expiration_date - date.today()).days
    
    @property
    def is_profitable(self):
        """Check if position is profitable"""
        if self.status == 'open':
            return self.unrealized_pnl > 0
        return self.realized_pnl > 0
    
    @property
    def profit_percentage(self):
        """Calculate profit percentage"""
        if self.status == 'open':
            pnl = self.unrealized_pnl
        else:
            pnl = self.realized_pnl
        
        if self.capital_required == 0:
            return 0
        return round((pnl / self.capital_required) * 100, 2)
    
    @property
    def profit_target_percentage(self):
        """Calculate percentage of max profit achieved"""
        if self.max_profit == 0:
            return 0
        
        pnl = self.unrealized_pnl if self.status == 'open' else self.realized_pnl
        return round((pnl / self.max_profit) * 100, 2)
    
    def __str__(self):
        return f"{self.symbol} {self.strategy} ({self.expiration_date})"
```

**Database Indexes:**
- Primary: `id`
- Foreign Key: `managed_account_id`
- Composite: `managed_account + status` (for account queries)
- Composite: `expiration_date + status` (for expiration alerts)
- Single: `symbol`, `strategy`, `status`

---

#### **Model 3: TradingRule**

```python
class TradingRule(TimeStampedModel):
    """
    Configurable trading rules for managed accounts
    Enforces risk limits and trading constraints
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='trading_rules'
    )
    
    rule_name = models.CharField(max_length=100)
    rule_type = models.CharField(
        max_length=30,
        choices=[
            ('position_limit', 'Position Size Limit'),
            ('risk_limit', 'Risk Limit'),
            ('exposure_limit', 'Exposure Limit'),
            ('profit_target', 'Profit Target'),
            ('stop_loss', 'Stop Loss'),
            ('time_based', 'Time-Based Rule'),
            ('greek_limit', 'Greek Limit'),
            ('sector_limit', 'Sector Exposure Limit')
        ]
    )
    
    rule_config = models.JSONField(
        default=dict,
        help_text="Rule configuration parameters"
    )
    # Example configurations:
    # Position Limit: {'max_position_size': 7000, 'max_contracts': 3}
    # Profit Target: {'target_percentage': 50, 'auto_close': True}
    # Stop Loss: {'loss_percentage': 200, 'auto_close': True}
    # Greek Limit: {'max_delta': 100, 'max_theta': -50}
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=1,
        help_text="Rule priority (1 = highest)"
    )
    violations_count = models.IntegerField(default=0)
    last_violation = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Trading Rule"
        verbose_name_plural = "Trading Rules"
        ordering = ['priority', 'rule_name']
        indexes = [
            models.Index(fields=['managed_account', 'is_active']),
            models.Index(fields=['rule_type']),
        ]
    
    def validate_position(self, position_data):
        """Validate a position against this rule"""
        # Implementation in service layer
        pass
    
    def __str__(self):
        return f"{self.rule_name} ({self.managed_account.account_name})"
```

---

#### **Model 4: TradingActivity**

```python
class TradingActivity(TimeStampedModel):
    """
    Activity log for all trading actions
    Provides complete audit trail
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    position = models.ForeignKey(
        OptionsPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    
    activity_type = models.CharField(
        max_length=30,
        choices=[
            ('account_created', 'Account Created'),
            ('account_modified', 'Account Modified'),
            ('position_opened', 'Position Opened'),
            ('position_closed', 'Position Closed'),
            ('position_adjusted', 'Position Adjusted'),
            ('alert_triggered', 'Alert Triggered'),
            ('rule_violated', 'Rule Violated'),
            ('fee_calculated', 'Fee Calculated'),
            ('report_generated', 'Report Generated'),
            ('manual_action', 'Manual Action')
        ]
    )
    
    description = models.TextField()
    
    data_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of relevant data at time of activity"
    )
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='trading_activities'
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Trading Activity"
        verbose_name_plural = "Trading Activities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['managed_account', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['performed_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
```

---

## 🔧 Service Layer Architecture

### **Service 1: ManagedTradingService**

```python
class ManagedTradingService(BaseInvestingService):
    """
    Core service for managed trading operations
    """
    
    def create_managed_account(self, client, account_data):
        """
        Create new managed trading account
        
        Args:
            client: User instance
            account_data: Dict with account parameters
        
        Returns:
            ManagedTradingAccount instance
        """
        pass
    
    def calculate_fees(self, account, period='monthly'):
        """
        Calculate management and performance fees
        
        Args:
            account: ManagedTradingAccount instance
            period: 'monthly', 'quarterly', or 'annual'
        
        Returns:
            Dict with fee breakdown
        """
        pass
    
    def get_account_summary(self, account):
        """
        Get comprehensive account summary
        
        Returns:
            Dict with account metrics
        """
        pass
    
    def check_trading_capacity(self, account, proposed_position):
        """
        Check if account can support new position
        
        Returns:
            Bool, List of violations (if any)
        """
        pass
```

---

### **Service 2: OptionsPositionService**

```python
class OptionsPositionService(BaseInvestingService):
    """
    Service for options position management
    """
    
    def create_position(self, account, position_data):
        """
        Create new options position
        
        Validates:
        - Account has buying power
        - Position meets risk limits
        - Position meets trading rules
        
        Returns:
            OptionsPosition instance or ValidationError
        """
        pass
    
    def close_position(self, position, exit_price, exit_reason):
        """
        Close an options position
        
        Calculates:
        - Final P&L
        - Updates account balance
        - Records exit details
        
        Returns:
            Updated OptionsPosition instance
        """
        pass
    
    def update_position_value(self, position, current_market_price):
        """
        Update position's current value and unrealized P&L
        
        Returns:
            Updated OptionsPosition instance
        """
        pass
    
    def should_close_position(self, position):
        """
        Evaluate if position should be closed
        
        Checks:
        - Profit target reached
        - Stop loss hit
        - Expiration approaching
        - Delta shifted
        
        Returns:
            Bool, List of reasons
        """
        pass
    
    def calculate_position_greeks(self, position):
        """
        Calculate net position greeks
        
        Returns:
            Dict with delta, theta, gamma, vega
        """
        pass
```

---

### **Service 3: RiskMonitoringService**

```python
class RiskMonitoringService(BaseInvestingService):
    """
    Real-time risk monitoring for managed accounts
    """
    
    def monitor_position(self, position):
        """
        Check position against risk parameters
        
        Returns:
            List of alerts (if any)
        """
        pass
    
    def monitor_account(self, account):
        """
        Check account-level risk metrics
        
        Returns:
            List of account-level alerts
        """
        pass
    
    def check_daily_loss_limit(self, account):
        """
        Check if account exceeded daily loss limit
        
        Returns:
            Bool, Current loss percentage
        """
        pass
    
    def aggregate_portfolio_risk(self, account):
        """
        Calculate total portfolio risk exposure
        
        Returns:
            Dict with risk metrics
        """
        pass
    
    def generate_risk_alert(self, account, position, alert_data):
        """
        Create risk alert and notify stakeholders
        
        Returns:
            RiskAlert instance
        """
        pass
```

---

### **Service 4: ReportingService**

```python
class ManagedTradingReportingService(BaseInvestingService):
    """
    Report generation for managed trading accounts
    """
    
    def generate_daily_summary(self, account):
        """
        Generate daily email summary
        
        Includes:
        - Current positions
        - Today's P&L
        - Any alerts
        - Upcoming expirations
        
        Returns:
            HTML email content
        """
        pass
    
    def generate_weekly_report(self, account):
        """
        Generate weekly performance report
        
        Includes:
        - Week's P&L
        - Positions opened/closed
        - Win rate
        - Performance chart
        
        Returns:
            HTML email content
        """
        pass
    
    def generate_monthly_statement(self, account):
        """
        Generate comprehensive monthly statement
        
        Includes:
        - Full position history
        - Performance analysis
        - Fee breakdown
        - Tax information
        - Comparison to benchmarks
        
        Returns:
            PDF document
        """
        pass
    
    def calculate_fees_for_period(self, account, start_date, end_date):
        """
        Calculate fees for specific period
        
        Returns:
            Dict with management and performance fees
        """
        pass
```

---

## 🔄 Workflow Architecture

### **Position Entry Workflow**

```
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Trader Identifies Opportunity                   │
│ - Market scan or manual analysis                        │
│ - Check symbol, strategy, entry criteria                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ STEP 2: Position Entry Form                             │
│ - Select managed account                                │
│ - Enter position details (symbol, strike, etc.)         │
│ - System calculates risk/reward                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ STEP 3: Pre-Trade Validation                            │
│ ✓ Account has sufficient buying power                   │
│ ✓ Position doesn't exceed risk limits                   │
│ ✓ Complies with trading rules                           │
│ ✓ No duplicate positions on symbol                      │
│ ✓ Greeks within acceptable range                        │
└────────────────────┬────────────────────────────────────┘
                     │
                ┌────▼────┐
                │ Valid?  │
                └─┬────┬──┘
           NO     │    │     YES
    ┌─────────────┘    └─────────────┐
    │                                 │
┌───▼──────────────────┐   ┌─────────▼────────────────────┐
│ Show Validation Error│   │ STEP 4: Execute Trade         │
│ - Display violations │   │ - Create OptionsPosition      │
│ - Allow corrections  │   │ - Reserve capital             │
│ - Re-validate        │   │ - Update account balance      │
└──────────────────────┘   │ - Log TradingActivity         │
                           │ - Generate confirmation       │
                           └─────────┬────────────────────┘
                                     │
                          ┌──────────▼────────────────────┐
                          │ STEP 5: Post-Trade Actions    │
                          │ - Send confirmation email     │
                          │ - Update dashboard            │
                          │ - Setup monitoring alerts     │
                          │ - Notify client (if configured)│
                          └───────────────────────────────┘
```

---

### **Position Monitoring Workflow**

```
┌─────────────────────────────────────────────────────────┐
│ CRON JOB: Run Every 15 Minutes During Market Hours      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ FOR EACH Active ManagedTradingAccount:                  │
│   FOR EACH Open OptionsPosition:                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 1. Fetch Current Market Data                            │
│ - Get current stock price                               │
│ - Get current option prices (if API available)          │
│ - Calculate current position value                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 2. Update Position Metrics                              │
│ - current_value = calculated from market data           │
│ - unrealized_pnl = current_value - entry_value          │
│ - profit_percentage = unrealized_pnl / capital * 100    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 3. Check Exit Criteria                                  │
│ ✓ Profit target (50% of max profit)                     │
│ ✓ Stop loss (200% of premium)                           │
│ ✓ Days to expiration (<= 5)                             │
│ ✓ Delta shift (> 0.50)                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                ┌────▼────┐
                │Criteria │
                │  Met?   │
                └─┬────┬──┘
           NO     │    │     YES
    ┌─────────────┘    └─────────────┐
    │                                 │
┌───▼──────────────┐      ┌──────────▼───────────────────┐
│ Continue Monitor │      │ 4. Generate Alert             │
│ - No action      │      │ - Create RiskAlert record     │
└──────────────────┘      │ - Send email to trader        │
                          │ - Dashboard notification      │
                          │ - Log activity                │
                          └──────────┬───────────────────┘
                                     │
                          ┌──────────▼───────────────────┐
                          │ 5. Auto-Close (if configured) │
                          │ OR                            │
                          │ Await Trader Action           │
                          └───────────────────────────────┘
```

---

## 🎨 User Interface Architecture

### **Admin/Trader Interface**

```
┌──────────────────────────────────────────────────────────┐
│                  MAIN DASHBOARD                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │All Accounts │ │All Positions│ │   Alerts    │       │
│  │   Summary   │ │   Summary   │ │  Requiring  │       │
│  │             │ │             │ │   Action    │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ACCOUNTS TABLE                                    │  │
│  │  Account | Client | Balance | P&L | Positions     │  │
│  │  ──────────────────────────────────────────────    │  │
│  │  CODA-OPT-001 | John D | $31,500 | +$1,500 | 3   │  │
│  │  CODA-OPT-002 | Jane S | $48,200 | -$800 | 5     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  OPEN POSITIONS TABLE                              │  │
│  │  Symbol|Strategy|DTE|P&L|Status|Actions            │  │
│  │  ─────────────────────────────────────────────     │  │
│  │  AAPL | Short Put | 12 | +$150 | 🟢 | [Close][✏️] │  │
│  │  MSFT | Bull Spread | 25 | +$75 | 🟢 | [Close][✏️]│  │
│  │  GOOGL| Cover Call | 5 | +$80 | 🟡 | [Close][✏️] │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  [+ New Position] [📊 Analytics] [📧 Reports]           │
└──────────────────────────────────────────────────────────┘
```

---

### **Client Portal Interface**

```
┌──────────────────────────────────────────────────────────┐
│              CLIENT DASHBOARD (Read-Only)                 │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Balance  │ │ Total P&L │ │ Monthly  │ │  Open    │  │
│  │ $31,500  │ │  +$1,500  │ │ Return   │ │Positions │  │
│  │   📈     │ │    🟢     │ │  +5.0%   │ │    3     │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  CURRENT POSITIONS                                 │  │
│  │  Symbol | Strategy | Entry | Expiry | P&L         │  │
│  │  ─────────────────────────────────────────────     │  │
│  │  AAPL   | Short Put | Oct 20 | Nov 22 | +$150    │  │
│  │  MSFT   | Spread    | Oct 18 | Nov 15 | +$75     │  │
│  │  GOOGL  | Cov Call  | Oct 15 | Nov 10 | +$80     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  PERFORMANCE CHART                                 │  │
│  │  (Line chart showing account value over time)     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  [📄 Monthly Statements] [💰 Fee Breakdown] [📞 Contact]│
└──────────────────────────────────────────────────────────┘
```

---

## 🔌 API Architecture

### **Internal APIs (for AJAX)**

#### **API Endpoint Plan:**

```
GET  /investing/managed/api/accounts/              # List all accounts
POST /investing/managed/api/accounts/              # Create account
GET  /investing/managed/api/accounts/<id>/         # Account details
PUT  /investing/managed/api/accounts/<id>/         # Update account

GET  /investing/managed/api/positions/             # List positions
POST /investing/managed/api/positions/             # Create position
GET  /investing/managed/api/positions/<id>/        # Position details
PUT  /investing/managed/api/positions/<id>/close/  # Close position

GET  /investing/managed/api/monitoring/<account_id>/ # Get monitoring data
GET  /investing/managed/api/alerts/<account_id>/     # Get active alerts
POST /investing/managed/api/alerts/<id>/resolve/     # Resolve alert

GET  /investing/managed/api/performance/<account_id>/ # Performance metrics
GET  /investing/managed/api/fees/<account_id>/        # Fee calculations
```

#### **Response Format:**

```json
{
    "status": "success",
    "data": {
        "account": {
            "id": 1,
            "account_number": "CODA-OPT-001",
            "current_balance": "31500.00",
            "total_pnl": "1500.00",
            "roi_percentage": "5.00"
        }
    },
    "meta": {
        "timestamp": "2025-10-22T14:30:00Z",
        "request_id": "abc-123-def"
    }
}
```

---

## 🔐 Security Architecture

### **Authentication Flow**

```
User Login
    │
    ├─> Django Session Authentication
    │
    ├─> Role Check:
    │   ├─> Super Admin: Full access
    │   ├─> Account Manager: Access assigned accounts
    │   ├─> Client: Access own account (read-only)
    │   └─> Auditor: Read-only all accounts
    │
    └─> Permission Granted
        │
        └─> CSRF Token Required for all POST/PUT/DELETE
```

### **Data Access Control**

```python
# View-level permission checking
@login_required
def managed_account_detail(request, account_id):
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    # Super admin: Can access any account
    if request.user.is_superuser:
        pass
    
    # Account manager: Can access assigned accounts
    elif account.account_manager == request.user:
        pass
    
    # Client: Can access own account
    elif account.client == request.user:
        pass
    
    # Everyone else: Denied
    else:
        return HttpResponseForbidden("Access denied")
    
    return render(request, 'investing/managed/account_detail.html', {'account': account})
```

---

## 📡 External Integration Architecture

### **Market Data Integration**

```
┌────────────────────────────────────────────┐
│  Market Data Providers (Priority Order)    │
├────────────────────────────────────────────┤
│  1. yfinance (Free, 15-min delay) ✅       │
│  2. Alpha Vantage (Freemium)               │
│  3. Polygon.io (Paid, institutional)       │
│  4. Interactive Brokers API (Best)         │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│  Data Fetching Service                     │
│  - Try primary source                      │
│  - Fallback to secondary if fails          │
│  - Cache successful responses              │
│  - Return error if all fail                │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│  Data Cache Layer (15-min TTL)             │
│  - Redis cache (if available)              │
│  - Django cache fallback                   │
│  - Database cache as last resort           │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│  Application Layer                         │
│  - Use cached data for calculations        │
│  - Update positions with latest prices     │
│  - Generate alerts based on new data       │
└────────────────────────────────────────────┘
```

---

## 🗄️ Data Flow Architecture

### **Position Lifecycle Data Flow**

```
Position Created
    │
    ├─> Save to OptionsPosition table
    │
    ├─> Update ManagedTradingAccount:
    │   ├─> cash_available -= capital_required
    │   ├─> cash_reserved += capital_required
    │   └─> total_trades += 1
    │
    ├─> Create TradingActivity record
    │
    └─> Send confirmation email

Position Updated (every 15 min)
    │
    ├─> Fetch market data
    │
    ├─> Calculate current_value
    │
    ├─> Update unrealized_pnl
    │
    ├─> Check alert criteria
    │
    └─> Generate alerts (if needed)

Position Closed
    │
    ├─> Update OptionsPosition:
    │   ├─> status = 'closed'
    │   ├─> exit_date = today
    │   ├─> exit_price = close_price
    │   ├─> realized_pnl = final calculation
    │   └─> exit_reason = reason
    │
    ├─> Update ManagedTradingAccount:
    │   ├─> cash_available += (capital + pnl)
    │   ├─> cash_reserved -= capital_required
    │   ├─> current_balance += pnl
    │   ├─> total_profit_loss += pnl
    │   ├─> winning_trades += 1 (if profitable)
    │   └─> losing_trades += 1 (if loss)
    │
    ├─> Create TradingActivity record
    │
    ├─> Update high_water_mark (if new high)
    │
    └─> Send closure notification
```

---

## 🚀 Technology Stack

### **Backend**
- **Framework**: Django 4.x
- **Database**: PostgreSQL (Production/UAT), SQLite (Local)
- **ORM**: Django ORM
- **Caching**: Redis (optional), Django cache
- **Task Queue**: Celery (for scheduled tasks)
- **Background Jobs**: Django-cron or Celery Beat

### **Frontend**
- **Framework**: Django Templates
- **JavaScript**: jQuery 3.6.0
- **AJAX**: jQuery.ajax()
- **Charts**: Chart.js or similar
- **UI**: Bootstrap 5 (existing)
- **Icons**: Font Awesome (existing)

### **External Services**
- **Market Data**: yfinance (primary), Alpha Vantage (backup)
- **Email**: Django email backend (existing)
- **File Storage**: Local/S3 for statements
- **Monitoring**: Django logging (existing)

---

## 📊 Performance Architecture

### **Database Optimization**

```python
# Efficient Queries
accounts = ManagedTradingAccount.objects.filter(
    status='active'
).select_related('client', 'account_manager').prefetch_related('positions')

# Aggregation
summary = accounts.aggregate(
    total_aum=Sum('current_balance'),
    total_pnl=Sum('total_profit_loss'),
    total_positions=Count('positions')
)

# Indexes
class ManagedTradingAccount(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['account_manager', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
```

### **Caching Strategy**

```python
from django.core.cache import cache

# Cache market data (15 min)
def get_stock_price(symbol):
    cache_key = f'price_{symbol}'
    price = cache.get(cache_key)
    
    if not price:
        price = fetch_from_api(symbol)
        cache.set(cache_key, price, 900)  # 15 min cache
    
    return price

# Cache account summary (5 min)
def get_account_summary(account_id):
    cache_key = f'account_summary_{account_id}'
    summary = cache.get(cache_key)
    
    if not summary:
        summary = calculate_account_summary(account_id)
        cache.set(cache_key, summary, 300)  # 5 min cache
    
    return summary
```

---

## 🔧 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   Templates  │  │     Forms    │  │   JavaScript   │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                       VIEW LAYER                             │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Account   │ │ Position  │ │   Risk   │ │ Reporting│   │
│  │   Views    │ │   Views   │ │  Views   │ │  Views   │   │
│  └────────────┘ └───────────┘ └──────────┘ └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     SERVICE LAYER                            │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │ Trading Service  │  │ Risk Monitoring Service      │    │
│  │ - create_pos()   │  │ - monitor_positions()        │    │
│  │ - close_pos()    │  │ - check_limits()             │    │
│  │ - calc_pnl()     │  │ - generate_alerts()          │    │
│  └──────────────────┘  └──────────────────────────────┘    │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │ Reporting Svc    │  │ Market Data Service          │    │
│  │ - daily_report() │  │ - fetch_prices()             │    │
│  │ - monthly_stmt() │  │ - fetch_options_chain()      │    │
│  │ - calc_fees()    │  │ - calculate_greeks()         │    │
│  └──────────────────┘  └──────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      MODEL LAYER                             │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │ManagedTradingAccount │  │   OptionsPosition        │    │
│  └──────────────────────┘  └──────────────────────────┘    │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │   TradingRule        │  │   TradingActivity        │    │
│  └──────────────────────┘  └──────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REUSED MODELS: Portfolio, RiskAssessment, etc       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    DATABASE LAYER                            │
│                     PostgreSQL                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Integration Architecture

### **Integration with Existing CODA Apps**

```
┌────────────────────────────────────────────────────────┐
│          Managed Options Trading App                   │
└────────────┬───────────────────────┬───────────────────┘
             │                       │
    ┌────────▼──────┐       ┌────────▼──────────┐
    │  Finance App  │       │   Accounts App    │
    │               │       │                   │
    │ Payment_Info  │◄──────┤  CustomerUser     │
    │ Transaction   │       │  Permissions      │
    │ Fee Billing   │       │  Authentication   │
    └───────────────┘       └───────────────────┘
```

**Integration Points:**
1. **Accounts App**:
   - Use `CustomerUser` for client and manager
   - Leverage existing authentication
   - Use permission system

2. **Finance App**:
   - Create `Payment_Information` records for fee billing
   - Record fees as `Transaction` entries
   - Link to main investor account

3. **Investing App**:
   - Reuse `Portfolio` model for position tracking
   - Leverage `RiskAssessment` and `RiskAlert`
   - Use `InvestmentAnalytics` for performance

---

## 📞 Communication Architecture

### **Notification System**

```
┌────────────────────────────────────────────┐
│         Notification Triggers              │
│  - Position opened                         │
│  - Position closed                         │
│  - Profit target reached                   │
│  - Stop loss hit                           │
│  - Daily summary (scheduled)               │
│  - Weekly report (scheduled)               │
│  - Monthly statement (scheduled)           │
└────────────┬───────────────────────────────┘
             │
┌────────────▼───────────────────────────────┐
│    Notification Router                     │
│    - Determine recipients                  │
│    - Check notification preferences        │
│    - Select channels (email/SMS/dashboard) │
└────────────┬───────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──────┐   ┌─────▼──────┐
│  Email   │   │ Dashboard  │
│  Service │   │ Notification│
│          │   │   Badge    │
└──────────┘   └────────────┘
```

---

## 🎯 Decision Flow Architecture

### **Trade Entry Decision Flow**

```
Opportunity Identified
    │
    ├─> Fetch Market Data
    │   ├─> Current stock price
    │   ├─> Options chain data
    │   ├─> IV Rank
    │   └─> Technical indicators
    │
    ├─> Evaluate Entry Criteria
    │   ├─> IV Rank > 30%? ✓
    │   ├─> Stock price trend? ✓
    │   ├─> DTE in range (30-45)? ✓
    │   ├─> No earnings within expiry? ✓
    │   └─> Delta in target range? ✓
    │
    ├─> Calculate Position Metrics
    │   ├─> Capital required
    │   ├─> Max profit
    │   ├─> Max loss
    │   ├─> Risk/reward ratio
    │   └─> Expected return
    │
    ├─> Validate Against Rules
    │   ├─> Check buying power
    │   ├─> Check position size limit
    │   ├─> Check total risk limit
    │   ├─> Check max positions
    │   └─> Check sector exposure
    │
    └─> Decision
        ├─> ✅ ALL PASS → Execute Trade
        └─> ❌ ANY FAIL → Reject with reason
```

### **Trade Exit Decision Flow**

```
Position Monitoring (every 15 min)
    │
    ├─> Update Current Value
    │
    ├─> Calculate Unrealized P&L
    │
    ├─> Check Exit Criteria:
    │   │
    │   ├─> Profit >= 50% of max? ──────► ✅ CLOSE (Profit Target)
    │   │
    │   ├─> Loss >= 200% of premium? ───► ✅ CLOSE (Stop Loss)
    │   │
    │   ├─> DTE <= 5 days? ─────────────► ✅ CLOSE (Expiration Risk)
    │   │
    │   ├─> Delta > 0.50? ──────────────► ⚠️ ALERT (Delta Shift)
    │   │
    │   └─> None met ───────────────────► Continue Monitoring
    │
    └─> If close triggered:
        │
        ├─> Generate alert
        ├─> Execute close (if auto-enabled)
        ├─> OR notify trader for approval
        └─> Log activity
```

---

## 🔒 Backup & Recovery Architecture

### **Backup Strategy**

```
Daily Automated Backup (2:00 AM)
    │
    ├─> Database Backup
    │   ├─> Full PostgreSQL dump
    │   ├─> Store in S3 or local
    │   └─> Retention: 30 days
    │
    ├─> File Backup
    │   ├─> Backup uploaded documents
    │   ├─> Backup generated reports
    │   └─> Retention: 90 days
    │
    └─> Verification
        ├─> Test backup integrity
        ├─> Log backup status
        └─> Alert if backup fails
```

### **Disaster Recovery**

```
System Failure Detected
    │
    ├─> Automatic Failover
    │   ├─> Switch to backup database
    │   ├─> Redirect traffic
    │   └─> Notify admin
    │
    └─> Manual Recovery (if needed)
        ├─> Restore from latest backup
        ├─> Verify data integrity
        ├─> Resume operations
        └─> Document incident
```

---

## 📈 Scalability Architecture

### **Scaling Plan**

| Stage | Clients | Positions | Architecture Changes |
|-------|---------|-----------|---------------------|
| **Stage 1** | 1-5 | <50 | Current architecture sufficient |
| **Stage 2** | 5-25 | 50-250 | Add Redis caching, database read replicas |
| **Stage 3** | 25-100 | 250-1000 | Load balancer, multiple app servers |
| **Stage 4** | 100+ | 1000+ | Microservices, dedicated options service |

### **Performance Optimization Points**

```python
# Query Optimization
accounts = ManagedTradingAccount.objects.filter(
    status='active'
).select_related(
    'client',
    'account_manager'
).prefetch_related(
    'positions',
    'trading_rules',
    'activities'
).only(
    'id', 'account_number', 'current_balance',
    'total_profit_loss', 'client__username'
)

# Caching
@cache_page(60)  # Cache view for 60 seconds
def account_dashboard(request, account_id):
    pass

# Database Indexes
class Meta:
    indexes = [
        models.Index(fields=['client', 'status']),
        models.Index(fields=['status', '-created_at']),
    ]
```

---

## 🎉 Architecture Summary

### **Key Design Principles**

1. **Separation of Concerns**
   - Models handle data structure
   - Services handle business logic
   - Views handle HTTP requests
   - Templates handle presentation

2. **Reusability**
   - Leverage 80% of existing investing app
   - Add 20% managed-account-specific code
   - Share services across features

3. **Security First**
   - Role-based access control
   - Data isolation per client
   - Complete audit trail
   - Encryption of sensitive data

4. **Scalability**
   - Database optimization
   - Caching strategies
   - Efficient queries
   - Can grow to 100+ clients

5. **Maintainability**
   - Clear code organization
   - Comprehensive documentation
   - Unit tests
   - Service layer abstraction

---

**Next Phase:** [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)  
**Previous Phase:** [02_REQUIREMENTS.md](02_REQUIREMENTS.md)  
**Return to:** [README.md](README.md)

