from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Investments,
    Investment_rates,
    Investor_Information,
    ShortPut,
    Portfolio,
    InvestmentsStrategy,
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingSession,
)


class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor_Information
        fields = ["model_type", "amount_invested", "duration"]


class InvestmentRateForm(forms.ModelForm):
    class Meta:
        model = Investment_rates
        fields = ["name", "base_amount", "duration"]
        # fields = "__all__"


class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investments
        fields = ["amount", "description"]
        # fields = "__all__"


class InvestmentsStrategyForm(forms.ModelForm):
    class Meta:
        model = InvestmentsStrategy
        fields = "__all__"


class OptionsForm(forms.ModelForm):
    on_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Date"
    )

    class Meta:
        model = ShortPut
        # fields = '__all__'
        fields = ["symbol", "comment", "on_date", "is_featured"]


class PortfolioForm(forms.ModelForm):
    # user = forms.CharField(widget = forms.HiddenInput(), required = False)
    # action = forms.CharField(widget=forms.HiddenInput(),)
    # implied_volatility_rank = forms.CharField(widget=forms.HiddenInput(),)
    earnings_date = forms.CharField(
        widget=forms.HiddenInput(),
    )
    symbol = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    industry = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    # strike_price = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    condition = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    # strategy = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # expiry = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    on_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Date"
    )
    is_active = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = Portfolio
        # fields = '__all__'
        fields = [
            "symbol",
            "industry",
            "action",
            "condition",
            "implied_volatility_rank",
            "expiry",
            "earnings_date",
            # 'strategy',
            "long_strike",
            "short_strike",
            "returns",
            "comment",
            "amount",
            "long_leg_delta",
            "short_leg_delta",
            "long_leg_theta",
            "short_leg_theta",
            "number_of_contract",
            "on_date",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):

        super(PortfolioForm, self).__init__(*args, **kwargs)
        if (
            kwargs.get("initial")
            and kwargs["initial"].get("create")
            and kwargs["initial"]["create"]
        ):
            self.fields["symbol"].widget.attrs["readonly"] = False
            self.fields["industry"].widget.attrs["readonly"] = False
            self.fields["condition"].widget.attrs["readonly"] = False
            # self.fields['strategy'].widget.attrs['readonly'] = False

            condition_CHOICES = [
                ("neutral", "neutral"),
                ("oversold", "oversold"),
                ("overbought", "overbought"),
            ]

            # strategy_CHOICES = [
            #     ('covered_calls', 'covered_calls'),
            #     ('shortputdata', 'shortputdata'),
            #     ('credit_spread', 'credit_spread'),
            # ]

            # Use ChoiceField in the form
            self.fields["condition"] = forms.ChoiceField(
                choices=condition_CHOICES,
            )
            # self.fields['strategy'] = forms.ChoiceField(choices=strategy_CHOICES,)
            self.fields["action"].widget = forms.TextInput()
            self.fields["implied_volatility_rank"].widget = forms.TextInput()
            self.fields["earnings_date"].widget = forms.DateInput(
                attrs={"type": "date"}
            )


# ===== NEW OPTIMIZED INVESTMENT FORMS =====

class OptimizedInvestmentForm(forms.Form):
    """Optimized form for investment creation."""
    
    amount = forms.DecimalField(
        label="Investment Amount",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('100.00'),
        max_value=Decimal('1000000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter investment amount'
        })
    )
    
    investment_type = forms.ChoiceField(
        label="Investment Type",
        choices=[
            ('stocks', 'Stocks'),
            ('bonds', 'Bonds'),
            ('mutual_funds', 'Mutual Funds'),
            ('etfs', 'ETFs'),
            ('options', 'Options'),
            ('crypto', 'Cryptocurrency')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    investment_plan_id = forms.IntegerField(
        label="Investment Plan ID",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter plan ID'
        })
    )
    
    notes = forms.CharField(
        label="Notes",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this investment'
        })
    )
    
    def clean_amount(self):
        """Validate investment amount."""
        amount = self.cleaned_data.get('amount')
        if amount and amount < Decimal('100.00'):
            raise forms.ValidationError("Minimum investment amount is $100")
        return amount


class OptimizedInvestmentRateForm(forms.Form):
    """Optimized form for investment rate creation."""
    
    rate_name = forms.CharField(
        label="Rate Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter rate name'
        })
    )
    
    rate_value = forms.DecimalField(
        label="Rate Value (%)",
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter rate percentage'
        })
    )
    
    rate_type = forms.ChoiceField(
        label="Rate Type",
        choices=[
            ('annual', 'Annual'),
            ('monthly', 'Monthly'),
            ('daily', 'Daily'),
            ('compound', 'Compound')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        label="Description",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add description for this rate'
        })
    )
    
    def clean_rate_value(self):
        """Validate rate value."""
        rate_value = self.cleaned_data.get('rate_value')
        if rate_value and rate_value <= 0:
            raise forms.ValidationError("Rate value must be greater than 0")
        return rate_value


class InvestmentStatusForm(forms.Form):
    """Form for updating investment status."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended')
    ]
    
    status = forms.ChoiceField(
        label="New Status",
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reason = forms.CharField(
        label="Reason for Change",
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for status change'
        })
    )


# ============================================================================
# MANAGED OPTIONS TRADING FORMS
# ============================================================================

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
            'fee_tier',
            'management_fee_percentage',
            'performance_fee_percentage',
            'performance_threshold',
            'max_position_risk',
            'max_total_risk',
            'max_daily_loss',
            'max_weekly_loss',
            'max_monthly_loss',
            'max_positions',
            'session_fee',
            'sessions_per_month',
            'monthly_platform_fee',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Name'}),
            'initial_capital': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '5000'}),
            'account_manager': forms.Select(attrs={'class': 'form-control'}),
            'fee_tier': forms.Select(attrs={'class': 'form-control'}),
            'management_fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '5'}),
            'performance_fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '50'}),
            'performance_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'max_position_risk': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_total_risk': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_daily_loss': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_weekly_loss': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_monthly_loss': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_positions': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'session_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sessions_per_month': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'monthly_platform_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter client to active investors only
        if 'client' in self.fields:
            from accounts.utilities.user_querysets import get_active_investors_queryset
            self.fields['client'].queryset = get_active_investors_queryset()
            self.fields['client'].empty_label = "--- Select Client (Investor) ---"
        
        # Filter account_manager to active staff only
        if 'account_manager' in self.fields:
            from accounts.utilities.user_querysets import get_active_staff_queryset
            self.fields['account_manager'].queryset = get_active_staff_queryset()
            self.fields['account_manager'].empty_label = "--- Select Account Manager (Staff) ---"
            self.fields['account_manager'].required = False
    
    def clean_initial_capital(self):
        capital = self.cleaned_data.get('initial_capital')
        if capital and capital < Decimal('5000.00'):
            raise ValidationError('Minimum account size is $5,000')
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
            'positions',
            'capital_required',
            'premium_collected',
            'max_profit',
            'max_loss',
            'position_delta',
            'position_theta',
            'position_gamma',
            'position_vega',
            'expiration_date',
            'notes'
        ]
        widgets = {
            'managed_account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ticker Symbol (e.g., AAPL)'}),
            'strategy': forms.Select(attrs={'class': 'form-control'}),
            'positions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON format: [{"type": "short_put", "strike": 170, "contracts": 1, "premium": 300}]'}),
            'capital_required': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'premium_collected': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_profit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_loss': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'position_delta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'position_theta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'position_gamma': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'position_vega': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Trade notes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter managed_account to active/paused accounts only
        if 'managed_account' in self.fields:
            self.fields['managed_account'].queryset = ManagedTradingAccount.objects.filter(
                status__in=['active', 'paused']
            ).select_related('client').order_by('account_number')
            self.fields['managed_account'].empty_label = "--- Select Account ---"
    
    def clean_symbol(self):
        symbol = self.cleaned_data.get('symbol')
        if symbol:
            return symbol.upper()
        return symbol
    
    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('managed_account')
        capital = cleaned_data.get('capital_required')
        
        if account and capital:
            if capital > account.available_buying_power:
                raise ValidationError(
                    f'Insufficient buying power. Available: ${account.available_buying_power:,.2f}'
                )
        
        return cleaned_data


class ClosePositionForm(forms.Form):
    """
    Form for closing options positions
    """
    
    exit_price = forms.DecimalField(
        label="Exit Price",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Exit price'})
    )
    
    exit_reason = forms.ChoiceField(
        label="Exit Reason",
        choices=OptionsPosition.EXIT_REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        label="Exit Notes",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for exit...'})
    )


class TradingSessionForm(forms.ModelForm):
    """
    Form for creating/editing trading sessions (consultative tier)
    """
    
    class Meta:
        model = TradingSession
        fields = [
            'managed_account',
            'session_date',
            'session_duration_minutes',
            'session_type',
            'topics_discussed',
            'positions_reviewed',
            'action_items',
            'session_notes',
            'client_feedback',
            'fee_charged',
            'recording_url',
        ]
        widgets = {
            'managed_account': forms.Select(attrs={'class': 'form-control'}),
            'session_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'session_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '15', 'step': '15'}),
            'session_type': forms.Select(attrs={'class': 'form-control'}),
            'topics_discussed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Topics covered...'}),
            'positions_reviewed': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'action_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '["Action 1", "Action 2"]'}),
            'session_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'client_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fee_charged': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recording_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter managed_account to consultative tier accounts only
        if 'managed_account' in self.fields:
            self.fields['managed_account'].queryset = ManagedTradingAccount.objects.filter(
                fee_tier='consultative',
                status__in=['active', 'paused']
            ).select_related('client').order_by('account_number')
            self.fields['managed_account'].empty_label = "--- Select Consultative Account ---"


class QuickPositionEntryForm(forms.Form):
    """
    Simplified form for quick position entry
    """
    
    account = forms.ModelChoiceField(
        queryset=ManagedTradingAccount.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Account"
    )
    
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ticker Symbol'}),
        label="Symbol"
    )
    
    strategy = forms.ChoiceField(
        choices=OptionsPosition.STRATEGY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Strategy"
    )
    
    strike_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Strike Price"
    )
    
    contracts = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label="Contracts"
    )
    
    premium = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Premium Collected"
    )
    
    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Expiration Date"
    )
    
    delta = forms.DecimalField(
        max_digits=8,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        label="Delta"
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Trade notes...'}),
        label="Notes"
    )
    
    def clean_symbol(self):
        return self.cleaned_data['symbol'].upper()
    
    def clean(self):
        cleaned_data = super().clean()
        contracts = cleaned_data.get('contracts', 1)
        strike = cleaned_data.get('strike_price', Decimal('0'))
        
        # Calculate capital required for short put (most common)
        capital_required = strike * Decimal('100') * contracts
        cleaned_data['capital_required'] = capital_required
        
        return cleaned_data
