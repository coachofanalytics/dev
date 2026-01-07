"""
Onboarding forms for simplified registration and profile completion.
"""
from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile, Category


class SimplifiedRegistrationForm(forms.ModelForm):
    """
    Simplified registration form - only collects essential information.

    Fields: first_name, last_name, email, category, password
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )
    # Use None initially to avoid database query at module import time
    # The queryset is set in __init__ to defer database access
    category = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True,
        help_text='Select your primary role on the platform',
        empty_label='-- Select Category --'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Defer database query to form instantiation time
        self.fields['category'].queryset = Category.objects.filter(is_active=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
                'autocomplete': 'family-name'
            }),
        }

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        """Validate passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data


class CompleteProfileForm(forms.ModelForm):
    """
    Complete profile form - collects remaining profile information after email verification.
    
    Fields: phone, country, document (ID/passport)
    """
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254 XXX XXX XXX',
            'autocomplete': 'tel'
        }),
        help_text='Enter your phone number with country code'
    )
    country = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kenya',
            'autocomplete': 'country-name'
        })
    )
    document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text='Upload ID or Passport (optional)'
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'country', 'document']

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        # Basic validation - ensure it starts with + and contains digits
        if phone and not phone.startswith('+'):
            raise forms.ValidationError('Phone number must start with country code (e.g., +254)')
        return phone
