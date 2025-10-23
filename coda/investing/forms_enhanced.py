"""
Enhanced Forms for Managed Options Trading

Realistic forms that handle multi-leg strategies and real market data.
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import ManagedTradingAccount, OptionsPosition


class MultiLegOptionsForm(forms.Form):
    """
    Enhanced form for multi-leg options strategies
    Handles Bull Put Spreads, Bear Call Spreads, Iron Condors, etc.
    """
    
    # Account Selection
    managed_account = forms.ModelChoiceField(
        queryset=ManagedTradingAccount.objects.filter(status='active'),
        empty_label="Select Account",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Symbol and Strategy
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'AAPL',
            'id': 'symbol-input'
        })
    )
    
    strategy = forms.ChoiceField(
        choices=[
            ('cash_secured_put', 'Cash-Secured Put'),
            ('covered_call', 'Covered Call'),
            ('bull_put_spread', 'Bull Put Spread'),
            ('bear_call_spread', 'Bear Call Spread'),
            ('iron_condor', 'Iron Condor'),
            ('iron_butterfly', 'Iron Butterfly'),
            ('straddle', 'Straddle'),
            ('strangle', 'Strangle'),
        ],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'strategy-select'})
    )
    
    # Leg 1 (Short leg for spreads)
    leg1_type = forms.ChoiceField(
        choices=[
            ('short_put', 'Short Put'),
            ('short_call', 'Short Call'),
        ],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'leg1-type'})
    )
    
    leg1_strike = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '1130.00',
            'id': 'leg1-strike'
        })
    )
    
    leg1_contracts = forms.IntegerField(
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'id': 'leg1-contracts'
        })
    )
    
    leg1_premium = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '15.50',
            'id': 'leg1-premium'
        })
    )
    
    # Leg 2 (Long leg for spreads) - Optional for single leg strategies
    leg2_type = forms.ChoiceField(
        choices=[
            ('', 'No Second Leg'),
            ('long_put', 'Long Put'),
            ('long_call', 'Long Call'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'leg2-type'})
    )
    
    leg2_strike = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '1100.00',
            'id': 'leg2-strike'
        })
    )
    
    leg2_contracts = forms.IntegerField(
        min_value=1,
        max_value=100,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'id': 'leg2-contracts'
        })
    )
    
    leg2_premium = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '8.50',
            'id': 'leg2-premium'
        })
    )
    
    # Greeks (will be auto-calculated from OptionPlay API)
    delta = forms.DecimalField(
        max_digits=6,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': '-0.76',
            'id': 'delta'
        })
    )
    
    theta = forms.DecimalField(
        max_digits=6,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': '0.05',
            'id': 'theta'
        })
    )
    
    # Expiration
    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'expiration-date'
        })
    )
    
    # Notes
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Trade notes...',
            'id': 'notes'
        })
    )
    
    def clean_symbol(self):
        symbol = self.cleaned_data.get('symbol')
        if symbol:
            return symbol.upper().strip()
        return symbol
    
    def clean(self):
        cleaned_data = super().clean()
        strategy = cleaned_data.get('strategy')
        leg2_type = cleaned_data.get('leg2_type')
        
        # Validate multi-leg strategies have both legs
        if strategy in ['bull_put_spread', 'bear_call_spread', 'iron_condor', 'iron_butterfly']:
            if not leg2_type:
                raise ValidationError(f"{strategy.replace('_', ' ').title()} requires a second leg")
        
        # Calculate and validate capital requirements
        account = cleaned_data.get('managed_account')
        if account:
            capital_required = self.calculate_capital_required(cleaned_data)
            if capital_required > account.available_buying_power:
                raise ValidationError(
                    f'Insufficient buying power. Required: ${capital_required:,.2f}, Available: ${account.available_buying_power:,.2f}'
                )
        
        return cleaned_data
    
    def calculate_capital_required(self, cleaned_data):
        """Calculate capital required based on strategy"""
        strategy = cleaned_data.get('strategy')
        leg1_strike = cleaned_data.get('leg1_strike', 0)
        leg1_contracts = cleaned_data.get('leg1_contracts', 0)
        leg2_strike = cleaned_data.get('leg2_strike', 0)
        leg2_contracts = cleaned_data.get('leg2_contracts', 0)
        
        if strategy == 'cash_secured_put':
            # For cash-secured put: strike * contracts * 100
            return leg1_strike * leg1_contracts * 100
        
        elif strategy in ['bull_put_spread', 'bear_call_spread']:
            # For spreads: (short_strike - long_strike) * contracts * 100
            return (leg1_strike - leg2_strike) * leg1_contracts * 100
        
        elif strategy in ['iron_condor', 'iron_butterfly']:
            # For iron condor: (short_strike - long_strike) * contracts * 100
            return (leg1_strike - leg2_strike) * leg1_contracts * 100
        
        return Decimal('0.00')


class OptionPlayIntegrationForm(forms.Form):
    """
    Form for OptionPlay API integration
    Shows top 5 recommended positions based on real market data
    """
    
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter symbol (e.g., AAPL)',
            'id': 'symbol-search'
        })
    )
    
    strategy_filter = forms.ChoiceField(
        choices=[
            ('all', 'All Strategies'),
            ('income', 'Income Strategies'),
            ('directional', 'Directional Strategies'),
            ('volatility', 'Volatility Strategies'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    risk_level = forms.ChoiceField(
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # This will be populated by JavaScript/AJAX
    recommended_positions = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'position-option'})
    )


class RealisticPositionDisplayForm(forms.Form):
    """
    Form for displaying realistic position information
    Shows capital usage, margin requirements, etc.
    """
    
    # This form is for display only - shows calculated values
    symbol = forms.CharField(disabled=True)
    strategy = forms.CharField(disabled=True)
    capital_required = forms.DecimalField(disabled=True)
    margin_used = forms.DecimalField(disabled=True)
    buying_power_remaining = forms.DecimalField(disabled=True)
    max_profit = forms.DecimalField(disabled=True)
    max_loss = forms.DecimalField(disabled=True)
    breakeven_price = forms.DecimalField(disabled=True)
    days_to_expiration = forms.IntegerField(disabled=True)
    implied_volatility = forms.DecimalField(disabled=True)
