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
