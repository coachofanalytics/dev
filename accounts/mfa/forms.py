"""
Forms for MFA functionality.
"""

from django import forms


class MFASetupForm(forms.Form):
    """Form for MFA setup verification."""

    token = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "autocomplete": "off",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "maxlength": "6",
            }
        ),
        label="Verification Code",
        help_text="Enter the 6-digit code from your authenticator app",
    )

    def clean_token(self):
        """Validate token is 6 digits."""
        token = self.cleaned_data.get("token")
        if not token or not token.isdigit() or len(token) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit code")
        return token


class MFAVerifyForm(forms.Form):
    """Form for MFA login verification."""

    token = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "autocomplete": "off",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "maxlength": "6",
                "autofocus": True,
            }
        ),
        label="Verification Code",
        help_text="Enter the 6-digit code from your authenticator app",
    )

    def clean_token(self):
        """Validate token is 6 digits."""
        token = self.cleaned_data.get("token")
        if not token or not token.isdigit() or len(token) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit code")
        return token


class BackupCodeForm(forms.Form):
    """Form for backup code verification."""

    code = forms.CharField(
        max_length=16,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "XXX-XXX-XXX-XXX",
                "autocomplete": "off",
                "style": "text-transform: uppercase;",
            }
        ),
        label="Backup Code",
        help_text="Enter one of your backup codes",
    )

    def clean_code(self):
        """Validate and normalize backup code."""
        code = self.cleaned_data.get("code")
        if not code:
            raise forms.ValidationError("Please enter a backup code")

        # Remove spaces and dashes, convert to uppercase
        normalized = code.replace(" ", "").replace("-", "").upper()

        if len(normalized) != 12:
            raise forms.ValidationError("Please enter a valid backup code")

        return code  # Return original format for verification


class MFADisableForm(forms.Form):
    """Form for disabling MFA (requires password confirmation)."""

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
            }
        ),
        label="Password",
        help_text="Enter your password to confirm disabling MFA",
    )
