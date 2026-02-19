"""
Shareholders Management System - Django Forms

Forms for Member registration, editing, and contribution logging with
server-side validation.

Migrated to investing app - models imported from shareholders app.
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

# Models imported from original shareholders app (preserves DB ownership)
from investing.models_shareholders import Member, LedgerEntry, LedgerEvidence, Deal


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
        required=False,
        help_text="Upload receipt, invoice, or supporting document",
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
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
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'USD',
                'placeholder': 'Currency code'
            }),
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
            
            # Phase 2: Set currency and exchange rate from DealConfig (read-only)
            try:
                config = self.deal.config
                # Set initial values from DealConfig
                self.fields['currency'].initial = config.base_currency
                self.fields['exchange_rate'].initial = config.fx_peg_rate
                
                # Make currency and exchange_rate read-only
                self.fields['currency'].widget.attrs['readonly'] = True
                self.fields['currency'].widget.attrs['class'] = 'form-control bg-light'
                self.fields['exchange_rate'].widget.attrs['readonly'] = True
                self.fields['exchange_rate'].widget.attrs['class'] = 'form-control bg-light'
                
                # Store rates for JavaScript dynamic calculation
                self.time_rate = config.time_rate
                self.work_rate = config.work_rate
                
            except Exception as e:
                # If no DealConfig, use defaults
                self.fields['currency'].initial = 'USD'
                self.fields['exchange_rate'].initial = Decimal('1.0000')
                self.time_rate = Decimal('50.00')  # Default fallback
                self.work_rate = Decimal('100.00')  # Default fallback
        
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
        # Phase 2: ALWAYS auto-calculate value_usd for TIME and WORK tiers (read-only enforcement)
        # ------------------------------------------------------------------
        value_usd = cleaned_data.get('value_usd')
        internal_units_value = cleaned_data.get('internal_units_value')
        
        # ALWAYS calculate for TIME and WORK (ignore any submitted value for security)
        if tier in ['TIME', 'WORK'] and internal_units_value:
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
        # Phase 2: Enforce currency and exchange_rate from DealConfig (read-only enforcement)
        # ------------------------------------------------------------------
        if self.deal:
            try:
                config = self.deal.config
                # Always override with DealConfig values (security: prevent tampering)
                cleaned_data['currency'] = config.base_currency
                cleaned_data['exchange_rate'] = config.fx_peg_rate
            except Exception:
                # Fallback to defaults if DealConfig not available
                cleaned_data['currency'] = 'USD'
                cleaned_data['exchange_rate'] = Decimal('1.0000')

        return cleaned_data
