from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import (
    Investments,
    Investment_rates,
    Investor_Information,
    # ShortPut,  # DELETED Nov 5, 2025
    # Portfolio,  # DELETED Nov 5, 2025
    InvestmentsStrategy,
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingSession,
    # Shareholders Management Models (consolidated March 2026)
    Member,
    LedgerEntry,
    LedgerEvidence,
    Deal,
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


# ============================================================
# DEPRECATED FORMS - Nov 5, 2025
# ============================================================
# OptionsForm and PortfolioForm are DEPRECATED
# ShortPut and Portfolio models were removed
# Use OptionsPosition and related services instead
#
# Commented out to prevent errors, but kept for reference
# ============================================================

# class OptionsForm(forms.ModelForm):
#     on_date = forms.DateField(
#         widget=forms.DateInput(attrs={"type": "date"}), label="Date"
#     )
# 
#     class Meta:
#         model = ShortPut
#         # fields = '__all__'
#         fields = ["symbol", "comment", "on_date", "is_featured"]


# (PortfolioForm class completely commented out - 75 lines removed)


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
            'current_value',
            'unrealized_pnl',
            'realized_pnl',
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
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unrealized_pnl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'realized_pnl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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


# =============================================================================
# SHAREHOLDERS MANAGEMENT FORMS
# =============================================================================
# CONSOLIDATED from investing/forms_shareholders.py — March 2026
# =============================================================================


# ---- Shared upload validators ------------------------------------------------

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
ALLOWED_DOC_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
MAX_PHOTO_SIZE = 2 * 1024 * 1024   # 2 MB
MAX_DOC_SIZE = 5 * 1024 * 1024     # 5 MB


def _validate_upload(file_obj, allowed_types, max_bytes, label):
    """Reusable file-upload validation."""
    if file_obj is None:
        return
    content_type = getattr(file_obj, 'content_type', '')
    if content_type not in allowed_types:
        nice = ', '.join(t.split('/')[-1].upper() for t in allowed_types)
        raise ValidationError(
            f"{label}: File type '{content_type}' is not allowed. "
            f"Accepted types: {nice}."
        )
    if file_obj.size > max_bytes:
        limit_mb = max_bytes / (1024 * 1024)
        raise ValidationError(
            f"{label}: File is too large ({file_obj.size / (1024*1024):.1f} MB). "
            f"Maximum allowed size is {limit_mb:.0f} MB."
        )


class MemberRegisterForm(forms.ModelForm):
    """Form for registering a new member/shareholder."""
    
    identity_document = forms.FileField(
        required=False,
        help_text="Optional: Upload ID, passport, or business registration (max 5 MB)",
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    profile_photo = forms.ImageField(
        required=False,
        help_text="Optional: Upload a profile photo (JPG, PNG, GIF, max 2 MB)",
        widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/gif'})
    )
    
    class Meta:
        model = Member
        fields = ['legal_name', 'member_type', 'role_title', 'email', 'phone', 'bio']
        widgets = {
            'legal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full legal name as per ID/certificate',
                'required': True
            }),
            'member_type': forms.Select(attrs={'class': 'form-control'}),
            'role_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Founder, Lead Developer, Investor'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 XXX XXX XXX'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief background or role description (optional)'
            }),
        }
    
    def clean_email(self):
        """Validate email uniqueness within the deal."""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for active members
            # Note: deal is set in the view before validation
            if hasattr(self, 'deal'):
                existing = Member.objects.filter(
                    deal=self.deal,
                    email=email,
                    is_archived=False
                ).exists()
                if existing:
                    raise ValidationError(
                        f"A member with email {email} already exists in this deal."
                    )
        return email
    
    def clean_legal_name(self):
        """Validate legal name is not empty and reasonable length."""
        name = self.cleaned_data.get('legal_name', '').strip()
        if not name:
            raise ValidationError("Legal name is required.")
        if len(name) < 2:
            raise ValidationError("Legal name must be at least 2 characters.")
        return name
    
    def clean_phone(self):
        """Ensure phone field returns empty string instead of None."""
        phone = self.cleaned_data.get('phone')
        return phone if phone else ''

    def clean_profile_photo(self):
        """Validate profile photo size and type."""
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            _validate_upload(photo, ALLOWED_IMAGE_TYPES, MAX_PHOTO_SIZE, 'Profile photo')
        return photo

    def clean_identity_document(self):
        """Validate identity document size and type."""
        doc = self.cleaned_data.get('identity_document')
        if doc:
            _validate_upload(doc, ALLOWED_DOC_TYPES, MAX_DOC_SIZE, 'Identity document')
        return doc


class MemberEditForm(forms.ModelForm):
    """Form for editing existing member profile."""

    profile_photo = forms.ImageField(
        required=False,
        help_text="Upload a new profile photo (JPG, PNG, GIF, max 2 MB)",
        widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/gif'})
    )
    identity_document = forms.FileField(
        required=False,
        help_text="Replace identity document (PDF, JPG, PNG, max 5 MB)",
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    class Meta:
        model = Member
        fields = ['legal_name', 'role_title', 'email', 'phone', 'bio', 'verified']
        widgets = {
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role_title': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.member_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        # SECURITY: Only superusers can modify verified status
        # For non-superusers, remove the field entirely so it cannot
        # be submitted via POST (disabled fields still send data).
        if self.user and not self.user.is_superuser:
            if 'verified' in self.fields:
                del self.fields['verified']
    
    def clean_email(self):
        """Validate email uniqueness (excluding current member)."""
        email = self.cleaned_data.get('email')
        if email and self.member_instance:
            existing = Member.objects.filter(
                deal=self.member_instance.deal,
                email=email,
                is_archived=False
            ).exclude(pk=self.member_instance.pk).exists()
            if existing:
                raise ValidationError(
                    f"Another member with email {email} already exists."
                )
        return email

    def clean_profile_photo(self):
        """Validate profile photo size and type."""
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            _validate_upload(photo, ALLOWED_IMAGE_TYPES, MAX_PHOTO_SIZE, 'Profile photo')
        return photo

    def clean_identity_document(self):
        """Validate identity document size and type."""
        doc = self.cleaned_data.get('identity_document')
        if doc:
            _validate_upload(doc, ALLOWED_DOC_TYPES, MAX_DOC_SIZE, 'Identity document')
        return doc


class ContributionLogForm(forms.ModelForm):
    """
    Form for logging a new contribution (creates LedgerEntry).

    Tier-specific fields:
      - CASH:    standard fields only (asset_class, value_usd, currency, etc.)
      - IN_KIND: + valuation_method (required)
      - TIME:    + role_multiplier (optional)
      - WORK:    + deliverable_title (required), impact_tier (required)

    These extra fields are stored in LedgerEntry.tier_metadata JSONField.
    """

    proof_document = forms.FileField(
        required=True,  # Phase 3: Made mandatory
        help_text="Upload receipt, invoice, or supporting document (Required)",
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png', 'required': True})
    )

    # ----- In-Kind tier field -----
    valuation_method = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Market appraisal, Purchase receipt, Third-party estimate'
        }),
        help_text="How was the USD value determined?"
    )

    # ----- Time tier field -----
    role_multiplier = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Senior Developer x1.5, Consultant x2.0'
        }),
        help_text="Role / rate multiplier label (optional)"
    )

    # ----- Work tier fields -----
    deliverable_title = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., MVP Backend API, Brand Identity Package'
        }),
        help_text="Title of the deliverable"
    )

    IMPACT_TIER_CHOICES = [
        ('', '-- Select impact tier --'),
        ('LOW', 'Low Impact'),
        ('MEDIUM', 'Medium Impact'),
        ('HIGH', 'High Impact'),
        ('CRITICAL', 'Critical / Strategic'),
    ]
    impact_tier = forms.ChoiceField(
        required=False,
        choices=IMPACT_TIER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Impact level of the deliverable"
    )

    class Meta:
        model = LedgerEntry
        fields = [
            'contributor', 'tier', 'asset_class', 'date',
            'internal_units_value', 'internal_units_label',
            'value_usd', 'currency', 'exchange_rate', 'notes'
        ]
        widgets = {
            'contributor': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'tier': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'asset_class': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Capital Injection, Dev Work, Office Lease',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'internal_units_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity (e.g., 15000, 120, 500)',
                'step': '0.01',
                'required': True
            }),
            'internal_units_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit (e.g., USD, hrs, pts, months)'
            }),
            'value_usd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Value in USD',
                'step': '0.01',
                'required': True
            }),
            'currency': forms.Select(
                choices=[('USD', 'USD'), ('KES', 'KES')],
                attrs={
                    'class': 'form-control',
                    'id': 'id_currency'  # Match Django's default ID pattern
                }
            ),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1.0000',
                'step': '0.0001'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or context (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.deal = kwargs.pop('deal', None)
        super().__init__(*args, **kwargs)

        # Filter contributors to current deal
        if self.deal:
            self.fields['contributor'].queryset = Member.objects.filter(
                deal=self.deal,
                is_archived=False
            ).order_by('legal_name')
            
            # Phase 2: Set currency and exchange rate — live rate from CurrencyConverter
            try:
                config = self.deal.config
                from investing.services.shareholders.deal_config_service import DealConfigService
                live_fx_rate = DealConfigService.get_live_fx_rate(config)
                # Set initial values: currency from DealConfig, rate from live API
                self.fields['currency'].initial = config.base_currency
                self.fields['exchange_rate'].initial = live_fx_rate
                
                # Phase 5: Currency editable for CASH tier (JS will handle)
                # exchange_rate always read-only (populated from live API)
                self.fields['exchange_rate'].widget.attrs['readonly'] = True
                self.fields['exchange_rate'].widget.attrs['class'] = 'form-control bg-light'
                
                # Store rates for JavaScript dynamic calculation
                self.time_rate = config.time_rate
                self.work_rate = config.work_rate
                self.fx_peg_rate = live_fx_rate  # Phase 5: For currency conversion — live rate
                
            except Exception as e:
                # If no DealConfig, use defaults
                self.fields['currency'].initial = 'USD'
                self.fields['exchange_rate'].initial = Decimal('1.0000')
                self.time_rate = Decimal('50.00')  # Default fallback
                self.work_rate = Decimal('100.00')  # Default fallback
                from investing.services.shareholders.deal_config_service import DealConfigService
                self.fx_peg_rate = DealConfigService.get_live_fx_rate()  # Live rate, no config fallback
        
        # Make value_usd not required for TIME and WORK tiers (will be auto-calculated)
        # User can still override if needed
        self.fields['value_usd'].required = False

    def clean_date(self):
        """Validate date is not in the future."""
        contribution_date = self.cleaned_data.get('date')
        if contribution_date and contribution_date > date.today():
            raise ValidationError("Contribution date cannot be in the future.")
        return contribution_date

    def clean_value_usd(self):
        """Validate value is positive (if provided)."""
        value = self.cleaned_data.get('value_usd')
        # Allow None for TIME and WORK tiers (will be auto-calculated)
        if value is not None and value <= 0:
            raise ValidationError("Value must be greater than zero.")
        return value

    def clean_internal_units_value(self):
        """Validate internal units is positive."""
        units = self.cleaned_data.get('internal_units_value')
        if units is not None and units <= 0:
            raise ValidationError("Internal units must be greater than zero.")
        return units
    
    def clean_proof_document(self):
        """Validate proof document upload (Phase 3: Required)."""
        proof = self.cleaned_data.get('proof_document')
        
        if not proof:
            raise ValidationError(
                "Proof of contribution is required. Please upload a receipt, invoice, "
                "or supporting document (PDF, JPG, PNG)."
            )
        
        # Validate file type and size
        _validate_upload(proof, ALLOWED_DOC_TYPES, MAX_DOC_SIZE, "Proof document")
        
        return proof
    
    def _get_dealconfig_rate(self, tier):
        """Get the valuation rate from DealConfig for a given tier."""
        if not self.deal:
            return None
        
        try:
            config = self.deal.config
            if tier == 'TIME':
                return config.time_rate
            elif tier == 'WORK':
                return config.work_rate
            else:
                return None
        except:
            return None
    
    def _calculate_value_for_tier(self, tier, internal_units_value, tier_metadata):
        """Calculate USD value based on tier and DealConfig rates."""
        rate = self._get_dealconfig_rate(tier)
        
        if rate is None:
            return None
        
        # Base calculation
        calculated_value = internal_units_value * rate
        
        # Apply impact multiplier for WORK tier
        if tier == 'WORK' and tier_metadata:
            impact_tier = tier_metadata.get('impact_tier', '')
            multipliers = {
                'LOW': Decimal('0.8'),
                'MEDIUM': Decimal('1.0'),
                'HIGH': Decimal('1.3'),
                'CRITICAL': Decimal('1.7'),
            }
            multiplier = multipliers.get(impact_tier, Decimal('1.0'))
            calculated_value = calculated_value * multiplier
        
        return calculated_value.quantize(Decimal('0.01'))

    def clean(self):
        """Tier-aware cross-field validation."""
        cleaned_data = super().clean()
        tier = cleaned_data.get('tier')
        internal_units_label = (cleaned_data.get('internal_units_label') or '').strip()

        # ------------------------------------------------------------------
        # Default unit labels per tier
        # ------------------------------------------------------------------
        if tier and not internal_units_label:
            label_defaults = {
                'CASH': 'USD',
                'IN_KIND': 'units',
                'TIME': 'hrs',
                'WORK': 'pts',
            }
            cleaned_data['internal_units_label'] = label_defaults.get(tier, 'units')

        # ------------------------------------------------------------------
        # Tier-specific required-field validation
        # ------------------------------------------------------------------
        if tier == 'IN_KIND':
            valuation_method = (cleaned_data.get('valuation_method') or '').strip()
            if not valuation_method:
                self.add_error(
                    'valuation_method',
                    'Valuation method is required for In-Kind contributions.'
                )

        elif tier == 'WORK':
            deliverable_title = (cleaned_data.get('deliverable_title') or '').strip()
            impact_tier = (cleaned_data.get('impact_tier') or '').strip()
            if not deliverable_title:
                self.add_error(
                    'deliverable_title',
                    'Deliverable title is required for Work contributions.'
                )
            if not impact_tier:
                self.add_error(
                    'impact_tier',
                    'Impact tier is required for Work contributions.'
                )

        # TIME: role_multiplier is optional, no validation needed.

        # ------------------------------------------------------------------
        # Build tier_metadata dict for the view to persist
        # ------------------------------------------------------------------
        tier_metadata = {}
        if tier == 'IN_KIND':
            tier_metadata['valuation_method'] = (
                cleaned_data.get('valuation_method') or ''
            ).strip()
        elif tier == 'TIME':
            tier_metadata['role_multiplier'] = (
                cleaned_data.get('role_multiplier') or ''
            ).strip()
        elif tier == 'WORK':
            tier_metadata['deliverable_title'] = (
                cleaned_data.get('deliverable_title') or ''
            ).strip()
            tier_metadata['impact_tier'] = (
                cleaned_data.get('impact_tier') or ''
            ).strip()

        cleaned_data['tier_metadata'] = tier_metadata
        
        # ------------------------------------------------------------------
        # Phase 5: Handle currency conversion for CASH tier
        # Phase 2: Auto-calculate value_usd for TIME and WORK tiers (read-only enforcement)
        # ------------------------------------------------------------------
        value_usd = cleaned_data.get('value_usd')
        internal_units_value = cleaned_data.get('internal_units_value')
        currency = cleaned_data.get('currency')
        
        # Phase 5: CASH tier with KES currency - auto-calculate USD value
        if tier == 'CASH' and currency == 'KES' and internal_units_value:
            # Convert KES to USD using exchange rate
            if self.deal:
                try:
                    config = self.deal.config
                    from investing.services.shareholders.deal_config_service import DealConfigService
                    fx_rate = DealConfigService.get_live_fx_rate(config)  # Live KES per 1 USD
                    # Convert: amount_kes / fx_rate = amount_usd
                    calculated_usd = internal_units_value / fx_rate
                    cleaned_data['value_usd'] = calculated_usd.quantize(Decimal('0.01'))
                    cleaned_data['exchange_rate'] = fx_rate
                    cleaned_data['_auto_calculated'] = True
                except Exception as e:
                    self.add_error(
                        'value_usd',
                        f'Unable to convert KES to USD. Please check DealConfig exchange rate.'
                    )
            else:
                self.add_error('currency', 'No DealConfig found for currency conversion.')
        
        # Phase 5: CASH tier with USD currency - use direct value
        elif tier == 'CASH' and currency == 'USD':
            if self.deal:
                try:
                    config = self.deal.config
                    cleaned_data['exchange_rate'] = Decimal('1.0000')  # No conversion needed
                except Exception:
                    cleaned_data['exchange_rate'] = Decimal('1.0000')
        
        # Phase 2: ALWAYS auto-calculate value_usd for TIME and WORK tiers (read-only enforcement)
        elif tier in ['TIME', 'WORK'] and internal_units_value:
            calculated_value = self._calculate_value_for_tier(tier, internal_units_value, tier_metadata)
            
            if calculated_value is not None:
                # Always override with calculated value (read-only enforcement)
                cleaned_data['value_usd'] = calculated_value
                cleaned_data['_auto_calculated'] = True
            else:
                # If we can't auto-calculate, show error
                self.add_error(
                    'value_usd',
                    f'Unable to auto-calculate value. Please ensure DealConfig has a {tier.lower()}_rate configured.'
                )
        
        # Ensure value_usd is always provided for CASH and IN_KIND tiers
        if tier in ['CASH', 'IN_KIND'] and not value_usd:
            self.add_error(
                'value_usd',
                'Value in USD is required for this contribution type.'
            )
        
        # ------------------------------------------------------------------
        # Phase 5: Enforce currency and exchange_rate from DealConfig 
        # (read-only enforcement for non-CASH tiers only)
        # ------------------------------------------------------------------
        if self.deal and tier not in ['CASH']:  # Phase 5: Allow CASH to use user-selected currency
            try:
                config = self.deal.config
                from investing.services.shareholders.deal_config_service import DealConfigService
                # Override with live rate for non-CASH tiers (security: prevent tampering)
                cleaned_data['currency'] = config.base_currency
                cleaned_data['exchange_rate'] = DealConfigService.get_live_fx_rate(config)
            except Exception:
                # Fallback to defaults if DealConfig not available
                cleaned_data['currency'] = 'USD'
                cleaned_data['exchange_rate'] = Decimal('1.0000')

        return cleaned_data
