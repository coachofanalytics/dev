"""Forms for the Document Processing portal."""
from django import forms
from django.core.validators import RegexValidator

from .models import (
    Application,
    SERVICE_CHOICES,
    REASON_CHOICES,
    DISTRICT_CHOICES,
    SERVICE_ID_RULES,
)


class ApplicationStep1Form(forms.ModelForm):
    """Step 1: personal and service information."""

    class Meta:
        model = Application
        fields = [
            "service",
            "first_name",
            "last_name",
            "id_number",
            "district",
            "sub_county",
            "reason",
        ]
        widgets = {
            "service": forms.Select(attrs={"class": "dp-input"}),
            "first_name": forms.TextInput(attrs={"class": "dp-input"}),
            "last_name": forms.TextInput(attrs={"class": "dp-input"}),
            "id_number": forms.TextInput(attrs={"class": "dp-input"}),
            "district": forms.Select(attrs={"class": "dp-input"}),
            "sub_county": forms.Select(attrs={"class": "dp-input"}),
            "reason": forms.Select(attrs={"class": "dp-input"}),
        }
        labels = {
            "service": "Service",
            "first_name": "First name",
            "last_name": "Last name",
            "id_number": "ID number",
            "district": "District",
            "sub_county": "Sub-county",
            "reason": "Reason for request",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sub-county depends on the chosen district; keep it optional in HTML.
        self.fields["sub_county"].required = False
        if self.data.get("district"):
            from .models import SUBCOUNTY_MAP
            options = SUBCOUNTY_MAP.get(self.data.get("district"), [])
            self.fields["sub_county"].choices = [("", "Select sub-county")] + [
                (o, o) for o in options
            ]
        else:
            self.fields["sub_county"].choices = [("", "Select district first")]

    def clean_id_number(self):
        service = self.cleaned_data.get("service")
        id_number = self.cleaned_data.get("id_number", "").strip()
        rule = SERVICE_ID_RULES.get(service)
        if not rule:
            return id_number
        if rule["digits"] and not id_number.isdigit():
            raise forms.ValidationError(
                f"{rule['label']} must contain only digits."
            )
        if not (rule["min"] <= len(id_number) <= rule["max"]):
            raise forms.ValidationError(
                f"{rule['label']} must be between "
                f"{rule['min']} and {rule['max']} characters."
            )
        return id_number

    def clean(self):
        cleaned = super().clean()
        district = cleaned.get("district")
        sub_county = cleaned.get("sub_county")
        if district and not sub_county:
            self.add_error("sub_county", "Please select a sub-county.")
        return cleaned


class ApplicationSummaryForm(forms.Form):
    """Step 2: notification preferences + certification."""

    notify_by_phone = forms.BooleanField(required=False, label="Notify me by phone")
    phone = forms.CharField(
        required=False,
        max_length=30,
        label="Phone number",
        validators=[
            RegexValidator(
                r"^\+?\d{9,15}$",
                "Enter a valid phone number (9-15 digits).",
            )
        ],
    )
    notify_by_email = forms.BooleanField(required=False, label="Notify me by email")
    email = forms.EmailField(required=False, label="Email address")
    certified = forms.BooleanField(
        required=True,
        label="I certify that the information provided is accurate and up to date.",
        error_messages={"required": "You must certify the information to continue."},
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("notify_by_phone") and not cleaned.get("phone"):
            self.add_error("phone", "Enter a phone number for notifications.")
        if cleaned.get("notify_by_email") and not cleaned.get("email"):
            self.add_error("email", "Enter an email address for notifications.")
        return cleaned


class PaymentMethodForm(forms.Form):
    """Payment method selection + payer phone for mobile money."""

    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("airtel", "Airtel Money"),
        ("card", "Debit/Credit Card"),
        ("cash", "Cash/Agent"),
        ("bank", "Bank Account"),
    ]
    method = forms.ChoiceField(choices=METHOD_CHOICES, widget=forms.RadioSelect)
    payer_phone = forms.CharField(
        required=False,
        max_length=30,
        label="Mobile money phone number",
        validators=[
            RegexValidator(
                r"^\+?\d{9,15}$",
                "Enter a valid phone number (9-15 digits).",
            )
        ],
    )
    transaction_id = forms.CharField(
        required=False,
        max_length=100,
        label="Transaction reference (optional)",
    )

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        if method in ("mtn", "airtel") and not cleaned.get("payer_phone"):
            self.add_error(
                "payer_phone",
                "Enter the mobile money phone number used to pay.",
            )
        return cleaned

        