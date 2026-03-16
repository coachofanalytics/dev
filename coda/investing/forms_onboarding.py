"""
Forms for Phase 6: Client Onboarding & Compliance
Risk assessment, application, and contract signing
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    InvestorRiskProfile,
    ManagedTradingApplication,
    ManagedTradingContract,
    ManagedTradingAccount
)



class RiskToleranceQuestionnaireForm(forms.Form):
    """
    10-question risk tolerance assessment
    Each question scored 1-10 points
    Total score 0-100 determines risk category
    """
    
    # Question 1: Investment Experience
    question_1 = forms.ChoiceField(
        label="1. How many years of investment experience do you have?",
        choices=[
            (1, "Less than 1 year (1 point)"),
            (3, "1-3 years (3 points)"),
            (5, "3-5 years (5 points)"),
            (7, "5-10 years (7 points)"),
            (10, "More than 10 years (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 2: Options Trading Experience
    question_2 = forms.ChoiceField(
        label="2. Have you traded options before?",
        choices=[
            (1, "Never (1 point)"),
            (3, "Limited experience (3 points)"),
            (5, "Some experience (5 points)"),
            (7, "Experienced (7 points)"),
            (10, "Very experienced (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 3: Risk Comfort Level
    question_3 = forms.ChoiceField(
        label="3. How comfortable are you with market volatility?",
        choices=[
            (1, "Very uncomfortable - prefer stability (1 point)"),
            (3, "Somewhat uncomfortable (3 points)"),
            (5, "Neutral (5 points)"),
            (7, "Comfortable (7 points)"),
            (10, "Very comfortable - embrace volatility (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 4: Loss Tolerance
    question_4 = forms.ChoiceField(
        label="4. What is the maximum loss you can tolerate in a single month?",
        choices=[
            (1, "0-2% (1 point)"),
            (3, "2-5% (3 points)"),
            (5, "5-10% (5 points)"),
            (7, "10-15% (7 points)"),
            (10, "15%+ (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 5: Investment Goals
    question_5 = forms.ChoiceField(
        label="5. What is your primary investment goal?",
        choices=[
            (1, "Capital preservation (1 point)"),
            (3, "Steady income (3 points)"),
            (5, "Balanced growth (5 points)"),
            (7, "Capital appreciation (7 points)"),
            (10, "Aggressive growth (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 6: Time Horizon
    question_6 = forms.ChoiceField(
        label="6. What is your investment time horizon?",
        choices=[
            (1, "Less than 1 year (1 point)"),
            (3, "1-3 years (3 points)"),
            (5, "3-5 years (5 points)"),
            (7, "5-10 years (7 points)"),
            (10, "More than 10 years (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 7: Financial Stability
    question_7 = forms.ChoiceField(
        label="7. How stable is your income?",
        choices=[
            (1, "Very unstable (1 point)"),
            (3, "Somewhat unstable (3 points)"),
            (5, "Stable (5 points)"),
            (7, "Very stable (7 points)"),
            (10, "Extremely stable + significant savings (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 8: Portfolio Allocation
    question_8 = forms.ChoiceField(
        label="8. What percentage of your portfolio are you willing to allocate to options trading?",
        choices=[
            (1, "Less than 5% (1 point)"),
            (3, "5-10% (3 points)"),
            (5, "10-20% (5 points)"),
            (7, "20-30% (7 points)"),
            (10, "More than 30% (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 9: Market Downturn Reaction
    question_9 = forms.ChoiceField(
        label="9. How would you react to a 20% market downturn?",
        choices=[
            (1, "Sell everything immediately (1 point)"),
            (3, "Reduce exposure significantly (3 points)"),
            (5, "Hold steady (5 points)"),
            (7, "Stay invested (7 points)"),
            (10, "Buy more - opportunity! (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    # Question 10: Decision Making Style
    question_10 = forms.ChoiceField(
        label="10. How do you typically make investment decisions?",
        choices=[
            (1, "Avoid all risk (1 point)"),
            (3, "Very cautiously (3 points)"),
            (5, "After careful analysis (5 points)"),
            (7, "Confidently based on research (7 points)"),
            (10, "Aggressively seek opportunities (10 points)"),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    def calculate_risk_score(self):
        """Calculate total risk score (0-100)"""
        total = 0
        for i in range(1, 11):
            answer = self.cleaned_data.get(f'question_{i}')
            if answer:
                total += int(answer)
        return total
    
    def get_risk_category(self):
        """Determine risk category based on score"""
        score = self.calculate_risk_score()
        if score <= 30:
            return 'conservative'
        elif score <= 60:
            return 'moderate'
        else:
            return 'aggressive'
    
    def get_recommended_tiers(self):
        """Get recommended fee tiers"""
        category = self.get_risk_category()
        if category == 'conservative':
            return ['consultative']
        elif category == 'moderate':
            return ['balanced', 'consultative']
        else:  # aggressive
            return ['elite', 'balanced', 'consultative']


class ManagedTradingApplicationForm(forms.ModelForm):
    """
    Application form for managed trading services
    Pre-filled with risk profile data
    """
    
    class Meta:
        model = ManagedTradingApplication
        fields = [
            'initial_capital',
            'fee_tier',
            'preferred_manager',
            'funding_method'
        ]
        widgets = {
            'initial_capital': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30000.00',
                'step': '0.01',
                'min': '5000.00'
            }),
            'fee_tier': forms.Select(attrs={'class': 'form-control'}),
            'preferred_manager': forms.Select(attrs={'class': 'form-control'}),
            'funding_method': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.risk_profile = kwargs.pop('risk_profile', None)
        super().__init__(*args, **kwargs)
        
        # Filter staff for preferred manager
        if 'preferred_manager' in self.fields:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['preferred_manager'].queryset = User.objects.filter(is_staff=True)
            self.fields['preferred_manager'].required = False
        
        # Add help text
        self.fields['initial_capital'].help_text = "Minimum $5,000 required"
        self.fields['fee_tier'].help_text = "Select tier based on your risk profile and capital"
        
        # Filter tier choices based on risk profile (if available)
        tier_choices = ManagedTradingAccount.FEE_TIER_CHOICES
        selectable_codes = set(ManagedTradingAccount.APPLICATION_SELECTABLE_TIERS)
        filtered_choices = [(k, v) for k, v in tier_choices if k in selectable_codes]

        if self.risk_profile:
            recommended = [code for code in self.risk_profile.recommended_tiers if code in selectable_codes]
            # Always allow consultative as legacy fallback
            if 'consultative' in selectable_codes and 'consultative' not in recommended:
                recommended.append('consultative')
            recommended_filtered = [(k, v) for k, v in tier_choices if k in recommended]
            if recommended_filtered:
                filtered_choices = recommended_filtered

        self.fields['fee_tier'].choices = [('', '--- Select Tier ---')] + filtered_choices
        if not self.fields['fee_tier'].initial and filtered_choices:
            self.fields['fee_tier'].initial = filtered_choices[0][0]
    
    def clean_initial_capital(self):
        """Validate minimum capital"""
        capital = self.cleaned_data.get('initial_capital')
        if capital and capital < Decimal('5000.00'):
            raise ValidationError("Minimum initial capital is $5,000")
        return capital
    
    def clean(self):
        """Validate capital meets tier minimum and tier matches risk profile"""
        cleaned_data = super().clean()
        capital = cleaned_data.get('initial_capital')
        tier = cleaned_data.get('fee_tier')
        
        if capital and tier:
            # Check capital meets tier minimum (using database configuration)
            from .models import FeeTierConfiguration
            try:
                tier_config = FeeTierConfiguration.objects.get(tier_code=tier, is_active=True)
                minimum = tier_config.minimum_capital
            except FeeTierConfiguration.DoesNotExist:
                # Fallback to hardcoded minimums
                tier_minimums = {
                    'balanced': Decimal('25000.00'),
                    'elite': Decimal('50000.00'),
                    'consultative': Decimal('25000.00'),
                    'starter': Decimal('5000.00'),
                    'professional': Decimal('15000.00'),
                    'premium': Decimal('25000.00'),
                    'co_invest': Decimal('100000.00'),
                    'custom': Decimal('25000.00'),
                }
                minimum = tier_minimums.get(tier, Decimal('5000.00'))
            
            tier_label = dict(ManagedTradingAccount.FEE_TIER_CHOICES).get(tier, tier.title())

            if capital < minimum:
                raise ValidationError(
                    f"The {tier_label} tier requires a minimum of ${minimum:,.2f}. "
                    f"You entered ${capital:,.2f}."
                )
            
            # Warn if tier doesn't match risk profile
            if self.risk_profile:
                recommended = self.risk_profile.recommended_tiers
                if tier not in recommended:
                    self.add_error('fee_tier', 
                        f"Warning: The {tier} tier is not recommended for your "
                        f"{self.risk_profile.risk_category} risk profile. "
                        f"Recommended tiers: {', '.join(recommended)}"
                    )
        
        return cleaned_data


class ContractReviewForm(forms.Form):
    """
    Form for reviewing and agreeing to contracts
    Used in the contract review page
    """
    
    acknowledge_ima = forms.BooleanField(
        label="I have read and agree to the Investment Management Agreement",
        required=True
    )
    
    acknowledge_risk = forms.BooleanField(
        label="I have read and understand the Options Trading Risk Disclosure",
        required=True
    )
    
    acknowledge_fees = forms.BooleanField(
        label="I have read and agree to the Fee Schedule Agreement",
        required=True
    )
    
    acknowledge_terms = forms.BooleanField(
        label="I have read and agree to the Terms of Service",
        required=True
    )
    
    signature_name = forms.CharField(
        label="Full Name (for signature)",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type your full legal name'
        })
    )
    
    signature_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        help_text="Digital signature will be captured"
    )


class ContractSignatureForm(forms.Form):
    """
    Simple form for signing a single contract
    Used in AJAX signature capture
    """
    
    signature_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_signature_data(self):
        """Validate signature data format"""
        data = self.cleaned_data.get('signature_data')
        if not data or not data.startswith('data:image'):
            raise ValidationError("Invalid signature data format")
        return data

